from flask import Flask, request, jsonify
from utils import *

app = Flask(__name__)

@app.route('/api/reviews')

def extract_reviews():
    url = request.args.get('page')
    
    if not url:
        return jsonify({"error": "Missing 'page' query parameter"}), 400

    css_selectors = fetch_css_selectors(url)
    tag_suggestions = get_tag_suggestions(css_selectors, api_key)
    reviews = fetch_all_reviews(
        url,
        tag_suggestions['review_tag'],
        tag_suggestions['author_tag'],
        tag_suggestions['rating_tag'],
        tag_suggestions['next_pagination_button_tag']
    )
    return jsonify(save_reviews_to_file(reviews))

if __name__ == '__main__':
    app.run(debug=True)
