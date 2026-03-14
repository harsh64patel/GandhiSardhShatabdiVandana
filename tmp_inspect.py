import requests
from bs4 import BeautifulSoup

url = "https://rameshozajournalistblog.wordpress.com/category/%E0%AA%97%E0%AA%BE%E0%AA%82%E0%AA%A7%E0%AB%80-%E0%AA%B8%E0%AA%BE%E0%AA%B0%E0%AB%8D%E0%AA%A7-%E0%AA%B6%E0%AA%A4%E0%AA%BE%E0%AA%AC%E0%AB%8D%E0%AA%A6%E0%AB%80-%E0%AA%B5%E0%AA%82%E0%AA%A6%E0%AA%A8/page/1/"
print('Fetching', url)

r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
print('Status', r.status_code)

soup = BeautifulSoup(r.text, 'html.parser')
posts = soup.select('article h2.entry-title a')
print('Found posts', len(posts))
for a in posts[:3]:
    print('-', a.text.strip(), a['href'])

if posts:
    print('\nFetching first post content...')
    r2 = requests.get(posts[0]['href'], headers={'User-Agent': 'Mozilla/5.0'})
    s2 = BeautifulSoup(r2.text, 'html.parser')
    c = s2.select_one('div.entry-content')
    print('content selector', bool(c))
    if c:
        print(c.text.strip()[:400])
