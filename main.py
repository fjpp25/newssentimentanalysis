import datetime
import urllib.parse
import requests
import time
from bs4 import BeautifulSoup
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')

NEWS_API_KEY = 'ec042041f329498f9b353e0ee519c55f'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

KEYWORDS = ['positive_word', 'negative_word', 'neutral_word']  # e.g., ['happy', 'sad', 'economy']

def fetch_news_urls(query='', num_articles=100, sortBy='popularity'):
    print(query)
    YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    params = {
        'q': query,
        'apiKey': NEWS_API_KEY,
        'from': YESTERDAY,  # Use yesterday to avoid free plan delay
        'sortBy': sortBy,
        'pageSize': min(num_articles, 100)
    }
    formatted_url = f"{NEWS_API_URL}?{urllib.parse.urlencode(params)}"
    print(formatted_url)
    url_list = []

    try:
        response = requests.get(formatted_url)
        print(response)
        response.raise_for_status()
        loaded_response = response.json()
        articles = loaded_response.get('articles', [])
        print(loaded_response)

        for article in articles:
            url_list.append(article.get('url', 'No URL found'))

        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        news_file = os.path.join(output_dir, "my_news_data.txt")
        with open(news_file, 'w', encoding='utf-8') as file:
            for url in url_list:
                file.write(url + '\n')
        print(url_list)

    except requests.RequestException as e:
        print(f"Error fetching news: {e}")

    return url_list

def go_through_articles(list_of_urls):
    sid = SentimentIntensityAnalyzer()
    article_data = []  # Store only relevant data and sentiment

    sum_of_positive = 0.0
    sum_of_neutral = 0.0
    sum_of_negative = 0.0

    for url in list_of_urls:
        try:
            url_response = requests.get(url, timeout=10)
            url_response.raise_for_status()

            if url_response.status_code == 200:
                soup = BeautifulSoup(url_response.text, 'html.parser')
                content_elements = soup.find_all(['p', 'div', 'article'])
                article_text = ' '.join([elem.get_text().strip() for elem in content_elements if elem.get_text().strip()])
            # Perform sentiment analysis
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
            time.sleep(1)  # Rate limiting
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