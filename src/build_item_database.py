import os
import sys
import json
import cv2

# Ensure src is in the path for direct script execution
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.tarkov_api import TarkovDevAPI

def build_item_database_with_progress(progress_callback=None, min_value: int = 1):
    """
    Builds a local database of valuable items for the scanner with progress updates.
    This downloads images and creates recognition templates.
    """
    if progress_callback:
        progress_callback(0, "Initializing API...")
    
    # Initialize API
    api = TarkovDevAPI()
    
    if progress_callback:
        progress_callback(5, "Fetching items from API...")
    
    # Fetch all items
    items = api.fetch_all_items()
    
    if progress_callback:
        progress_callback(15, f"Processing {len(items)} items...")

    # Filter for items with prices
    items_to_process = []
    items_missing_price = 0
    items_with_price = 0
    for item in items:
        # Find the highest priceRUB in sellFor
        best_price = 0
        if 'sellFor' in item and item['sellFor']:
            for sell_option in item['sellFor']:
                price_rub = sell_option.get('priceRUB', 0)
                if price_rub and price_rub > best_price:
                    best_price = price_rub
        if best_price > 0:
            items_with_price += 1
        else:
            items_missing_price += 1
        # Include all items (since min_value is now 1)
        items_to_process.append({
            'name': item['name'],
            'price': best_price,
            'width': item['width'],
            'height': item['height']
        })
    
    # Sort by value
    items_to_process.sort(key=lambda x: x['price'], reverse=True)
    
    if progress_callback:
        progress_callback(25, f"Found {len(items_to_process)} items. Creating directories...")
    
    # Download images and create templates
    templates_dir = "data/items"
    os.makedirs(templates_dir, exist_ok=True)
    # Also ensure cache/data exists for API
    os.makedirs("data/cache/data", exist_ok=True)
    
    # Check for existing items to avoid re-downloading images
    existing_items = set()
    if os.path.exists(templates_dir):
        for json_file in os.listdir(templates_dir):
            if json_file.endswith('.json'):
                item_name = json_file[:-5]  # Remove .json extension
                existing_items.add(item_name)
    
    new_items = 0
    existing_items_updated = 0
    
    if progress_callback:
        progress_callback(30, f"Checking {len(existing_items)} existing items...")
    
    all_items = []
    for i, item_info in enumerate(items_to_process):  # Process all items
        if progress_callback:
            progress = 30 + (i / len(items_to_process)) * 65  # 30% to 95%
            progress_callback(progress, f"Processing {item_info['name']} ({i+1}/{len(items_to_process)})")
        
        item = api.get_item_by_name(item_info['name'])
        if not item:
            continue
        # Sanitize the item name for filenames
        safe_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item['name']).strip()
        
        template_path = os.path.join(templates_dir, f"{safe_name}.png")
        image_filename = f"{safe_name}.png"
        
        # Only download/process image if it doesn't exist
        if not os.path.exists(template_path):
            image_url = item.get('gridImageLink') or item.get('iconLink')
            if image_url:
                image_path = api.download_item_image(item['name'], image_url)
                if image_path and os.path.exists(image_path):
                    img = cv2.imread(image_path)
                    if img is not None:
                        img_resized = cv2.resize(img, (63, 63))
                        cv2.imwrite(template_path, img_resized)
        
        trader_price = api.get_best_trader_price(item['name'])
        if trader_price is None:
            trader_price = {"price": 0, "trader": "None", "currency": "RUB"}
        
        all_items.append({
            'name': item['name'],
            'short_name': item.get('shortName', ''),
            'trader_price': trader_price,
            'avg_flea_price': 0,  # Flea market disabled this wipe
            'grid_size': [item['width'], item['height']],
            'image_filename': image_filename
        })
        print(f"Added {item['name']} with price {trader_price['price']}")
    
    # Write all items to a single items.json file
    with open(os.path.join('data', 'items.json'), 'w', encoding='utf-8') as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(all_items)} items to data/items.json")

