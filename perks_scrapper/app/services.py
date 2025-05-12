# Placeholder for business logic and service integrations (Firecrawl, Exa, OpenAI, Airtable) 

import os
import json
from typing import List, Optional, Tuple, Dict
import asyncio

from dotenv import load_dotenv
from pydantic import ValidationError
from openai import OpenAI, AsyncOpenAI
from firecrawl import FirecrawlApp
from exa_py import Exa
import requests # Using requests for basic Airtable interaction

from .models import (
    PerkDetails,
    ScrapingDecision,
    AirtableRecord,
    AggregatedPerkInfo
)
from .prompts import (
    DEV_MSG_EXTRACT_PERK,
    USER_MSG_EXTRACT_PERK_TEMPLATE,
    DEV_MSG_DECIDE_NEXT_STEP,
    USER_MSG_DECIDE_NEXT_STEP_TEMPLATE,
    DEV_MSG_AGGREGATE_INFO,
    USER_MSG_AGGREGATE_INFO_TEMPLATE,
)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_URL_FIELD = os.getenv("AIRTABLE_URL_FIELD", "URL") # Default field names
AIRTABLE_DESCRIPTION_FIELD = os.getenv("AIRTABLE_DESCRIPTION_FIELD", "Description")

MAX_SCRAPE_DEPTH = 3
OPENAI_MODEL = "gpt-4o" # Using gpt-4o as gpt-4.1 is not a valid model ID

# --- API Clients ---
try:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    # Using AsyncOpenAI for potential parallel calls later
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY not found in environment variables.")
    firecrawl_client = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY not found in environment variables.")
    exa_client = Exa(api_key=EXA_API_KEY)

    if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME]):
        raise ValueError("Airtable configuration (API Key, Base ID, Table Name) missing in environment variables.")
    AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    airtable_headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

except ValueError as e:
    print(f"Error initializing clients: {e}")
    # Handle initialization errors appropriately (e.g., exit, raise)
    raise SystemExit(f"Initialization failed: {e}")

# Placeholder for business logic and service integrations (Firecrawl, Exa, OpenAI, Airtable)

async def get_airtable_record(record_id: str) -> Optional[AirtableRecord]:
    """Fetches a specific record from Airtable by its ID."""
    url = f"{AIRTABLE_API_URL}/{record_id}"
    try:
        response = requests.get(url, headers=airtable_headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        record_data = response.json()
        fields = record_data.get('fields', {})
        return AirtableRecord(
            id=record_data['id'],
            url=fields.get(AIRTABLE_URL_FIELD),
            current_description=fields.get(AIRTABLE_DESCRIPTION_FIELD)
            # Map other fields here if needed
        )
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Airtable record {record_id}: {e}")
    except ValidationError as e:
        print(f"Error validating Airtable data for {record_id}: {e}")
    except KeyError as e:
        print(f"Missing expected key in Airtable response for {record_id}: {e}")
    return None

async def update_airtable_record(record_id: str, data_to_update: Dict):
    """Updates specific fields of an Airtable record."""
    url = f"{AIRTABLE_API_URL}/{record_id}"
    payload = json.dumps({"fields": data_to_update})
    try:
        response = requests.patch(url, headers=airtable_headers, data=payload)
        response.raise_for_status()
        print(f"Successfully updated Airtable record {record_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error updating Airtable record {record_id}: {e}")
        return False

async def scrape_url(url: str) -> Optional[dict]:
    """Scrapes a single URL using Firecrawl."""
    print(f"Scraping URL: {url}")
    try:
        # Requesting markdown and html (for link extraction)
        scrape_params = {
            'pageOptions': {
                 # 'onlyMainContent': True, # Example option, uncomment if needed
            },
            'extractorOptions': { # Specify formats within extractorOptions for older versions?
                'mode': 'markdown', # Assuming mode sets the primary format
                'outputFormat': 'markdown' # Explicitly asking? Or maybe just formats key?
                # Let's try just passing formats directly in params based on some examples
            },
            # Trying simpler params structure based on scrape examples
            'formats': ['markdown', 'html']

        }
        scrape_result = firecrawl_client.scrape_url(url, params=scrape_params)

        # Check if scrape was successful and returned expected data
        if scrape_result and 'markdown' in scrape_result and 'html' in scrape_result:
            return scrape_result
        else:
            print(f"Warning: Incomplete scrape result for {url}. Missing markdown or html.")
            return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

async def search_web(query: str) -> Optional[List[Dict]]:
    """Performs a web search using Exa."""
    print(f"Searching web with Exa: '{query}'")
    try:
        # Using search_and_contents to get snippets
        search_results = exa_client.search_and_contents(query, num_results=5, use_autoprompt=True)
        return search_results.results
    except Exception as e:
        print(f"Error searching web with Exa: {e}")
        return None

async def extract_perk_details_from_text(content: str, url: str) -> Optional[PerkDetails]:
    """Uses OpenAI to extract PerkDetails from text."""
    print(f"Extracting perk details from: {url}")
    user_message = USER_MSG_EXTRACT_PERK_TEMPLATE.format(url=url, scraped_content=content[:4000]) # Limit context size

    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": DEV_MSG_EXTRACT_PERK},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"} # Request JSON output
            # If using older OpenAI versions or need Pydantic integration, use the `.responses.parse` method shown in custom instructions
        )
        response_content = response.choices[0].message.content
        if response_content:
            # Parse the JSON string into a dictionary
            details_dict = json.loads(response_content)
            # Validate with Pydantic model
            perk_details = PerkDetails(**details_dict)
            perk_details.source_urls.append(url) # Add source URL
            return perk_details
        else:
            print(f"OpenAI did not return content for perk extraction from {url}.")
            return None

    except json.JSONDecodeError as e:
        print(f"Error decoding OpenAI JSON response for perk extraction: {e}. Response: {response_content}")
        return None
    except ValidationError as e:
        print(f"Error validating OpenAI response against PerkDetails model: {e}. Response: {response_content}")
        return None
    except Exception as e:
        print(f"Error calling OpenAI for perk extraction ({url}): {e}")
        return None


