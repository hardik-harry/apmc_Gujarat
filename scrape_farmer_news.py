import requests
from bs4 import BeautifulSoup

def get_farmer_news():
    url = "https://www.divyabhaskar.co.in/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    news_list = []
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Keywords related to farmers in Gujarati: ખેડૂત (farmer), ખેતી (farming), પાક (crop), કૃષિ (agriculture)
        keywords = ['ખેડૂત', 'ખેતી', 'પાક', 'કૃષિ']

        articles = soup.find_all(['h2', 'h3', 'a', 'p', 'span'])
        seen_texts = set()

        for article in articles:
            text = article.get_text().strip()
            if any(keyword in text for keyword in keywords):
                if len(text) > 15 and text not in seen_texts: # Filter out very short UI elements
                    seen_texts.add(text)
                    link = ""
                    # Try to find a link associated with this text
                    if article.name == 'a' and article.has_attr('href'):
                        link = article['href']
                    else:
                        parent_a = article.find_parent('a')
                        if parent_a and parent_a.has_attr('href'):
                            link = parent_a['href']
                    
                    if link and not link.startswith('http'):
                        link = "https://www.divyabhaskar.co.in" + link
                    
                    news_list.append({"title": text, "link": link})
        return news_list

    except Exception as e:
        print(f"An error occurred scraping news: {e}")
        return []

if __name__ == "__main__":
    # For testing independently
    news = get_farmer_news()
    with open('farmer_news_output.md', 'w', encoding='utf-8') as f:
        f.write(f"Found {len(news)} news items related to farmers:\n\n")
        for item in news:
            f.write(f"**Headline:** {item['title']}\n")
            if item['link']:
                f.write(f"**Link:** [{item['link']}]({item['link']})\n")
            f.write("-" * 50 + "\n")
        print("Scraping completed. Results saved to farmer_news_output.md")
