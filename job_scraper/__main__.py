from job_scraper.utils import build_linkedin_url
from job_scraper.scraper import LinkedInScraper

def main():
    url = input("Enter LinkedIn job search URL: ").strip()
    if not url:
        url = build_linkedin_url()
        # url = "https://www.linkedin.com/jobs/search/?keywords=Python&location=Lahore&geoId=104112529"
    # LinkedInScraper().scrape_jobs_with_requests(url)
    LinkedInScraper().scrape_jobs_with_webdriver(url)
    

if __name__ == "__main__":
    main()
