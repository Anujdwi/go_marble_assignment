import requests
import cohere
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import re



def fetch_css_selectors(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    css_selectors = []

    review_keywords = r"(review|comment|feedback|text|body|content|post|entry|description|testimonial|rev(iew)?|customer|summary)"
    author_keywords = r"(author|user|name|profile|by|writer|creator|reviewer|posted\sby|submitter)"
    rating_keywords = r"(rating|stars|score|rank|grade|level|points|rate|review\-score|feedback\-rating)"
    pagination_keywords = r"(next|pagination|nav|page|forward|load\-more|show\-more|continue|arrow\-right|scroll\-next)"


    def extract_selectors(element):
        tag = element.name
        classes = element.get("class")
        id_value = element.get("id")
        class_selector = f".{'.'.join(classes)}" if classes else None
        id_selector = f"#{id_value}" if id_value else None

    # Define a helper function for regex matching
        def match_keywords(value, keywords):
            return value and re.search(keywords, value, re.IGNORECASE)

    # Check for class names
        if classes:
            for class_name in classes:
                if match_keywords(class_name, review_keywords):
                    css_selectors.append(f".{class_name}")
                elif match_keywords(class_name, author_keywords):
                    css_selectors.append(f".{class_name}")
                elif match_keywords(class_name, rating_keywords):
                    css_selectors.append(f".{class_name}")
                elif match_keywords(class_name, pagination_keywords):
                    css_selectors.append(f".{class_name}")

    # Check for ID attributes
        if id_value:
            if match_keywords(id_value, review_keywords):
                css_selectors.append(f"#{id_value}")
            elif match_keywords(id_value, author_keywords):
                css_selectors.append(f"#{id_value}")
            elif match_keywords(id_value, rating_keywords):
                css_selectors.append(f"#{id_value}")
            elif match_keywords(id_value, pagination_keywords):
                css_selectors.append(f"#{id_value}")

    # Check for tag names
        if match_keywords(tag, review_keywords):
            css_selectors.append(tag)
        elif match_keywords(tag, author_keywords):
            css_selectors.append(tag)
        elif match_keywords(tag, rating_keywords):
            css_selectors.append(tag)
        elif match_keywords(tag, pagination_keywords):
            css_selectors.append(tag)

    # Recursively check children elements
        for child in element.children:
            if hasattr(child, "children"):
                extract_selectors(child)


    extract_selectors(soup)
    print(css_selectors)
    return list(set(css_selectors))

def get_tag_suggestions(css_selectors, api_key):
    # Initialize Cohere client
    co = cohere.Client(api_key)
    
    # Create the prompt
    prompt = f"""You are given a list of CSS selectors extracted from a website:
{json.dumps(css_selectors, indent=2)}

Your task is to analyze these selectors and determine the best matches for the following elements:
1. Review text body
2. Author name
3. Rating element
4. Next pagination button

### Guidelines for Selection:
- **Review Text Body:** Look for classes, IDs, or tags containing terms such as 'review', 'comment', 'text', 'content', 'body', 'feedback', 'testimonial', or similar keywords.
- **Author Name:** Identify selectors containing words like 'author', 'user', 'name', 'profile', 'by', 'reviewer', 'creator', or 'submitter'.
- **Rating Element:** Focus on selectors with terms like 'rating', 'stars', 'score', 'rank', 'grade', 'review-score', or similar indicators of numeric or star-based ratings.
- **Next Pagination Button:** Look for terms such as 'next', 'pagination', 'nav', 'page', 'load-more', 'show-more', 'forward', 'arrow-right', or similar navigation elements.

### Constraints:
- Use regex patterns to identify relevant selectors for each element based on keyword matches in class names, IDs, and tag names.
- Prioritize selectors with multiple keyword matches or stronger indicators.
- Return only the most relevant selector for each category.

### Expected Output Format:
You must return only a JSON object in the following exact format:
{{
    "review_tag": "selector_for_review_body",
    "author_tag": "selector_for_author_name",
    "rating_tag": "selector_for_rating",
    "next_pagination_button_tag": "selector_for_next_button"
}}
"""
    
    # Query Cohere API
    try:
        response = co.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=300,
        )
        print("Cohere API Response:", response.generations)
        if not response.generations or not response.generations[0].text:
            print("Error: Empty response from Cohere API")
            return {
                "review_tag": None,
                "author_tag": None,
                "rating_tag": None,
                "next_pagination_button_tag": None
            }
        return json.loads(response.generations[0].text.strip())
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {
            "review_tag": None,
            "author_tag": None,
            "rating_tag": None,
            "next_pagination_button_tag": None
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "review_tag": None,
            "author_tag": None,
            "rating_tag": None,
            "next_pagination_button_tag": None
        }
    
