import requests
from bs4 import BeautifulSoup
import re

def get_social_links_from_website(url):
    social_media_patterns = [
        'facebook.com',
        'linkedin.com/company',
        'twitter.com',
        'instagram.com',
        'youtube.com',
        'pinterest.com'
    ]
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        found_links = set() # Use a set to avoid duplicates
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(pattern in href for pattern in social_media_patterns):
                found_links.add(href)
                
        return list(found_links)
        
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

# Example usage:
company_url = "http://www.waltonplc.com" 
links = get_social_links_from_website(company_url)
print(links)