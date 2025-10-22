from urllib.parse import urlencode, quote_plus
from job_scraper.logger import logger
from fake_useragent import UserAgent
from job_scraper import WORKPLACE_TYPES, EXPERIENCE_LEVELS, JOB_TYPES, TIME_POSTED, COOKIE


def prompt_selection(title: str, options: dict, allow_empty=True):
    """Show options and return selected LinkedIn codes."""
    print(f"\n{title}")
    for key, (label, _) in options.items():
        print(f"  {key}. {label}")
    user_input = input("Enter numbers (comma separated, or leave empty for all): ").strip()

    if not user_input and allow_empty:
        return None

    selected = [x.strip() for x in user_input.split(",")]
    codes = []
    for s in selected:
        if s in options:
            codes.append(options[s][1])
        else:
            logger.warning(f"Ignored invalid option: {s}")

    return codes if codes else None


def build_linkedin_url():
    logger.info("=== LinkedIn Job Search URL Builder ===")

    base_url = "https://www.linkedin.com/jobs/search/?"

    keywords = input("🔍 Enter job keywords (e.g., Data Scientist): ").strip()
    location = input("📍 Enter location (default=Worldwide): ").strip() or "Worldwide"

    work_type = prompt_selection("🏠 Workplace Type", WORKPLACE_TYPES)
    experience = prompt_selection("📍 Experience Level", EXPERIENCE_LEVELS)
    job_type = prompt_selection("💼 Job Type", JOB_TYPES)
    time_posted = prompt_selection("⏰ Time Posted", TIME_POSTED)

    params = {
        "keywords": keywords,
        "location": location
    }

    if work_type:
        params["f_WT"] = ",".join(work_type)
    if experience:
        params["f_E"] = ",".join(experience)
    if job_type:
        params["f_JT"] = ",".join(job_type)
    if time_posted and any(time_posted):
        params["f_TPR"] = ",".join(time_posted)

    url = base_url + urlencode(params, quote_via=quote_plus)
    print(f"\n✅ Generated LinkedIn URL:\n{url}\n")
    return url


def parse_cookies(raw_text: str) -> str:
    """
    Normalize cookies pasted from browser, cookie editors, or exported CSV.
    Converts them to 'key=value; key2=value2' format for HTTP headers.
    """
    text = raw_text.strip().replace('"', '').replace("'", "")
    cookies = {}

    # Case 1: Already formatted (key=value; key2=value2)
    if ";" in text and "=" in text and "\t" not in text:
        return text.strip()

    # Split into lines and handle tab-separated cookie dumps
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        # Handle tab-separated exports
        if "\t" in line:
            parts = line.split("\t")
            if len(parts) >= 2:
                name, value = parts[0], parts[1]
                if name and value and not name.startswith("."):
                    cookies[name.strip()] = value.strip()
        # Handle normal key=value lines
        elif "=" in line:
            name, value = line.split("=", 1)
            if name and value:
                cookies[name.strip()] = value.strip()

    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def get_headers():
    lines = []
    # cookie_header = parse_cookies(raw_cookies)

    headers = {
        "User-Agent": UserAgent().random,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.linkedin.com/jobs/",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cookie": COOKIE,
    }
    return headers

def save_html(content: str, filename: str = "debug_page.html"):
    """Utility to save HTML content to a file for debugging."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Saved HTML content to {filename} for debugging.")