import re
import os
import json
import copy
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import config
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langfuse import Langfuse

# get keys for your project from https://cloud.langfuse.com
os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY

os.environ["PERPLEXITY_API_KEY"] = config.PERPLEXITY_API_KEY

# Initialize Langfuse client (prompt management)
langfuse = Langfuse(
  secret_key=os.environ["LANGFUSE_SECRET_KEY"],
  public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
  host=os.environ["LANGFUSE_HOST"]
)

from src.gpt_extractor import extract_with_gpt, scrape_website_with_firecrawl
from src.perplexity_extractor import extract_with_perplexity


############# Handle printing
def print_perks(perks):
    if perks is None:  
        print("Error: Perks data is None. No data to display.")
        return 
    
    for key, value in perks.items():
        line = f"{key}: {value}"
        print(f'{line[:100]}...')  


############# Logic to analyse URLs
def is_email(text):
    # RFC 5322 compliant email regex pattern (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, text))


def is_url_alive(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def access_page_with_cookies(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'agree') or contains(text(), 'AGREE')]"))
            )
            cookie_button.click()
            print("OK: Accepted cookies")
        except:
            print("INFO: No cookie banner detected")
        
        return 200
    except Exception as e:
        print(f"INFO: Selenium failed: {e}")
        return None
    finally:
        driver.quit()


def is_fake_200(scraped_text):
    
    try:

        # Initialize Langfuse CallbackHandler for Langchain (tracing)
        langfuse_callback_handler = CallbackHandler()

        # Get current production version of prompt
        langfuse_prompt = langfuse.get_prompt("fake-status-200-identifier")

        # Transform into Langchain PromptTemplate 
        langchain_prompt = ChatPromptTemplate.from_template(
                langfuse_prompt.get_langchain_prompt(),
                metadata={"langfuse_prompt": langfuse_prompt},
            )

        #Create Langchain chain based on prompt
        model = ChatOpenAI(
            model=langfuse_prompt.config["model"], 
            temperature=str(langfuse_prompt.config["temperature"])
        )
        
        chain = langchain_prompt | model

        # we pass the callback handler to the chain to trace the run in Langfuse
        response = chain.invoke(input=scraped_text,config={"callbacks":[langfuse_callback_handler]})
                
        # Log identified patterns for debugging
        if response.content == 404:
            print(f"   => Fake 404/Closed form detected by LLM")
            return 404
        elif response.content == 200:
            print("OK. Page active")
            return 200
        else:
            print("Unexpected result from Langfuse.")
        
        
    except Exception as e:
        print(f"Error using GPT API: {e}")
        
        return 0


