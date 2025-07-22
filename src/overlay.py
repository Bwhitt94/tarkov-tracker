import tkinter as tk
from tkinter import ttk
from typing import List, Dict
import threading

class PriceOverlay:
    """Creates an overlay window to display item prices."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.items = []
        
    def setup_window(self):
        """Configures the overlay window properties."""
        # Set window title
        self.root.title("Tarkov Price Scanner")
        
        # Make window semi-transparent
        self.root.attributes('-alpha', 0.9)
        
        # Keep window on top of other windows
        self.root.attributes('-topmost', True)
        
        # Remove window decorations for cleaner look
        self.root.overrideredirect(True)
        
        # Set window size and position (top-right corner)
        window_width = 300
        window_height = 400
        screen_width = self.root.winfo_screenwidth()
        x_position = screen_width - window_width - 20
        y_position = 20
        
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Dark theme colors
        self.root.configure(bg='#1a1a1a')
        
    def create_widgets(self):
        """Creates the UI elements."""
        # Header
        header_frame = tk.Frame(self.root, bg='#1a1a1a')
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        title_label = tk.Label(
            header_frame,
            text="Inventory Values",
            font=('Arial', 14, 'bold'),
            fg='#c7a06f',
            bg='#1a1a1a'
        )
        title_label.pack(side='left')
        
        # Close button
        close_button = tk.Button(
            header_frame,
            text="✕",
            command=self.close,
            font=('Arial', 12),
            fg='white',
            bg='#1a1a1a',
            bd=0,
            padx=5,
            cursor='hand2'
        )
        close_button.pack(side='right')
        
        # Separator
        separator = tk.Frame(self.root, height=2, bg='#444')
        separator.pack(fill='x', padx=10, pady=5)
        
        # Scrollable item list
        self.canvas = tk.Canvas(self.root, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=self.canvas.yview)
        self.item_frame = tk.Frame(self.canvas, bg='#1a1a1a')
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.item_frame, anchor='nw')
        
        self.canvas.pack(side='left', fill='both', expand=True, padx=(10, 0))
        scrollbar.pack(side='right', fill='y')
        
        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            font=('Arial', 10),
            fg='#888',
            bg='#1a1a1a'
        )
        self.status_label.pack(side='bottom', pady=5)
        
    def _on_mousewheel(self, event):
        """Handles mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def update_items(self, items: List[Dict]):
        """Updates the displayed items."""
        # Clear existing items
        for widget in self.item_frame.winfo_children():
            widget.destroy()
            
        if not items:
            no_items_label = tk.Label(
                self.item_frame,
                text="No items detected",
                font=('Arial', 12),
                fg='#888',
                bg='#1a1a1a'
            )
            no_items_label.pack(pady=20)
            return
            
        # Add items
        total_value = 0
        for item in items:
            item_row = tk.Frame(self.item_frame, bg='#1a1a1a')
            item_row.pack(fill='x', padx=5, pady=2)
            
            # Item name
            name_label = tk.Label(
                item_row,
                text=item['name'],
                font=('Arial', 11),
                fg='white',
                bg='#1a1a1a',
                anchor='w'
            )
            name_label.pack(side='left', fill='x', expand=True)
            
            # Item price
            price = item.get('price', 0)
            price_label = tk.Label(
                item_row,
                text=f"₽{price:,}",
                font=('Arial', 11, 'bold'),
                fg='#4caf50',
                bg='#1a1a1a'
            )
            price_label.pack(side='right')
            
            total_value += price
            
        # Update canvas scroll region
        self.item_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Update status with total value
        self.status_label.config(text=f"Total: ₽{total_value:,}")
        
    def show(self):
        """Shows the overlay window."""
        self.root.deiconify()
        
    def hide(self):
        """Hides the overlay window."""
        self.root.withdraw()
        
    def close(self):
        """Closes the overlay window."""
        self.root.withdraw()  # Hide the window instead of quitting
        
    def run(self):
        """Starts the overlay window main loop."""
        self.root.mainloop()