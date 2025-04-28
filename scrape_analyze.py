import argparse
import os
from firecrawl import FirecrawlApp
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def scrape_with_firecrawl(url: str, api_key: str) -> str | None:
    """Scrapes the content of a given URL using Firecrawl."""
    try:
        app = FirecrawlApp(api_key=api_key)
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

def analyze_with_openai(content: str, api_key: str) -> str | None:
    """Analyzes the given content using OpenAI's chat completion."""
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Analyze the following text content and provide a brief summary."},
                {"role": "user", "content": content}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing content with OpenAI: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Scrape a URL with Firecrawl and analyze its content with OpenAI.')
    parser.add_argument('url', type=str, help='The URL to scrape and analyze.')
    args = parser.parse_args()

    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not firecrawl_api_key:
        print("Error: FIRECRAWL_API_KEY environment variable not set.")
        return
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    print(f"Scraping URL: {args.url}...")
    scraped_content = scrape_with_firecrawl(args.url, firecrawl_api_key)

    if scraped_content:
        print("Scraping successful. Analyzing content with OpenAI...")
        # Limit content size to avoid hitting OpenAI limits if necessary
        max_content_length = 15000 # Adjust as needed based on typical token limits
        if len(scraped_content) > max_content_length:
            print(f"Warning: Content truncated to {max_content_length} characters for analysis.")
            scraped_content = scraped_content[:max_content_length]

        analysis = analyze_with_openai(scraped_content, openai_api_key)
        if analysis:
            print("\n--- OpenAI Analysis ---")
            print(analysis)
            print("-----------------------\n")
        else:
            print("Analysis failed.")
    else:
        print("Scraping failed.")

if __name__ == "__main__":
    main() 