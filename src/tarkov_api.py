import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
import time

class TarkovDevAPI:
    """
    Interfaces with the tarkov.dev GraphQL API to fetch item data.
    This class handles querying, caching, and rate limiting.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        # The tarkov.dev GraphQL endpoint
        self.api_url = "https://api.tarkov.dev/graphql"
        
        # Cache directory for storing item data and images
        self.cache_dir = cache_dir
        self.ensure_cache_dirs()
        
        # In-memory cache for quick access
        self.item_cache = {}
        self.last_full_update = None
        
        # Rate limiting - tarkov.dev is generous but we should be respectful
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def ensure_cache_dirs(self):
        """Creates necessary cache directories if they don't exist."""
        # Create directory structure for caching
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "data"), exist_ok=True)
        
    def rate_limit(self):
        """Ensures we don't hammer the API with too many requests."""
        # Calculate time since last request
        time_since_last = time.time() - self.last_request_time
        
        # If we're requesting too fast, wait a bit
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
            
        # Update last request time
        self.last_request_time = time.time()
        
    def execute_query(self, query: str, variables: Dict = None) -> Optional[Dict]:
        """
        Executes a GraphQL query against the tarkov.dev API.
        
        Think of this as sending a very specific request to the librarian,
        asking for exactly the information we need.
        """
        self.rate_limit()
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                if "errors" in data:
                    print(f"GraphQL errors: {data['errors']}")
                    return None
                return data.get("data")
            except requests.exceptions.Timeout:
                print(f"[DIAG] Timeout occurred on attempt {attempt} for API request.")
            except requests.exceptions.RequestException as e:
                print(f"[DIAG] Error querying tarkov.dev on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"[DIAG] Retrying API request (attempt {attempt + 1})...")
        print("[DIAG] All attempts to query tarkov.dev failed.")
        return None
            
    def fetch_all_items(self) -> List[Dict]:
        """
        Fetches all items from tarkov.dev with their prices and image URLs.
        This is like asking for the entire item catalog.
        """
        print("Fetching all items from tarkov.dev...")
        
        # This GraphQL query is like a detailed shopping list
        # We're asking for specific fields we need for our scanner
        query = """
        {
            items {
                id
                name
                shortName
                normalizedName
                iconLink
                gridImageLink
                basePrice
                width
                height
                avg24hPrice
                low24hPrice
                high24hPrice
                lastLowPrice
                sellFor {
                    source
                    price
                    currency
                    priceRUB
                    vendor {
                        name
                        normalizedName
                    }
                }
            }
        }
        """
        
        # Execute the query
        result = self.execute_query(query)
        
        if result and "items" in result:
            items = result["items"]
            print(f"Fetched {len(items)} items from tarkov.dev")
            
            # Cache the results
            self._cache_items(items)
            
            return items
        else:
            print("Failed to fetch items from tarkov.dev")
            return []
            
    def _cache_items(self, items: List[Dict]):
        """
        Caches item data both in memory and on disk.
        This is like organizing our library for quick access later.
        """
        # Update in-memory cache
        for item in items:
            self.item_cache[item["name"]] = item
            # Also cache by normalized name for flexibility
            self.item_cache[item["normalizedName"]] = item
            
        # Save to disk for persistence
        cache_file = os.path.join(self.cache_dir, "data", "all_items.json")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "items": items
            }, f, indent=2, ensure_ascii=False)
            
        self.last_full_update = datetime.now()
        print(f"Cached {len(items)} items to {cache_file}")
        
    def load_cache(self) -> bool:
        """
        Loads cached item data from disk if available and recent.
        Returns True if cache was loaded successfully.
        """
        cache_file = os.path.join(self.cache_dir, "data", "all_items.json")
        
        if not os.path.exists(cache_file):
            return False
            
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Check if cache is recent (less than 6 hours old)
            cache_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() - cache_time > timedelta(hours=6):
                print("Cache is too old, will fetch fresh data")
                return False
                
            # Load items into memory
            items = data["items"]
            for item in items:
                self.item_cache[item["name"]] = item
                self.item_cache[item["normalizedName"]] = item
                
            self.last_full_update = cache_time
            print(f"Loaded {len(items)} items from cache")
            return True
            
        except Exception as e:
            print(f"Error loading cache: {e}")
            return False
            
    def get_item_by_name(self, name: str) -> Optional[Dict]:
        """
        Gets item data by name, using cache if available.
        This is like looking up a specific book by its title.
        """
        # Check if we have data loaded
        if not self.item_cache:
            # Try to load from cache first
            if not self.load_cache():
                # If no cache, fetch from API
                self.fetch_all_items()
                
        # Look up the item (try exact match first, then normalized)
        item = self.item_cache.get(name)
        if not item:
            # Try normalized name (lowercase, no spaces)
            normalized = name.lower().replace(" ", "-")
            item = self.item_cache.get(normalized)
            
        return item
        
    def download_item_image(self, item_name: str, image_url: str) -> Optional[str]:
        """
        Downloads and caches an item's image.
        Returns the local path to the cached image.
        """
        if not image_url:
            return None
            
        # Create a safe filename from the item name
        safe_filename = "".join(c for c in item_name if c.isalnum() or c in "- ").strip()
        image_path = os.path.join(self.cache_dir, "images", f"{safe_filename}.png")
        
        # If we already have the image, return its path
        if os.path.exists(image_path):
            return image_path
            
        try:
            # Download the image
            print(f"Downloading image for {item_name}...")
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Save the image
            with open(image_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"Saved image to {image_path}")
            return image_path
            
        except Exception as e:
            print(f"Error downloading image for {item_name}: {e}")
            return None
            
    def get_best_trader_price(self, item_name: str) -> Optional[Dict]:
        """
        Gets the best trader price for an item.
        This finds which trader offers the most money for your item.
        """
        item = self.get_item_by_name(item_name)
        if not item or "sellFor" not in item:
            return None
            
        best_price = 0
        best_trader = None
        
        # Look through all trader prices
        for sell_option in item["sellFor"]:
            # We're interested in trader prices (not flea market)
            if sell_option["source"] == "trader":
                price_rub = sell_option.get("priceRUB", 0)
                if price_rub > best_price:
                    best_price = price_rub
                    best_trader = sell_option
                    
        if best_trader:
            return {
                "price": best_price,
                "trader": best_trader["vendor"]["name"],
                "currency": best_trader["currency"]
            }
            
        return None