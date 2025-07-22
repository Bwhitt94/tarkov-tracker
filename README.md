# Tarkov Item Tracker

Item Value Overlay and Database for Escape from Tarkov

## Features
- Download and build a local database of all valuable Tarkov items (with images and prices)
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
- All item images and metadata are stored in `data/items/`.
- Press the "Build/Download Items" button in the GUI to update the database.

## Project Structure
- `src/` - Core logic and modules
- `gui.py` - Main GUI application
- `data/items/` - Downloaded item images and metadata (auto-generated)
- `requirements.txt` - Python dependencies
- `.gitignore` - Files and folders excluded from git

## Contributing
Pull requests and issues are welcome! Please open an issue for bugs or feature requests.

## License
MIT License (add LICENSE file if desired)

## Credits
- Uses data from [tarkov.dev](https://tarkov.dev/)
- Created by Bwhitt94 and contributors
