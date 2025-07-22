import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
from PIL import Image, ImageTk
import glob
import sys

# Import the build_item_database function
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from build_item_database import build_item_database

ITEMS_DIR = os.path.join('data', 'items')

class ItemDatabaseGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Tarkov Item Database GUI')
        self.geometry('1000x700')
        self.resizable(True, True)
        self.items = []
        self.filtered_items = []
        self.images = {}
        self.create_widgets()
        self.load_items()

    def create_widgets(self):
        # Top frame for controls
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_var = tk.StringVar(value='Ready')
        self.search_var = tk.StringVar()
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()

        tk.Label(control_frame, text='Search:').pack(side=tk.LEFT)
        search_entry = tk.Entry(control_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        tk.Label(control_frame, text='Min Price:').pack(side=tk.LEFT, padx=(10,0))
        min_entry = tk.Entry(control_frame, textvariable=self.min_price_var, width=8)
        min_entry.pack(side=tk.LEFT)
        min_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        tk.Label(control_frame, text='Max Price:').pack(side=tk.LEFT, padx=(10,0))
        max_entry = tk.Entry(control_frame, textvariable=self.max_price_var, width=8)
        max_entry.pack(side=tk.LEFT)
        max_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        build_btn = tk.Button(control_frame, text='Build/Download Items', command=self.start_build)
        build_btn.pack(side=tk.LEFT, padx=10)

        tk.Label(control_frame, textvariable=self.status_var, fg='blue').pack(side=tk.LEFT, padx=10)

        # Table for items
        self.tree = ttk.Treeview(self, columns=('Name', 'Price', 'Size'), show='headings', height=25)
        self.tree.heading('Name', text='Name')
        self.tree.heading('Price', text='Price')
        self.tree.heading('Size', text='Size')
        self.tree.column('Name', width=350)
        self.tree.column('Price', width=100, anchor='e')
        self.tree.column('Size', width=80, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Image and details
        self.img_label = tk.Label(self)
        self.img_label.pack(pady=5)
        self.details_text = tk.Text(self, height=6, width=120, state='disabled')
        self.details_text.pack(padx=10, pady=5)

    def start_build(self):
        self.status_var.set('Building item database...')
        threading.Thread(target=self.build_items, daemon=True).start()

    def build_items(self):
        try:
            build_item_database()
            self.status_var.set('Database build complete! Reloading items...')
            self.load_items()
        except Exception as e:
            self.status_var.set(f'Error: {e}')
            messagebox.showerror('Error', str(e))

    def load_items(self):
        self.items = []
        self.images = {}
        for json_file in glob.glob(os.path.join(ITEMS_DIR, '*.json')):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    item = json.load(f)
                    self.items.append(item)
            except Exception as e:
                print(f'Error loading {json_file}: {e}')
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
        self.filtered_items = []
        for item in self.items:
            name = item.get('name', '').lower()
            price = item.get('trader_price', {}).get('price', 0) or item.get('avg_flea_price', 0)
            if search and search not in name:
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            self.filtered_items.append(item)
        self.update_table()

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.filtered_items:
            price = item.get('trader_price', {}).get('price', 0) or item.get('avg_flea_price', 0)
            size = 'x'.join(str(x) for x in item.get('grid_size', [1,1]))
            self.tree.insert('', 'end', iid=item['name'], values=(item['name'], f'{price:,}', size))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        name = selected[0]
        item = next((i for i in self.filtered_items if i['name'] == name), None)
        if not item:
            return
        # Load image
        safe_name = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name).strip()
        img_path = os.path.join(ITEMS_DIR, f'{safe_name}.png')
        if os.path.exists(img_path):
            img = Image.open(img_path).resize((63, 63))
            self.images[name] = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.images[name])
        else:
            self.img_label.config(image='')
        # Show details
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, json.dumps(item, indent=2, ensure_ascii=False))
        self.details_text.config(state='disabled')

if __name__ == '__main__':
    app = ItemDatabaseGUI()
    app.mainloop() 