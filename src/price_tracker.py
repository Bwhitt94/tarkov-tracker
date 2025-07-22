import requests
import json
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

class PriceTracker:
    """Tracks and retrieves current Tarkov item prices."""
    
    def __init__(self, cache_duration_hours: int = 6):
        # We'll cache prices to avoid hitting the API too often
        self.price_cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # Fallback prices for common items (in case API is down)
        self.fallback_prices = {
            "Graphics Card": {"trader": "Mechanic", "price": 285000},
            "Bitcoin": {"trader": "Therapist", "price": 445000},
            "LEDX": {"trader": "Therapist", "price": 890000},
            "Red Rebel": {"trader": "Jaeger", "price": 2800000},
            # Add more as needed
        }
    
    def get_item_price(self, item_name: str) -> Optional[Dict]:
        """
        Gets the current price for an item.
        Returns dict with trader name and price, or None if not found.
        """
        # Check cache first
        if item_name in self.price_cache:
            cached_data = self.price_cache[item_name]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
        
        # Try to fetch from API
        api_price = self.fetch_from_api(item_name)
        if api_price:
            # Cache the result
            self.price_cache[item_name] = {
                'data': api_price,
                'timestamp': datetime.now()
            }
            return api_price
        
        # Fall back to stored prices
        return self.fallback_prices.get(item_name)
    
    def fetch_from_api(self, item_name: str) -> Optional[Dict]:
        """
        Fetches current price from Tarkov-Market API.
        Note: You'll need to register for an API key at https://tarkov-market.com
        """
        # This is a simplified example - the actual API might work differently
        try:
            # For demo purposes, we'll simulate API response
            # In reality, you'd make an actual API call here
            simulated_prices = {
                "Graphics Card": {"trader": "Mechanic", "price": 285000},
                "Bitcoin": {"trader": "Therapist", "price": 445000},
                "LEDX": {"trader": "Therapist", "price": 890000},
            }
            
            if item_name in simulated_prices:
                return simulated_prices[item_name]
                
        except Exception as e:
            print(f"Error fetching price for {item_name}: {e}")
        
        return None
    
    def save_cache(self, filename: str = "price_cache.json"):
        """Saves the price cache to disk."""
        cache_data = {
            item: {
                'data': info['data'],
                'timestamp': info['timestamp'].isoformat()
            }
            for item, info in self.price_cache.items()
        }
        
        with open(filename, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def load_cache(self, filename: str = "price_cache.json"):
        """Loads price cache from disk."""
        try:
            with open(filename, 'r') as f:
                cache_data = json.load(f)
                
            self.price_cache = {
                item: {
                    'data': info['data'],
                    'timestamp': datetime.fromisoformat(info['timestamp'])
                }
                for item, info in cache_data.items()
            }
            
            print(f"Loaded {len(self.price_cache)} cached prices")
            
        except FileNotFoundError:
            print("No cache file found, starting fresh")
        except Exception as e:
            print(f"Error loading cache: {e}")