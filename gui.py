import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
from PIL import Image, ImageTk
import glob
import sys
import time
from pathlib import Path

# Import the build_item_database function
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from build_item_database import build_item_database
from overlay import PriceOverlay
from main import TarkovScanner

ITEMS_DIR = os.path.join('data', 'items')

class ItemDatabaseGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Tarkov Item Tracker - Escape from Tarkov')
        self.geometry('1400x900')
        self.resizable(True, True)
        
        # Tarkov theme colors - more EFT-appropriate
        self.tarkov_dark = '#1a1a1a'
        self.tarkov_darker = '#0d0d0d'
        self.tarkov_gray = '#2d2d2d'
        self.tarkov_light_gray = '#404040'
        self.tarkov_yellow = '#c7a06f'  # EFT gold
        self.tarkov_orange = '#8b4513'  # Dark orange
        self.tarkov_red = '#8b0000'     # Dark red
        self.tarkov_green = '#2d5016'   # Dark green
        self.tarkov_blue = '#1e3a5f'    # Dark blue
        self.tarkov_white = '#d4d4d4'   # Muted white
        self.tarkov_text = '#b0b0b0'    # Text color
        
        # Configure Tarkov theme
        self.configure(bg=self.tarkov_dark)
        self.setup_tarkov_theme()
        
        self.items = []
        self.filtered_items = []
        self.images = {}
        self.categories = {}
        self.overlay = None
        self.overlay_running = False
        self.scanner = None
        self.scanning = False
        self.last_refresh_time = 0
        self.auto_refresh_enabled = True
        self.create_widgets()
        self.load_items()  # Always load existing data on startup
        self.status_var.set('Ready. Last update: ' + self.get_last_update() + '. Click "Build/Download Items" to refresh (recommended every 2 weeks).')
        
        # Start auto-refresh timer
        self.schedule_auto_refresh()

    def setup_tarkov_theme(self):
        """Configure Tarkov-themed styling."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for different widgets
        style.configure('Tarkov.TFrame', background=self.tarkov_dark)
        style.configure('Tarkov.TLabel', background=self.tarkov_dark, foreground=self.tarkov_white)
        style.configure('Tarkov.TButton', 
                       background=self.tarkov_gray, 
                       foreground=self.tarkov_white,
                       borderwidth=2,
                       focuscolor=self.tarkov_yellow)
        
        # Treeview styling
        style.configure('Tarkov.Treeview',
                       background=self.tarkov_darker,
                       foreground=self.tarkov_white,
                       fieldbackground=self.tarkov_darker,
                       borderwidth=0)
        
        style.configure('Tarkov.Treeview.Heading',
                       background=self.tarkov_gray,
                       foreground=self.tarkov_yellow,
                       borderwidth=1)
        
        # Combobox styling
        style.configure('Tarkov.TCombobox',
                       background=self.tarkov_light_gray,
                       foreground=self.tarkov_white,
                       fieldbackground=self.tarkov_light_gray,
                       borderwidth=2,
                       selectbackground=self.tarkov_yellow,
                       selectforeground=self.tarkov_dark)
        
        # Combobox dropdown styling
        style.map('Tarkov.TCombobox',
                 fieldbackground=[('readonly', self.tarkov_light_gray)],
                 selectbackground=[('readonly', self.tarkov_yellow)],
                 selectforeground=[('readonly', self.tarkov_dark)])
        
        # Entry styling
        style.configure('Tarkov.TEntry',
                       background=self.tarkov_darker,
                       foreground=self.tarkov_white,
                       fieldbackground=self.tarkov_darker,
                       borderwidth=1)
        
        # Additional combobox dropdown list styling
        try:
            # Configure the dropdown list colors (this might not work on all systems)
            self.option_add('*TCombobox*Listbox.background', self.tarkov_light_gray)
            self.option_add('*TCombobox*Listbox.foreground', self.tarkov_white)
            self.option_add('*TCombobox*Listbox.selectBackground', self.tarkov_yellow)
            self.option_add('*TCombobox*Listbox.selectForeground', self.tarkov_dark)
        except:
            pass  # Fallback if styling doesn't work

    def create_widgets(self):
        # Configure grid weights for resizable layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top frame for controls
        control_frame = tk.Frame(self, bg=self.tarkov_dark, relief='raised', bd=2)
        control_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        control_frame.grid_columnconfigure(8, weight=1)  # Make status label expand

        self.status_var = tk.StringVar(value='Ready')
        self.search_var = tk.StringVar()
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()
        self.category_var = tk.StringVar(value='All Categories')
        self.price_source_var = tk.StringVar(value='Traders')  # Default to traders only

        # Title
        title_label = tk.Label(control_frame, text='TARKOV ITEM TRACKER', 
                              font=('Arial', 16, 'bold'), 
                              bg=self.tarkov_dark, fg=self.tarkov_yellow)
        title_label.grid(row=0, column=0, columnspan=16, pady=(0, 10))

        # Progress bar frame (hidden by default)
        self.progress_frame = tk.Frame(control_frame, bg=self.tarkov_dark, relief='sunken', bd=2)
        self.progress_frame.grid(row=2, column=0, columnspan=16, sticky='ew', pady=5)
        self.progress_frame.grid_remove()  # Hidden by default
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400, mode='determinate')
        self.progress_bar.pack(pady=5)
        
        # Progress label
        self.progress_label = tk.Label(self.progress_frame, text='', 
                                      bg=self.tarkov_dark, fg=self.tarkov_text, font=('Arial', 9))
        self.progress_label.pack(pady=2)

        # Search controls
        tk.Label(control_frame, text='Search:', bg=self.tarkov_dark, fg=self.tarkov_white, font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w')
        search_entry = tk.Entry(control_frame, textvariable=self.search_var, width=25, 
                               bg=self.tarkov_darker, fg=self.tarkov_white, 
                               insertbackground=self.tarkov_yellow, relief='sunken', bd=2)
        search_entry.grid(row=1, column=1, padx=5, sticky='w')
        search_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        # Price filters
        tk.Label(control_frame, text='Min Price:', bg=self.tarkov_dark, fg=self.tarkov_white, font=('Arial', 10, 'bold')).grid(row=1, column=2, padx=(10,0), sticky='w')
        min_entry = tk.Entry(control_frame, textvariable=self.min_price_var, width=12, 
                            bg=self.tarkov_darker, fg=self.tarkov_white, 
                            insertbackground=self.tarkov_yellow, relief='sunken', bd=2)
        min_entry.grid(row=1, column=3, sticky='w')
        min_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        tk.Label(control_frame, text='Max Price:', bg=self.tarkov_dark, fg=self.tarkov_white, font=('Arial', 10, 'bold')).grid(row=1, column=4, padx=(10,0), sticky='w')
        max_entry = tk.Entry(control_frame, textvariable=self.max_price_var, width=12, 
                            bg=self.tarkov_darker, fg=self.tarkov_white, 
                            insertbackground=self.tarkov_yellow, relief='sunken', bd=2)
        max_entry.grid(row=1, column=5, sticky='w')
        max_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        # Category filter
        tk.Label(control_frame, text='Category:', bg=self.tarkov_dark, fg=self.tarkov_white, font=('Arial', 10, 'bold')).grid(row=1, column=6, padx=(10,0), sticky='w')
        self.category_combo = ttk.Combobox(control_frame, textvariable=self.category_var, width=18, state='readonly', style='Tarkov.TCombobox')
        self.category_combo.grid(row=1, column=7, sticky='w', padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())

        # Price source filter
        tk.Label(control_frame, text='Price Source:', bg=self.tarkov_dark, fg=self.tarkov_white, font=('Arial', 10, 'bold')).grid(row=1, column=8, padx=(10,0), sticky='w')
        self.price_source_combo = ttk.Combobox(control_frame, textvariable=self.price_source_var, width=12, state='readonly', style='Tarkov.TCombobox')
        self.price_source_combo['values'] = ('Traders', 'Flea Market', 'Best Price')
        self.price_source_combo.grid(row=1, column=9, sticky='w', padx=5)
        self.price_source_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())

        # Build button
        build_btn = tk.Button(control_frame, text='🔧 Update Items', command=self.start_build,
                             bg=self.tarkov_gray, fg=self.tarkov_white, font=('Arial', 10, 'bold'),
                             relief='raised', bd=3, padx=10, activebackground=self.tarkov_light_gray)
        build_btn.grid(row=1, column=10, padx=10, sticky='w')

        # Refresh button
        refresh_btn = tk.Button(control_frame, text='🔄 Refresh', command=self.manual_refresh,
                               bg=self.tarkov_gray, fg=self.tarkov_white, font=('Arial', 10, 'bold'),
                               relief='raised', bd=3, padx=10, activebackground=self.tarkov_light_gray)
        refresh_btn.grid(row=1, column=11, padx=5, sticky='w')

        # Scan button
        self.scan_btn = tk.Button(control_frame, text='🔍 Start Scan', command=self.toggle_scan,
                                 bg=self.tarkov_gray, fg=self.tarkov_white, font=('Arial', 10, 'bold'),
                                 relief='raised', bd=3, padx=10, activebackground=self.tarkov_light_gray)
        self.scan_btn.grid(row=1, column=12, padx=5, sticky='w')

        # Overlay control buttons
        self.start_overlay_btn = tk.Button(control_frame, text='▶ Start Overlay', command=self.start_overlay,
                                          bg=self.tarkov_gray, fg=self.tarkov_white, font=('Arial', 10, 'bold'),
                                          relief='raised', bd=3, padx=10, activebackground=self.tarkov_light_gray)
        self.start_overlay_btn.grid(row=1, column=13, padx=5, sticky='w')
        
        self.stop_overlay_btn = tk.Button(control_frame, text='⏹ Stop Overlay', command=self.stop_overlay,
                                         bg=self.tarkov_gray, fg=self.tarkov_white, font=('Arial', 10, 'bold'),
                                         relief='raised', bd=3, padx=10, state='disabled', activebackground=self.tarkov_light_gray)
        self.stop_overlay_btn.grid(row=1, column=14, padx=5, sticky='w')

        # Status label
        status_label = tk.Label(control_frame, textvariable=self.status_var, fg=self.tarkov_yellow, 
                               bg=self.tarkov_dark, font=('Arial', 9))
        status_label.grid(row=1, column=15, padx=10, sticky='ew')

        # Main content frame
        main_frame = tk.Frame(self, bg=self.tarkov_dark, relief='sunken', bd=3)
        main_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview with thumbnails
        columns = ('Thumbnail', 'Name', 'Price', 'Size', 'Category')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15, style='Tarkov.Treeview')
        
        # Configure columns with thumbnail column
        self.tree.heading('Thumbnail', text='')
        self.tree.heading('Name', text='Item Name')
        self.tree.heading('Price', text='Price (₽)')
        self.tree.heading('Size', text='Grid Size')
        self.tree.heading('Category', text='Category')
        
        self.tree.column('Thumbnail', width=80, anchor='center', stretch=False)  # Fixed width for thumbnails
        self.tree.column('Name', width=350, anchor='w')
        self.tree.column('Price', width=120, anchor='e')
        self.tree.column('Size', width=80, anchor='center')
        self.tree.column('Category', width=150, anchor='w')
        
        # Add scrollbars
        tree_scroll_y = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(main_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Grid the tree and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x.grid(row=1, column=0, sticky='ew')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Bottom frame for details
        details_frame = tk.Frame(self, bg=self.tarkov_dark, relief='raised', bd=2)
        details_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        details_frame.grid_columnconfigure(1, weight=1)

        # Left side - Image and basic info
        left_frame = tk.Frame(details_frame, bg=self.tarkov_dark)
        left_frame.grid(row=0, column=0, padx=10, pady=5, sticky='n')
        
        # Item image
        self.img_label = tk.Label(left_frame, text='Select an item to view details', 
                                 bg=self.tarkov_dark, fg=self.tarkov_white, font=('Arial', 10))
        self.img_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Basic info frame
        info_frame = tk.Frame(left_frame, bg=self.tarkov_dark)
        info_frame.grid(row=1, column=0, padx=5, pady=5, sticky='ew')
        
        # Item name label
        self.item_name_label = tk.Label(info_frame, text='', 
                                       bg=self.tarkov_dark, fg=self.tarkov_yellow, 
                                       font=('Arial', 12, 'bold'), wraplength=200)
        self.item_name_label.grid(row=0, column=0, pady=2)
        
        # Price label
        self.price_label = tk.Label(info_frame, text='', 
                                   bg=self.tarkov_dark, fg=self.tarkov_white, 
                                   font=('Arial', 11, 'bold'))
        self.price_label.grid(row=1, column=0, pady=2)
        
        # Size label
        self.size_label = tk.Label(info_frame, text='', 
                                  bg=self.tarkov_dark, fg=self.tarkov_text, 
                                  font=('Arial', 10))
        self.size_label.grid(row=2, column=0, pady=2)
        
        # Category label
        self.category_label = tk.Label(info_frame, text='', 
                                      bg=self.tarkov_dark, fg=self.tarkov_text, 
                                      font=('Arial', 10))
        self.category_label.grid(row=3, column=0, pady=2)
        
        # Right side - Detailed info
        right_frame = tk.Frame(details_frame, bg=self.tarkov_dark)
        right_frame.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Details header
        details_header = tk.Label(right_frame, text='Item Details', 
                                 bg=self.tarkov_dark, fg=self.tarkov_yellow, 
                                 font=('Arial', 11, 'bold'))
        details_header.grid(row=0, column=0, pady=(0, 5), sticky='w')
        
        # Details text with Tarkov styling
        self.details_text = tk.Text(right_frame, height=10, width=60, 
                                   bg=self.tarkov_darker, fg=self.tarkov_white,
                                   insertbackground=self.tarkov_yellow,
                                   selectbackground=self.tarkov_gray,
                                   font=('Consolas', 9),
                                   relief='sunken', bd=2)
        self.details_text.grid(row=1, column=0, sticky='ew', pady=5)

    def start_overlay(self):
        """Start the Tarkov scanner overlay."""
        if not self.overlay_running:
            try:
                # Create overlay if it doesn't exist
                if not self.overlay:
                    self.overlay = PriceOverlay()
                
                # Show the overlay
                self.overlay.show()
                self.overlay_running = True
                
                # Connect to scanner if it exists
                if self.scanner:
                    self.scanner.overlay = self.overlay
                
                self.start_overlay_btn.config(state='disabled')
                self.stop_overlay_btn.config(state='normal')
                self.status_var.set('Overlay shown! You can now use the overlay window.')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to show overlay: {e}')

    def stop_overlay(self):
        """Stop the Tarkov scanner overlay."""
        if self.overlay_running and self.overlay:
            try:
                self.overlay.hide()  # Hide instead of closing
                self.overlay_running = False
                
                self.start_overlay_btn.config(state='normal')
                self.stop_overlay_btn.config(state='disabled')
                self.status_var.set('Overlay hidden.')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to hide overlay: {e}')

    def toggle_scan(self):
        """Start or stop the Tarkov scanner."""
        if not self.scanning:
            # Confirmation dialog before starting scan
            if not messagebox.askyesno('Start Scan', 'Are you sure you want to start the scanner?\nMake sure your inventory is visible in Escape from Tarkov.'):
                self.status_var.set('Scan cancelled.')
                return
            try:
                # Initialize scanner if not already done
                if not self.scanner:
                    self.scanner = TarkovScanner()
                    self.scanner.overlay = self.overlay  # Connect overlay to scanner
                
                # Start scanning
                self.scanner.toggle_scanning()
                self.scanning = True
                
                # Update button
                self.scan_btn.config(text='⏹ Stop Scan', bg=self.tarkov_red, activebackground=self.tarkov_red)
                self.status_var.set('Scanner started! Press F9 to toggle, F10 to show/hide overlay, ESC to exit.')
                
                # Start a thread to monitor scanner updates
                threading.Thread(target=self.monitor_scanner_updates, daemon=True).start()
                
            except Exception as e:
                messagebox.showerror('Error', f'Failed to start scanner: {e}')
        else:
            try:
                # Stop scanning
                if self.scanner:
                    self.scanner.toggle_scanning()
                
                self.scanning = False
                
                # Update button
                self.scan_btn.config(text='🔍 Start Scan', bg=self.tarkov_gray, activebackground=self.tarkov_light_gray)
                self.status_var.set('Scanner stopped.')
                
            except Exception as e:
                messagebox.showerror('Error', f'Failed to stop scanner: {e}')

    def schedule_auto_refresh(self):
        """Schedule the next auto-refresh check."""
        if self.auto_refresh_enabled:
            # Check for new items every 30 seconds
            self.after(30000, self.check_for_updates)

    def check_for_updates(self):
        """Check if new items have been added and refresh if needed."""
        try:
            # Get current file count and modification times
            current_files = set()
            current_mtime = 0
            
            for json_file in glob.glob(os.path.join(ITEMS_DIR, '*.json')):
                current_files.add(json_file)
                mtime = os.path.getmtime(json_file)
                if mtime > current_mtime:
                    current_mtime = mtime
            
            # If files have changed since last refresh, reload
            if current_mtime > self.last_refresh_time:
                self.last_refresh_time = current_mtime
                self.load_items()
                self.status_var.set(f'Auto-refreshed: {len(self.items)} items loaded')
            
        except Exception as e:
            print(f"Auto-refresh error: {e}")
        
        # Schedule next check
        self.schedule_auto_refresh()

    def manual_refresh(self):
        """Manually refresh the item list."""
        self.status_var.set('Refreshing items...')
        self.load_items()
        self.status_var.set(f'Manual refresh complete: {len(self.items)} items loaded')

    def get_item_category(self, item_name):
        """Determine item category based on name."""
        name_lower = item_name.lower()
        
        # Weapon categories
        if any(word in name_lower for word in ['rifle', 'carbine', 'assault']):
            return 'Assault Rifles'
        elif any(word in name_lower for word in ['pistol', 'revolver']):
            return 'Pistols'
        elif any(word in name_lower for word in ['shotgun']):
            return 'Shotguns'
        elif any(word in name_lower for word in ['sniper', 'bolt-action']):
            return 'Sniper Rifles'
        elif any(word in name_lower for word in ['machine gun', 'lmg']):
            return 'Machine Guns'
        
        # Equipment categories
        elif any(word in name_lower for word in ['helmet', 'mask']):
            return 'Headgear'
        elif any(word in name_lower for word in ['armor', 'vest', 'plate carrier']):
            return 'Body Armor'
        elif any(word in name_lower for word in ['backpack', 'bag']):
            return 'Backpacks'
        
        # Ammunition
        elif any(word in name_lower for word in ['ammo', 'ammunition', 'round']):
            return 'Ammunition'
        
        # Keys and access
        elif any(word in name_lower for word in ['key', 'keycard', 'access']):
            return 'Keys & Access'
        
        # Medical
        elif any(word in name_lower for word in ['medkit', 'bandage', 'splint', 'painkiller', 'stimulant']):
            return 'Medical'
        
        # Food and drink
        elif any(word in name_lower for word in ['water', 'food', 'drink', 'crackers', 'meat']):
            return 'Food & Drink'
        
        # Tools and parts
        elif any(word in name_lower for word in ['tool', 'screwdriver', 'wrench', 'pliers']):
            return 'Tools'
        
        # Attachments
        elif any(word in name_lower for word in ['scope', 'sight', 'muzzle', 'suppressor', 'grip', 'stock']):
            return 'Attachments'
        
        # Containers
        elif any(word in name_lower for word in ['case', 'container', 'box']):
            return 'Containers'
        
        # Valuables
        elif any(word in name_lower for word in ['gold', 'diamond', 'emerald', 'ruby', 'figurine', 'lion']):
            return 'Valuables'
        
        # Misc
        else:
            return 'Miscellaneous'

    def load_items(self):
        self.items = []
        self.images = {}
        self.categories = set()
        
        for json_file in glob.glob(os.path.join(ITEMS_DIR, '*.json')):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    item = json.load(f)
                    item['category'] = self.get_item_category(item['name'])
                    self.categories.add(item['category'])
                    self.items.append(item)
            except Exception as e:
                print(f'Error loading {json_file}: {e}')
        
        # Update category dropdown
        categories = ['All Categories'] + sorted(list(self.categories))
        self.category_combo['values'] = categories
        
        self.apply_filters()

    def apply_filters(self):
        search = self.search_var.get().lower()
        try:
            min_price = int(self.min_price_var.get()) if self.min_price_var.get() else None
        except ValueError:
            min_price = None
        try:
            max_price = int(self.max_price_var.get()) if self.max_price_var.get() else None
        except ValueError:
            max_price = None
        
        selected_category = self.category_var.get()
        
        self.filtered_items = []
        for item in self.items:
            name = item.get('name', '').lower()
            category = item.get('category', '')
            
            # Fix: Handle None values for trader_price and avg_flea_price
            trader_price = item.get('trader_price')
            if trader_price is None:
                trader_price = {}
            price = trader_price.get('price', 0) or item.get('avg_flea_price', 0)
            # Ensure price is a valid number
            if price is None:
                price = 0
            price = int(price)
            
            # Apply filters
            if search and search not in name:
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            if selected_category != 'All Categories' and category != selected_category:
                continue
                
            self.filtered_items.append(item)
        
        self.update_table()

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        
        for item in self.filtered_items:
            # Get or create thumbnail image
            safe_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item['name']).strip()
            img_path = os.path.join(ITEMS_DIR, f'{safe_name}.png')
            
            # Create thumbnail key
            thumbnail_key = f"{item['name']}_thumb"
            
            if os.path.exists(img_path) and thumbnail_key not in self.images:
                try:
                    # Create small thumbnail (60x60 for list)
                    img = Image.open(img_path).resize((60, 60), Image.Resampling.LANCZOS)
                    self.images[thumbnail_key] = ImageTk.PhotoImage(img)
                except:
                    self.images[thumbnail_key] = None
            
            # Get price based on selected source
            price_source = self.price_source_var.get()
            trader_price = item.get('trader_price', {})
            flea_price = item.get('avg_flea_price', 0)
            
            if price_source == 'Traders':
                price = trader_price.get('price', 0) if trader_price else 0
            elif price_source == 'Flea Market':
                price = flea_price if flea_price else 0
            elif price_source == 'Best Price':
                trader_val = trader_price.get('price', 0) if trader_price else 0
                flea_val = flea_price if flea_price else 0
                price = max(trader_val, flea_val)
            else:
                price = 0
            
            if price is None:
                price = 0
            price = int(price)
            
            # Get size
            size = 'x'.join(str(x) for x in item.get('grid_size', [1,1]))
            
            # Insert item with thumbnail
            item_id = self.tree.insert('', 'end', 
                values=('', item['name'], f'{price:,}', size, item.get('category', '')))
            
            # Set thumbnail indicator
            if thumbnail_key in self.images and self.images[thumbnail_key]:
                self.tree.set(item_id, 'Thumbnail', '🖼️')
            else:
                self.tree.set(item_id, 'Thumbnail', '❌')

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        item_name = self.tree.item(item_id)['values'][1]  # Name is in column 1 (Thumbnail, Name, Price, Size, Category)
        item = next((i for i in self.filtered_items if i['name'] == item_name), None)
        
        if not item:
            return
        
        # Load and display larger image
        safe_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in item_name).strip()
        img_path = os.path.join(ITEMS_DIR, f'{safe_name}.png')
        
        if os.path.exists(img_path):
            try:
                # Display larger image (200x200 for detail view)
                img = Image.open(img_path).resize((200, 200), Image.Resampling.LANCZOS)
                self.images[f"{item_name}_large"] = ImageTk.PhotoImage(img)
                self.img_label.config(image=self.images[f"{item_name}_large"], text='')
            except Exception as e:
                self.img_label.config(image='', text=f'Error loading image: {e}')
        else:
            self.img_label.config(image='', text='No image available')
        
        # Update basic info labels
        self.item_name_label.config(text=item_name)
        
        # Format price based on selected source
        price_source = self.price_source_var.get()
        trader_price = item.get('trader_price', {})
        flea_price = item.get('avg_flea_price', 0)
        
        if price_source == 'Traders':
            price = trader_price.get('price', 0) if trader_price else 0
            price_text = f"Trader Price: {price:,} ₽"
        elif price_source == 'Flea Market':
            price = flea_price if flea_price else 0
            price_text = f"Flea Price: {price:,} ₽"
        elif price_source == 'Best Price':
            trader_val = trader_price.get('price', 0) if trader_price else 0
            flea_val = flea_price if flea_price else 0
            price = max(trader_val, flea_val)
            price_text = f"Best Price: {price:,} ₽"
        else:
            price_text = "Price: N/A"
        
        self.price_label.config(text=price_text)
        
        # Update size and category
        size = 'x'.join(str(x) for x in item.get('grid_size', [1,1]))
        self.size_label.config(text=f"Grid Size: {size}")
        
        category = item.get('category', 'Unknown')
        self.category_label.config(text=f"Category: {category}")
        
        # Show detailed info in text area
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        # Format detailed information nicely
        details = f"""Item Information:
