import requests
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp, JsonConfig
from pydantic import BaseModel, Field
import os
import config


def is_url_alive(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def scraper_beautiful_soup(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        texts = soup.find_all(['h1', 'h2', 'p', 'li'])
        page_text = "\n".join(t.get_text(strip=True) for t in texts)
        return page_text
    except Exception:
        return 


















