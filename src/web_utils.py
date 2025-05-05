import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# checks for 200 code from url
def is_url_alive(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# gets text from url
def scraper_beautiful_soup(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        texts = soup.find_all(['h1', 'h2', 'p', 'li'])
        page_text = "\n".join(t.get_text(strip=True) for t in texts)
        return page_text
    except Exception:
        return 

# deals with pages that have cookies to allow scraping
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
        
        page_source = driver.page_source
        if is_fake_404(page_source):
            print("ERROR: Detected 404-like error inside page (Selenium)")
            return 404
        
        return 200
    except Exception as e:
        print(f"INFO: Selenium failed: {e}")
        return None
    finally:
        driver.quit()

# checks if pages with 200 code are in reality active
def is_fake_404(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Check <title>
    if soup.title and any(word in soup.title.text.lower() for word in ["404", "page not found", "not found", "error"]):
        return True
    
    # Check main heading
    h1 = soup.find("h1")
    if h1 and any(word in h1.text.lower() for word in ["404", "page not found", "not found", "error"]):
        return True
    
    # Optional: check for known error container divs/classes
    error_keywords = ["error-page", "not-found", "404"]
    for keyword in error_keywords:
        if soup.find(class_=lambda x: x and keyword in x):
            return True
    
    return False

# gets the status code from each page
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
        
        # If 200 OK, double-check page content
        if is_fake_404(response.text):
            print("ERROR: Detected 404-like error inside page (GET content)")
            return 404
        
        return response.status_code
    except requests.RequestException as e:
        print(f"ERROR: Requests failed: {e}")
        # As fallback, use Selenium
        return access_page_with_cookies(url)

