import os
import sys
import json
import cv2

# Ensure src is in the path for direct script execution
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.tarkov_api import TarkovDevAPI

def build_item_database(min_value: int = 50000):
    """
    Builds a local database of valuable items for the scanner.
    This downloads images and creates recognition templates.
    """
    print("Building Tarkov item database...")
    print(f"Fetching items worth more than {min_value} rubles...")
    
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

    # Filter for valuable items
    valuable_items = []
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
        # Only include items above our threshold
        if best_price >= min_value:
            valuable_items.append({
                'name': item['name'],
                'price': best_price,
                'width': item['width'],
                'height': item['height']
            })
    print(f"[DIAG] Items with nonzero price: {items_with_price}")
    print(f"[DIAG] Items missing price: {items_missing_price}")
    print(f"[DIAG] Valuable items found: {len(valuable_items)}")
    print("[DIAG] Top 5 valuable items:")
    for vitem in valuable_items[:5]:
        print(json.dumps(vitem, indent=2))
    
    # Sort by value
    valuable_items.sort(key=lambda x: x['price'], reverse=True)
    
    print(f"Found {len(valuable_items)} valuable items")
    print("\nTop 20 most valuable items:")
    for item in valuable_items[:20]:
        print(f"  - {item['name']}: {item['price']:,} rubles")
    
    # Download images and create templates
    print("\nDownloading item images...")
    templates_dir = "data/items"
    os.makedirs(templates_dir, exist_ok=True)
    # Also ensure cache/data exists for API
    os.makedirs("data/cache/data", exist_ok=True)
    
    for i, item_info in enumerate(valuable_items):  # Process all valuable items
        item = api.get_item_by_name(item_info['name'])
        if not item:
            continue
        # Sanitize the item name for filenames
        safe_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item['name']).strip()
        # Download image
        image_url = item.get('gridImageLink') or item.get('iconLink')
        if image_url:
            image_path = api.download_item_image(item['name'], image_url)
            if image_path and os.path.exists(image_path):
                # Copy to templates directory
                template_path = os.path.join(templates_dir, f"{safe_name}.png")
                # Load and process the image
                img = cv2.imread(image_path)
                if img is not None:
                    img_resized = cv2.resize(img, (63, 63))
                    cv2.imwrite(template_path, img_resized)
                    # Create JSON data file
                    json_path = os.path.join(templates_dir, f"{safe_name}.json")
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            'name': item['name'],
                            'short_name': item.get('shortName', ''),
                            'trader_price': api.get_best_trader_price(item['name']),
                            'avg_flea_price': item.get('avg24hPrice', 0),
                            'grid_size': [item['width'], item['height']]
                        }, f, indent=2, ensure_ascii=False)
                print(f"[{i+1}/{len(valuable_items)}] Processed {item['name']}")
                
    print("\nDatabase build complete!")
    print(f"Templates saved to: {os.path.abspath(templates_dir)}")

if __name__ == "__main__":
    # Run this to build your item database
    build_item_database(min_value=1)  # Items worth 100k+ rubles