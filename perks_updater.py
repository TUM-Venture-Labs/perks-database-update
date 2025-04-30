import os
import json
import time

import config
from src.web_utils import scraper_beautiful_soup, access_page_with_cookies, is_fake_404, get_url_status_code
from src.airtable_utils import get_records, update_record, update_perks_info
from src.gpt_extractor import gpt_extract_info
from src.perplexity_extractor import extract_perk_info

# get perplexity API key and add it to the environment variables
perplexity_api_key = os.environ.get(config.PERPLEXITY_API_KEY)


def print_hello():
    """Print a concise and visually appealing explanation of the program."""
    
    print("\033[1;36m🔍 PERKS DATABASE UPDATER\033[0m")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1mPROCESS FLOW:\033[0m")
    print("  1. \033[1;32mFetch records\033[0m from Airtable perks database")
    print("  2. \033[1;32mVerify URL status\033[0m (active/inactive) for each perk")
    print("  3. \033[1;32mUpdate status in Airtable\033[0m for any changed perks")
    print("  4. \033[1;32mScrape active websites\033[0m using two methods:")
    print("     - BeautifulSoup + GPT-4o extraction")
    print("     - Perplexity API with subpage crawling")
    print("  5. \033[1;32mCombine results\033[0m from both scraping methods")
    print("  6. \033[1;32mUpdate Airtable\033[0m with the combined perk information")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1mEXTRACTED DATA:\033[0m")
    print("  • Provider description")
    print("  • What you get")
    print("  • How to get it")
    print("  • Monetary value")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\n\n")

# main status processing logic - loop over airtable rows
def process_records(records):

    perks_wo_link  = []
    perks_active   = []
    perks_inactive = []
    perks_updated  = []

    for record in records:
        fields = record.get('fields', {})
        perk_name = fields.get("Name")
        perk_url = fields.get("Link")
        current_status = fields.get("Status", "").lower()  # Default to empty string if missing

        # Case 1: No URL available
        if not perk_url:
            perks_wo_link.append(perk_name)
            continue
        
        # Case 1: No URL or it's an email (contains "@")
        if not perk_url or "@" in perk_url:
            perks_wo_link.append(perk_name)
            continue

        # Case 2: URL available but missing http
        if not perk_url.startswith(('http://', 'https://')):
            perk_url = 'http://' + perk_url

        print(f'\nProcessing perk: {perk_name}, at {perk_url}')

        # Check URL status
        status_code = get_url_status_code(perk_url)

        if status_code == 200:
            print(f"OK: Link is active (Status Code: {status_code})")

            if current_status != "active":
                
                update_record(record['id'], {"Status": "active"})
                perks_active.append(perk_name)
                perks_updated.append(perk_name)  # Only append if status changed

            perks_active.append(perk_name)

        elif status_code is None:
            print(f"ERROR: Failed to reach URL (Status Code: {status_code})")

            if current_status != "broken/expired":
                update_record(record['id'], {"Status": "broken/expired"})
                perks_updated.append(perk_name)

            perks_inactive.append(perk_name)

        else:
            print(f"ERROR: Link is inactive (Status Code: {status_code})")

            if current_status != "broken/expired":
                update_record(record['id'], {"Status": "broken/expired"})
                perks_updated.append(perk_name)

            perks_inactive.append(perk_name)
        
        time.sleep(1)  # polite rate limiting

    # Final summary
    print("Perks without link :", perks_wo_link)
    print("Perks active       :", perks_active)
    print("Perks inactive     :", perks_inactive)
    print("Perks updated      :", perks_updated)

    return perks_wo_link, perks_active, perks_inactive, perks_updated

# two methods for scraping are used which return dicts: this method combines both dicts into 1
def combine_perk_dicts(dict1, dict2):
    """
    Combine two perk information dictionaries into a single dictionary
    with the most comprehensive information.
    
    Args:
        dict1: First dictionary with perk information
        dict2: Second dictionary with perk information
        
    Returns:
        A combined dictionary with the best information from both sources
    """
    # Define standard keys for our output
    standard_keys = [
        "Brief description of the provider",
        "What you get",
        "How to get it",
        "Value"
    ]
    
    # Create mapping for possible variations in key names
    key_mapping = {
        "Brief description of the provider": ["Brief description of the provider", "Provider Description"],
        "What you get": ["What you get", "What You Get"],
        "How to get it": ["How to get it", "How To Get It"],
        "Value": ["Value", "Money Value"]
    }
    
    # Initialize result dictionary
    result = {}
    
    # Process each standard key
    for std_key in standard_keys:
        # Get all possible key variations
        possible_keys = key_mapping[std_key]
        
        # Get values from both dictionaries if they exist
        values = []
        for key in possible_keys:
            if key in dict1 and dict1[key] not in ["Not found", "Error parsing", ""]:
                values.append(dict1[key])
            if key in dict2 and dict2[key] not in ["Not found", "Error parsing", ""]:
                values.append(dict2[key])
        
        # Choose the best value
        if values:
            # For description fields, choose the longest one
            if std_key in ["Brief description of the provider", "What you get", "How to get it"]:
                result[std_key] = max(values, key=len)
            # For value field, prefer the one with $ if available
            elif std_key == "Value":
                dollar_values = [v for v in values if '$' in str(v)]
                if dollar_values:
                    result[std_key] = dollar_values[0]
                else:
                    result[std_key] = values[0]
        else:
            # If no good value found, use "Not found"
            result[std_key] = "Not found"
    
    return result

# recieves all active perks, scrapes the websites and returns a dict with the desired info
def scrap_website(records):
    
    def print_perks(perks):
        for key, value in perks.items():
            print(f"{key}: {value}")
    
    print("\nNumber of active perks to be scraped: ", len(records))

    # filter 'records' to consider only the active perks
    results_bs_gpt = {}
    results_perplexity = {}
    all_results = {}

    for record in records:
        # extract information from argument records
        fields = record.get('fields', {})
        perk_name = fields.get("Name")
        perk_url = fields.get("Link")
        print(f"\n{'-' * 75}\nAnalyzing perk: {perk_name}\n{'-' * 75}")

        # SCRAPER 1: BeautifulSoup - scrape the url's text with beautiful soup
        print("Analysing with method 1 - beautiful soup + chatGPT")
        bs_page_text = scraper_beautiful_soup(perk_url)
        gpt_extraction = gpt_extract_info(bs_page_text)
        results_bs_gpt[perk_name] = gpt_extraction
        print_perks(gpt_extraction)

        # SCRAPER 2
        print("\nAnalysing with method 2 - perplexity")        
        results_perplexity = extract_perk_info(
            url=perk_url,
            perplexity_api_key=perplexity_api_key,
            crawl_subpages=True,
            max_subpages=10
        )
        print_perks(results_perplexity)
        
        # Combine results of both scraping methods
        combined_results = combine_perk_dicts(results_perplexity, results_bs_gpt)
        print(f'\nCombined result of both scraping methods:')
        print_perks(combined_results)
        all_results[perk_name] = combined_results
        
    return all_results


if __name__ == "__main__":

    print_hello()

    process_records_flag = 0

    # extract perk database table from airtable
    records = get_records()

    if process_records_flag == 1:

        # identify which records are active/inactive and update status on airtable
        perks_wo_link, perks_active, perks_inactive, _ = process_records(records)

        # Write it to a file (each item on a new line)
        with open('perks_active.txt', 'w') as f:
            for item in perks_active:
                f.write(item + '\n')

    else:
        # Read the list of active perk to avoid reruning the whole analysis 
        with open('perks_active.txt', 'r') as f:
            perks_active = [line.strip() for line in f]

    # filter all the records from airtable - we only scratch the ones which are active
    records_active = [item for item in records if item['fields'].get('Name') in perks_active]

    # scrape the active websites to update information: 
    scraped_info = scrap_website(records_active)

    # see how many websites were scraped successfully
    # code here

    # update airtable with the new info
    update_perks_info(scraped_info)

