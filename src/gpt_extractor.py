import os
import re
import time
import json
import config
from typing import Dict
from firecrawl import FirecrawlApp, ScrapeOptions

os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["FIRECRAWL_API_KEY"] = config.FIRECRAWL_API_KEY
os.environ["PERPLEXITY_API_KEY"] = config.PERPLEXITY_API_KEY


def scrape_website_with_firecrawl(url: str) -> str:
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

    # Crawl a website:
    crawl_result = app.crawl_url(
        url, limit=10, 
        scrape_options=ScrapeOptions(formats=['markdown']),
    )

    # Concatenate all markdown content from each crawled page
    all_text = "\n\n".join(doc.markdown for doc in crawl_result.data)
    time.sleep(60)
    #print(all_text)

    return all_text


def extract_with_gpt(text: str) -> Dict[str, str]:

    try:
        # For this function to work, you need to set up the OpenAI API client
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        prompt = f"""
        You are an information extraction assistant.

        Given the text below, extract the following fields:

        - "Provider Description": A very brief (1-2 sentences) description of the company or organization offering the perk.
        - "What You Get": Summarize clearly what the perk provides (discount, credits, service, etc.).
        - "How To Get It": Instructions on how someone can claim or access the perk.
        - "Value": The financial value of the perk (in USD or EUR if available). If no value is clear, return "Not found".

        **Important rules**:
        - Do not invent missing information.
        - If a field cannot be found, respond exactly with "Not found".
        - Output only valid JSON, no commentary.
        - The "Value" is a number, if not found write "Not found".

        Text to analyze:
        \"\"\"
        {text[:15000]}  # Limit text size to avoid token limits
        \"\"\"

        Respond in this exact JSON format:
        {{
            "Brief description of the provider": "",
            "What you get": "",
            "How to get it": "",
            "Value": ""
        }}
        """

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract the JSON part only
        try:
            json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
            extracted = json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Parsing error: {e}")
            extracted = {
                "Brief description of the provider": "Error parsing",
                "What you get": "Error parsing",
                "How to get it": "Error parsing",
                "Value": "Error parsing"
            }
        
        return extracted
    except Exception as e:
        print(f"Error with GPT extraction: {e}")
        return {
            "Brief description of the provider": "Not found",
            "What you get": "Not found",
            "How to get it": "Not found",
            "Value": "Not found"
        }

