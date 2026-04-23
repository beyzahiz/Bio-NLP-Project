from transformers import pipeline

class BioProcessor:
    def __init__(self):
        # BioBERT tabanlı NER modelini Hugging Face'ten yüklüyorum
        # Bu model genetik terimleri, hastalıkları ve ilaçları tanımak için eğitilmiştir.
        print("BioBERT modeli yükleniyor, bu biraz zaman alabilir...")
        self.ner_pipeline = pipeline(
            "ner", 
            model="d4data/biomedical-ner-all", # Çok kapsamlı bir medikal NER modeli
            aggregation_strategy="simple"      # Kelime parçalarını birleştirir (Örn: "Dia", "betes" -> "Diabetes")
        )

    def extract_entities(self, text):
        """Metin içindeki medikal varlıkları bulur."""
        if not text:
            return []
        
        entities = self.ner_pipeline(text)
        return entities

    def clean_entities(self, entities):
        """Karmaşık sonuçları temizler ve sadece anlamlı olanları döndürür."""
        cleaned = []
        for ent in entities:
            # Sadece belirli güven skorunun (score) üzerindekileri alalım
            if ent['score'] > 0.70:
                cleaned.append({
                    "word": ent['word'],
                    "label": ent['entity_group'],
                    "confidence": round(ent['score'], 2)
                })
        return cleaned