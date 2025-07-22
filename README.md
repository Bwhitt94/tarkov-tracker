# Tarkov Item Tracker

Item Value Overlay and Database for Escape from Tarkov

## Features
- Download and build a local database of all Tarkov items (with images and prices)
- Modern GUI for searching, filtering, and viewing items and prices
- One-click item database update
- View item images and metadata
- Search and filter by name and price
- Git versioned and ready for collaboration

## Setup
1. **Clone the repository:**
   ```sh
   git clone https://github.com/Bwhitt94/tarkov-tracker.git
   cd tarkov-tracker
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   pip install pillow
   ```
3. **Run the GUI:**
   ```sh
   python gui.py
   ```

## Usage
- Use the GUI to build/download the item database, search, filter, and view items.
- All item metadata is stored in `data/items.json` (single file, easy to search/filter).
- All item images are stored in `data/items/` as PNGs (for template matching and display).
- Press the "Update Items" button in the GUI to refresh the database.

## Project Structure
- `src/` - Core logic and modules
- `gui.py` - Main GUI application
- `data/items.json` - Downloaded item metadata (single file)
- `data/items/` - Downloaded item images (auto-generated)
- `requirements.txt` - Python dependencies
- `.gitignore` - Files and folders excluded from git

## Contributing
Pull requests and issues are welcome! Please open an issue for bugs or feature requests.

## License
MIT License (add LICENSE file if desired)

## Credits
- Uses data from [tarkov.dev](https://tarkov.dev/)
- Created by Bwhitt94 and contributors

## TODO / Ideas for Future Improvements
- [ ] **Trader/Flea Price Extraction:** Improve price extraction logic to support future wipes and show flea prices when available.
- [ ] **Barter/Quest Item Highlighting:** Visually indicate items that are only used for barter or quests.
- [ ] **Better Item Recognition:** Use machine learning or advanced template matching for more accurate in-inventory item detection.
- [ ] **Overlay Customization:** Allow users to customize overlay size, position, and transparency.
- [ ] **Settings UI:** Add a settings panel in the GUI for user preferences (theme, price source, etc).
- [ ] **Performance Optimization:** Speed up item database build and GUI loading for large item sets.
- [ ] **Multi-language Support:** Add translations for the GUI and item names.
- [ ] **Auto-Update Items:** Optionally auto-refresh item prices and images on a schedule.
- [ ] **Export/Import:** Allow users to export filtered item lists or import custom item data.
- [ ] **Advanced Filtering:** Add more filters (by slot, by trader, by barter, by quest, etc).
- [ ] **Integration with Tarkov-Market API:** For more up-to-date flea prices and trends.
- [ ] **Better Error Handling:** More user-friendly error messages and diagnostics.
- [ ] **Unit Tests:** Add automated tests for core modules and GUI.
- [ ] **Plugin System:** Allow community plugins for custom overlays, item sources, or integrations.
