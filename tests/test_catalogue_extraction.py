"""
Test suite for catalogue extraction functionality
"""
from agents.catalogue_matcher import CatalogueAgent
from tools.scraper import CatalogueScraper
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def test_catalogue_scraper_find_product():
    """Test that CatalogueScraper can find products in mock catalogue"""
    scraper = CatalogueScraper()

    # Test exact match
    result = scraper.find_product("BAP WIT")
    assert result is not None, "Should find BAP WIT in catalogue"
    assert result["name"] == "Bananas White (Fairtrade)", "Product name should match"
    assert result["price"] == 1.79, "Price should match"
    assert result["category"] == "Fruit", "Category should match"

    # Test another product
    result = scraper.find_product("AH BIO MLK")
    assert result is not None, "Should find AH BIO MLK in catalogue"
    assert result["name"] == "AH Organic Semi-Skimmed Milk 1L", "Product name should match"

    # Test non-existent product
    result = scraper.find_product("NONEXISTENT")
    assert result is None, "Should return None for non-existent product"

    print("✅ CatalogueScraper tests passed!")


def test_catalogue_agent_matching():
    """Test that CatalogueAgent can match receipt items to catalogue"""
    agent = CatalogueAgent()

    # Test with known items
    raw_items = [
        {"raw_name": "BAP WIT", "price": 1.79, "quantity": 1},
        {"raw_name": "AH BIO MLK", "price": 1.35, "quantity": 1},
        {"raw_name": "UNKNOWN ITEM", "price": 2.50, "quantity": 1}
    ]

    matched_items = agent.execute(raw_items)

    assert len(matched_items) == 3, "Should match all items"

    # Check first item (known)
    assert matched_items[0]["product_name"] == "Bananas White (Fairtrade)", "First item should be matched"
    assert matched_items[0]["category"] == "Fruit", "Category should be set"
    assert matched_items[0]["catalogue_price"] == 1.79, "Catalogue price should match"

    # Check second item (known)
    assert matched_items[1]["product_name"] == "AH Organic Semi-Skimmed Milk 1L", "Second item should be matched"
    assert matched_items[1]["category"] == "Dairy", "Category should be set"

    # Check third item (unknown - should fallback)
    assert matched_items[2]["product_name"] == "UNKNOWN ITEM", "Unknown item should use raw_name"
    assert matched_items[2]["category"] == "Uncategorized", "Unknown item should be uncategorized"

    print("✅ CatalogueAgent tests passed!")


if __name__ == "__main__":
    print("Running catalogue extraction tests...")
    test_catalogue_scraper_find_product()
    test_catalogue_agent_matching()
    print("\n✅ All catalogue extraction tests passed!")
