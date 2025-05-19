import os
import json
import time
import config
from pyairtable import Table
from src.utils import handle_scraping
from src.airtable_utils import get_records, update_perks_info
from langfuse import Langfuse
from langfuse.openai import OpenAI

langfuse = Langfuse()

# get perplexity API key and add it to the environment variables
perplexity_api_key = os.environ.get(config.PERPLEXITY_API_KEY)

# Initialize Airtable table connection once
table = Table(
    config.AIRTABLE_API_KEY_PERKS,
    config.AIRTABLE_BASE_ID_PERKS,
    config.AIRTABLE_TABLE_ID_PERKS
)

process_records_flag = 1


def print_hello():
    """Print a concise and visually appealing explanation of the program."""
    
    print("\033[1;36m🔍 PERKS DATABASE UPDATER\033[0m")
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
    print("  • Provider description")
    print("  • What you get")
    print("  • How to get it")
    print("  • Monetary value")
    print("\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m")
    print("\n\n")



if __name__ == "__main__":

    # program opening
    print_hello()

    # 1. extract perk database table from airtable
    current_records = get_records(table)

    # 2. get updated information on the perk
    gpt_prompt = langfuse.get_prompt("extract_perk_info_from_url")
    updated_records = handle_scraping(gpt_prompt, process_records_flag, current_records, update_type = "perks")
    
    # 3. update airtable with the new info
    update_perks_info(table, updated_records)

