"""INFORMATION:

Main Function: extract_perk_info() scrapes websites to extract information about company perks and discounts

Crawling Process:
1. Scrapes main URL with Selenium (handles JavaScript, cookies, popups)
2. Finds and prioritizes relevant subpages (up to a configurable limit)
3. Collects text content from all pages into a single document

Information Extraction:
1. Uses GPT-4o to extract structured data about perks (provider, benefits, access instructions, value)
2. Fields marked "Not found" indicate missing information

Perplexity Integration:
1. Only triggered when information gaps exist after website extraction
2. Sends targeted queries about company perks to Perplexity's API
3. Captures both Perplexity's response and source URLs

Enrichment Process:
1. Combines website text with Perplexity results
2. Uses a second GPT call to fill in missing information
3. Returns complete data with metadata about crawled pages

Link Prioritization:
1. Analyzes found links and prioritizes those containing keywords like "perk," "benefit," "discount"
2. Ensures crawling focuses on the most relevant pages first

Fallback Mechanisms:
1. Regular requests as backup if Selenium fails
2. Enhanced GPT extraction if Perplexity fails
3. Robust error handling throughout
"""


import requests
import json
import re
import time
from bs4 import BeautifulSoup
import os
from typing import Dict, Any, Optional, List, Set
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import config
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["PERPLEXITY_API_KEY"] = config.PERPLEXITY_API_KEY


def extract_perk_info(url: str, perplexity_api_key: Optional[str] = None, crawl_subpages: bool = True, max_subpages: int = 5) -> Dict[str, Any]:
    """
    Extract perk information from a URL and optionally its subpages, with Perplexity API integration.
    
    Args:
        url: The URL to scrape for perk information
        perplexity_api_key: Optional API key for Perplexity
        crawl_subpages: Whether to crawl subpages of the website
        max_subpages: Maximum number of subpages to crawl
        
    Returns:
        A dictionary containing the extracted perk information
    """
    # Step 1: Scrape the main URL
    scraped_text = scrape_website_with_selenium(url)
    if not scraped_text:
        return {
            "error": "Failed to scrape the website",
            "url": url
        }
    
    # Step 2: Crawl subpages if requested
    all_text = scraped_text
    subpage_info = {}
    
    if crawl_subpages:
        print(f"Crawling subpages of {url}...")
        subpages = find_subpages(url, max_pages=max_subpages)
        
        for idx, subpage_url in enumerate(subpages):
            print(f"Scraping subpage {idx+1}/{len(subpages)}: {subpage_url}")
            subpage_text = scrape_website_with_selenium(subpage_url)
            if subpage_text:
                subpage_info[subpage_url] = {
                    "text": subpage_text[:5000],  # Store a truncated version for reference
                    "full_text": subpage_text  # Store the full text for extraction
                }
                all_text += f"\n\n--- CONTENT FROM SUBPAGE: {subpage_url} ---\n\n{subpage_text}"
    
    # Step 3: Try to extract information using GPT from all gathered text
    extracted_info = extract_with_gpt(all_text)
    
    # Step 4: If we still have missing information, use Perplexity API
    if perplexity_api_key and has_missing_info(extracted_info):
        domain = extract_domain(url)
        company_name = extract_company_name(domain)
        supplementary_info = search_perplexity(company_name, perplexity_api_key)
        
        if supplementary_info:
            # Combine all text for final extraction
            combined_text = all_text + f"\n\nAdditional information from Perplexity search:\n{supplementary_info}"
            
            # Re-extract with all available information
            final_info = extract_with_gpt(combined_text)
            
            # If there are still missing fields, use the enrichment function
            if has_missing_info(final_info):
                return enrich_with_perplexity(final_info, supplementary_info)
            return final_info
    
    # Include metadata about the crawl
    result = extracted_info.copy()
    result["metadata"] = {
        "main_url": url,
        "subpages_crawled": len(subpage_info) if crawl_subpages else 0,
        "subpage_urls": list(subpage_info.keys()) if crawl_subpages else []
    }
    
    return result


