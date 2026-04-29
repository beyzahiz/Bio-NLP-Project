import requests
import sqlite3
import pandas as pd
import xml.etree.ElementTree as ET # XML parçalamak için

class PubMedFetcher:
    def __init__(self, db_path="data/pubmed_cache.db"):
        self.db_path = db_path
        
        # Klasörün varlığını kontrol et, yoksa oluştur
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self._create_table()

    def _create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                query TEXT,
                title TEXT,
                abstract TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def fetch_abstracts(self, disease_name, max_results=10):
        # Önce veritabanındaki sayıyı kontrol edilir
        cached_data = self._check_cache(disease_name)
        
        # eğer veritabanında yeterli veya daha fazla makale varsa, direkt döndürür
        if cached_data and len(cached_data) >= max_results:
            print(f"'{disease_name}' için yeterli veri ({len(cached_data)}) yerel veritabanında bulundu.")
            return cached_data[:max_results]

        # eğer veritabanında hiç yoksa veya istenenden az varsa API'ye gider
        print(f"'{disease_name}' için veritabanında yeterli kayıt yok. API'den yeni veriler ekleniyor...")
        
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        search_url = f"{base_url}esearch.fcgi?db=pubmed&term={disease_name}&retmax={max_results}&retmode=json"
        
        response = requests.get(search_url).json()
        id_list = response.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            return cached_data if cached_data else []

        ids = ",".join(id_list)
        fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={ids}&retmode=xml"
        fetch_response = requests.get(fetch_url)
        
        articles = self._parse_xml(fetch_response.content, disease_name)
        
        # yeni gelenleri kaydeder 
        self._save_to_cache(articles)
        
        # güncel veriyi tekrar çeker ve istenen miktarda döndür
        updated_data = self._check_cache(disease_name)
        return updated_data[:max_results]

    def _check_cache(self, query):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT id, title, abstract FROM articles WHERE query=?", conn, params=(query,))
        conn.close()
        return df.to_dict('records') if not df.empty else None

    def _save_to_cache(self, articles):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for art in articles:
            cursor.execute("INSERT OR IGNORE INTO articles VALUES (?, ?, ?, ?)", 
                           (art['id'], art['query'], art['title'], art['abstract']))
        conn.commit()
        conn.close()

    def _parse_xml(self, xml_content, query):
        root = ET.fromstring(xml_content)
        parsed_articles = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.find(".//PMID").text
            title = article.find(".//ArticleTitle").text
            abstract_text = ""
            abstract_element = article.find(".//AbstractText")
            if abstract_element is not None:
                abstract_text = abstract_element.text
            
            parsed_articles.append({
                "id": pmid,
                "query": query,
                "title": title,
                "abstract": abstract_text
            })
        return parsed_articles