import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import sys
import os

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS Navigation System - Menu Główne")
        self.root.geometry("600x700")
        self.root.configure(bg='#f5f5f5')
        
        # Centruj okno
        self.center_window()
        
        self.setup_ui()
    
    def center_window(self):
        """Centruje okno na ekranie"""
        self.root.update_idletasks()
        width = 600
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Header
        header_frame = tk.Frame(self.root, bg='#1976D2', pady=30)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(header_frame, 
                text="🗺️ GPS NAVIGATION SYSTEM",
                bg='#1976D2', fg='white',
                font=('Arial', 24, 'bold')).pack()
        
        tk.Label(header_frame,
                text="System nawigacji i zarządzania mapami",
                bg='#1976D2', fg='#BBDEFB',
                font=('Arial', 12)).pack(pady=(5, 0))
        
        # Main content
        content_frame = tk.Frame(self.root, bg='#f5f5f5', pady=30)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=40)
        
        tk.Label(content_frame,
                text="Wybierz aplikację:",
                bg='#f5f5f5', font=('Arial', 14, 'bold'),
                fg='#333').pack(pady=(0, 20))
        
        # Przyciski aplikacji
        self.create_app_button(
            content_frame,
            "🧭 NAVIGATOR",
            "Nawigacja w czasie rzeczywistym",
            '#FF5722',
            self.open_navigator,
            require_auth=False
        )
        
        self.create_app_button(
            content_frame,
            "🗺️ MAP MAKER",
            "Tworzenie i edycja map GPS",
            '#4CAF50',
            self.open_mapmaker,
            require_auth=True
        )
        
        self.create_app_button(
            content_frame,
            "📊 GRAPH ANALYZER",
            "Analiza i znajdowanie najkrótszej ścieżki",
            '#2196F3',
            self.open_graph,
            require_auth=True
        )
        
        self.create_app_button(
            content_frame,
            "🏷️ MAP MANAGER",
            "Zarządzanie etykietami i punktami",
            '#9C27B0',
            self.open_map_manager,
            require_auth=True
        )
        
        # Footer
        footer_frame = tk.Frame(self.root, bg='#e0e0e0', pady=15)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Label(footer_frame,
                text="🔒 Aplikacje administracyjne wymagają hasła",
                bg='#e0e0e0', font=('Arial', 9),
                fg='#666').pack()
        
        tk.Button(footer_frame, text="❌ Zamknij",
                 command=self.root.quit,
                 bg='#757575', fg='white',
                 font=('Arial', 9, 'bold'),
                 padx=20, pady=5).pack(pady=(10, 0))
    
    def create_app_button(self, parent, title, description, color, command, require_auth=False):
        """Tworzy przycisk aplikacji"""
        button_frame = tk.Frame(parent, bg='white', relief=tk.RAISED, borderwidth=2)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Ramka wewnętrzna
        inner_frame = tk.Frame(button_frame, bg='white', padx=20, pady=15)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tytuł
        title_label = tk.Label(inner_frame,
                               text=title,
                               bg='white',
                               font=('Arial', 16, 'bold'),
                               fg=color)
        title_label.pack(anchor=tk.W)
        
        # Opis
        desc_label = tk.Label(inner_frame,
                             text=description,
                             bg='white',
                             font=('Arial', 10),
                             fg='#666')
        desc_label.pack(anchor=tk.W, pady=(2, 8))
        
        # Badge dla aplikacji wymagających autoryzacji
        if require_auth:
            badge_label = tk.Label(inner_frame,
                                  text="🔒 Wymaga hasła administratora",
                                  bg='white',
                                  font=('Arial', 8, 'italic'),
                                  fg='#999')
            badge_label.pack(anchor=tk.W)
        
        # Przycisk uruchomienia
        launch_btn = tk.Button(inner_frame,
                              text="▶ Uruchom",
                              command=lambda: self.launch_app(command, require_auth),
                              bg=color, fg='white',
                              font=('Arial', 11, 'bold'),
                              padx=20, pady=8,
                              cursor='hand2')
        launch_btn.pack(anchor=tk.E)
        
        # Hover effect
        def on_enter(e):
            button_frame.configure(relief=tk.RAISED, borderwidth=3)
        
        def on_leave(e):
            button_frame.configure(relief=tk.RAISED, borderwidth=2)
        
        button_frame.bind('<Enter>', on_enter)
        button_frame.bind('<Leave>', on_leave)
    
    def launch_app(self, command, require_auth):
        """Uruchamia aplikację z opcjonalną autoryzacją"""
        if require_auth:
            if not self.authenticate():
                return
        
        command()
    
    def authenticate(self):
        """Prosta autoryzacja administratora"""
        password = simpledialog.askstring(
            "Autoryzacja Administratora",
            "Podaj hasło administratora:",
            show='*'
        )
        
        if password == "admin":
            messagebox.showinfo("Sukces", "✓ Autoryzacja pomyślna!")
            return True
        elif password is not None:  # Użytkownik wpisał coś (nie anulował)
            messagebox.showerror("Błąd", "✗ Nieprawidłowe hasło!")
        
        return False
    
    def open_navigator(self):
        """Otwiera aplikację Navigator"""
        self.open_app("navigator.py", "Navigator")
    
    def open_mapmaker(self):
        """Otwiera aplikację Map Maker"""
        self.open_app("mapmaker_new.py", "Map Maker")
    
    def open_graph(self):
        """Otwiera aplikację Graph Analyzer"""
        self.open_app("graph.py", "Graph Analyzer")
    
    def open_map_manager(self):
        """Otwiera aplikację Map Manager"""
        self.open_app("map_manager.py", "Map Manager")
    
    def open_app(self, filename, app_name):
        """Otwiera wybraną aplikację jako osobny proces"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, filename)
        
        if not os.path.exists(app_path):
            messagebox.showerror("Błąd", f"Nie znaleziono pliku:\n{app_path}")
            return
        
        try:
            # Uruchom aplikację jako osobny proces
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, app_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, app_path])
            
            # Zamknij menu po uruchomieniu aplikacji
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się uruchomić {app_name}:\n{e}")

def main():
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()

if __name__ == "__main__":
    main()