async def decide_next_action(
    original_description: Optional[str],
    gathered_info: List[PerkDetails],
    last_scraped_content: str,
    last_scraped_url: str,
    current_depth: int,
    search_performed: bool
) -> Optional[ScrapingDecision]:
    """Uses OpenAI to decide the next step in the process."""
    print(f"Deciding next action. Depth: {current_depth}, Search performed: {search_performed}")
    gathered_info_json = json.dumps([p.model_dump(exclude_none=True) for p in gathered_info], indent=2)

    user_message = USER_MSG_DECIDE_NEXT_STEP_TEMPLATE.format(
        original_description=original_description or "Not available",
        gathered_info_json=gathered_info_json,
        last_scraped_content=last_scraped_content[:4000], # Limit context
        last_scraped_url=last_scraped_url,
        current_depth=current_depth,
        max_depth=MAX_SCRAPE_DEPTH,
        search_performed=search_performed
    )

    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": DEV_MSG_DECIDE_NEXT_STEP},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        if response_content:
            decision_dict = json.loads(response_content)
            decision = ScrapingDecision(**decision_dict)
            print(f"Decision: {decision.action}, Reason: {decision.reasoning}")
            return decision
        else:
            print("OpenAI did not return content for decision making.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decoding OpenAI JSON response for decision: {e}. Response: {response_content}")
        return None
    except ValidationError as e:
        print(f"Error validating OpenAI response against ScrapingDecision model: {e}. Response: {response_content}")
        return None
    except Exception as e:
        print(f"Error calling OpenAI for decision making: {e}")
        return None

async def aggregate_information(
    initial_record: AirtableRecord,
    scraped_perks: List[PerkDetails],
    search_results: Optional[List[Dict]]
) -> Optional[PerkDetails]:
    """Uses OpenAI to aggregate all collected information."""
    print("Aggregating all collected information...")

    initial_data_json = initial_record.model_dump_json(indent=2) if initial_record else "{}"
    scraped_data_list_json = json.dumps([p.model_dump(exclude_none=True) for p in scraped_perks], indent=2)
    search_results_json = json.dumps(search_results, indent=2) if search_results else "[]"

    user_message = USER_MSG_AGGREGATE_INFO_TEMPLATE.format(
        initial_data_json=initial_data_json,
        scraped_data_list_json=scraped_data_list_json,
        search_results_json=search_results_json
    )

    try:
        response = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": DEV_MSG_AGGREGATE_INFO},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        if response_content:
            aggregated_dict = json.loads(response_content)
            aggregated_perk = PerkDetails(**aggregated_dict)
            # Combine source URLs from all scraped data
            all_source_urls = set(url for perk in scraped_perks for url in perk.source_urls)
            aggregated_perk.source_urls = list(all_source_urls)
            print("Aggregation complete.")
            return aggregated_perk
        else:
            print("OpenAI did not return content for aggregation.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decoding OpenAI JSON response for aggregation: {e}. Response: {response_content}")
        return None
    except ValidationError as e:
        print(f"Error validating OpenAI response against PerkDetails model during aggregation: {e}. Response: {response_content}")
        return None
    except Exception as e:
        print(f"Error calling OpenAI for aggregation: {e}")
        return None


# --- Main Orchestration Logic ---

