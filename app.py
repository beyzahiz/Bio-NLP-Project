import streamlit as st
import pandas as pd
from src.fetcher import PubMedFetcher
from src.processor import BioProcessor

# Sayfa ayarları
st.set_page_config(page_title="BioMiner Pro", page_icon="🧬", layout="wide")

# --- ÖZEL LACİVERT TEMA VE GÖRSEL DÜZENLEME (CSS) ---
st.markdown("""
    <style>
    /* Slider ve buton renklerini laciverte çevirir */
    .stSlider > div [data-baseweb="slider"] > div > div { background-color: #1a2a6c; }
    .stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] { color: #1a2a6c; }
    
    /* Üst taraftaki Mavi Gradient Banner */
    .header-box {
        background: linear-gradient(90deg, #0f0c29, #302b63, #24243e);
        padding: 40px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Bilgi mesajı kutusu (Yeşil) */
    .info-box {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4caf50;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER BÖLÜMÜ ---
st.markdown("""
    <div class="header-box">
        <h1>🧬 Bio-NLP: PubMed Literatür Madenciliği</h1>
        <p>Hastalık adını girin; yapay zeka PubMed makalelerini tarayıp genleri ve tıbbi terimleri profesyonel bir özet halinde sunsun.</p>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Analiz Ayarları")
    
    # 1'den 20'ye kadar makale seçimi
    max_results = st.slider("İncelenecek Makale Sayısı", 1, 20, 10)
    
    min_confidence = st.slider(
        "Yapay Zeka Analiz Hassasiyeti", 
        0.0, 1.0, 0.6,
        help="Daha keşif odaklı sonuçlar için hassasiyeti düşürebilirsiniz."
    )
    st.caption("ℹ️ İpucu: Daha keşif odaklı sonuçlar için hassasiyeti düşürebilirsiniz.")

@st.cache_resource
def load_tools():
    return PubMedFetcher(), BioProcessor()

fetcher, processor = load_tools()

# --- ANA İÇERİK ---
st.markdown("### 🔎 Literatür Sorgusu")
query = st.text_input("Araştırmak istediğiniz hastalık:", placeholder="Örn: Parkinson...")

if query:
    with st.spinner("Makaleler analiz ediliyor..."):
        # NOT: Burada 'max_results' parametresini gönderiyoruz. 
        # Fetcher içindeki SQL sorgusuna 'LIMIT' eklememiz gerekecek.
        articles = fetcher.fetch_abstracts(query, max_results=max_results)
        
        # 1. SORUNUN ÇÖZÜMÜ: Eğer veritabanından daha fazla gelirse, burada buduyoruz (Slicing)
        articles = articles[:max_results]
        
        if not articles:
            st.warning("Makale bulunamadı.")
        else:
            # Kaç makale bulunduğu bilgisini içeren yeşil kutu
            st.markdown(f"""
                <div class="info-box">
                    Toplam {len(articles)} makale bulundu. Analiz sonuçları aşağıda listeleniyor.
                </div>
            """, unsafe_allow_html=True)
            
            all_findings = []
            all_found_entities = []
            
            for art in articles:
                # Makale Başlığı (Mavi ve kalın)
                st.markdown(f"##### 📄 :blue[{art['title']}]")
                
                full_text = f"{art['title']}. {art['abstract']}"
                raw_ents = processor.extract_entities(full_text)
                clean_ents = processor.clean_entities(raw_ents)
                filtered = [e for e in clean_ents if e['confidence'] >= min_confidence]
                
                # AI Analiz Detayları Expander
                with st.expander("🔍 AI Analiz Detaylarını Gör"):
                    if filtered:
                        df = pd.DataFrame(filtered)
                        df.columns = ["Terim", "Tür", "Güven Skoru"]
                        st.table(df)
                        keywords = ", ".join([e['word'] for e in filtered])
                        all_found_entities.extend([e['word'] for e in filtered])
                    else:
                        st.write("Belirlenen hassasiyet oranında kritik terim bulunamadı.")
                        keywords = "Terim bulunamadı"

                # Makale Özeti Expander
                with st.expander("📝 Makale Özetini Oku"):
                    st.write(art['abstract'])
                
                all_findings.append({
                    "Title": art['title'],
                    "Keywords": keywords,
                    "Abstract": art['abstract']
                })
                st.divider()

            # --- ANALİZ VE RAPOR ---
            if all_found_entities:
                st.header("📊 Genel Analiz")
                top_words = processor.get_top_entities([{'word': w} for w in all_found_entities], limit=10)
                chart_data = pd.DataFrame(top_words, columns=['Terim', 'Frekans'])
                st.bar_chart(chart_data.set_index('Terim'))

                # TXT Rapor hazırlama (Aynı kalıyor)
                report_text = f"BIO-NLP ANALİZ RAPORU\nSorgu: {query.upper()}\n" + "="*50 + "\n\n"
                for item in all_findings:
                    report_text += f"BAŞLIK: {item['Title']}\nTERİMLER: {item['Keywords']}\nÖZET: {item['Abstract']}\n" + "-"*30 + "\n\n"

                st.download_button(
                    label="📥 Analiz Raporunu İndir (.txt)",
                    data=report_text,
                    file_name=f"{query}_analiz.txt",
                    mime="text/plain",
                )