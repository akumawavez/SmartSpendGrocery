from agents.base import Agent
from tools.scraper import CatalogueScraper

class CatalogueAgent(Agent):
    def __init__(self):
        super().__init__(name="CatalogueMatcher")
        self.scraper = CatalogueScraper()

    def execute(self, raw_items):
        print(f"Matching {len(raw_items)} items against catalogue...")
        matched_items = []
        for item in raw_items:
            # In a real agent, this would be a loop with self-correction
            # "Search for BAP WIT" -> "Found Bananas" -> "Confirm match"
            
            match = self.scraper.find_product(item["raw_name"])
            if match:
                enhanced_item = {
                    **item,
                    "product_name": match["name"],
                    "category": match["category"],
                    "catalogue_price": match["price"],
                    "is_bonus": match["is_bonus"]
                }
                matched_items.append(enhanced_item)
            else:
                # Fallback for unknown items
                matched_items.append({
                    **item,
                    "product_name": item["raw_name"],
                    "category": "Uncategorized",
                    "catalogue_price": item["price"],
                    "is_bonus": False
                })
        
        return matched_items
