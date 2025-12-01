class ReceiptParser:
    def parse(self, file_path):
        # Mock implementation
        # In reality, this would use OCR (e.g., Google Cloud Vision) and Gemini
        print(f"Parsing receipt from {file_path}...")
        
        # Return a mock list of items found in a typical AH receipt
        return [
            {"raw_name": "BAP WIT", "price": 1.79, "quantity": 1},
            {"raw_name": "AH BIO MLK", "price": 1.35, "quantity": 1},
            {"raw_name": "BB ROERBAK ITAL", "price": 2.49, "quantity": 1},
            {"raw_name": "COMMANDEUR", "price": 3.99, "quantity": 1} # Beer
        ]