def find_subpages(url: str, max_pages: int = 5) -> List[str]:
    """
    Find subpages of a given URL.
    
    Args:
        url: The base URL to find subpages for
        max_pages: Maximum number of subpages to return
        
    Returns:
        A list of subpage URLs
    """
    try:
        # Parse the base URL to get the domain
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Use Selenium to get the page with JavaScript rendered
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Handle cookie banners
        try:
            cookie_button_patterns = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'I Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//a[contains(text(), 'Accept')]"
            ]
            
            for pattern in cookie_button_patterns:
                try:
                    cookie_button = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, pattern))
                    )
                    cookie_button.click()
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
        except Exception as e:
            print(f"Error handling cookies: {e}")
        
        # Extract all links
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        # Find all links
        subpages = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Normalize the URL
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                # Only include links to the same domain
                parsed_href = urlparse(href)
                if parsed_href.netloc != base_domain:
                    continue
                full_url = href
            else:
                # Relative URL
                full_url = urljoin(url, href)
            
            # Exclude common non-relevant pages and fragments
            if any(x in full_url for x in ['#', 'javascript:', 'mailto:', 'tel:']):
                continue
                
            # Remove URL fragments
            full_url = full_url.split('#')[0]
            
            # Add to set of subpages if it's different from the original URL
            if full_url != url:
                subpages.add(full_url)
                
                # Limit to max_pages
                if len(subpages) >= max_pages:
                    break
        
        # Prioritize pages that might contain perk information
        prioritized_subpages = []
        keywords = ['perk', 'benefit', 'discount', 'offer', 'deal', 'promo', 'special', 'reward']
        
        # First add pages with relevant keywords
        for subpage in subpages:
            if any(keyword in subpage.lower() for keyword in keywords):
                prioritized_subpages.append(subpage)
                
        # Then add other pages up to max_pages
        remaining_slots = max_pages - len(prioritized_subpages)
        for subpage in subpages:
            if subpage not in prioritized_subpages and remaining_slots > 0:
                prioritized_subpages.append(subpage)
                remaining_slots -= 1
                
        return prioritized_subpages[:max_pages]
        
    except Exception as e:
        print(f"Error finding subpages: {e}")
        return []


def scrape_website_with_selenium(url: str) -> str:
    """
    Scrape a website using Selenium to handle cookies and pop-ups.
    
    Args:
        url: The URL to scrape
        
    Returns:
        The scraped text content
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Handle common cookie banners and popups
        try:
            # List of common cookie accept button patterns
            cookie_button_patterns = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'I Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//button[contains(text(), 'Accept Cookies')]",
                "//a[contains(text(), 'Accept')]",
                "//a[contains(text(), 'Accept All')]",
                "//div[contains(@class, 'cookie')]//*[contains(text(), 'Accept')]",
                "//div[contains(@id, 'cookie')]//*[contains(text(), 'Accept')]",
                "//div[contains(@class, 'gdpr')]//*[contains(text(), 'Accept')]",
                "//div[contains(@id, 'gdpr')]//*[contains(text(), 'Accept')]"
            ]
            
            # Try each pattern
            for pattern in cookie_button_patterns:
                try:
                    cookie_button = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, pattern))
                    )
                    cookie_button.click()
                    print(f"Clicked cookie banner using pattern: {pattern}")
                    time.sleep(1)
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
                
            # Handle popups (like newsletter signups, etc.)
            popup_close_patterns = [
                "//button[contains(@class, 'close')]",
                "//div[contains(@class, 'popup')]//*[contains(@class, 'close')]",
                "//div[contains(@class, 'modal')]//*[contains(@class, 'close')]",
                "//button[contains(text(), 'No thanks')]",
                "//button[contains(text(), 'Close')]",
                "//a[contains(text(), 'Close')]",
                "//span[contains(@class, 'close')]",
                "//div[contains(@class, 'popup')]//button",
                "//div[contains(@class, 'modal')]//button"
            ]
            
            for pattern in popup_close_patterns:
                try:
                    popup_button = WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, pattern))
                    )
                    popup_button.click()
                    print(f"Closed popup using pattern: {pattern}")
                    time.sleep(1)
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
        except Exception as e:
            print(f"Error handling cookies/popups: {e}")
        
        # Wait for content to load
        time.sleep(2)
        
        # Scroll down to load lazy content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text - remove extra whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        driver.quit()
        return text
    except Exception as e:
        print(f"Error scraping {url} with Selenium: {e}")
        # Fallback to regular scraping if Selenium fails
        return scrape_website_regular(url)


def scrape_website_regular(url: str) -> str:
    """
    Scrape the content of a website using regular requests as fallback.
    
    Args:
        url: The URL to scrape
        
    Returns:
        The scraped text content
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text - remove extra whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"Error scraping {url} with regular method: {e}")
        return ""


