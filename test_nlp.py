from src.processor import BioProcessor

processor = BioProcessor()
sample_text = "The BRCA1 gene mutation is highly associated with breast cancer risk and treatment with Metformin."
results = processor.extract_entities(sample_text)
cleaned = processor.clean_entities(results)

print(cleaned)