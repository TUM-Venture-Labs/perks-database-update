import os
import json
import time
import config
from src.utils import print_hello, is_email, print_perks
from src.utils import  get_url_status_code, save_perks_status, save_formatted_text
from src.airtable_utils import get_records, update_record, update_perks_info
from src.gpt_extractor import extract_with_gpt, scrape_website_with_firecrawl
from src.perplexity_extractor import extract_perk_info_perplexity

# get perplexity API key and add it to the environment variables
perplexity_api_key = os.environ.get(config.PERPLEXITY_API_KEY)

scrape_links_flag = 1
process_records_flag = 1

# main status processing logic - loop over airtable rows
def process_records(records):

    perks_wo_link  = []
    perks_w_email  = []
    perks_active   = []
    perks_inactive = []
    perks_updated  = []

    for record in records:
        fields = record.get('fields', {})
        perk_name = fields.get("Name")
        perk_url = fields.get("Link")
        current_status = fields.get("Status", "").lower()  # Default to empty string if missing

        # Skip if already marked as broken/expired
        if current_status == "broken/expired":
            # Still count it in the inactive list for reporting
            perks_inactive.append(perk_name)
            continue

        # Case 1: No URL available
        if not perk_url:
            perks_wo_link.append(perk_name)
            continue
        
        # Case 2: URL is actually an email address
        if is_email(perk_url):
            perks_w_email.append(perk_name)
            perks_wo_link.append(perk_name)
            continue

        # Case 2: URL available but missing http
        if not perk_url.startswith(('http://', 'https://')):
            perk_url = 'http://' + perk_url
            fields["Link"] = perk_url

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
        
        time.sleep(1)  

    # Final summary
    print(f"Perks without link ({len(perks_wo_link)})                                  :", perks_wo_link)
    print(f"Perks active ({len(perks_active)})                                        :", perks_active)
    print(f"Perks inactive ({len(perks_inactive)})                                     :", perks_inactive)
    print(f"Perks updated ({len(perks_updated)})                                      :", perks_updated)
    print(f"Perks without link (with email instead of URL) ({len(perks_w_email)})     :", perks_w_email)

    return perks_wo_link, perks_active, perks_inactive, perks_updated


# recieves all active perks, scrapes the websites and returns a dict with the desired info
def scrape(records):
    
    print("\nNumber of active perks to be scraped: ", len(records))

    # filter 'records' to consider only the active perks
    results = {}

    for record in records:
        # 1. extract information from argument records
        fields = record.get('fields', {})
        url = fields.get("Link")
        name = fields.get("Name")

        # 2. extract information with Firecrawl scraping and ChatGPT
        print(f"\n{'-' * 75}\nAnalyzing perk: {name}\n{'-' * 75}")
        print(f"Analyzing with method 1 - Firecrawl and gpt-4.1-nano")
        
        # Step 1: scrape main URL page with Firecrawl 
        scraped_text = scrape_website_with_firecrawl(url)
        # Step 2: extract structured info with gpt-4.1-nano
        structured_info_gpt = extract_with_gpt(scraped_text)
        print_perks(structured_info_gpt)
        print("\n")

        # 3. if we still have missing information, use Perplexity Search
        if any(value == "Not found" for value in structured_info_gpt.values()):

            enriched_info = extract_perk_info_perplexity( 
                url       = url,
                perk_name = fields.get("Name"), 
                gpt_info  = structured_info_gpt
            )

            results[name] = enriched_info

        else:
            results[name] = structured_info_gpt

        print_perks(results[name])
  
    return results


def handle_scraping(flag, records_active, file_path="results/scraped_info.json"):

    if flag == 1:
        # Run the scraping function
        scraped_info = scrape(records_active)
        
        # Save the scraped information directly to a JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scraped_info, f, indent=2)
        print(f"Data successfully saved to {file_path}")
        
        # Also save in the requested text format
        save_formatted_text(scraped_info, file_path.replace('.json', '.txt'))
        
        return scraped_info
    
    elif flag == 0:
        # Read the scraped information from the JSON file
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                scraped_info = json.load(f)
            print(f"Data successfully loaded from {file_path}")
            
            # Also save in the requested text format (in case it doesn't exist)
            save_formatted_text(scraped_info, file_path.replace('.json', '.txt'))
            
            return scraped_info
        else:
            print(f"Warning: File {file_path} does not exist.")
            return {}
    
    else:
        raise ValueError("Flag must be either 0 or 1")



if __name__ == "__main__":

    # program opening
    print_hello()

    # 1. extract perk database table from airtable
    records = get_records()

    # 2. update status of the perk - identify which records are active/inactive and update status on airtable
    if process_records_flag == 1:
        perks_wo_link, perks_active, perks_inactive, perks_updated = process_records(records)
        save_perks_status(perks_wo_link, perks_active, perks_inactive, perks_updated)

    else:
        with open('results/perks_active.txt', 'r') as f:
            perks_active = [line.strip() for line in f]

    # 3. filter all the records from airtable - we only scratch the ones which are active
    records_active = [item for item in records if item['fields'].get('Name') in perks_active]

    # 4. gather info about active perks: selenium + ChatGPT + Perplexity
    scraped_info = handle_scraping(scrape_links_flag, records_active)

    # 5. update airtable with the new info
    update_perks_info(scraped_info)

