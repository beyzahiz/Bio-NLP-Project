from src.fetcher import PubMedFetcher
from src.processor import BioProcessor

def run_pipeline(disease_query):
    # 1. Başlatıcılar
    fetcher = PubMedFetcher()
    processor = BioProcessor()
    
    print(f"\n--- '{disease_query}' ile ilgili makaleler analiz ediliyor ---\n")
    
    # 2. Verileri Çek (Cache mekanizması burada çalışacak)
    articles = fetcher.fetch_abstracts(disease_query, max_results=3)
    
    if not articles:
        print("Makale bulunamadı.")
        return

    all_findings = []

    # 3. Her makaleyi tek tek işle
    for art in articles:
        print(f"İşleniyor: {art['title'][:50]}...")
        
        # Başlık ve özeti birleştirip analiz edelim
        full_text = f"{art['title']}. {art['abstract']}"
        
        raw_entities = processor.extract_entities(full_text)
        clean_entities = processor.clean_entities(raw_entities)
        
        all_findings.append({
            "title": art['title'],
            "entities": clean_entities
        })

    # 4. Sonuçları ekrana bas
    print("\nANALİZ SONUÇLARI ")
    for finding in all_findings:
        print(f"\nMakale: {finding['title']}")
        for ent in finding['entities']:
            print(f"  - [{ent['label']}] {ent['word']} (Güven: {ent['confidence']})")

if __name__ == "__main__":
    query = input("Hangi hastalığı araştırmak istersiniz? (Örn: Alzheimer): ")
    run_pipeline(query)