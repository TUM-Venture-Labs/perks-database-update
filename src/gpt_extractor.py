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


import time
import os
from firecrawl import FirecrawlApp, ScrapeOptions

def scrape_website_with_firecrawl(url: str, max_retries: int = 3) -> str | None:
    """Scrapes the content of a given URL using Firecrawl with rate limit handling."""
    
    # Check API key first
    if "FIRECRAWL_API_KEY" not in os.environ:
        print("Error: FIRECRAWL_API_KEY environment variable not set")
        return None
    
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} for URL: {url}")
            
            crawl_result = app.crawl_url(
                url, 
                limit=2, 
                scrape_options=ScrapeOptions(formats=['markdown', 'html'])
            )
            
            # Check if crawl was successful and has data
            if crawl_result and hasattr(crawl_result, 'data') and crawl_result.data:
                scraped_data = "\n\n".join(doc.markdown for doc in crawl_result.data if hasattr(doc, 'markdown'))
                if scraped_data:
                    print(f'Successfully scraped website. ')#Result: {scraped_data[:80]} ...')
                    return scraped_data
                else:
                    print(f"No markdown content found for URL: {url}")
                    return None
            else:
                print(f"No data returned for URL: {url}")
                return None
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error scraping URL {url}: {error_msg}")
            
            # Check if it's a rate limit error (429)
            if "429" in error_msg or "Rate limit exceeded" in error_msg:
                if attempt < max_retries - 1:  # Don't wait on the last attempt
                    # Extract wait time from error message or use default
                    wait_time = 60  # Default 1 minute wait
                    if "retry after" in error_msg.lower():
                        try:
                            # Try to extract wait time from error message
                            import re
                            match = re.search(r'retry after (\d+)', error_msg.lower())
                            if match:
                                wait_time = int(match.group(1))
                        except:
                            pass
                    
                    print(f"Rate limit hit. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print("Rate limit exceeded and max retries reached")
                    return None
            else:
                # For non-rate-limit errors, don't retry
                print(f"Non-retryable error occurred: {error_msg}")
                return None
    
    print(f"Failed to scrape {url} after {max_retries} attempts")
    return None


def extract_with_gpt(langfuse_prompt: str, scraped_text: str) -> Dict[str, str]:
    """ Implementation based on https://langfuse.com/docs/prompts/example-openai-functions """

    try:
        # For this function to work, you need to set up the OpenAI API client        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Stringify the JSON schema
        json_schema_str = ', '.join([f"'{key}': {value}" for key, value in langfuse_prompt.config["json_schema"].items()])

        # Compile prompt with stringified version of json schema
        system_message = langfuse_prompt.compile(json_schema=json_schema_str)
        
        # Format as OpenAI messages
        messages = [
            {"role":"system","content": system_message},
            {"role":"user","content":scraped_text}
        ]
        
        # Get additional config
        model = langfuse_prompt.config["model"]
        temperature = langfuse_prompt.config["temperature"]
        
        # Execute LLM call
        res = client.chat.completions.create(
            model = model,
            temperature = temperature,
            messages = messages,
            response_format = { "type": "json_object" },
            langfuse_prompt = langfuse_prompt # capture used prompt version in trace
        )
        
        # Parse response as JSON
        res = json.loads(res.choices[0].message.content)
        print("Successfully extracted with GPT using Langfuse prompt.\n")
        
        return res
    except Exception as e:
        print(f"Error with GPT extraction: {e}")
        return None