═══════════════════════════════════════════════════════════════

Name: {item_name}
Short Name: {item.get('short_name', 'N/A')}
Category: {category}
Grid Size: {size}

Pricing Information:
═══════════════════════════════════════════════════════════════

Trader Information:
{json.dumps(trader_price, indent=2, ensure_ascii=False) if trader_price else 'No trader data available'}

Flea Market Information:
{json.dumps({'avg_flea_price': flea_price}, indent=2, ensure_ascii=False) if flea_price else 'Flea market disabled this wipe'}

Raw Item Data:
═══════════════════════════════════════════════════════════════
{json.dumps(item, indent=2, ensure_ascii=False)}"""
        
        self.details_text.insert(tk.END, details)
        self.details_text.config(state='disabled')

    def start_build(self):
        # Show progress bar and disable build button
        self.progress_frame.grid()
        self.progress_var.set(0)
        self.progress_label.config(text='Initializing...')
        self.status_var.set('Checking for new items...')
        
        # Disable build button during process
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button) and 'Build' in child.cget('text'):
                        child.config(state='disabled')
        
        threading.Thread(target=self.build_items, daemon=True).start()

    def build_items(self):
        try:
            # Import here to avoid circular imports
            from src.build_item_database import build_item_database_with_progress
            
            # Call the progress-aware build function
            build_item_database_with_progress(self.update_progress)
            
            # Hide progress bar and re-enable build button
            self.progress_frame.grid_remove()
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Button) and 'Build' in child.cget('text'):
                            child.config(state='normal')
            
            self.status_var.set('Update complete! Reloading items...')
            self.load_items()
            self.status_var.set('Update complete! Items refreshed.')
        except Exception as e:
            # Hide progress bar and re-enable build button on error
            self.progress_frame.grid_remove()
            for widget in self.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Button) and 'Build' in child.cget('text'):
                            child.config(state='normal')
            
            self.status_var.set(f'Error: {e}')
            messagebox.showerror('Error', str(e))

    def update_progress(self, progress, message):
        """Update progress bar and label from build thread"""
        self.progress_var.set(progress)
        self.progress_label.config(text=message)
        self.update_idletasks()  # Force GUI update

    def monitor_scanner_updates(self):
        """Monitor scanner updates and update status"""
        while self.scanning and self.scanner:
            try:
                # Check if scanner has any updates
                if hasattr(self.scanner, 'update_queue') and not self.scanner.update_queue.empty():
                    update = self.scanner.update_queue.get_nowait()
                    if "items" in update:
                        item_count = len(update["items"])
                        self.status_var.set(f'Scanner active - Detected {item_count} items')
                    elif "error" in update:
                        self.status_var.set(f'Scanner error: {update["error"]}')
                
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Error monitoring scanner: {e}")
                break

    def get_last_update(self):
        # Try to get the last update time from the cache file
        import glob, os, json
        cache_file = os.path.join('data', 'cache', 'data', 'all_items.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    ts = data.get('timestamp')
                    if ts:
                        return ts.split('T')[0]
            except Exception:
                pass
        return 'Unknown'

if __name__ == '__main__':
    app = ItemDatabaseGUI()
    app.mainloop() 