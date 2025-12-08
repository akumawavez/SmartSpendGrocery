import requests
from bs4 import BeautifulSoup
import re
from config.llm_config import get_llm_config
import json
import google.generativeai as genai

class CatalogueScraper:
    def __init__(self):
        # Mock database of AH products (fallback)
        self.mock_catalogue = {
            "BAP WIT": {"name": "Bananas White (Fairtrade)", "category": "Fruit", "price": 1.79, "is_bonus": False},
            "AH BIO MLK": {"name": "AH Organic Semi-Skimmed Milk 1L", "category": "Dairy", "price": 1.35, "is_bonus": False},
            "BB ROERBAK ITAL": {"name": "Bellella Italian Stir Fry Mix", "category": "Vegetables", "price": 2.49, "is_bonus": True},
            "COMMANDEUR": {"name": "Gulpener Commandeur Beer", "category": "Alcohol", "price": 3.99, "is_bonus": False}
        }
        self.llm_config = None
        self._working_model = None
        try:
            self.llm_config = get_llm_config()
            self._working_model = self._get_working_model()
        except Exception as e:
            print(f"Warning: LLM not configured: {e}")
            pass  # Fallback to mock if LLM not configured
    
    def _get_available_models(self):
        """List available models from the API"""
        try:
            models = genai.list_models()
            available = []
            for model in models:
                # Check if model supports generateContent
                if 'generateContent' in model.supported_generation_methods:
                    available.append(model.name)
            return available
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def _get_working_model(self):
        """Get a working model for text generation"""
        if not self.llm_config:
            return None
        
        try:
            # First, try to list available models
            available_models = self._get_available_models()
            if available_models:
                # Try preferred models in order
                preferred_models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro', 'gemini-pro-latest']
                for pref in preferred_models:
                    for avail in available_models:
                        if pref in avail.lower():
                            clean_name = avail
                            # Remove 'models/' prefix if present
                            if clean_name.startswith('models/'):
                                clean_name = clean_name.replace('models/', '')
                            try:
                                model = genai.GenerativeModel(clean_name)
                                print(f"Using model: {clean_name}")
                                return model
                            except Exception as e:
                                print(f"Failed to use model {clean_name}: {e}")
                                continue
                
                # Try any available model
                for avail in available_models:
                    clean_name = avail
                    if clean_name.startswith('models/'):
                        clean_name = clean_name.replace('models/', '')
                    try:
                        model = genai.GenerativeModel(clean_name)
                        print(f"Using available model: {clean_name}")
                        return model
                    except Exception as e:
                        print(f"Failed to use model {clean_name}: {e}")
                        continue
            
            # Fallback: try common model names directly
            fallback_models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro']
            for model_name in fallback_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    print(f"Using fallback model: {model_name}")
                    return model
                except Exception as e:
                    print(f"Fallback model {model_name} failed: {e}")
                    continue
        except Exception as e:
            print(f"Error getting working model: {e}")
        
        return None

    def find_product(self, query):
        """Find product in catalogue - uses mock for now, can be enhanced with real scraping"""
        print(f"Scraping catalogue for: {query}")
        return self.mock_catalogue.get(query)
    
    def _translate_to_dutch(self, query):
        """Translate English query to Dutch for better search results on ah.nl"""
        if not self._working_model:
            return query
        
        try:
            # Check if query contains English words (simple heuristic)
            common_english_words = ['milk', 'bread', 'bananas', 'chicken', 'beef', 'cheese', 
                                   'yogurt', 'butter', 'eggs', 'tomatoes', 'potatoes', 'onions',
                                   'apples', 'oranges', 'strawberries', 'grapes', 'water',
                                   'juice', 'coffee', 'tea', 'sugar', 'salt', 'pepper']
            
            query_lower = query.lower()
            has_english = any(word in query_lower for word in common_english_words)
            
            if not has_english:
                # Might already be Dutch, return as is
                return query
            
            # Translate to Dutch
            translate_prompt = f"""Translate the following English product name or category to Dutch. 
Return ONLY the Dutch translation, no explanation, no additional text.

English: "{query}"
Dutch:"""
            
            response = self._working_model.generate_content(translate_prompt)
            dutch_query = response.text.strip()
            
            # Clean up response (remove quotes if present)
            dutch_query = dutch_query.strip('"').strip("'").strip()
            
            print(f"Translated '{query}' to '{dutch_query}'")
            return dutch_query
            
        except Exception as e:
            print(f"Translation failed, using original query: {e}")
            return query
    
    def search_products_google(self, search_query, max_results=10):
        """
        Search for products on Albert Heijn using Google Search via Gemini
        Returns list of products with prices
        """
        if not self._working_model:
            # Try to get a working model if we don't have one
            self._working_model = self._get_working_model()
            if not self._working_model:
                print("No working model available, falling back to web scraping")
                return self.search_products_web_scrape(search_query, max_results)
        
        # Translate English to Dutch for better search results
        dutch_query = self._translate_to_dutch(search_query)
        
        try:
            # Use Gemini to search and extract product information
            prompt = f"""You are searching for products on Albert Heijn (ah.nl) website for the query: "{dutch_query}"

CRITICAL REQUIREMENTS:
1. Return EXACTLY {max_results} different products (or as many as available if less than {max_results})
2. Include various brands, sizes, types, and varieties of the product
3. Each product must be unique (different brand, size, or type)
4. Search the actual ah.nl website and extract real product information

Please provide a JSON array with EXACTLY {max_results} products (or fewer if not enough available) with the following structure:
[
    {{
        "name": "Product full name from ah.nl",
        "image_url": "Full URL to product image from ah.nl",
        "price_without_membership": price in euros as float (e.g., 1.99),
        "price_with_membership": price in euros as float if different, otherwise same as price_without_membership,
        "discount_offer": "discount description in Dutch (e.g., 'BONUS', '2+1 GRATIS', '10% korting') or empty string '' if no discount",
        "url": "product URL on ah.nl",
        "category": "product category in English (e.g., 'Dairy', 'Fruit', 'Vegetables', 'Meat', 'Bakery', 'Beverages', 'Snacks')",
        "is_bonus": true or false,
        "unit": "unit description (e.g., '1L', '500g', 'per stuk')"
    }},
    ... (repeat for {max_results} products)
]

Extract from Albert Heijn (ah.nl) website:
- Real product names as they appear on ah.nl
- Product images from ah.nl (use full URLs)
- Actual prices in euros
- Membership prices if available (AH Premium discounts)
- Any BONUS offers or promotions
- Proper product categories

Return ONLY a valid JSON array with {max_results} products. No explanations, no markdown, just the JSON array."""

            response = self._working_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean JSON response (remove markdown code blocks if present)
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            products = json.loads(response_text)
            
            # Ensure we have a list
            if not isinstance(products, list):
                print(f"Warning: Expected list but got {type(products)}")
                return []
            
            # Log how many products were found
            print(f"Found {len(products)} products from Gemini")
            
            # If we got fewer results than requested, that's okay - return what we have
            if len(products) < max_results:
                print(f"Note: Got {len(products)} products, requested {max_results}")
            
            # Limit results to max_results
            return products[:max_results] if len(products) > max_results else products
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            try:
                print(f"Response was: {response_text[:200]}...")
            except:
                print("Could not retrieve response text")
            # Fallback to web scraping
            return self.search_products_web_scrape(search_query, max_results)
        except Exception as e:
            print(f"Error searching products with Gemini: {str(e)}")
            # Fallback to web scraping
            return self.search_products_web_scrape(search_query, max_results)
    
    def search_products_web_scrape(self, search_query, max_results=10):
        """
        Alternative method: Scrape Albert Heijn website directly
        This is a fallback if Google Search doesn't work well
        """
        try:
            # Translate to Dutch if needed
            dutch_query = self._translate_to_dutch(search_query)
            
            # Search URL for Albert Heijn
            search_url = f"https://www.ah.nl/zoeken?query={dutch_query.replace(' ', '+')}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Try to find product cards (this will need to be adjusted based on AH's actual HTML structure)
            product_cards = soup.find_all('div', class_=re.compile(r'product|card|item', re.I))[:max_results]
            
            for card in product_cards:
                try:
                    name_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'title|name|product', re.I))
                    price_elem = card.find(['span', 'div'], class_=re.compile(r'price', re.I))
                    
                    if name_elem and price_elem:
                        name = name_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True)
                        
                        # Extract price (look for euro amounts)
                        price_match = re.search(r'€?\s*(\d+[,.]?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', '.'))
                            
                            # Try to find product image
                            img_elem = card.find('img')
                            image_url = ""
                            if img_elem:
                                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                                if image_url and not image_url.startswith('http'):
                                    image_url = f"https://www.ah.nl{image_url}" if image_url.startswith('/') else ""
                            
                            # Try to find discount/bonus info
                            bonus_elem = card.find(['span', 'div'], class_=re.compile(r'bonus|actie|korting|discount', re.I))
                            discount_offer = ""
                            is_bonus = False
                            if bonus_elem:
                                discount_offer = bonus_elem.get_text(strip=True)
                                is_bonus = True
                            elif "bonus" in price_text.lower() or "actie" in price_text.lower():
                                discount_offer = "BONUS"
                                is_bonus = True
                            
                            # Try to extract unit/volume
                            unit_elem = card.find(['span', 'div'], class_=re.compile(r'unit|volume|size', re.I))
                            unit = unit_elem.get_text(strip=True) if unit_elem else ""
                            
                            products.append({
                                "name": name,
                                "image_url": image_url,
                                "price_without_membership": price,
                                "price_with_membership": price,  # Default to same if not found
                                "discount_offer": discount_offer,
                                "url": "",
                                "category": "Unknown",
                                "is_bonus": is_bonus,
                                "unit": unit
                            })
                except:
                    continue
            
            return products
            
        except Exception as e:
            print(f"Error web scraping: {str(e)}")
            return []
