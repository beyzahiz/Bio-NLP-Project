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
    max_results = st.slider("İncelenecek Makale Sayısı", 1, 20, 5)
    min_confidence = st.slider(
        "Yapay Zeka Analiz Hassasiyeti", 
        0.0, 1.0, 0.6,
        help="Yüksek değerler daha kesin sonuçlar verir, düşük değerler daha fazla terim yakalar. Hassasiyeti artırırsanız sadece AI'nın çok emin olduğu tıbbi terimler listelenir.",
    )

@st.cache_resource
def load_tools():
    return PubMedFetcher(), BioProcessor()

fetcher, processor = load_tools()

query = st.text_input("Araştırmak istediğiniz hastalık:", placeholder="Örn: Alzheimer, Diabetes..")

if query:
    with st.spinner("Yapay zeka makaleleri analiz ediyor. Lütfen bekleyin."):
        articles = fetcher.fetch_abstracts(query, max_results=max_results)
        
        if not articles:
            st.warning("Makale bulunamadı.")
        else:
            all_findings = []
            all_found_entities = []
            
            for art in articles:
                st.subheader(f"📄 {art['title']}")
                
                full_text = f"{art['title']}. {art['abstract']}"
                raw_ents = processor.extract_entities(full_text)
                clean_ents = processor.clean_entities(raw_ents)
                filtered = [e for e in clean_ents if e['confidence'] >= min_confidence]
                
                # 1. Tıklayınca açılan AI Analiz Detayları (Tablo burada gizli)
                with st.expander("🔍 AI Analiz Detaylarını Gör"):
                    if filtered:
                        df = pd.DataFrame(filtered)
                        # Tabloyu daha şık göstermek için sütun isimlerini Türkçeleştirebiliriz
                        df.columns = ["Terim", "Tür", "Güven Skoru"]
                        st.table(df)
                        keywords = ", ".join([e['word'] for e in filtered])
                        all_found_entities.extend([e['word'] for e in filtered])
                    else:
                        st.write("Bu makalede kriterlere uygun terim bulunamadı.")
                        keywords = "Terim bulunamadı"

                # 2. Tıklayınca açılan Makale Özeti
                with st.expander("📝 Makale Özetini Oku"):
                    st.write(art['abstract'])
                
                all_findings.append({
                    "Title": art['title'],
                    "Keywords": keywords,
                    "Abstract": art['abstract']
                })
                st.divider()

            # --- ANALİZ VE İNDİRME ---
            if all_found_entities:
                st.header("📊 Genel Analiz")
                top_words = processor.get_top_entities([{'word': w} for w in all_found_entities], limit=10)
                chart_data = pd.DataFrame(top_words, columns=['Terim', 'Frekans'])
                st.bar_chart(chart_data.set_index('Terim'))

                report_text = f"BIO-NLP LİTERATÜR ANALİZ RAPORU\nSorgu: {query.upper()}\n" + "="*50 + "\n\n"
                for item in all_findings:
                    report_text += f"BAŞLIK: {item['Title']}\n"
                    report_text += f"TERİMLER: {item['Keywords']}\n"
                    report_text += f"ÖZET: {item['Abstract']}\n"
                    report_text += "-"*30 + "\n\n"

                st.download_button(
                    label="📥 Profesyonel Literatür Raporunu İndir (.txt)",
                    data=report_text,
                    file_name=f"{query}_BioNLP_Rapor.txt",
                    mime="text/plain",
                )