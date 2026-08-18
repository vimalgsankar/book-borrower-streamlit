import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://openlibrary.org/search.json?q=subject:fiction&limit=300"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    print("Fetching from OpenLibrary...")
    data = json.loads(urllib.request.urlopen(req, context=ctx).read())
    books = []
    seen = set()
    for doc in data.get('docs', []):
        if 'title' in doc and 'author_name' in doc:
            title = doc['title']
            if title in seen:
                continue
            seen.add(title)
            books.append({
                "title": title,
                "author": doc['author_name'][0],
                "genre": "Fiction",
                "description": "A wonderful fiction novel.",
                "rating": round(3.5 + (0.1 * (len(title) % 15)), 1)
            })
            if len(books) == 250:
                break
    with open('books.json', 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=2)
    print(f"Saved {len(books)} books.")
except Exception as e:
    print(e)
