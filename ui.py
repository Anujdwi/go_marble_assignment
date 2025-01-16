import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Function to scrape reviews (example implementation)
def fetch_reviews(url):
    # Configure Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service("chromedriver")  # Update with the correct path
    driver = webdriver.Chrome(service=service, options=chrome_options)

    reviews = []
    try:
        driver.get(url)
        # Example selectors for reviews
        review_elements = driver.find_elements(By.CSS_SELECTOR, ".review-class")  # Update based on website structure
        for element in review_elements:
            title = element.find_element(By.CSS_SELECTOR, ".review-title").text
            body = element.find_element(By.CSS_SELECTOR, ".review-body").text
            rating = element.find_element(By.CSS_SELECTOR, ".review-rating").text
            reviews.append({"Title": title, "Body": body, "Rating": rating})
    except Exception as e:
        st.error(f"Error fetching reviews: {e}")
    finally:
        driver.quit()
    
    return pd.DataFrame(reviews)

# Streamlit UI
st.title("Enter the website")

# URL input
url = st.text_input("Enter the product page URL:")

# Fetch reviews button
if st.button("Fetch Reviews"):
    if url:
        with st.spinner("Fetching reviews..."):
            reviews_df = fetch_reviews(url)
            if not reviews_df.empty:
                st.success("Reviews fetched successfully!")
                
                # Display reviews as a table
                st.write("Sample Reviews:")
                st.dataframe(reviews_df.head())
                
                # Download button for the reviews file
                csv = reviews_df.to_csv(index=False)
                st.download_button(
                    label="Download Reviews as CSV",
                    data=csv,
                    file_name="reviews.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No reviews found. Please check the URL.")
    else:
        st.error("Please enter a valid URL.")