def get_url_status_code(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        # HEAD request first
        response = session.head(url, allow_redirects=True, timeout=5)
        
        # If HEAD gives bad result, retry GET anyway
        if response.status_code >= 400:
            print("ERROR: HEAD request failed or returned error, retrying with GET...")
            response = session.get(url, allow_redirects=True, timeout=10)

        # After GET:
        if response.status_code == 404:
            print("ERROR: 404 Not Found (confirmed by requests)")
            return 404

        if 400 <= response.status_code < 600 and response.status_code not in [401, 403, 405]:
            print(f"ERROR: HTTP error {response.status_code} (confirmed by requests)")
            return response.status_code

        # If GET gives suspicious access issue
        if response.status_code in [401, 403, 405]:
            print("ERROR: Access issue detected (GET), trying with Selenium...")
            selenium_result = access_page_with_cookies(url)
            return selenium_result
        
        
        return response.status_code
    except requests.RequestException as e:
        print(f"ERROR: Requests failed: {e}")
        # As fallback, use Selenium
        return access_page_with_cookies(url)


############# Methods to save to local directory
def save_perks_status(perks_wo_link, perks_active, perks_inactive, perks_updated):
    # Ensure the results directory exists
    dir = 'results_perks_update/'
    os.makedirs(dir, exist_ok=True)

    # Names of files to save the values
    perks_names = ['perks_wo_link', 'perks_active', 'perks_inactive', 'perks_updated']

    for i, perks in enumerate([perks_wo_link, perks_active, perks_inactive, perks_updated]):
        # Fallback to empty list if None is passed
        if perks is None:
            perks = []
        with open(f'{dir}{perks_names[i]}.txt', 'w', encoding='utf-8') as f:
            for item in perks:
                # Only write non-None items, and always write as string
                if item is not None:
                    f.write(f"{str(item)}\n")


#####################
# main status processing logic - loop over airtable rows
def process_records(records, gpt_prompt):

    perks_wo_link  = []
    perks_w_email  = []
    perks_active   = []
    perks_inactive = []
    perks_updated  = []

    # dict with the info to be scraped and updated on airtable
    updated_records = {record['id']: record.copy() for record in records}

    # loop over each record (row on airtable)
    for record in records:
        fields    = record.get('fields', {})
        perk_id   = record.get('id')
        perk_name = fields.get("Name")
        perk_url  = fields.get("Link")
        current_status = fields.get("Status", "").lower()  
        
        print(f"\n{'-' * 75}\nAnalyzing perk: {perk_name}")

        # Skip if already marked as broken/expired
        if current_status == "broken/expired":
            print("INFO: Record already marked as broken/expired. ")
            # Still count it in the inactive list for reporting
            perks_inactive.append(perk_name)
            updated_records[perk_id]['fields']["Status"] = "broken/expired"
            continue

        # Case 1: No URL available
        if not perk_url:
            print("INFO: No URL available on Airtable. ")
            perks_wo_link.append(perk_name)
            continue
        
        # Case 2: URL is actually an email address
        if is_email(perk_url):
            print("INFO: No URL available on Airtable. ")
            perks_w_email.append(perk_name)
            perks_wo_link.append(perk_name)
            continue

        # Case 3: URL available but missing http
        if not perk_url.startswith(('http://', 'https://')):
            perk_url = 'http://' + perk_url
            fields["Link"] = perk_url

        # Check URL status (200 if active)
        status_code = get_url_status_code(perk_url)

        if status_code == 200:
            print(f"OK: Link is active (Status Code: {status_code})")
            
            if current_status != "active":
                updated_records[perk_id]['fields']["Status"] = "active"
                perks_active.append(perk_name)
                perks_updated.append(perk_name)  # Only append if status changed

            perks_active.append(perk_name)

            # Online scrape the website if the link is active: pass 'results' dict by reference and modify it
            scrape(updated_records[perk_id]['fields'], gpt_prompt)

        elif status_code is None:
            print(f"ERROR: Failed to reach URL (Status Code: {status_code})")

            if current_status != "broken/expired":
                updated_records[perk_id]['fields']["Status"] = "broken/expired"
                perks_updated.append(perk_name)

            perks_inactive.append(perk_name)

        else:
            print(f"ERROR: Link is inactive (Status Code: {status_code})")

            if current_status != "broken/expired":
                updated_records[perk_id]['fields']["Status"] = "broken/expired"
                perks_updated.append(perk_name)

            perks_inactive.append(perk_name)
        
        print(f"{'-' * 75}")

    save_perks_status(perks_wo_link, perks_active, perks_inactive, perks_updated)

    return updated_records

# recieves all active perks, scrapes the websites and returns a dict with the desired info
def scrape(fields, gpt_prompt):
    
    # 1. extract information from argument records
    perk_url = fields.get("Link")
    perk_name = fields.get("Name")

    # 2. extract information with Firecrawl
    print(f"Analyzing with method 1 - Firecrawl and gpt-4.1-nano")
    scraped_text = scrape_website_with_firecrawl(perk_url)
    
    # 3. check if this is an active link - although the code is 200 we need to check if this is a closed form or an inactive page
    if is_fake_200(scraped_text):
        print("ERROR: Detected 404-like error inside page (closed form or inactive page)")
        fields["Status"] = "broken/expired"
    
    else:

        # 4. extract structured info with gpt-4.1-nano
        structured_info_gpt = extract_with_gpt(gpt_prompt, scraped_text)
        print_perks(structured_info_gpt)

        # 5. if we still have missing information, use Perplexity Search
        if any(value == "Not found" for value in structured_info_gpt.values()):
            enriched_info = extract_with_perplexity(perk_url, perk_name, structured_info_gpt)
            new_info = enriched_info
        else:
            new_info = structured_info_gpt

        # update the value of fields (passed by reference)
        for key, value in new_info.items():
            if key in fields:  
                fields[key] = value

# 
def handle_scraping(gpt_prompt, flag, records, update_type):

    file_path = f'results_{update_type}_update/scraped_info.json'

    if flag == 1:
        # Run the scraping function
        scraped_info = process_records(records, gpt_prompt)
        
        # Save the scraped information directly to a JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scraped_info, f, indent=2)
        print(f"Data successfully saved to {file_path}")
        
        return scraped_info
    
    elif flag == 0:
        # Read the scraped information from the JSON file
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                scraped_info = json.load(f)
            print(f"Data successfully loaded from {file_path}")
            
            return scraped_info
        else:
            print(f"Warning: File {file_path} does not exist.")
            return {}
    else:
        raise ValueError("Flag must be either 0 or 1")