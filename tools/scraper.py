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
                preferred_models = [
                    'gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro', 'gemini-pro-latest']
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
            fallback_models = ['gemini-1.5-flash',
                               'gemini-pro', 'gemini-1.5-pro']
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
            has_english = any(
                word in query_lower for word in common_english_words)

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
        Search for products on Albert Heijn using web scraping (primary) and Gemini (for structuring)
        Returns list of products with prices
        """
        # Translate English to Dutch for better search results
        dutch_query = self._translate_to_dutch(search_query)

        # Primary method: Web scraping to get actual products from ah.nl
        print(f"Searching Albert Heijn for: {dutch_query}")
        products = self.search_products_web_scrape(dutch_query, max_results)

        # If web scraping didn't return enough results, try to enhance with Gemini
        if len(products) < max_results and self._working_model:
            print(
                f"Web scraping returned {len(products)} products, trying to enhance with Gemini...")
            try:
                # Use Gemini to structure and enhance the scraped data
                enhanced_products = self._enhance_products_with_gemini(
                    products, dutch_query, max_results - len(products))
                products.extend(enhanced_products)
            except Exception as e:
                print(f"Gemini enhancement failed: {e}")

        return products[:max_results]

    def _enhance_products_with_gemini(self, existing_products, query, additional_needed):
        """Use Gemini to generate additional product suggestions based on the query"""
        if not self._working_model or additional_needed <= 0:
            return []

        try:
            existing_names = [p.get('name', '') for p in existing_products]

            prompt = f"""Based on the search query "{query}" for Albert Heijn products, suggest {additional_needed} additional different products that would be available.

Already found products: {', '.join(existing_names[:5])}

Provide a JSON array with {additional_needed} different products (different brands, sizes, or types) with this structure:
[
    {{
        "name": "Product name",
        "image_url": "",
        "price_without_membership": estimated price as float,
        "price_with_membership": same as price_without_membership,
        "discount_offer": "",
        "url": "",
        "category": "category name",
        "is_bonus": false,
        "unit": "unit description"
    }}
]

