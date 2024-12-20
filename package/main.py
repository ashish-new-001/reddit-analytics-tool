from flask import Flask, render_template, request, send_file
import praw
import prawcore
from textblob import TextBlob
import json
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Replace with your app credentials
CLIENT_ID = "Hv2CsYGXf4W4K_ixeRErTA"
CLIENT_SECRET = "Ia5yxU7wr5ipVCknwByGqx7YfrRvaQ"
USER_AGENT = "GoldRude9007"

# Authenticate with Reddit
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return "Positive"
    elif analysis.sentiment.polarity < 0:
        return "Negative"
    else:
        return "Neutral"

# Function to fetch posts
def fetch_posts(subreddits, limit=5, time_filter='all'):
    posts = []
    for subreddit_name in subreddits:
        try:
            subreddit = reddit.subreddit(subreddit_name.strip())
            for post in subreddit.top(limit=limit, time_filter=time_filter):
                sentiment = analyze_sentiment(post.title)
                posts.append({
                    'subreddit': subreddit_name,
                    'title': post.title,
                    'score': post.score,
                    'comments': post.num_comments,
                    'link': f"https://reddit.com{post.permalink}",
                    'sentiment': sentiment
                })
        except Exception as e:
            print(f"Error fetching posts from r/{subreddit_name}: {e}")
            # Continue to the next subreddit without halting the loop
            continue
    return posts


# Function to save posts to a JSON file
def save_to_json(posts):
    filename = f"reddit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(posts, f, indent=4)
    return filename

# Function to save posts to a CSV file
def save_to_csv(posts):
    filename = f"reddit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Subreddit', 'Title', 'Score', 'Comments', 'Sentiment', 'Link'])
        for post in posts:
            writer.writerow([post['subreddit'], post['title'], post['score'], post['comments'], post['sentiment'], post['link']])
    return filename

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def results():
    subreddits = request.form['subreddits'].split(',')
    time_filter = request.form.get('time_filter', 'all')
    sort_by = request.form.get('sort_by', 'score')
    post_limit = int(request.form.get('post_limit', 5))  # Default to 5 posts if not specified

    # Initialize an empty list to collect all posts
    all_posts = []

    for subreddit in subreddits:
        # Fetch posts for each subreddit and append them to the all_posts list
        posts = fetch_posts([subreddit], limit=post_limit, time_filter=time_filter)
        all_posts.extend(posts)

    # Sort the combined list of posts based on the user's choice
    if sort_by in ['score', 'comments']:
        all_posts = sorted(all_posts, key=lambda x: x[sort_by], reverse=True)
    elif sort_by == 'subreddit':
        all_posts = sorted(all_posts, key=lambda x: x[sort_by])

    # Render the results page with all combined posts
    return render_template('results.html', posts=all_posts)


@app.route('/save', methods=['POST'])
def save():
    posts = json.loads(request.form['posts'])
    file_format = request.form.get('file_format', 'json')
    if file_format == 'json':
        filename = save_to_json(posts)
    elif file_format == 'csv':
        filename = save_to_csv(posts)
    else:
        return "Invalid file format", 400
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)