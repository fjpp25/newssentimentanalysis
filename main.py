import datetime
import urllib.parse
import requests
import time
from bs4 import BeautifulSoup
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')

NEWS_API_KEY = 'ec042041f329498f9b353e0ee519c55f'   # TODO: find a way to encrypt my private API key
NEWS_API_URL = 'https://newsapi.org/v2/everything'

KEYWORDS = ['positive_word', 'negative_word', 'neutral_word']  # e.g., ['happy', 'sad', 'economy']

# first, we make a query to the News API server, which requires:
# - a search term (eg. forex, markets, dollar, etc)
# - an API key, as NewsAPI requires a license
# - a date, which should be today since we are looking for fast information
# - the way in which we want to sort the articles
# - and the maximum number of results, which for the free plan is maxed out at 100 per query.
# This query returns a json response with news articles and their respective information that contain
# the term we searched for. Then, we go through each of those articles, save each of their URLs in a list,
# and return that list so that it can be consumed by the next function.
def fetch_news_urls(query='', num_articles=100, sortBy='popularity'):
    TODAY = datetime.date.today().strftime('%Y-%m-%d')
    YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    params = {
        'q': query,
        'apiKey': NEWS_API_KEY,
        'from': YESTERDAY,  # TODO: build logic to check if today's news appear, and use yesterday yesterday to avoid free plan delay
        'sortBy': sortBy,
        'pageSize': min(num_articles, 100) # NewsAPI has a maximum number of 100 results, which can be worked around by making multiple queries for different terms
    }
    # We need to format the URL with our parameters:
    formatted_url = f"{NEWS_API_URL}?{urllib.parse.urlencode(params)}"
    url_list = []

    # We envelop our actions in a try/catch so that we can handle request exceptions:
    try:
        response = requests.get(formatted_url)
        response.raise_for_status()
        # the response Json gives us a list of articles that contain the search term
        loaded_response = response.json()
        articles = loaded_response.get('articles', [])
        print(loaded_response)
        print(articles)
        # under each Article section of the response json, we fetch the corresponding URL and append it to the URL list
        for article in articles:
            url_list.append(article.get('url', 'No URL found'))

        # for debugging purposes, I decided to save the URL list in a txt file, we can do away with this section altogether if needed
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        news_file = os.path.join(output_dir, "my_news_urls.txt")
        with open(news_file, 'w', encoding='utf-8') as file:
            for url in url_list:
                file.write(url + '\n')
    # here we just handle the request exception with an error message; during testing, no exception ever came up
    except requests.RequestException as e:
        print(f"Error fetching news: {e}")

    return url_list

# In the sentiment analysis function, the idea is to fetch the HTMl text content of each of the previously saved URLs,
# and then, using the SentimentIntensityAnalyzer from nltk, we analyze content of each article word by word, where some words
# imply a positive sentiment (e.g. "hopeful", "bullish"), some imply a negative sentiment (e.g. "fearful", "nearish"). and
# some words imply a neutral sentiment (e.g. "economy"). Some words carry more "sentiment points", positive or negative,
# than others - for example, "panic" is worse than "concern". To fully understand this, please refer to the
# SentimentIntensityAnalizer documentation.
def go_through_articles(list_of_urls):
    sid = SentimentIntensityAnalyzer()
    article_data = []  # Store only relevant data and sentiment

    # we use somatorium variables to add up the sentiments contained in each article
    sum_of_positive = 0.0
    sum_of_neutral = 0.0
    sum_of_negative = 0.0

    for url in list_of_urls:
        # Once again, we handle everything within a try/catch, so as to handle possible request exceptions. Some articles
        # may have automation protection software that blocks automated or repeated requests, for example.
        try:
            url_response = requests.get(url, timeout=10)
            url_response.raise_for_status()

            # We only do anything if the URL response is 200, since otherwise there would be no article content
            if url_response.status_code == 200:
                soup = BeautifulSoup(url_response.text, 'html.parser')
                content_elements = soup.find_all(['p', 'div', 'article'])
                article_text = ' '.join([elem.get_text().strip() for elem in content_elements if elem.get_text().strip()])
                # Here we perform sentiment analysis
                sentiment_scores = sid.polarity_scores(article_text)
                sentiment = {
                    'compound': sentiment_scores['compound'],  # Overall sentiment score
                    'positive': sentiment_scores['pos'],
                    'negative': sentiment_scores['neg'],
                    'neutral': sentiment_scores['neu']
                }
                sum_of_positive += sentiment_scores['pos']
                sum_of_neutral += sentiment_scores['neu']
                sum_of_negative += sentiment_scores['neg']
                # Store only necessary data
                article_data.append({
                    'url': url,
                    'text': article_text[:100],  # Store first 500 chars to save memory
                    'sentiment': sentiment
                })
                print(f"Processed {url}: Sentiment = {sentiment}")
            time.sleep(1)  # We use a 1 second sleep so as to avoid rate limiting by article websites
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            article_data.append({'url': url, 'text': '', 'sentiment': {'error': str(e)}})
        except Exception as e:
            print(f"Error processing {url}: {e}")
            article_data.append({'url': url, 'text': '', 'sentiment': {'error': str(e)}})

        print("sum of positive sentiment is:")
        print(sum_of_positive)
        print("sum of neutral sentiment is:")
        print(sum_of_neutral)
        print("sum of negative sentiment is:")
        print(sum_of_negative)

    return article_data

def main():
    list_of_urls = fetch_news_urls(query='markets', num_articles=49, sortBy='popularity')
    go_through_articles(list_of_urls)

if __name__ == "__main__":
    main()