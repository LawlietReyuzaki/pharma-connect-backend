"""
Wikipedia and Wikimedia Commons Utilities
Provides functions to search Wikipedia, fetch summaries, images, and metadata with proper attribution.
"""

import requests
import logging
import re
from urllib.parse import quote, unquote

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = "RedDotPharmacyBot/1.0 (https://red-dot-pharmacy.replit.app; medical-chatbot)"


def wiki_search_top_title(query):
    """
    Search Wikipedia for the best matching page title.
    
    Args:
        query: The search query string
        
    Returns:
        The best matching page title or None if not found
    """
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
            "srprop": "snippet"
        }
        
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        search_results = data.get("query", {}).get("search", [])
        if search_results:
            return search_results[0].get("title")
        
        return None
        
    except Exception as e:
        logging.error(f"Wikipedia search error: {e}")
        return None


def fetch_wiki_summary(title):
    """
    Fetch the summary/extract of a Wikipedia page.
    
    Args:
        title: The Wikipedia page title
        
    Returns:
        A dictionary with title, summary, and page_url
    """
    try:
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "exsentences": 5,
            "inprop": "url",
            "format": "json"
        }
        
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":
                return {
                    "title": page_data.get("title", title),
                    "summary": page_data.get("extract", ""),
                    "page_url": page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{quote(title)}")
                }
        
        return None
        
    except Exception as e:
        logging.error(f"Wikipedia summary fetch error: {e}")
        return None


def fetch_wiki_images(title, max_images=4):
    """
    Fetch image file titles from a Wikipedia page.
    
    Args:
        title: The Wikipedia page title
        max_images: Maximum number of images to fetch (default 4)
        
    Returns:
        List of image file titles (e.g., "File:Example.jpg")
    """
    try:
        params = {
            "action": "query",
            "titles": title,
            "prop": "images",
            "imlimit": max_images + 5,
            "format": "json"
        }
        
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        image_titles = []
        
        for page_id, page_data in pages.items():
            if page_id != "-1":
                images = page_data.get("images", [])
                for img in images:
                    img_title = img.get("title", "")
                    if img_title and not any(
                        skip in img_title.lower() 
                        for skip in ["icon", "logo", "flag", ".svg", "commons-logo", "wikidata", "padlock"]
                    ):
                        image_titles.append(img_title)
                        if len(image_titles) >= max_images:
                            break
        
        return image_titles
        
    except Exception as e:
        logging.error(f"Wikipedia images fetch error: {e}")
        return []


