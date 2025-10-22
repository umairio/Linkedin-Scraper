# Job Scraper

A Python tool to scrape job listings from LinkedIn.

## Installation

### From Source
1. Clone or download the repository.
2. Navigate to the project directory.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install firefox --wth-deps
   ```
4. Run the scraper:
   ```bash
   python -m job_scraper
   ```


## Usage

The tool will prompt you to enter a LinkedIn job search URL or build one interactively.

You will need to provide LinkedIn cookies for authentication. The tool will guide you through pasting them.

Scraped jobs are saved to `jobs.csv` and `jobs.json`.

## Requirements

- Python 3.8+
- LinkedIn account (for cookies)

## Cross-Platform

This package works on Windows, Ubuntu, and Android (with Termux).

## License

MIT