async def process_perk_update(record_id: str) -> AggregatedPerkInfo:
    """Orchestrates the entire process for a single Airtable record."""
    print(f"\n--- Starting update process for Airtable record: {record_id} ---")
    initial_record = await get_airtable_record(record_id)

    if not initial_record or not initial_record.url:
        msg = f"Could not fetch initial record or URL missing for {record_id}."
        print(msg)
        return AggregatedPerkInfo(record_id=record_id, initial_url=None, updated_details=PerkDetails(), status='error', message=msg)

    current_url = str(initial_record.url)
    all_scraped_details: List[PerkDetails] = [] # Store details from all successful scrapes
    visited_urls = set()
    search_results: Optional[List[Dict]] = None
    search_performed = False
    tasks = [] # For potential parallel operations

    for depth in range(MAX_SCRAPE_DEPTH + 1): # +1 to allow initial scrape at depth 0
        if not current_url or current_url in visited_urls:
            print(f"Skipping already visited or invalid URL: {current_url}")
            break # Stop if URL is invalid or visited

        visited_urls.add(current_url)
        print(f"\n[Depth {depth}] Processing URL: {current_url}")

        scraped_data = await scrape_url(current_url)
        if not scraped_data or 'markdown' not in scraped_data:
            print(f"Failed to scrape or get markdown for {current_url}. Stopping crawl for this path.")
            break # Stop this path if scraping fails

        # Attempt to extract structured info from the current page
        extracted_details = await extract_perk_details_from_text(scraped_data['markdown'], current_url)
        if extracted_details:
            all_scraped_details.append(extracted_details)
            print(f"Successfully extracted details from {current_url}")
        else:
            print(f"Could not extract structured details from {current_url}")

        # Decide next step (only if not at max depth)
        if depth < MAX_SCRAPE_DEPTH:
            decision = await decide_next_action(
                original_description=initial_record.current_description,
                gathered_info=all_scraped_details,
                last_scraped_content=scraped_data['markdown'],
                last_scraped_url=current_url,
                current_depth=depth,
                search_performed=search_performed
            )

            if not decision:
                print("Failed to get decision from AI. Stopping.")
                break

            if decision.action == 'scrape_further' and decision.relevant_urls_to_scrape:
                # Find the first valid, unvisited URL to scrape next
                next_url_found = False
                for next_url in decision.relevant_urls_to_scrape:
                    str_next_url = str(next_url)
                    if str_next_url not in visited_urls:
                        current_url = str_next_url
                        next_url_found = True
                        print(f"AI decided to scrape further: {current_url}")
                        break # Go to the next iteration with this URL
                if not next_url_found:
                    print("AI suggested scraping further, but no valid unvisited URLs provided. Stopping crawl.")
                    break
            elif decision.action == 'search_web' and decision.search_query and not search_performed:
                print(f"AI decided to search web. Query: '{decision.search_query}'")
                # Run search in parallel (or could be sequential)
                search_results = await search_web(decision.search_query)
                search_performed = True
                # After search, we might need another decision or just proceed to aggregation
                # For simplicity here, we'll proceed to aggregation after the loop finishes
                # or if the decision is 'aggregate'
                print("Continuing scraping process after initiating web search.")
                # Need to decide what URL to process next if search is done in parallel
                # For now, let's assume we stop scraping this path after search
                break

            elif decision.action == 'aggregate':
                print("AI decided to aggregate information now.")
                break # Exit loop to aggregate
            elif decision.action == 'stop':
                print("AI decided to stop the process.")
                break # Exit loop
            else:
                 # Handle cases like scrape_further with no URLs, or unexpected actions
                 print(f"AI returned action '{decision.action}' which requires no further scraping action now. Proceeding to aggregation.")
                 break
        else:
            print(f"Reached max depth ({MAX_SCRAPE_DEPTH}). Moving to aggregation.")
            break # Reached max depth

    # Aggregation Step
    print("\n--- Aggregating final results ---")
    final_perk_details = await aggregate_information(
        initial_record=initial_record,
        scraped_perks=all_scraped_details,
        search_results=search_results
    )

    if final_perk_details:
        # Prepare data for Airtable update
        update_payload = {}
        if final_perk_details.description:
            update_payload[AIRTABLE_DESCRIPTION_FIELD] = final_perk_details.description
        # Add other fields to update based on extracted details and env var config
        # e.g., if AIRTABLE_FUNDING_FIELD is set:
        # funding_field = os.getenv("AIRTABLE_FUNDING_FIELD")
        # if funding_field and final_perk_details.funding_or_credits:
        #    update_payload[funding_field] = final_perk_details.funding_or_credits

        if update_payload:
            print(f"Attempting to update Airtable record {record_id} with: {update_payload}")
            success = await update_airtable_record(record_id, update_payload)
            status = 'updated' if success else 'needs_review'
            message = "Update successful." if success else "Failed to update Airtable record."
        else:
            status = 'needs_review'
            message = "Aggregation complete, but no specific fields identified for update."

        return AggregatedPerkInfo(
            record_id=record_id,
            initial_url=initial_record.url,
            updated_details=final_perk_details,
            status=status,
            message=message
        )
    else:
        msg = f"Failed to aggregate information for {record_id}."
        print(msg)
        return AggregatedPerkInfo(
            record_id=record_id,
            initial_url=initial_record.url,
            updated_details=PerkDetails(), # Empty details
            status='error',
            message=msg
        ) 