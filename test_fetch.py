from src.fetcher import PubMedFetcher

fetcher = PubMedFetcher()
results = fetcher.fetch_abstracts("Diabetes", max_results=3)

for res in results:
    print(f"ID: {res['id']}\nBaşlık: {res['title']}\n---")