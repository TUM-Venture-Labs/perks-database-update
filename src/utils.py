import re
import os
import json
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Simple function to get the HTTP status code of a webpage and follow redirects. Handles SSL certificate issues on macOS.
def get_page_status(url, timeout=10):
    try:
        # First try with normal verification, allowing redirects
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response.status_code, response.url
    except requests.exceptions.SSLError:
        # If we get an SSL error, try with verification disabled
        try:
            response = requests.get(url, verify=False, timeout=timeout, allow_redirects=True)
            return response.status_code, response.url
        except Exception as e:
            print(f"Error checking {url}: {str(e)}")
            return None, None
    except Exception as e:
        print(f"Error checking {url}: {str(e)}")
        return None, None


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


############# Methods to save to local directory
def save_records_status(records_wo_link, records_active, records_inactive, records_updated, update_type):
    # Ensure the results directory exists
    dir = f'results_{update_type}_update/'
    os.makedirs(dir, exist_ok=True)

    # Names of files to save the values
    names = ['wo_link', 'active', 'inactive', 'updated']

    for i, records in enumerate([records_wo_link, records_active, records_inactive, records_updated]):
        # Fallback to empty list if None is passed
        if records is None:
            records = []
        with open(f'{dir}{names[i]}.txt', 'w', encoding='utf-8') as f:
            for item in records:
                # Only write non-None items, and always write as string
                if item is not None:
                    f.write(f"{str(item)}\n")


#####################
# main status processing logic - loop over airtable rows
def process_records(records, gpt_prompt, update_type):

    records_wo_link  = []
    records_w_email  = []
    records_active   = []
    records_inactive = []
    records_changed  = []

    # dict with the info to be scraped and updated on airtable
    updated_records = {record['id']: record.copy() for record in records}

    # loop over each record (row on airtable)
    for record in records:
        fields    = record.get('fields', {})
        id   = record.get('id')
        name = fields.get("Name")
        url  = fields.get("Link")

        if update_type == 'funding':
            current_status = "active" 
        elif update_type == 'perks':
            current_status = fields.get("Status", "").lower()  
        
        print(f"\n{'-' * 75}\nAnalyzing {update_type}: {name}")

        # Skip if already marked as broken/expired
        if current_status == "broken/expired":
            print("INFO: Record already marked as broken/expired. ")
            # Still count it in the inactive list for reporting
            records_inactive.append(name)
            updated_records[id]['fields']["Status"] = "broken/expired"
            continue

        # Case 1: No URL available
        if not url:
            print("INFO: No URL available on Airtable. ")
            records_wo_link.append(name)
            continue
        
        # Case 2: URL is actually an email address
        if is_email(url):
            print("INFO: No URL available on Airtable. ")
            records_w_email.append(name)
            records_wo_link.append(name)
            continue

        # Case 3: URL available but missing http
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            fields["Link"] = url

        # Making a get request
        status_code, final_url = get_page_status(url)#response.status_code # get_url_status_code(url)

        if status_code == 200:
            print(f"OK: Link is active (Status Code: {status_code})")
            
            if current_status != "active":
                updated_records[id]['fields']["Status"] = "active"
                records_changed.append(name) # Only append if status changed

            records_active.append(name)

            # Online scrape the website if the link is active: pass 'results' dict by reference and modify it
            scrape(updated_records[id]['fields'], gpt_prompt)

        # redirect status code
        elif status_code == 403:
            print(f"WARNING: Link is redirecting to new page. Updating link on Airtable... (Status Code: {status_code})")
            updated_records[id]['fields']["Link"] = final_url
        
        elif status_code is None:
            print(f"ERROR: Failed to reach URL (Status Code: {status_code})")

            if current_status != "broken/expired":
                updated_records[id]['fields']["Status"] = "broken/expired"
                records_changed.append(name) # Only append if status changed

            records_inactive.append(name)

        else:
            print(f"ERROR: Link is inactive (Status Code: {status_code})")

            if current_status != "broken/expired":
                updated_records[id]['fields']["Status"] = "broken/expired"
                records_changed.append(name)

            records_inactive.append(name)
        
        print(f"{'-' * 75}")

    save_records_status(records_wo_link, records_active, records_inactive, records_changed, update_type)

    return updated_records

# recieves all active perks, scrapes the websites and returns a dict with the desired info
def scrape(fields, gpt_prompt):
    
    # 1. extract information from argument records
    url = fields.get("Link")
    name = fields.get("Name")

    # 2. extract information with Firecrawl
    print(f"Analyzing with method 1 - Firecrawl and gpt-4.1-nano")
    scraped_text = scrape_website_with_firecrawl(url)
    
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
            enriched_info = extract_with_perplexity(url, name, structured_info_gpt, gpt_prompt)
            new_info = enriched_info
        else:
            new_info = structured_info_gpt

        # update the value of fields (passed by reference)
        if new_info is not None:  # Add this check to prevent the error
            for key, value in new_info.items():
                if key in fields:  
                    fields[key] = value
        else:
            print(f"Warning: No information retrieved for {fields.get('name', 'unknown perk')}")

# 
def handle_scraping(gpt_prompt, flag, records, update_type):

    file_path = f'results_{update_type}_update/scraped_info.json'

    if flag == 1:
        # Run the scraping function
        scraped_info = process_records(records, gpt_prompt, update_type)
        
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