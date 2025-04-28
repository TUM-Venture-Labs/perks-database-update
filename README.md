# perks-database-update

This is a repo to automate the update of the perks database stored in airtable.

## Current Approach

*   Airtable is used as the data source for perks.
*   A Python script (`scrape_analyze.py`) uses Firecrawl to scrape web pages and OpenAI (GPT-4o) to perform basic analysis/summarization.

## Setup

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in the root directory and add your API keys:
    ```
    FIRECRAWL_API_KEY='your_firecrawl_api_key'
    OPENAI_API_KEY='your_openai_api_key'
    ```

## Usage

To scrape and analyze a single URL:

```bash
python scrape_analyze.py <url_to_scrape>
```

Example:

```bash
python scrape_analyze.py https://example.com
```