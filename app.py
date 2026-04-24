import streamlit as st
import pandas as pd
from src.fetcher import PubMedFetcher
from src.processor import BioProcessor

# Sayfa ayarları
st.set_page_config(page_title="Bio-NLP PubMed Analyzer", layout="wide")

st.title("🧬 Bio-NLP: PubMed Literatür Madenciliği")
st.markdown("Hastalık ismi girin, AI makalelerdeki genleri ve tıbbi terimleri bulsun.")

# Sidebar - Ayarlar Güncellemesi
with st.sidebar:
    st.header(" Analiz Ayarları")
    max_results = st.slider("İncelenecek Makale Sayısı", 1, 20, 5)
    
    # Teknik terimi kullanıcı dostu yaptık
    min_confidence = st.slider(
        "Yapay Zeka Hassasiyeti (Güven Skoru)", 
        0.0, 1.0, 0.6,
        help="Yüksek değerler daha kesin sonuçlar verir, düşük değerler daha fazla terim yakalar."
    )
    st.info(" Hassasiyeti artırırsanız sadece AI'nın çok emin olduğu tıbbi terimler listelenir.")

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
                st.header("📊 Literatürde Öne Çıkan Terimler")
                st.write("Arattığınız hastalıkla ilgili makalelerde en sık rastlanan anahtar kelimeler:")
    
                top_words = processor.get_top_entities([{'word': w} for w in all_found_entities], limit=10)
                chart_data = pd.DataFrame(top_words, columns=['Tıbbi Terim', 'Geçme Sıklığı'])
    
                # Daha şık bir bar chart
                st.bar_chart(chart_data.set_index('Tıbbi Terim'))

            
            if articles:
                report_data = []
    
                for art in articles:
                    full_text = f"{art['title']}. {art['abstract']}"
                    raw_ents = processor.extract_entities(full_text)
                    clean_ents = processor.clean_entities(raw_ents)
        
        # Sadece terim isimlerini virgülle birleştirerek bir string yapalım
                    terms_string = ", ".join([e['word'] for e in clean_ents if e['confidence'] >= min_confidence])
        
                    report_data.append({
                        "Makale Başlığı": art['title'],
                        "Özet": art['abstract'],
                        "Tespit Edilen Kritik Terimler": terms_string
                    })
    
    # Raporu oluştur
                df_report = pd.DataFrame(report_data)
                csv_report = df_report.to_csv(index=False).encode('utf-8-sig') # Türkçe karakterler için 'utf-8-sig'

                st.download_button(
                    label="📄 Detaylı Literatür Raporunu İndir (CSV)",
                    data=csv_report,
                    file_name=f"{query}_detayli_rapor.csv",
                    mime="text/csv",
                )