def build_item_database(min_value: int = 1):
    """
    Builds a local database of valuable items for the scanner.
    This downloads images and creates recognition templates.
    """
    print("Building Tarkov item database...")
    print(f"Fetching all items...")
    
    # Initialize API
    api = TarkovDevAPI()
    
    # Fetch all items
    items = api.fetch_all_items()
    print(f"[DIAG] Total items fetched from API: {len(items)}")

    # Print first 5 items for diagnostics
    print("[DIAG] Sample item data:")
    for sample in items[:5]:
        print(json.dumps({
            'name': sample.get('name'),
            'avg24hPrice': sample.get('avg24hPrice'),
            'basePrice': sample.get('basePrice'),
            'sellFor': sample.get('sellFor')
        }, indent=2))

    # Diagnostics: count items with images
    items_with_images = [item for item in items if item.get('gridImageLink') or item.get('iconLink')]
    print(f"[DIAG] Items with at least one image: {len(items_with_images)}")

    # Filter for items with prices
    items_to_process = []
    items_missing_price = 0
    items_with_price = 0
    for item in items:
        # Find the highest priceRUB in sellFor
        best_price = 0
        if 'sellFor' in item and item['sellFor']:
            for sell_option in item['sellFor']:
                price_rub = sell_option.get('priceRUB', 0)
                if price_rub and price_rub > best_price:
                    best_price = price_rub
        if best_price > 0:
            items_with_price += 1
        else:
            items_missing_price += 1
        # Include all items (since min_value is now 1)
        items_to_process.append({
            'name': item['name'],
            'price': best_price,
            'width': item['width'],
            'height': item['height']
        })
    print(f"[DIAG] Items with nonzero price: {items_with_price}")
    print(f"[DIAG] Items missing price: {items_missing_price}")
    print(f"[DIAG] Items to process: {len(items_to_process)}")
    print("[DIAG] Top 5 most valuable items:")
    for vitem in sorted(items_to_process, key=lambda x: x['price'], reverse=True)[:5]:
        print(json.dumps(vitem, indent=2))
    
    # Sort by value
    items_to_process.sort(key=lambda x: x['price'], reverse=True)
    
    print(f"Found {len(items_to_process)} items")
    print("\nTop 20 most valuable items:")
    for item in items_to_process[:20]:
        print(f"  - {item['name']}: {item['price']:,} rubles")
    
    # Check for existing items to avoid re-downloading images
    print("\nChecking existing items...")
    existing_items = set()
    templates_dir = "data/items"
    if os.path.exists(templates_dir):
        for json_file in os.listdir(templates_dir):
            if json_file.endswith('.json'):
                item_name = json_file[:-5]  # Remove .json extension
                existing_items.add(item_name)
    
    print(f"Found {len(existing_items)} existing items")
    os.makedirs(templates_dir, exist_ok=True)
    # Also ensure cache/data exists for API
    os.makedirs("data/cache/data", exist_ok=True)
    
    new_items = 0
    existing_items_updated = 0
    
    for i, item_info in enumerate(items_to_process):  # Process all items
        item = api.get_item_by_name(item_info['name'])
        if not item:
            continue
        # Sanitize the item name for filenames
        safe_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item['name']).strip()
        
        # Check if item already exists
        template_path = os.path.join(templates_dir, f"{safe_name}.png")
        json_path = os.path.join(templates_dir, f"{safe_name}.json")
        
        if safe_name in existing_items:
            # Item exists, just update JSON data (prices may have changed)
            existing_items_updated += 1
            trader_price = api.get_best_trader_price(item['name'])
            if trader_price is None:
                trader_price = {"price": 0, "trader": "None", "currency": "RUB"}
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'name': item['name'],
                    'short_name': item.get('shortName', ''),
                    'trader_price': trader_price,
                    'avg_flea_price': 0,  # Flea market disabled this wipe
                    'grid_size': [item['width'], item['height']]
                }, f, indent=2, ensure_ascii=False)
        else:
            # New item, download image and create files
            new_items += 1
            image_url = item.get('gridImageLink') or item.get('iconLink')
            if image_url:
                image_path = api.download_item_image(item['name'], image_url)
                if image_path and os.path.exists(image_path):
                    # Load and process the image
                    img = cv2.imread(image_path)
                    if img is not None:
                        img_resized = cv2.resize(img, (63, 63))
                        cv2.imwrite(template_path, img_resized)
                        # Create JSON data file
                        trader_price = api.get_best_trader_price(item['name'])
                        if trader_price is None:
                            trader_price = {"price": 0, "trader": "None", "currency": "RUB"}
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                'name': item['name'],
                                'short_name': item.get('shortName', ''),
                                'trader_price': trader_price,
                                'avg_flea_price': 0,  # Flea market disabled this wipe
                                'grid_size': [item['width'], item['height']]
                            }, f, indent=2, ensure_ascii=False)
                print(f"[{i+1}/{len(items_to_process)}] Downloaded new item: {item['name']}")
            else:
                print(f"[{i+1}/{len(items_to_process)}] No image for new item: {item['name']}")
                
    print(f"\nDatabase build complete!")
    print(f"New items downloaded: {new_items}")
    print(f"Existing items updated: {existing_items_updated}")
    print(f"Templates saved to: {os.path.abspath(templates_dir)}")

if __name__ == "__main__":
    # Run this to build your item database
    build_item_database_with_progress(min_value=1)  # All items