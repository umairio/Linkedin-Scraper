from cloudscraper import create_scraper
from bs4 import BeautifulSoup
import pandas as pd
from job_scraper.logger import logger
from job_scraper.utils import get_headers
import re
import time
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from playwright.sync_api import sync_playwright
from datetime import datetime
import asyncio
from playwright_stealth import Stealth


class LinkedInScraper:
    def __init__(self):
        self.session = create_scraper()
        self.headers = get_headers()

    def update_url_page(self, url: str, page_num: int) -> str:
        """
        Update the LinkedIn job search URL with a new 'start' value for pagination.
        LinkedIn uses 'start' (offset) instead of 'pageNum'.
        Example:
            https://www.linkedin.com/jobs/search/?keywords=python&start=0
            → https://www.linkedin.com/jobs/search/?keywords=python&start=25
        """
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        query["start"] = [str((page_num - 1) * 25)]

        query.pop("pageNum", None)

        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def get_job_cards(self, content):
        soup = BeautifulSoup(content, "html.parser")
        return soup.select(".base-card")

    def scrape_jobs_with_requests(self, url: str, max_pages: int = 10):
        headers = get_headers()
        jobs_found = 0
        df = pd.DataFrame()
        logger.info(f"Starting scrape from: {url}")

        for page in range(1, max_pages + 1):
            page_url = self.update_url_page(url, page)
            logger.debug(f"Fetching page {page}: {page_url}")
            try:
                r = self.session.get(page_url, headers=self.headers, timeout=15)
                r.raise_for_status()
            except Exception as e:
                logger.error(f"Request failed on page {page + 1}: {e}")
                break

            job_cards = self.get_job_cards(r.text)

            if not job_cards:
                logger.info(f"No more jobs found after page {page + 1}. Stopping.")
                break
                
            logger.info(f"Found {len(job_cards)} jobs on page {page + 1}")

            df = self.scrape_job_cards(job_cards, df)

            page += 1

            jobs_found += len(job_cards)
            logger.info(f"Scraped {jobs_found} jobs so far.")
            time.sleep(2)
        self.save_df(df)
        

    def scrape_job_cards(self, job_cards, df=pd.DataFrame()):
        jobs_found = 0
        if not job_cards:
            return df
        for _, card in enumerate(job_cards, 1):
            link = card.select_one("a")["href"] if card.select_one("a") else None
            if not link:
                continue

            if not link.startswith("https://"):
                link = f"https://www.linkedin.com{link}"

            # Extract Job ID
            match = re.search(r'/view/[^/]+-(\d+)', link)
            job_id = match.group(1) if match else None
            if not df.empty and job_id in df["id"].values:
                logger.info(f"Duplicate job ID found: {job_id}")
                continue
            job_data = {
                "id": job_id,
                "title": card.select_one(".base-search-card__title").get_text(strip=True) if card.select_one(".base-search-card__title") else None,
                "company": card.select_one(".base-search-card__subtitle").get_text(strip=True) if card.select_one(".base-search-card__subtitle") else None,
                "location": card.select_one(".job-search-card__location").get_text(strip=True) if card.select_one(".job-search-card__location") else None,
                "link": link,
                "date": card.select_one("time")["datetime"] if card.select_one("time") else None,
                "seniority": None,
                "employment_type": None,
                "industries": None,
                "description": None,
            }

            # Fetch job details page
            try:
                resp = self.session.get(link, headers=self.headers, timeout=15)
                resp.raise_for_status()
                job_soup = BeautifulSoup(resp.text, "html.parser")

                criteria = job_soup.select(".description__job-criteria-item")

                for item in criteria:
                    header = item.select_one(".description__job-criteria-subheader")
                    value = item.select_one(".description__job-criteria-text")
                    if not header or not value:
                        continue

                    header_text = header.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)

                    if "seniority" in header_text:
                        job_data["seniority"] = value_text
                    elif "employment type" in header_text:
                        job_data["employment_type"] = value_text
                    elif "job function" in header_text:
                        job_data["job_function"] = value_text
                    elif "industr" in header_text:  # matches "industry" or "industries"
                        job_data["industries"] = value_text

                # Job description
                desc_elem = job_soup.select_one(".description__text, .show-more-less-html__markup")
                job_data["description"] = desc_elem.get_text(separator="\n", strip=True) if desc_elem else None

            except Exception as e:
                logger.warning(e)
            
            jobs_found += 1
            logger.debug(f"Parsed job {jobs_found}: {job_data['title']} @ {job_data['company']}")
            if df.empty: df = pd.DataFrame(columns=job_data.keys())
            df.loc[len(df)] = job_data
            time.sleep(1)
        return df
    
    def safe_selector(self, selector):
        try:
            return self.page.query_selector(selector)
        except Exception as e:
            logger.error(e)
            return None

    def is_loading_visible(self, selector=".loader__icon-svg--small"):
        if el := self.page.query_selector(selector):
            return el.is_visible()
        return False

    def parse_total_jobs(self, text: str) -> int:
        """Extracts a clean integer job count from strings like '5,000+', '5,000 jobs', etc."""
        if not text:
            return 0
        text = text.strip()
        match = re.search(r'(\d[\d,]*)', text)
        if match:
            return int(match.group(1).replace(',', ''))
        return 10000

    def close_auth_page(self):
        if auth := self.safe_selector(".modal__overlay--visible > section:nth-child(1) > button:nth-child(1) > icon:nth-child(1) > svg:nth-child(1)"):
            auth.click()

    def scrape_cards_with_driver(self, url):
        with Stealth().use_sync(sync_playwright()) as p:
            cards = []
            browser = p.firefox.launch(headless=False)
            self.page = browser.new_page()
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(3_000)
            self.close_auth_page()
            total_jobs = self.safe_selector(".results-context-header__job-count")
            total_jobs.click()
            total_job = self.parse_total_jobs(total_jobs.text_content())
            logger.info(f"{total_job} jobs Remaining...")
            try:
                while len(cards) < total_job:
                    self.close_auth_page()
                    self.page.keyboard.press("End")
                    self.page.wait_for_timeout(5_000)

                    if button := self.page.query_selector(".infinite-scroller__show-more-button.infinite-scroller__show-more-button--visible"):
                        logger.info("Found show more button, clicking it...")
                        button.click()

                    if self.is_loading_visible():
                        logger.info("Waiting for loading to finish...")
                        self.page.wait_for_timeout(5_000)
                        self.page.keyboard.press("End")

                        if self.is_loading_visible():
                            self.page.reload(timeout=5_000)
                            logger.warning("Loading took too long, reloading page...")
                            self.safe_selector(".results-context-header__job-count").click()
                            self.page.keyboard.press("End")

                    # cards = self.page.query_selector_all(".base-card")
                    cards = self.get_job_cards(self.page.content())
                    self.safe_selector(".results-context-header__job-count").click()

                    logger.debug(f"Found {len(cards)}/{total_job} job cards")
                    if self.has_all_jobs_loaded(): break
            except Exception as e:
                logger.error(e)
            # cards = self.get_job_cards(self.page.content())
            logger.success(f"Found {len(cards)} job cards")
            if "browser" in locals(): browser.close()
            return cards

    def has_all_jobs_loaded(self):
        selectors = [
            "text=You've viewed all jobs for this search",
            "div.see-more-jobs__viewed-all",
            "div.see-more-jobs__viewed-all p.inline-notification__text"
        ]

        for selector in selectors:
            try:
                el = self.page.locator(selector)
                if el.count() > 0 and el.first.is_visible():
                    logger.info("All jobs loaded.")
                    return True
            except Exception:
                continue
        return False

    def save_df(self, df=pd.DataFrame()):
        if df.empty:
            logger.warning("No jobs found to save.")
        else:
            ddf = df.drop_duplicates(subset=["id"])
            logger.success(f"Scraping completed. Total unique jobs found: {len(ddf)}, duplicates removed: {len(df) - len(ddf)}")
            ddf.to_csv("jobs.csv", index=False)
            ddf.to_json("jobs.json", orient="records")
            logger.success(f"✅ Saved {len(ddf)} jobs → jobs.csv & jobs.json")

        # return df
    
    def scrape_jobs_with_webdriver(self, url):
        cards = self.scrape_cards_with_driver(url)
        df = self.scrape_job_cards(cards)
        self.save_df(df)