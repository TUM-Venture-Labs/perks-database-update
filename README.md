# perks-database-update

This is a repo to automate the update of the perks database stored in Airtable.

## Repository Programs

This repository contains two main programs:

### 1. scrape_analyze.py

A single-URL scraper and analyzer.

* Uses Firecrawl to scrape web pages
* Uses OpenAI (GPT-4o) to perform basic analysis/summarization
* Processes one URL at a time

### 2. perks_updater.py

A comprehensive Airtable perks database updater.

```
🔍 PERKS DATABASE UPDATER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROCESS FLOW:
  1. Fetch records from Airtable perks database
  2. Verify URL status (active/inactive) for each perk
  3. Update status in Airtable for any changed perks
  4. Scrape active websites using two methods:
     - BeautifulSoup + GPT-4o extraction
     - Perplexity API with subpage crawling
  5. Combine results from both scraping methods
  6. Update Airtable with the combined perk information
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTED DATA:
  • Provider description
  • What you get
  • How to get it
  • Monetary value
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Setup

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running scrape_analyze.py

1. Create a `.env` file in the root directory and add your API keys:
   ```
   FIRECRAWL_API_KEY='your_firecrawl_api_key'
   OPENAI_API_KEY='your_openai_api_key'
   ```

2. To scrape and analyze a single URL:
   ```bash
   python scrape_analyze.py <url_to_scrape>
   ```

   Example:
   ```bash
   python scrape_analyze.py https://example.com
   ```

## Running perks_updater.py

1. Create a `config.py` file in the main directory with the following API keys:
   ```python
   # API Keys
   OPENAI_API_KEY = "your_openai_api_key"
   PERPLEXITY_API_KEY = "your_perplexity_api_key"
   
   # Airtable configuration
   AIRTABLE_API_KEY = "your_airtable_api_key"
   AIRTABLE_BASE_ID = "your_airtable_base_id"
   AIRTABLE_TABLE_NAME = "your_airtable_table_name"
   ```

2. Run the perks updater:
   ```bash
   python perks_updater.py
   ```

## Requirements

Both programs use the same dependencies, which are listed in `requirements.txt`.

Main dependencies include:
- OpenAI API
- Perplexity API
- Airtable
- BeautifulSoup
- Requests
- Python-dotenv