def fetch_all_reviews(url, review_tag, author_tag, rating_tag, next_page_button_tag):
    # Set up Selenium WebDriver
    service = Service("chromedriver.exe")  # Update this path
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()  # Maximize window for better visibility

    try:
        # Open the webpage
        driver.get(url)
        wait = WebDriverWait(driver, 10)  # Wait for elements to load

        all_reviews = []
        page_number = 1  # Track the current page number for debugging

        while True:
            handle_popups(driver)
            try:
                # Wait for the reviews section to load
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, review_tag)))

                # Get the current page source and parse it with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Find all review elements using the passed review_tag, author_tag, and rating_tag
                review_elements = soup.select(review_tag)
                author_elements = soup.select(author_tag)
                rating_elements = soup.select(rating_tag)

                # Extract reviews, authors, and ratings
                for review, author, rating in zip(review_elements, author_elements, rating_elements):
                    review_text = review.get_text(strip=True)
                    author_name = author.get_text(strip=True)
                    rating_score = rating.get("data-score", "N/A")  # Extract 'data-score' or use 'N/A' if missing
                    all_reviews.append({
                        "review": review_text,
                        "author": author_name,
                        "rating": rating_score
                    })

                print(f"Page {page_number} scraped successfully with {len(review_elements)} reviews.")
                page_number += 1

                # Scroll the "Next Page" button into view and click it
                try:
                    next_page_button = driver.find_element(By.CSS_SELECTOR, next_page_button_tag)
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_page_button_tag))).click()
                    time.sleep(2)  # Small pause to ensure the page loads
                except (NoSuchElementException, TimeoutException):
                    print("No more pages to scrape or 'Next Page' button not found.")
                    break
                except ElementClickInterceptedException as e:
                    print(f"Click intercepted on page {page_number}: {str(e)}")
                    ActionChains(driver).move_to_element_with_offset(next_page_button, 0, 0).click().perform()
            except Exception as e:
                print(f"Error scraping page {page_number}: {str(e)}")
                break

    finally:
        # Ensure the browser is closed properly
        driver.quit()

    return all_reviews

def handle_popups(driver):
    try:
        popups = driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], [class*='needsclick']")
        for popup in popups:
            if popup.is_displayed():
                print("Found and dismissing a popup.")
                close_button = popup.find_element(By.CSS_SELECTOR, "button, .close, .dismiss, [aria-label='Close']")
                if close_button.is_displayed() and close_button.is_enabled():
                    close_button.click()
                    time.sleep(1)  
                    return True
    except NoSuchElementException:
        print("No dismissable pop-ups found.")
    except Exception as e:
        print(f"Error while handling pop-ups: {e}")
    return False

# Save reviews to a JSON file
def save_reviews_to_file(reviews, filename="reviews.json"):
    data = {
        "reviews_count": len(reviews),
        "reviews": reviews,
    }
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Reviews saved to {filename}")
    return data 

if __name__ == "__main__":
    # URL of the webpage to scrape
    url = "https://2717recovery.com/products/recovery-cream"  # Replace with the target URL
    

    # CSS Selectors for this specific site
    css_selectors = fetch_css_selectors(url)
    tag_suggestions = get_tag_suggestions(css_selectors, api_key)
    reviews = fetch_all_reviews(
        url,
        tag_suggestions['review_tag'],
        tag_suggestions['author_tag'],
        tag_suggestions['rating_tag'],
        tag_suggestions['next_pagination_button_tag']
    )
    save_reviews_to_file(reviews)