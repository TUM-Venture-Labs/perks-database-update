import os
import json
import time
import config
from pyairtable import Table
from src.utils import handle_scraping
from src.airtable_utils import get_records, update_funding_info
from langfuse import Langfuse
from langfuse.openai import OpenAI
langfuse = Langfuse()

# get perplexity API key and add it to the environment variables
perplexity_api_key = os.environ.get(config.PERPLEXITY_API_KEY)

# Initialize Airtable table connection once
table = Table(
    config.AIRTABLE_API_KEY_FUNDING,
    config.AIRTABLE_BASE_ID_FUNDING,
    config.AIRTABLE_TABLE_ID_FUNDING
)


def print_hello():    
    print("\033[1;36m🔍 FUNDING OVERVIEW UPDATER\033[0m")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1mPROCESS FLOW:\033[0m")
    print("  1. \033[1;32mFetch records\033[0m from Airtable perks database")
    print("  2. \033[1;32mVerify URL status\033[0m (active/inactive) for each perk")
    print("  3. \033[1;32mScrape active websites\033[0m using two methods:")
    print("     - Firecrawl + GPT-4.1-nano extraction")
    print("     - Perplexity API with subpage crawling")
    print("  4. \033[1;32mCombine results\033[0m from both scraping methods")
    print("  5. \033[1;32mUpdate Airtable\033[0m with the combined perk information")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\033[1mEXTRACTED DATA:\033[0m")
    print("  • Summary")
    print("  • Requirements")
    print("  • Benefits")
    print("  • Funding amount")
    print("  • Next deadline")
    print("  • Stage (Acceleration, Incubation, etc)")
    print("  • Industry focus")
    print("  • EXIST phase")
    print("  • Region (Bavaria, European, etc")
    print("  • Program duration")
    print("  • Last edited time (date)")
    print("  • Target group (scientists, startups, etc)")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\n\n")


if __name__ == "__main__":

    # program opening
    print_hello()

    # 1. Extract perk database table from airtable
    current_records = get_records(table)

    # 2. Get current prompt version from Langfuse
    process_records_flag = 1
    gpt_prompt = langfuse.get_prompt("extract_funding_info_from_url")
    print(gpt_prompt.prompt)
    print(gpt_prompt.config["json_schema"])

    # 3. Loop over URL's on airtable and crawl for content using Firecrawl. Use gpt_promp from langfuse to gather info
    updated_records = handle_scraping(gpt_prompt, process_records_flag, current_records, update_type = "funding")
    
    # 4. update airtable with the new info
    update_funding_info(table, updated_records)

