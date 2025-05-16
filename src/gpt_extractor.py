import os
import re
import time
import json
import config
from typing import Dict
from langfuse import Langfuse
from langfuse.openai import OpenAI
langfuse = Langfuse()


from firecrawl import FirecrawlApp, ScrapeOptions

os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["FIRECRAWL_API_KEY"] = config.FIRECRAWL_API_KEY
os.environ["PERPLEXITY_API_KEY"] = config.PERPLEXITY_API_KEY


def scrape_website_with_firecrawl(url: str) -> str | None:
    """Scrapes the content of a given URL using Firecrawl."""
    try:
        app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

        # scrape website 
        scraped_data = app.scrape_url(url)

        if 'markdown' in scraped_data:
            return scraped_data['markdown']
        elif 'content' in scraped_data:
             # Fallback to content if markdown is not available
            return scraped_data['content']
        else:
            print("Error: Could not find 'markdown' or 'content' in scraped data.")
            print(f"Scraped data keys: {scraped_data.keys()}")
            return None
    except Exception as e:
        print(f"Error scraping URL {url} with Firecrawl: {e}")
        return None


def extract_with_gpt(prompt, scraped_text: str) -> Dict[str, str]:

    try:
        # For this function to work, you need to set up the OpenAI API client        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Stringify the JSON schema
        json_schema_str = ', '.join([f"'{key}': {value}" for key, value in prompt.config["json_schema"].items()])

        # Compile prompt with stringified version of json schema
        system_message = prompt.compile(json_schema=json_schema_str)
        
        # Format as OpenAI messages
        messages = [
            {"role":"system","content": system_message},
            {"role":"user","content":scraped_text}
        ]
        
        # Get additional config
        model = prompt.config["model"]
        temperature = prompt.config["temperature"]
        
        # Execute LLM call
        res = client.chat.completions.create(
            model = model,
            temperature = temperature,
            messages = messages,
            response_format = { "type": "json_object" },
            langfuse_prompt = prompt # capture used prompt version in trace
        )
        
        # Parse response as JSON
        res = json.loads(res.choices[0].message.content)
        
        return res
    except Exception as e:
        print(f"Error with GPT extraction: {e}")
        return {
            "Brief description of the provider": "Not found",
            "What you get": "Not found",
            "How to get it": "Not found",
            "Value": "Not found"
        }

