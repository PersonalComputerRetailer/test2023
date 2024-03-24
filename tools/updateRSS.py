import feedparser
from bs4 import BeautifulSoup
import requests
from datetime import datetime

# Function to extract relevant information from your website's HTML
def extract_information(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = soup.find_all('li')  # Assuming each <li> contains an article
    articles_info = []
    for article in articles:
        title = article.find('a').text.strip()
        link = article.find('a')['href']
        date_string = article.find('time')['datetime']
        # Parse date string to datetime object
        pubDate = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%a, %d %b %Y %H:%M:%S")
        description = f"Published on {pubDate}"
        articles_info.append({'title': title, 'link': link, 'description': description, 'pubDate': pubDate})
    return articles_info

# Function to generate RSS feed
def generate_rss(articles_info):
    rss_feed = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss_feed += '<rss version="2.0">\n'
    rss_feed += '<channel>\n'
    rss_feed += '<title>WILL\'s CYBER BLOG</title>\n'
    rss_feed += '<link>https://willscyber.net/blog/blog.html</link>\n'
    rss_feed += '<description>WILL\'s CYBER BLOG</description>\n'
    rss_feed += '<language>en-us</language>\n'
    rss_feed += f'<lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S")} GMT</lastBuildDate>\n'
    rss_feed += f'<pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S")} GMT</pubDate>\n'
    for article in articles_info:
        rss_feed += '<item>\n'
        rss_feed += f'<title>{article["title"]}</title>\n'
        rss_feed += f'<link>{article["link"]}</link>\n'
        rss_feed += f'<description>{article["description"]}</description>\n'
        rss_feed += f'<pubDate>{article["pubDate"]}</pubDate>\n'  # Use the publication date of the article
        rss_feed += '</item>\n'
    rss_feed += '</channel>\n'
    rss_feed += '</rss>\n'
    return rss_feed

# URL of your website
website_url = 'https://willscyber.net/blog/blog.html'
response = requests.get(website_url)
if response.status_code == 200:
    html_content = response.content
    articles_info = extract_information(html_content)
    rss_feed = generate_rss(articles_info)
    with open('../blog/willscyber_blog_feed.xml', 'w', encoding='utf-8') as f:
        f.write(rss_feed)
    print('RSS feed generated successfully!')
else:
    print('Failed to retrieve website content.')