def get_commons_metadata(file_title):
    """
    Fetch metadata for a Wikimedia Commons file including URL, license, and attribution.
    
    Args:
        file_title: The file title (e.g., "File:Example.jpg")
        
    Returns:
        Dictionary with url, license, license_url, artist, and credit
    """
    try:
        params = {
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json"
        }
        
        response = requests.get(
            COMMONS_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            if page_id != "-1":
                imageinfo = page_data.get("imageinfo", [{}])[0]
                extmeta = imageinfo.get("extmetadata", {})
                
                artist_html = extmeta.get("Artist", {}).get("value", "Unknown")
                artist = re.sub(r'<[^>]+>', '', artist_html).strip()
                artist = artist[:100] if len(artist) > 100 else artist
                
                license_name = extmeta.get("LicenseShortName", {}).get("value", "Unknown License")
                license_url = extmeta.get("LicenseUrl", {}).get("value", "")
                
                if not license_url and "cc" in license_name.lower():
                    license_url = "https://creativecommons.org/licenses/"
                elif not license_url:
                    license_url = "https://commons.wikimedia.org/wiki/Commons:Licensing"
                
                return {
                    "url": imageinfo.get("url", ""),
                    "thumb_url": imageinfo.get("url", "").replace("/commons/", "/commons/thumb/") + "/300px-" + file_title.replace("File:", "") if imageinfo.get("url") else "",
                    "license": license_name,
                    "license_url": license_url,
                    "artist": artist if artist and artist != "Unknown" else "Wikimedia Commons contributor",
                    "credit": "Wikimedia Commons",
                    "description": extmeta.get("ImageDescription", {}).get("value", "")[:200] if extmeta.get("ImageDescription") else ""
                }
        
        return None
        
    except Exception as e:
        logging.error(f"Commons metadata fetch error for {file_title}: {e}")
        return None


def get_image_direct_url(file_title):
    """
    Get the direct URL for a Wikipedia/Commons image.
    
    Args:
        file_title: The file title
        
    Returns:
        Direct URL to the image or None
    """
    try:
        params = {
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 300,
            "format": "json"
        }
        
        response = requests.get(
            COMMONS_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":
                imageinfo = page_data.get("imageinfo", [{}])[0]
                return imageinfo.get("thumburl") or imageinfo.get("url")
        
        return None
        
    except Exception as e:
        logging.error(f"Image URL fetch error: {e}")
        return None


def collect_wikipedia_resources(query):
    """
    Collect Wikipedia page summary for a query.
    Images are intentionally skipped — Commons.wikimedia.org causes
    network timeouts and the images are not reliable enough for display.

    Args:
        query: The search query

    Returns:
        Dictionary with title, page_url, summary, images=[], success
    """
    result = {
        "title": None,
        "page_url": None,
        "summary": None,
        "images": [],
        "success": False
    }

    try:
        title = wiki_search_top_title(query)
        if not title:
            return result

        summary_data = fetch_wiki_summary(title)
        if not summary_data:
            return result

        result["title"] = summary_data["title"]
        result["page_url"] = summary_data["page_url"]
        result["summary"] = summary_data["summary"]
        result["success"] = True

        logging.info(f"Wikipedia fetched for '{query}': {result['title']}")
        return result

    except Exception as e:
        logging.error(f"Wikipedia fetch error: {e}")
        return result


def build_wiki_context(wiki_data):
    """
    Build a context string from Wikipedia data to append to the AI prompt.
    
    Args:
        wiki_data: Dictionary from collect_wikipedia_resources()
        
    Returns:
        Formatted context string for the AI prompt
    """
    if not wiki_data or not wiki_data.get("success"):
        return ""
    
    context_parts = [
        f"\n[Wikipedia Context]",
        f"Topic: {wiki_data['title']}",
        f"Summary: {wiki_data['summary'][:500] if wiki_data.get('summary') else 'No summary available'}",
    ]
    
    if wiki_data.get("images"):
        context_parts.append(f"Related images available: {len(wiki_data['images'])} images from Wikimedia Commons")
    
    context_parts.append(
        "Use this Wikipedia information as additional context for your response. "
        "Ensure medical accuracy and always recommend consulting a healthcare professional."
    )
    
    return "\n".join(context_parts)


def extract_medical_keywords(text):
    """
    Extract medical keywords for Wikipedia search using fast heuristics only.
    No extra LLM calls — keeps latency low.

    Args:
        text: User's question/message

    Returns:
        Refined search query for Wikipedia
    """
    medical_keywords = [
        "fever", "headache", "pain", "cough", "cold", "flu", "diabetes",
        "blood pressure", "heart", "stomach", "infection", "allergy",
        "medicine", "drug", "treatment", "symptom", "disease", "condition",
        "paracetamol", "aspirin", "ibuprofen", "antibiotic", "hypertension",
        "asthma", "arthritis", "cancer", "depression", "anxiety", "vaccine",
        "diarrhea", "vomiting", "nausea", "rash", "pneumonia", "malaria",
        "dengue", "hepatitis", "tuberculosis", "cholesterol", "thyroid",
    ]

    text_lower = text.lower()
    found = [kw for kw in medical_keywords if kw in text_lower]
    if found:
        return " ".join(found[:3])

    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
    if words:
        return " ".join(words[:4])

    return text[:80]
