from scraper.utils import build_linkedin_url
from scraper.scraper import JobScraper, JobScraperPlaywright

def main():
    url = input("Enter LinkedIn job search URL: ").strip()
    if not url:
        url = build_linkedin_url()
        # url = "https://www.linkedin.com/jobs/search/?keywords=Python&location=Lahore&geoId=104112529"
    # JobScraper().scrape_jobs_with_requests(url)
    JobScraperPlaywright().scrape_jobs_with_webdriver(url)
    

if __name__ == "__main__":
    main()
