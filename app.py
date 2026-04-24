import streamlit as st
import pandas as pd
from src.fetcher import PubMedFetcher
from src.processor import BioProcessor

# Sayfa ayarları
st.set_page_config(page_title="Bio-NLP PubMed Analyzer", layout="wide")

st.title("🧬 Bio-NLP: PubMed Literatür Madenciliği")
st.markdown("Hastalık ismi girin, AI makalelerdeki genleri ve tıbbi terimleri bulsun.")

# Sidebar - Ayarlar
with st.sidebar:
    st.header("⚙️ Ayarlar")
    max_results = st.slider("Makale Sayısı", 1, 20, 5)
    min_confidence = st.slider("Güven Skoru Filtresi", 0.0, 1.0, 0.6)

# Modelleri yükle (Caching sayesinde sadece 1 kez yüklenir)
@st.cache_resource
def load_tools():
    return PubMedFetcher(), BioProcessor()

fetcher, processor = load_tools()

# Arama Alanı
query = st.text_input("Araştırmak istediğiniz hastalık:", placeholder="Örn: Alzheimer, Breast Cancer...")

if query:
    with st.spinner("Makaleler getiriliyor ve analiz ediliyor..."):
        articles = fetcher.fetch_abstracts(query, max_results=max_results)
        
        if not articles:
            st.warning("Makale bulunamadı.")
        else:
            all_found_entities = []
            
            # Sonuçları göster
            for art in articles:
                with st.expander(f"📄 {art['title']}"):
                    full_text = f"{art['title']}. {art['abstract']}"
                    raw_ents = processor.extract_entities(full_text)
                    clean_ents = processor.clean_entities(raw_ents)
                    
                    # Filtrelenmiş sonuçlar
                    filtered = [e for e in clean_ents if e['confidence'] >= min_confidence]
                    
                    if filtered:
                        df = pd.DataFrame(filtered)
                        st.table(df) # Terimleri tablo olarak bas
                        all_found_entities.extend([e['word'] for e in filtered])
                    else:
                        st.write("Kritik terim bulunamadı.")

            # --- ANALİZ BÖLÜMÜ ---
            if all_found_entities:
                st.divider()
                st.header("📊 Genel Analiz")
                top_words = processor.get_top_entities([{'word': w} for w in all_found_entities], limit=5)
                
                # Grafik oluşturma
                chart_data = pd.DataFrame(top_words, columns=['Terim', 'Frekans'])
                st.bar_chart(chart_data.set_index('Terim'))