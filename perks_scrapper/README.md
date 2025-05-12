# Perks Scraper AI Agent

This project implements an AI agent designed to automate the process of updating startup perk information stored in an Airtable database. It uses web scraping and AI analysis to keep perk details like descriptions, funding info, deadlines, and eligibility criteria up-to-date.

## Workflow

The agent performs the following steps for a given perk record (identified by its Airtable record ID):

1.  **Fetch Initial Data**: Retrieves the perk's current URL and description from the specified Airtable base and table.
2.  **Scrape Starting URL**: Uses Firecrawl to scrape the content (Markdown and HTML) from the initial URL.
3.  **Initial Analysis**: Extracts structured perk details (`PerkDetails` model) from the scraped content using OpenAI (`gpt-4o` with JSON mode).
4.  **Iterative Crawling & Analysis (Depth-Limited):**
    *   **Decision Making**: An OpenAI call (`ScrapingDecision` model) analyzes the gathered information, the original description, and the content of the last scraped page to decide the next action:
        *   `scrape_further`: If potentially relevant links are found on the current page and the depth limit (default: 3) is not reached, scrape one of those links.
        *   `search_web`: If more information is needed and a web search hasn't been performed yet, use Exa AI to search for the perk details. This is done only once per record.
        *   `aggregate`: If enough information seems to be gathered or the process should conclude.
        *   `stop`: If the AI decides no further action is needed.
    *   **Scraping/Extraction**: If scraping further, the process repeats for the new URL.
5.  **Aggregation**: Once crawling stops (due to depth limit, AI decision, or errors), another OpenAI call (`PerkDetails` model) synthesizes all information collected from initial data, all scraped pages, and the web search (if performed) into a single, consolidated set of perk details.
6.  **Update Airtable**: Compares the aggregated description (and potentially other configured fields) with the original. If changes are detected, it updates the corresponding fields in the Airtable record.
7.  **Return Result**: Returns the final aggregated information (`AggregatedPerkInfo` model), including the update status.

## Technology Stack

*   **Python**: 3.11+
*   **Framework**: FastAPI
*   **Web Scraping**: Firecrawl (`firecrawl-py`)
*   **Web Search**: Exa AI (`exa-py`)
*   **AI Analysis & Structured Output**: OpenAI API (`openai` SDK, `gpt-4o` model)
*   **Data Validation**: Pydantic V2
*   **Dependency Management**: Poetry
*   **Environment Variables**: `python-dotenv`
*   **Database Interaction**: `requests` (for Airtable REST API)

## Project Structure

```
perks_scrapper/
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI application, endpoints
│   ├── models.py       # Pydantic models for data structures
│   ├── prompts.py      # Prompts and developer messages for OpenAI
│   └── services.py     # Core logic, API client interactions, orchestration
├── .env              # Environment variables (API keys, Airtable config) - !! GITIGNORE !!
├── pyproject.toml    # Poetry configuration and dependencies
└── README.md         # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd perks_scrapper
    ```

2.  **Install Poetry:** (If you don't have it already)
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```
    *(Refer to the official [Poetry documentation](https://python-poetry.org/docs/#installation) for other installation methods)*

3.  **Install Dependencies:**
    ```bash
    poetry install
    ```

4.  **Configure Environment Variables:**
    *   Create a `.env` file in the `perks_scrapper` directory (root of the project).
    *   Copy the contents from the example below and replace the placeholder values with your actual credentials and Airtable details.

    ```dotenv
    # .env file content
    OPENAI_API_KEY="your_openai_api_key"
    FIRECRAWL_API_KEY="your_firecrawl_api_key"
    EXA_API_KEY="your_exa_api_key"

    AIRTABLE_API_KEY="your_airtable_api_key"
    AIRTABLE_BASE_ID="your_airtable_base_id"
    AIRTABLE_TABLE_NAME="YourPerksTableName"
    AIRTABLE_URL_FIELD="URLFieldName"                 # Name of the column containing the starting URL
    AIRTABLE_DESCRIPTION_FIELD="DescriptionFieldName" # Name of the column containing the perk description to update
    # Optional: Add other field names if you want to update them
    # AIRTABLE_FUNDING_FIELD="FundingFieldName"
    # AIRTABLE_DURATION_FIELD="DurationFieldName"
    # AIRTABLE_DEADLINE_FIELD="DeadlineFieldName"
    ```

## Running the Application

1.  **Activate the virtual environment:**
    ```bash
    poetry shell
    ```

2.  **Start the FastAPI server:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `--reload`: Automatically restarts the server when code changes are detected (useful for development).

3.  **Access the API:**
    *   The API documentation (Swagger UI) will be available at [http://localhost:8000/docs](http://localhost:8000/docs).
    *   The root endpoint is at [http://localhost:8000/](http://localhost:8000/).

## Usage

Send a POST request to the `/update-perk` endpoint with a JSON body containing the Airtable record ID you want to process:

**Example Request (using `curl`):**

```bash
curl -X POST "http://localhost:8000/update-perk" \
     -H "Content-Type: application/json" \
     -d '{
           "airtable_record_id": "recXXXXXXXXXXXXXX" # Replace with a valid record ID from your table
         }'
```

**Example Response (Success):**

```json
{
  "record_id": "recXXXXXXXXXXXXXX",
  "initial_url": "https://example-perk.com/program",
  "updated_details": {
    "name": "Example Perk Program",
    "description": "Updated description summarizing the benefits...",
    "funding_or_credits": "$10,000 AWS Credits",
    "duration": "12 months",
    "application_deadline": "2024-12-31",
    "eligibility_criteria": "Early-stage startups with less than $1M funding.",
    "source_urls": [
      "https://example-perk.com/program",
      "https://example-perk.com/details"
    ]
  },
  "status": "updated",
  "message": "Update successful."
}
```

**Example Response (Needs Review / Error):**

```json
{
  "record_id": "recYYYYYYYYYYYYYY",
  "initial_url": "https://another-perk.com",
  "updated_details": { /* ... details found ... */ },
  "status": "needs_review",
  "message": "Aggregation complete, but no specific fields identified for update." 
}
// Or an error status/message if something failed catastrophically
```

## Notes & Considerations

*   **Error Handling**: Basic error handling is included, but robust production systems would require more comprehensive logging and error management.
*   **Airtable Rate Limits**: Be mindful of Airtable API rate limits (typically 5 requests per second per base). If processing many records, implement rate limiting or batching.
*   **Long-Running Tasks**: The current implementation runs the process synchronously within the API request. For production, consider using background task queues (like Celery, RQ, or Arq) to handle the potentially long-running scraping and analysis process, preventing API timeouts.
*   **HTML Link Extraction**: The current implementation relies on the AI (`ScrapingDecision`) to identify relevant links. A more robust approach could involve parsing the HTML (`scraped_data['html']`) using libraries like `BeautifulSoup` to extract `<a>` tags and then filtering them before or during the AI decision step.
*   **Cost**: Running web scrapes and multiple GPT-4o calls per record can incur costs. Monitor your API usage.
*   **Security**: Ensure your `.env` file is never committed to version control.