Return only valid JSON array."""

            response = self._working_model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean JSON response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            additional_products = json.loads(response_text)
            if isinstance(additional_products, list):
                return additional_products[:additional_needed]
            return []

        except Exception as e:
            print(f"Error enhancing with Gemini: {e}")
            return []

    def search_products_web_scrape(self, search_query, max_results=10):
        """
        Scrape Albert Heijn website directly to get real product data
        This is the primary method for getting actual products
        """
        try:
            # Search URL for Albert Heijn
            search_url = f"https://www.ah.nl/zoeken?query={search_query.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            print(f"Fetching: {search_url}")
            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            products = []

            # Albert Heijn uses specific data attributes and classes
            # Try multiple selectors to find products
            selectors = [
                ('article', {'class': re.compile(r'product|card', re.I)}),
                ('div', {'data-testid': re.compile(r'product', re.I)}),
                ('div', {'class': re.compile(
                    r'product-tile|product-card|product-item', re.I)}),
                ('li', {'class': re.compile(r'product', re.I)}),
            ]

            product_elements = []
            for tag, attrs in selectors:
                found = soup.find_all(tag, attrs)
                if found:
                    # Get more to filter
                    product_elements = found[:max_results * 2]
                    print(f"Found {len(found)} elements using {tag} selector")
                    break

            if not product_elements:
                # Fallback: search for any element with product-related text
                product_elements = soup.find_all(['div', 'article', 'li'],
                                                 string=re.compile(r'€|\d+[,.]\d{2}', re.I))[:max_results * 2]

            print(
                f"Processing {len(product_elements)} potential product elements")

            for element in product_elements[:max_results * 2]:
                try:
                    # Find product name
                    name = ""
                    name_selectors = [
                        ('h3', {}),
                        ('h2', {}),
                        ('a', {'class': re.compile(r'link|title|name', re.I)}),
                        ('span', {'class': re.compile(
                            r'title|name|product-name', re.I)}),
                    ]

                    for tag, attrs in name_selectors:
                        name_elem = element.find(tag, attrs)
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            if name and len(name) > 3:
                                break

                    if not name:
                        continue

                    # Find price
                    price = None
                    price_text = ""
                    price_selectors = [
                        ('span', {'class': re.compile(r'price|amount', re.I)}),
                        ('div', {'class': re.compile(r'price', re.I)}),
                        ('span', {'data-testid': re.compile(r'price', re.I)}),
                    ]

                    for tag, attrs in price_selectors:
                        price_elem = element.find(tag, attrs)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            # Extract price (look for euro amounts)
                            price_match = re.search(
                                r'€?\s*(\d+[,.]?\d*)', price_text)
                            if price_match:
                                price = float(price_match.group(
                                    1).replace(',', '.'))
                                break

                    # Also search in element text if not found
                    if price is None:
                        element_text = element.get_text()
                        price_match = re.search(
                            r'€?\s*(\d+[,.]?\d{2})', element_text)
                        if price_match:
                            price = float(price_match.group(
                                1).replace(',', '.'))

                    if price is None:
                        continue

                    # Find product URL/link
                    product_url = ""
                    link_elem = element.find('a', href=True)
                    if link_elem:
                        product_url = link_elem.get('href', '')
                        if product_url:
                            if product_url.startswith('//'):
                                product_url = 'https:' + product_url
                            elif product_url.startswith('/'):
                                product_url = f"https://www.ah.nl{product_url}"
                            elif not product_url.startswith('http'):
                                product_url = f"https://www.ah.nl/{product_url}"
                    
                    # Also try to find URL in data attributes
                    if not product_url:
                        product_url = element.get('href', '') or element.get('data-href', '') or element.get('data-url', '')
                        if product_url and not product_url.startswith('http'):
                            if product_url.startswith('/'):
                                product_url = f"https://www.ah.nl{product_url}"
                            else:
                                product_url = f"https://www.ah.nl/{product_url}"

                    # Find product image
                    image_url = ""
                    img_elem = element.find('img')
                    if img_elem:
                        image_url = img_elem.get('src', '') or img_elem.get(
                            'data-src', '') or img_elem.get('data-lazy-src', '')
                        if image_url:
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            elif image_url.startswith('/'):
                                image_url = f"https://www.ah.nl{image_url}"
                            elif not image_url.startswith('http'):
                                image_url = f"https://www.ah.nl/{image_url}"

                    # Find discount/bonus info
                    discount_offer = ""
                    is_bonus = False
                    bonus_text = element.get_text()
                    if re.search(r'bonus|actie|korting|aanbieding', bonus_text, re.I):
                        is_bonus = True
                        # Try to extract bonus text
                        bonus_match = re.search(
                            r'(bonus|actie|korting|aanbieding)[\s:]*([^\n]*)', bonus_text, re.I)
                        if bonus_match:
                            discount_offer = bonus_match.group(
                                0)[:50]  # Limit length
                        else:
                            discount_offer = "BONUS"

                    # Find unit/volume
                    unit = ""
                    unit_match = re.search(
                        r'(\d+[.,]?\d*\s*(kg|g|L|l|ml|st|stuks?|x))', element.get_text(), re.I)
                    if unit_match:
                        unit = unit_match.group(1)

                    # Determine category (simple heuristic)
                    category = "Other"
                    name_lower = name.lower()
                    if any(word in name_lower for word in ['melk', 'kaas', 'yoghurt', 'boter', 'eieren']):
                        category = "Dairy"
                    elif any(word in name_lower for word in ['brood', 'bagel', 'croissant', 'krentenbol']):
                        category = "Bakery"
                    elif any(word in name_lower for word in ['banaan', 'appel', 'sinaasappel', 'aardbei']):
                        category = "Fruit"
                    elif any(word in name_lower for word in ['tomaat', 'komkommer', 'sla', 'wortel']):
                        category = "Vegetables"
                    elif any(word in name_lower for word in ['vlees', 'kip', 'rundvlees', 'worst']):
                        category = "Meat"
                    elif any(word in name_lower for word in ['bier', 'wijn', 'drank']):
                        category = "Beverages"

                    products.append({
                        "name": name,
                        "image_url": image_url,
                        "price_without_membership": price,
                        "price_with_membership": price,  # Default to same if not found
                        "discount_offer": discount_offer,
                        "url": product_url,
                        "category": category,
                        "is_bonus": is_bonus,
                        "unit": unit
                    })

                    if len(products) >= max_results:
                        break

                except Exception as e:
                    print(f"Error processing product element: {e}")
                    continue

            print(f"Successfully scraped {len(products)} products")
            return products

        except requests.exceptions.RequestException as e:
            print(f"Network error scraping Albert Heijn: {str(e)}")
            return []
        except Exception as e:
            print(f"Error web scraping: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
