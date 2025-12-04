import os
import json
from pathlib import Path
from config.llm_config import get_llm_config
import google.generativeai as genai
from PIL import Image


class ReceiptParser:
    def __init__(self):
        """Initialize the parser with LLM configuration"""
        self.llm_config = get_llm_config()
        self.model = None  # Will be set to an available model
        self._working_model_name = None  # Cache the working model name

    def _is_image_file(self, file_path):
        """Check if file is an image based on extension"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        return Path(file_path).suffix.lower() in image_extensions

    def _read_text_file(self, file_path):
        """Read text from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return None

    def _get_available_models(self):
        """List available models from the API"""
        try:
            models = genai.list_models()
            available = []
            for model in models:
                # Check if model supports generateContent (needed for vision)
                if 'generateContent' in model.supported_generation_methods:
                    available.append(model.name)
            return available
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def _extract_text_from_image(self, file_path):
        """Extract text from image using Gemini Vision API"""
        prompt = """Extract all text from this receipt image. Return the raw text exactly as it appears, preserving line breaks and structure."""
        image = Image.open(file_path)

        # First, try to get available models
        available_models = self._get_available_models()
        if available_models:
            print(f"Found {len(available_models)} available models")
            # Try models in order of preference
            preferred_models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro', 'gemini-pro-vision']
            model_names_to_try = []
            
            # Add preferred models that are available
            for pref in preferred_models:
                # Check if any available model contains this name
                for avail in available_models:
                    if pref in avail.lower():
                        model_names_to_try.append(avail)
                        break
            
            # Add any other available models
            for avail in available_models:
                if avail not in model_names_to_try:
                    model_names_to_try.append(avail)
        else:
            # Fallback to trying common model names
            model_names_to_try = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro', 'gemini-pro-vision']

        # Try each model
        for model_name in model_names_to_try:
            try:
                # Handle model name format - GenerativeModel expects name without 'models/' prefix
                clean_model_name = model_name
                if model_name.startswith('models/'):
                    clean_model_name = model_name.replace('models/', '')
                
                print(f"Trying model: {clean_model_name}")
                vision_model = genai.GenerativeModel(clean_model_name)
                response = vision_model.generate_content([prompt, image])

                if response and response.text:
                    print(f"Successfully extracted text using {clean_model_name}")
                    # Cache the working model name for text parsing
                    self._working_model_name = model_name
                    return response.text
            except Exception as e:
                print(f"Model {model_name} failed: {str(e)[:100]}")  # Truncate long errors
                continue

        # If all models failed, try using the configured model from llm_config
        try:
            vision_model = self.llm_config.get_model()
            response = vision_model.generate_content([prompt, image])
            if response and response.text:
                print("Successfully extracted text using configured model")
                return response.text
        except Exception as e:
            print(f"Configured model also failed: {e}")

        print("Warning: Could not extract text from image with any available model")
        return None

    def _get_working_model(self):
        """Get a working model for text generation, reusing the OCR model if available"""
        # If we already found a working model, reuse it
        if self._working_model_name:
            try:
                clean_name = self._working_model_name
                if clean_name.startswith('models/'):
                    clean_name = clean_name.replace('models/', '')
                return genai.GenerativeModel(clean_name)
            except:
                pass
        
        # Otherwise, find an available model
        available_models = self._get_available_models()
        if available_models:
            # Try preferred models for text generation
            preferred_models = ['gemini-pro-latest', 'gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
            for pref in preferred_models:
                for avail in available_models:
                    if pref in avail.lower():
                        clean_name = avail
                        if clean_name.startswith('models/'):
                            clean_name = clean_name.replace('models/', '')
                        try:
                            model = genai.GenerativeModel(clean_name)
                            self._working_model_name = avail
                            return model
                        except:
                            continue
            
            # Try any available model
            for avail in available_models:
                clean_name = avail
                if clean_name.startswith('models/'):
                    clean_name = clean_name.replace('models/', '')
                try:
                    model = genai.GenerativeModel(clean_name)
                    self._working_model_name = avail
                    return model
                except:
                    continue
        
        # Fallback: try common model names
        for model_name in ['gemini-pro-latest', 'gemini-pro', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(model_name)
                self._working_model_name = model_name
                return model
            except:
                continue
        
        raise Exception("No available models found for text generation")
    
    def _parse_receipt_text(self, receipt_text):
        """Parse receipt text into structured items using Gemini"""
        if not receipt_text:
            return []

        prompt = f"""You are a receipt parser. Extract all items from this receipt text and return them as a JSON array.

Receipt text:
{receipt_text}

For each item, extract:
- raw_name: The product name as it appears on the receipt (keep abbreviations like "BAP WIT", "AH BIO MLK")
- price: The price as a number (float)
- quantity: The quantity as a number (default to 1 if not specified)

Return ONLY a valid JSON array, no other text. Example format:
[
    {{"raw_name": "BAP WIT", "price": 1.79, "quantity": 1}},
    {{"raw_name": "AH BIO MLK", "price": 1.35, "quantity": 1}}
]

If you cannot find any items, return an empty array [].
"""

        try:
            # Get a working model (will reuse the one from OCR if available)
            model = self._get_working_model()
            response = model.generate_content(prompt)

            if response and response.text:
                # Extract JSON from response (handle markdown code blocks if present)
                text = response.text.strip()
                if text.startswith('```'):
                    # Remove markdown code blocks
                    lines = text.split('\n')
                    text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
                elif text.startswith('```json'):
                    lines = text.split('\n')
                    text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
                
                # Parse JSON
                items = json.loads(text)
                if isinstance(items, list):
                    return items
                else:
                    print(f"Warning: Expected list, got {type(items)}")
                    return []
            else:
                print("Warning: No response from LLM")
                return []
                
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from LLM response: {e}")
            print(f"Response was: {response.text if response else 'None'}")
            return []
        except Exception as e:
            print(f"Error parsing receipt text: {e}")
            return []

    def parse(self, file_path):
        """Parse receipt from file (image or text) using OCR and LLM"""
        print(f"Parsing receipt from {file_path}...")

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return []

        # Extract text based on file type
        if self._is_image_file(file_path):
            print("Detected image file, using OCR...")
            receipt_text = self._extract_text_from_image(file_path)
        else:
            print("Detected text file, reading directly...")
            receipt_text = self._read_text_file(file_path)

        if not receipt_text:
            print("Warning: Could not extract text from receipt")
            return []

        print(f"Extracted text ({len(receipt_text)} characters)")

        # Parse text into structured items
        items = self._parse_receipt_text(receipt_text)

        print(f"Parsed {len(items)} items from receipt")
        return items