def extract_with_gpt(text: str) -> Dict[str, str]:
    """
    Use OpenAI GPT to extract perk information from text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Extracted information
    """
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
- "Money Value": The financial value of the perk (in USD or EUR if available). If no value is clear, return "Not found".

**Important rules**:
- Do not invent missing information.
- If a field cannot be found, respond exactly with "Not found".
- Output only valid JSON, no commentary.

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
            model="gpt-4o",
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


def has_missing_info(extracted_info: Dict[str, str]) -> bool:
    """
    Check if there is any missing information in the extracted data.
    
    Args:
        extracted_info: The extracted information dictionary
        
    Returns:
        True if any field has "Not found" value, False otherwise
    """
    return any(value == "Not found" for value in extracted_info.values())


def extract_domain(url: str) -> str:
    """
    Extract the domain name from a URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        The extracted domain name
    """
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if match:
        return match.group(1)
    return url


def extract_company_name(domain: str) -> str:
    """
    Extract a company name from a domain.
    
    Args:
        domain: The domain name
        
    Returns:
        The extracted company name
    """
    # Remove TLD
    company = re.sub(r'\.\w+$', '', domain)
    # Remove subdomains
    company = company.split('.')[-1]
    return company


def search_perplexity(query: str, api_key: str) -> str:
    """
    Search for information using the Perplexity API.
    
    Args:
        query: The search query
        api_key: The Perplexity API key
        
    Returns:
        The search results text
    """
    try:
        # Construct a query specifically about perks or benefits
        enhanced_query = f"{query} company perks discounts benefits offers"
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "pplx-7b-online",  # Use the appropriate model
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant that helps find detailed information about company perks, discounts, and special offers. Focus on finding specific details about what benefits are offered, their value, and how to access them. Search the web for the most current information."
                },
                {
                    "role": "user",
                    "content": f"I need detailed information about perks, discounts, or special offers provided by {enhanced_query}. Please search for specific details about:\n1. What exactly is offered (discounts, credits, services, etc.)\n2. The financial value of these perks\n3. How someone can claim or access these perks\n4. Any eligibility requirements"
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        json_response = response.json()
        if "choices" in json_response and len(json_response["choices"]) > 0:
            perplexity_text = json_response["choices"][0]["message"]["content"]
            
            # Extract sources if available
            sources = []
            if "links" in json_response:
                sources = json_response["links"]
            elif "sources" in json_response:
                sources = json_response["sources"]
            
            # Combine the text and sources
            result = perplexity_text
            if sources:
                result += "\n\nSources:\n"
                for idx, source in enumerate(sources[:5]):  # Limit to first 5 sources
                    result += f"{idx+1}. {source}\n"
            
            return result
        else:
            print("Unexpected response structure from Perplexity API")
            return ""
    except Exception as e:
        print(f"Error with Perplexity search: {e}")
        return ""


def enrich_with_perplexity(extracted_info: Dict[str, str], perplexity_text: str) -> Dict[str, str]:
    """
    Enrich the extracted information with data from Perplexity.
    
    Args:
        extracted_info: The original extracted information
        perplexity_text: The text from Perplexity API
        
    Returns:
        Enriched information dictionary
    """
    if not perplexity_text:
        return extracted_info
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        prompt = f"""
You are an information enrichment assistant. You have two sources of information about a company perk:

1. Initial extracted data:
{json.dumps(extracted_info, indent=2)}

2. Additional information from web search:
{perplexity_text}

Your task is to fill in any "Not found" fields in the initial data using the additional information.
Important rules:
- Only add information that is clearly stated in the additional information.
- Do not modify fields that already have content (not "Not found").
- If you cannot find information to fill a "Not found" field, keep it as "Not found".
- Output only valid JSON, no commentary.

Respond with the updated JSON:
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract the JSON part
        try:
            json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
            enriched = json.loads(json_str)
            return enriched
        except Exception as e:
            print(f"⚠️ Parsing error during enrichment: {e}")
            return extracted_info
    except Exception as e:
        print(f"Error enriching with Perplexity data: {e}")
        return extracted_info


