from app.agents.map_extractor import MAPExtractor

extractor = MAPExtractor()
test_doc = {
    "text": "All Authorised Dealer banks shall ensure that export proceeds are repatriated to India within 9 months from date of shipment and report via EDPMS. Failure to comply will result in penalty under FEMA."
}
result = extractor.extract(test_doc)
print(result)