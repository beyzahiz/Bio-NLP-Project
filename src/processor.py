from transformers import pipeline

class BioProcessor:
    def __init__(self):
        print("BioBERT modeli yükleniyor...")
        # mevcut stratejide 'simple' yerine 'first' yaparak kelime birleşimi sorunu çözüldü
        self.ner_pipeline = pipeline(
            "ner", 
            model="d4data/biomedical-ner-all", 
            aggregation_strategy="first" 
        )

    def extract_entities(self, text):
        """Metin içindeki medikal varlıkları bulur."""
        if not text:
            return []
        
        entities = self.ner_pipeline(text)
        return entities

    def clean_entities(self, entities):
        cleaned = []
        seen = set() # Aynı kelimeyi tekrar listelememek için
        
        for ent in entities:
            word = ent['word'].strip().lower()
            label = ent['entity_group']
            
            # Çok kısa veya anlamsız karakterleri eleme
            if len(word) < 3:
                continue
                
            # Tekrar edenleri engelleme
            if (word, label) not in seen:
                cleaned.append({
                    "word": word.capitalize(),
                    "label": label,
                    "confidence": float(ent['score'])
                })
                seen.add((word, label))
        
        # Alfabetik sıralama
        return sorted(cleaned, key=lambda x: x['word'])
    
    
    def get_top_entities(self, all_entities, limit=10):
        """Tüm makalelerdeki terimlerin frekansını hesaplar."""
        from collections import Counter
        
        # Sadece kelimeleri bir listeye toplama
        words = [ent['word'] for ent in all_entities]
        return Counter(words).most_common(limit)