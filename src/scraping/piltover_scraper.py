import json
import requests
from typing import Dict, List, Optional, Any
import time
import urllib.parse


class PiltoverArchiveAPIScraper:
    """
    Scraper for Piltover Archive using their direct API endpoint.
    This approach is much more reliable than HTML scraping.
    """
    
    def __init__(self):
        self.base_url = "https://piltoverarchive.com"
        self.api_endpoint = "/api/trpc/cards.search"
        self.session = requests.Session()
        
        # Set headers similar to browser, but let requests handle encoding
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            # Let requests negotiate encoding it supports
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
            'Referer': 'https://piltoverarchive.com/cards',
            'Origin': 'https://piltoverarchive.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive',
            'trpc-accept': 'application/jsonl',
            'x-trpc-source': 'nextjs-react'
        })
    
    def get_all_cards(self) -> List[Dict]:
        """
        Fetch all cards from the API using the discovered endpoint.
        
        Returns:
            List of card dictionaries with full information
        """
        # The exact payload structure discovered by the user
        payload = {
            "0": {
                "json": {
                    "searchQuery": "",
                    "colorIds": [],
                    "type": None,
                    "super": None,
                    "rarity": None,
                    "setName": None,
                    "energyRange": {"min": 0, "max": 12},
                    "mightRange": {"min": 0, "max": 10},
                    "powerRange": {"min": 0, "max": 4},
                    "advancedSearchEnabled": False
                },
                "meta": {
                    "values": {
                        "type": ["undefined"],
                        "super": ["undefined"],
                        "rarity": ["undefined"],
                        "setName": ["undefined"]
                    }
                }
            }
        }
        
        try:
            print("Fetching all cards from Piltover Archive API...")
            
            # Build the query parameters exactly as the browser does
            query_params = {
                'batch': '1',
                'input': json.dumps(payload)
            }
            
            # Encode the query parameters
            encoded_params = urllib.parse.urlencode(query_params)
            url = f"{self.base_url}{self.api_endpoint}?{encoded_params}"
            
            # Make GET request (not POST)
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                response.raise_for_status()
            
            # Parse the response - it's a stream of JSON objects
            cards = self._parse_api_response(response.text)

            # Fallback: if nothing parsed, try without batch wrapper endpoint shape
            if not cards:
                try:
                    # Some deployments might return a single JSON object; try parsing as JSON then unwrap
                    obj = response.json()
                    cards = self._parse_api_response_obj(obj)
                except Exception:
                    pass
            print(f"Successfully fetched {len(cards)} cards!")
            return cards
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching cards: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    def _parse_api_response(self, response_text: str) -> List[Dict]:
        """
        Parse the API response which contains multiple JSON objects.
        The response format is multiple JSON objects separated by newlines.
        
        Args:
            response_text: Raw response text from the API
            
        Returns:
            List of parsed card dictionaries
        """
        cards = []
        
        # Split by lines and parse each JSONL object (tRPC streams JSON lines)
        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            # tRPC shape: {"result":{"data":{"json":[2,0,[[cards]]]}}}
            json_payload = None
            if isinstance(data, dict):
                if 'result' in data and isinstance(data['result'], dict):
                    json_payload = (
                        data.get('result', {})
                            .get('data', {})
                            .get('json')
                    )
                elif 'json' in data:
                    json_payload = data.get('json')

            if isinstance(json_payload, list) and len(json_payload) > 2:
                card_data = json_payload[2]
                # card_data is typically [[cards]] -> list nesting levels
                cards.extend(self._flatten_cards(card_data))

        return cards

    def _parse_api_response_obj(self, obj: Dict) -> List[Dict]:
        cards: List[Dict] = []
        try:
            json_payload = obj.get('result', {}).get('data', {}).get('json')
            if isinstance(json_payload, list) and len(json_payload) > 2:
                cards = self._flatten_cards(json_payload[2])
        except Exception:
            pass
        
        return cards

    def _flatten_cards(self, nested: Any) -> List[Dict]:
        """Extract card dicts from nested list structures produced by tRPC."""
        out: List[Dict] = []
        def walk(node):
            if isinstance(node, dict):
                if 'id' in node and 'name' in node:
                    out.append(node)
            elif isinstance(node, list):
                for x in node:
                    walk(x)
        walk(nested)
        return out
    
    def get_cards_by_set(self, set_prefix: str) -> List[Dict]:
        """
        Filter cards by set prefix (e.g., 'OGN' for Origin, 'OGS' for Proving Grounds)
        
        Args:
            set_prefix: Set prefix to filter by
            
        Returns:
            List of cards from the specified set
        """
        all_cards = self.get_all_cards()
        
        # Filter cards by set prefix
        set_cards = []
        for card in all_cards:
            if 'cardVariants' in card:
                for variant in card['cardVariants']:
                    if 'variantNumber' in variant and variant['variantNumber'].startswith(set_prefix):
                        set_cards.append(card)
                        break
        
        print(f"Found {len(set_cards)} cards from set {set_prefix}")
        return set_cards
    
    def extract_missing_fields(self, card: Dict) -> Dict:
        """
        Extract the missing fields we need: description, flavor text, and artist.
        
        Args:
            card: Card dictionary from the API
            
        Returns:
            Dictionary with the missing fields
        """
        result = {
            'name': card.get('name', ''),
            'description': card.get('description', ''),
            'flavor_text': '',
            'artist': ''
        }
        
        # Extract flavor text and artist from the first variant
        if 'cardVariants' in card and card['cardVariants']:
            variant = card['cardVariants'][0]  # Use first variant
            result['flavor_text'] = variant.get('flavorText', '')
            result['artist'] = variant.get('artist', '')
        
        return result
    
    def save_cards_to_file(self, cards: List[Dict], filepath: str) -> bool:
        """
        Save cards data to a JSON file.
        
        Args:
            cards: List of card dictionaries
            filepath: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the same structure as the original API response
            data = {
                "json": [2, 0, [[cards]]]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved {len(cards)} cards to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving cards to file: {e}")
            return False


def main():
    """Test the scraper"""
    scraper = PiltoverArchiveAPIScraper()
    
    # Test fetching all cards
    print("Testing API scraper...")
    cards = scraper.get_all_cards()
    
    if cards:
        print(f"\nSuccessfully fetched {len(cards)} cards!")
        print("\nSample card data:")
        sample_card = cards[0]
        print(f"Name: {sample_card.get('name', 'N/A')}")
        print(f"Type: {sample_card.get('type', 'N/A')}")
        print(f"Description: {sample_card.get('description', 'N/A')[:100]}...")
        
        if 'cardVariants' in sample_card and sample_card['cardVariants']:
            variant = sample_card['cardVariants'][0]
            print(f"Variant: {variant.get('variantNumber', 'N/A')}")
            print(f"Flavor Text: {variant.get('flavorText', 'N/A')}")
            print(f"Artist: {variant.get('artist', 'N/A')}")
        
        # Test set filtering
        print("\nTesting set filtering...")
        ogn_cards = scraper.get_cards_by_set('OGN')
        ogs_cards = scraper.get_cards_by_set('OGS')
        
        print(f"OGN cards: {len(ogn_cards)}")
        print(f"OGS cards: {len(ogs_cards)}")
        
    else:
        print("Failed to fetch cards")


if __name__ == "__main__":
    main()
