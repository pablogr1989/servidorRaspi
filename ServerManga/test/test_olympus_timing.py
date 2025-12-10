# test_olympus_timing.py (crear en raiz proyecto)

import time
from playwright.sync_api import sync_playwright

url = 'https://olympusbiblioteca.com/series/comic-27-220-225-565464565465'

with sync_playwright() as p:
    t_start = time.time()
    
    browser = p.chromium.launch(headless=True)
    t_browser = time.time()
    print(f"Browser launch: {t_browser - t_start:.2f}s")
    
    page = browser.new_page()
    t_page = time.time()
    print(f"New page: {t_page - t_browser:.2f}s")
    
    page.goto(url, timeout=30000)
    t_goto = time.time()
    print(f"Page load: {t_goto - t_page:.2f}s")
    
    page.wait_for_selector('.chapter-name', timeout=15000)
    t_selector = time.time()
    print(f"Wait selector: {t_selector - t_goto:.2f}s")
    
    chapter_divs = page.query_selector_all('.chapter-name')
    t_query = time.time()
    print(f"Query all: {t_query - t_selector:.2f}s")
    
    chapter_text = chapter_divs[0].inner_text()
    t_text = time.time()
    print(f"Get text: {t_text - t_query:.2f}s")
    
    browser.close()
    t_close = time.time()
    print(f"Close browser: {t_close - t_text:.2f}s")
    
    print(f"\nTOTAL: {t_close - t_start:.2f}s")
    print(f"Chapter: {chapter_text}")