import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import math
import os
from typing import Dict, List, Tuple, Optional

class MapManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Map Manager - Zarządzanie etykietami punktów")
        self.root.geometry("1200x800")
        
        # Dane
        self.map_data = None
        self.map_filename = None
        self.all_paths = []
        self.all_connections = []
        self.point_labels = {}  # ID punktu -> etykieta (np. "Sala 308")
        
        # Wizualizacja
        self.selected_point = None
        self.point_objects = {}  # ID punktu -> obiekty canvas
        
        # Lasso mode
        self.lasso_mode = False
        self.delete_lasso_mode_active = False
        self.lasso_points = []
        self.lasso_polygon = None
        self.selected_points = []  # Punkty zaznaczone lassem
        
        # Add node mode
        self.add_node_mode_active = False
        
        # Grid alignment
        self.grid_size = 20  # Domyślny rozmiar siatki w pikselach
        
        self.setup_ui()
        
        # Auto-wczytaj plik przy starcie
        self.root.after(100, self.auto_load_file)
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Panel górny - przyciski
        top_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(top_frame, text="💾 Zapisz wszystkie zmiany", 
                 command=self.save_all_changes,
                 bg='#2196F3', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(top_frame, text="🔲 Wyrównaj do siatki", 
                 command=self.align_to_grid,
                 bg='#607D8B', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="🎯 Lasso (grupuj)", 
                 command=self.toggle_lasso_mode,
                 bg='#E91E63', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(top_frame, text="🏷️ Dodaj etykietę", 
                 command=self.add_label_to_selected,
                 bg='#FF9800', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="✏️ Edytuj etykietę", 
                 command=self.edit_label,
                 bg='#9C27B0', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="🗑️ Usuń etykietę", 
                 command=self.remove_label,
                 bg='#f44336', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(top_frame, text="📋 Lista etykiet", 
                 command=self.show_labels_list,
                 bg='#00BCD4', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(top_frame, text="⬅️ Menu", 
                 command=self.return_to_menu,
                 bg='#607D8B', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Panel dolny - dodatkowe funkcje
        bottom_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        bottom_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(bottom_frame, text="➖ Usuń węzeł", 
                 command=self.delete_node,
                 bg='#FF5722', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(bottom_frame, text="🗑️ Usuń lassem", 
                 command=self.delete_lasso_mode,
                 bg='#D32F2F', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(bottom_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(bottom_frame, text="📊 Przegląd feedbacku", 
                 command=self.show_feedback,
                 bg='#673AB7', fg='white', font=('Arial', 10, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Panel informacyjny
        info_frame = tk.Frame(self.root, bg='#e3f2fd', pady=8)
        info_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.info_label = tk.Label(info_frame, 
                                   text="Wczytaj mapę aby rozpocząć zarządzanie etykietami",
                                   bg='#e3f2fd', font=('Arial', 11), fg='#1565c0')
        self.info_label.pack()
        
        # Panel główny - canvas i sidebar
        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas (lewa strona)
        canvas_frame = tk.Frame(main_frame, bg='white')
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(canvas_frame, text="MAPA - Kliknij na punkt aby dodać etykietę",
                bg='white', font=('Arial', 10, 'bold'), fg='#333').pack(pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#f5f5f5', cursor='hand2')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<Button-1>', self.on_point_click)
        
        # Sidebar (prawa strona)
        sidebar_frame = tk.Frame(main_frame, bg='#fafafa', width=300)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        sidebar_frame.pack_propagate(False)
        
        tk.Label(sidebar_frame, text="SZCZEGÓŁY PUNKTU",
                bg='#3F51B5', fg='white', font=('Arial', 11, 'bold'),
                pady=10).pack(fill=tk.X)
        
        # Informacje o wybranym punkcie
        details_frame = tk.Frame(sidebar_frame, bg='white', pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(details_frame, text="Wybrany punkt:", bg='white',
                font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        self.selected_point_label = tk.Label(details_frame, text="Brak",
                                             bg='white', font=('Arial', 10),
                                             fg='#666')
        self.selected_point_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        tk.Label(details_frame, text="Aktualna etykieta:", bg='white',
                font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        self.current_label_text = tk.Label(details_frame, text="Brak etykiety",
                                           bg='white', font=('Arial', 11),
                                           fg='#2196F3', wraplength=250)
        self.current_label_text.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        tk.Label(details_frame, text="Współrzędne:", bg='white',
                font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        self.coords_label = tk.Label(details_frame, text="x: -, y: -",
                                     bg='white', font=('Arial', 9), fg='#666')
        self.coords_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        tk.Label(details_frame, text="Połączenia:", bg='white',
                font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        self.connections_label = tk.Label(details_frame, text="0",
                                          bg='white', font=('Arial', 9), fg='#666')
        self.connections_label.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Przyciski szybkiego dostępu
        tk.Label(sidebar_frame, text="SZYBKIE AKCJE",
                bg='#3F51B5', fg='white', font=('Arial', 10, 'bold'),
                pady=8).pack(fill=tk.X)
        
        quick_frame = tk.Frame(sidebar_frame, bg='#fafafa')
        quick_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(quick_frame, text="🏢 Sala/Pokój", 
                 command=lambda: self.quick_label("sala"),
                 bg='#4CAF50', fg='white', font=('Arial', 9),
                 width=12).pack(pady=2, fill=tk.X)
        
        tk.Button(quick_frame, text="🚪 Wejście", 
                 command=lambda: self.quick_label("wejście"),
                 bg='#2196F3', fg='white', font=('Arial', 9),
                 width=12).pack(pady=2, fill=tk.X)
        
        tk.Button(quick_frame, text="🛗 Winda", 
                 command=lambda: self.quick_label("winda"),
                 bg='#FF9800', fg='white', font=('Arial', 9),
                 width=12).pack(pady=2, fill=tk.X)
        
        tk.Button(quick_frame, text="🚶 Schody", 
                 command=lambda: self.quick_label("schody"),
                 bg='#9C27B0', fg='white', font=('Arial', 9),
                 width=12).pack(pady=2, fill=tk.X)
        
        tk.Button(quick_frame, text="🚻 Toaleta", 
                 command=lambda: self.quick_label("toaleta"),
                 bg='#00BCD4', fg='white', font=('Arial', 9),
                 width=12).pack(pady=2, fill=tk.X)
        
        tk.Button(quick_frame, text="🔀 Skrzyżowanie", 
                 command=lambda: self.quick_label("skrzyżowanie"),
                 bg='#795548', fg='white', font=('Arial', 9),
                 width=12).pack(pady=2, fill=tk.X)
        
        # Status bar
        self.status_label = tk.Label(self.root, 
                                     text="Wczytaj mapę GPS aby rozpocząć",
                                     font=('Arial', 9), bg='#e0e0e0', pady=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_map(self):
        """Wczytuje mapę z pliku JSON"""
        filename = "gps_paths.json"
        
        if not os.path.exists(filename):
            messagebox.showerror("Błąd", f"Nie znaleziono pliku {filename}!\nUtwórz mapę w Map Maker.")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.map_data = json.load(f)
            
            self.map_filename = filename
            self.all_paths = self.map_data.get('paths', [])
            self.all_connections = self.map_data.get('connections', [])
            
            # Wczytaj istniejące etykiety jeśli są
            self.point_labels = self.map_data.get('point_labels', {})
            
            # Policz punkty
            total_points = sum(len(path['points']) for path in self.all_paths)
            labeled_points = len(self.point_labels)
            
            self.info_label['text'] = (f"✓ Wczytano: {len(self.all_paths)} ścieżek, "
                                      f"{total_points} punktów | "
                                      f"Etykiet: {labeled_points}")
            
            self.status_label['text'] = f"Mapa: {filename} | Kliknij na punkt aby dodać etykietę"
            
            self.draw_map()
            
            messagebox.showinfo("Mapa wczytana",
                              f"Wczytano mapę:\n\n"
                              f"Ścieżki: {len(self.all_paths)}\n"
                              f"Punkty: {total_points}\n"
                              f"Połączenia: {len(self.all_connections)}\n"
                              f"Etykiety: {labeled_points}")
            return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać mapy:\n{e}")
            return False
    
    def draw_map(self):
        """Rysuje mapę na canvas"""
        if not self.all_paths:
            return
        
        self.canvas.delete('all')
        self.point_objects.clear()
        
        # Rysuj połączenia
        for connection in self.all_connections:
            from_id = str(connection['from'])
            to_id = str(connection['to'])
            
            from_point = self.find_point(from_id)
            to_point = self.find_point(to_id)
            
            if from_point and to_point:
                self.canvas.create_line(
                    from_point['x'], from_point['y'],
                    to_point['x'], to_point['y'],
                    fill='#BDBDBD', width=2, tags='connection'
                )
        
        # Rysuj punkty
        for path in self.all_paths:
            for point in path['points']:
                if point['x'] == 0 and point['y'] == 0:
                    continue
                
                point_id = str(point['id'])
                x, y = point['x'], point['y']
                
                # Kolor zależny od tego czy punkt ma etykietę
                if point_id in self.point_labels:
                    color = '#4CAF50'  # Zielony - ma etykietę
                    radius = 8
                else:
                    color = '#2196F3'  # Niebieski - brak etykiety
                    radius = 6
                
                # Rysuj punkt
                oval = self.canvas.create_oval(
                    x - radius, y - radius,
                    x + radius, y + radius,
                    fill=color, outline='#1565C0', width=2,
                    tags=('point', f'point_{point_id}')
                )
                
                # Zapisz obiekt
                self.point_objects[point_id] = {
                    'oval': oval,
                    'point': point,
                    'x': x,
                    'y': y
                }
                
                # Jeśli ma etykietę, pokaż ją
                if point_id in self.point_labels:
                    label_text = self.point_labels[point_id]
                    self.canvas.create_text(
                        x, y - 15,
                        text=label_text,
                        font=('Arial', 8, 'bold'),
                        fill='#1B5E20',
                        tags=('label', f'label_{point_id}')
                    )
    
    def find_point(self, point_id: str) -> Optional[dict]:
        """Znajduje punkt po ID"""
        for path in self.all_paths:
            for point in path['points']:
                if str(point['id']) == point_id:
                    return point
        return None
    
    def on_point_click(self, event):
        """Obsługa kliknięcia na punkt"""
        # Znajdź najbliższy punkt
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(clicked_item)
        
        # Sprawdź czy kliknięto na punkt
        point_id = None
        for tag in tags:
            if tag.startswith('point_'):
                point_id = tag.replace('point_', '')
                break
        
        if not point_id or point_id not in self.point_objects:
            return
        
        # Zaznacz wybrany punkt
        self.select_point(point_id)
    
    def select_point(self, point_id: str):
        """Zaznacza wybrany punkt"""
        # Odznacz poprzedni
        if self.selected_point:
            old_oval = self.point_objects[self.selected_point]['oval']
            old_color = '#4CAF50' if self.selected_point in self.point_labels else '#2196F3'
            self.canvas.itemconfig(old_oval, outline='#1565C0', width=2)
        
        # Zaznacz nowy
        self.selected_point = point_id
        oval = self.point_objects[point_id]['oval']
        self.canvas.itemconfig(oval, outline='#FF5722', width=4)
        
        # Aktualizuj sidebar
        point = self.point_objects[point_id]['point']
        x, y = point['x'], point['y']
        
        self.selected_point_label['text'] = f"ID: {point_id}"
        self.coords_label['text'] = f"x: {x:.1f}, y: {y:.1f}"
        
        # Policz połączenia
        connections = sum(1 for conn in self.all_connections 
                         if str(conn['from']) == point_id or str(conn['to']) == point_id)
        self.connections_label['text'] = str(connections)
        
        # Pokaż etykietę jeśli istnieje
        if point_id in self.point_labels:
            self.current_label_text['text'] = self.point_labels[point_id]
            self.current_label_text['fg'] = '#4CAF50'
        else:
            self.current_label_text['text'] = "Brak etykiety"
            self.current_label_text['fg'] = '#999'
        
        self.status_label['text'] = f"Wybrany punkt ID: {point_id} | Użyj przycisków aby zarządzać etykietą"
    
    def add_label_to_selected(self):
        """Dodaje etykietę do wybranego punktu"""
        if not self.selected_point:
            messagebox.showwarning("Brak wyboru", "Najpierw wybierz punkt na mapie!")
            return
        
        # Pobierz etykietę od użytkownika
        label = simpledialog.askstring(
            "Dodaj etykietę",
            f"Wprowadź etykietę dla punktu ID {self.selected_point}:",
            initialvalue=self.point_labels.get(self.selected_point, "")
        )
        
        if label:
            self.point_labels[self.selected_point] = label
            self.draw_map()
            self.select_point(self.selected_point)  # Odśwież sidebar
            
            self.info_label['text'] = f"✓ Dodano etykietę: {label}"
    
    def quick_label(self, label_type: str):
        """Szybkie dodanie etykiety predefiniowanego typu"""
        if not self.selected_point:
            messagebox.showwarning("Brak wyboru", "Najpierw wybierz punkt na mapie!")
            return
        
        # Poproś o szczegóły (np. numer sali)
        detail = simpledialog.askstring(
            "Szczegóły",
            f"Podaj szczegóły dla '{label_type}' (np. numer):",
            initialvalue=""
        )
        
        if detail is not None:  # Użytkownik nie anulował
            if detail:
                label = f"{label_type.capitalize()} {detail}"
            else:
                label = label_type.capitalize()
            
            self.point_labels[self.selected_point] = label
            self.draw_map()
            self.select_point(self.selected_point)
            
            self.info_label['text'] = f"✓ Dodano: {label}"
    
    def edit_label(self):
        """Edytuje etykietę wybranego punktu"""
        if not self.selected_point:
            messagebox.showwarning("Brak wyboru", "Najpierw wybierz punkt na mapie!")
            return
        
        if self.selected_point not in self.point_labels:
            messagebox.showinfo("Brak etykiety", "Ten punkt nie ma etykiety. Użyj 'Dodaj etykietę'.")
            return
        
        current = self.point_labels[self.selected_point]
        new_label = simpledialog.askstring(
            "Edytuj etykietę",
            f"Edytuj etykietę punktu ID {self.selected_point}:",
            initialvalue=current
        )
        
        if new_label:
            self.point_labels[self.selected_point] = new_label
            self.draw_map()
            self.select_point(self.selected_point)
            
            self.info_label['text'] = f"✓ Zaktualizowano: {new_label}"
    
    def remove_label(self):
        """Usuwa etykietę wybranego punktu"""
        if not self.selected_point:
            messagebox.showwarning("Brak wyboru", "Najpierw wybierz punkt na mapie!")
            return
        
        if self.selected_point not in self.point_labels:
            messagebox.showinfo("Brak etykiety", "Ten punkt nie ma etykiety do usunięcia.")
            return
        
        label = self.point_labels[self.selected_point]
        if messagebox.askyesno("Potwierdzenie", f"Usunąć etykietę '{label}'?"):
            del self.point_labels[self.selected_point]
            self.draw_map()
            self.select_point(self.selected_point)
            
            self.info_label['text'] = f"✓ Usunięto etykietę"
    
    def show_labels_list(self):
        """Pokazuje listę wszystkich etykiet"""
        if not self.point_labels:
            messagebox.showinfo("Brak etykiet", "Nie dodano jeszcze żadnych etykiet!")
            return
        
        # Utwórz okno z listą
        list_window = tk.Toplevel(self.root)
        list_window.title("Lista etykiet")
        list_window.geometry("500x600")
        
        tk.Label(list_window, text="WSZYSTKIE ETYKIETY",
                bg='#3F51B5', fg='white', font=('Arial', 12, 'bold'),
                pady=10).pack(fill=tk.X)
        
        # Lista z przewijaniem
        list_frame = tk.Frame(list_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                            font=('Arial', 10), selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Wypełnij listę
        sorted_labels = sorted(self.point_labels.items(), key=lambda x: x[1])
        for point_id, label in sorted_labels:
            listbox.insert(tk.END, f"ID {point_id}: {label}")
        
        # Przycisk "Pokaż na mapie"
        def show_on_map():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                point_id, _ = sorted_labels[index]
                self.select_point(point_id)
                list_window.destroy()
        
        tk.Button(list_window, text="📍 Pokaż na mapie",
                 command=show_on_map,
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                 pady=8).pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(list_window, text=f"Łącznie etykiet: {len(self.point_labels)}",
                bg='#e0e0e0', font=('Arial', 9), pady=5).pack(fill=tk.X)
    
    def save_all_changes(self):
        """Zapisuje wszystkie zmiany do pliku JSON (etykiety, punkty, połączenia)"""
        if not self.map_data or not self.map_filename:
            messagebox.showwarning("Brak mapy", "Najpierw wczytaj mapę!")
            return
        
        try:
            # Aktualizuj dane mapy
            self.map_data['paths'] = self.all_paths
            self.map_data['connections'] = self.all_connections
            self.map_data['point_labels'] = self.point_labels
            
            # Zapisz
            with open(self.map_filename, 'w', encoding='utf-8') as f:
                json.dump(self.map_data, f, indent=2, ensure_ascii=False)
            
            total_points = sum(len(path['points']) for path in self.all_paths)
            
            messagebox.showinfo("Zapisano",
                              f"Wszystkie zmiany zapisane do:\n{self.map_filename}\n\n"
                              f"Ścieżki: {len(self.all_paths)}\n"
                              f"Punkty: {total_points}\n"
                              f"Połączenia: {len(self.all_connections)}\n"
                              f"Etykiety: {len(self.point_labels)}")
            
            self.info_label['text'] = f"✓ Zapisano wszystkie zmiany"
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać:\n{e}")
    
    def save_labels(self):
        """Stara funkcja - przekierowanie do save_all_changes"""
        self.save_all_changes()
    
    def align_to_grid(self):
        """Wyrównuje wszystkie punkty do siatki o zadanym rozmiarze"""
        if not self.map_data:
            messagebox.showwarning("Brak mapy", "Najpierw wczytaj mapę!")
            return
        
        # Dialog z opcjami siatki
        dialog = tk.Toplevel(self.root)
        dialog.title("Wyrównaj do siatki")
        dialog.geometry("350x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="WYRÓWNANIE DO SIATKI",
                bg='#607D8B', fg='white', font=('Arial', 12, 'bold'),
                pady=10).pack(fill=tk.X)
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Rozmiar siatki (piksele):",
                font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        grid_var = tk.IntVar(value=self.grid_size)
        
        slider = tk.Scale(frame, from_=5, to=100, orient=tk.HORIZONTAL,
                         variable=grid_var, length=250)
        slider.pack(fill=tk.X, pady=(0, 10))
        
        preview_label = tk.Label(frame, text=f"Siatka: {self.grid_size}px x {self.grid_size}px",
                                font=('Arial', 9), fg='#666')
        preview_label.pack(pady=(0, 15))
        
        def update_preview(*args):
            val = grid_var.get()
            preview_label['text'] = f"Siatka: {val}px x {val}px"
        
        grid_var.trace('w', update_preview)
        
        # Informacja o zmianach
        total_points = sum(len(path['points']) for path in self.all_paths)
        info_text = f"Ta operacja wyrówna {total_points} punktów.\n" \
                   f"Punkty będą przesunięte do najbliższego\n" \
                   f"węzła siatki. Połączenia zostaną zachowane."
        
        tk.Label(frame, text=info_text, font=('Arial', 9),
                fg='#666', justify=tk.LEFT).pack(pady=(0, 15))
        
        def apply_alignment():
            self.grid_size = grid_var.get()
            dialog.destroy()
            self._perform_grid_alignment()
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="✓ Wyrównaj",
                 command=apply_alignment,
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                 padx=20).pack(side=tk.LEFT, expand=True, padx=(0, 5))
        
        tk.Button(btn_frame, text="✗ Anuluj",
                 command=dialog.destroy,
                 bg='#757575', fg='white', font=('Arial', 10, 'bold'),
                 padx=20).pack(side=tk.RIGHT, expand=True, padx=(5, 0))
    
    def _perform_grid_alignment(self):
        """Wykonuje wyrównanie punktów do siatki"""
        if not self.map_data:
            return
        
        aligned_count = 0
        
        # Wyrównaj wszystkie punkty we wszystkich ścieżkach
        for path in self.all_paths:
            for point in path['points']:
                old_x, old_y = point['x'], point['y']
                
                # Wyrównaj do najbliższego węzła siatki
                new_x = round(point['x'] / self.grid_size) * self.grid_size
                new_y = round(point['y'] / self.grid_size) * self.grid_size
                
                if new_x != old_x or new_y != old_y:
                    point['x'] = new_x
                    point['y'] = new_y
                    aligned_count += 1
        
        # Przelicz odległości w połączeniach
        self._recalculate_connections()
        
        # Odśwież widok
        self.draw_map()
        
        messagebox.showinfo("Wyrównano",
                          f"Wyrównano {aligned_count} punktów do siatki {self.grid_size}px.\n"
                          f"Połączenia zostały przeliczone.\n\n"
                          f"Pamiętaj aby zapisać zmiany!")
        
        self.info_label['text'] = f"✓ Wyrównano {aligned_count} punktów do siatki {self.grid_size}px"
    
    def _recalculate_connections(self):
        """Przelicza odległości w połączeniach po zmianie pozycji punktów"""
        # Stwórz mapę ID -> współrzędne
        point_coords = {}
        for path in self.all_paths:
            for point in path['points']:
                point_coords[point['id']] = (point['x'], point['y'])
        
        # Przelicz odległości
        for conn in self.all_connections:
            from_id = conn['from']
            to_id = conn['to']
            
            if from_id in point_coords and to_id in point_coords:
                x1, y1 = point_coords[from_id]
                x2, y2 = point_coords[to_id]
                
                distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                conn['distance'] = round(distance, 2)
    
    def toggle_lasso_mode(self):
        """Przełącza tryb lasso do grupowego zaznaczania"""
        self.lasso_mode = not self.lasso_mode
        
        if self.lasso_mode:
            self.info_label['text'] = "🎯 TRYB LASSO: Narysuj obszar wokół punktów do zaznaczenia"
            self.info_label['bg'] = '#FFE0F0'
            self.canvas['cursor'] = 'crosshair'
            
            # Zmień bindowanie canvas
            self.canvas.unbind('<Button-1>')
            self.canvas.bind('<Button-1>', self.lasso_start)
            self.canvas.bind('<B1-Motion>', self.lasso_draw)
            self.canvas.bind('<ButtonRelease-1>', self.lasso_end)
            
            # Reset zaznaczenia
            self.lasso_points = []
            self.selected_points = []
            if self.lasso_polygon:
                self.canvas.delete(self.lasso_polygon)
                self.lasso_polygon = None
        else:
            self.info_label['text'] = "Kliknij na punkt aby dodać etykietę"
            self.info_label['bg'] = '#e3f2fd'
            self.canvas['cursor'] = 'hand2'
            
            # Przywróć normalne bindowanie
            self.canvas.unbind('<B1-Motion>')
            self.canvas.unbind('<ButtonRelease-1>')
            self.canvas.bind('<Button-1>', self.on_point_click)
            
            # Wyczyść lasso
            if self.lasso_polygon:
                self.canvas.delete(self.lasso_polygon)
                self.lasso_polygon = None
            self.lasso_points = []
    
    def lasso_start(self, event):
        """Rozpoczyna rysowanie lasso"""
        self.lasso_points = [(event.x, event.y)]
        if self.lasso_polygon:
            self.canvas.delete(self.lasso_polygon)
            self.lasso_polygon = None
    
    def lasso_draw(self, event):
        """Rysuje lasso podczas przeciągania"""
        self.lasso_points.append((event.x, event.y))
        
        if self.lasso_polygon:
            self.canvas.delete(self.lasso_polygon)
        
        if len(self.lasso_points) > 2:
            # Rysuj polygon
            flat_points = [coord for point in self.lasso_points for coord in point]
            self.lasso_polygon = self.canvas.create_polygon(
                flat_points,
                outline='#E91E63', width=2, fill='',
                dash=(5, 5), tags='lasso'
            )
    
    def lasso_end(self, event):
        """Kończy rysowanie lasso i zaznacza punkty wewnątrz"""
        if len(self.lasso_points) < 3:
            return
        
        # Zamknij polygon
        self.lasso_points.append(self.lasso_points[0])
        
        # Znajdź punkty wewnątrz polygonu
        self.selected_points = []
        for path in self.all_paths:
            for point in path['points']:
                if self._point_in_polygon(point['x'], point['y'], self.lasso_points):
                    self.selected_points.append(point['id'])
        
        if self.lasso_polygon:
            self.canvas.delete(self.lasso_polygon)
            self.lasso_polygon = None
        
        if self.selected_points:
            # Podświetl zaznaczone punkty
            self.draw_map()
            for point_id in self.selected_points:
                if point_id in self.point_objects:
                    oval, text = self.point_objects[point_id]
                    self.canvas.itemconfig(oval, fill='#E91E63', width=3)
            
            # Pokaż dialog przypisania etykiety
            self._show_group_label_dialog()
        else:
            messagebox.showinfo("Brak punktów", "W zaznaczonym obszarze nie ma punktów.")
        
        self.lasso_points = []
    
    def _point_in_polygon(self, x, y, polygon):
        """Sprawdza czy punkt (x,y) znajduje się wewnątrz polygonu (ray casting algorithm)"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _show_group_label_dialog(self):
        """Pokazuje dialog do przypisania etykiety dla grupy punktów"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Etykieta dla grupy")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="GRUPOWE PRZYPISANIE ETYKIETY",
                bg='#E91E63', fg='white', font=('Arial', 12, 'bold'),
                pady=10).pack(fill=tk.X)
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"Zaznaczono {len(self.selected_points)} punktów",
                font=('Arial', 11, 'bold')).pack(pady=(0, 15))
        
        tk.Label(frame, text="Przypisz etykietę do wszystkich zaznaczonych punktów:",
                font=('Arial', 10)).pack(anchor=tk.W, pady=(0, 5))
        
        entry_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=entry_var, font=('Arial', 12), width=30)
        entry.pack(fill=tk.X, pady=(0, 15))
        entry.focus()
        
        # Szybkie przyciski
        tk.Label(frame, text="Lub wybierz szablon:",
                font=('Arial', 9), fg='#666').pack(anchor=tk.W, pady=(0, 5))
        
        quick_frame = tk.Frame(frame)
        quick_frame.pack(fill=tk.X, pady=(0, 15))
        
        templates = [
            ("🏢 Sala/Pokój", "Sala "),
            ("🚪 Wejście", "Wejście"),
            ("🛗 Winda", "Winda"),
            ("🚶 Schody", "Schody"),
            ("🚻 Toaleta", "Toaleta"),
            ("🔀 Korytarz", "Korytarz")
        ]
        
        for i, (btn_text, template) in enumerate(templates):
            row = i // 2
            col = i % 2
            tk.Button(quick_frame, text=btn_text,
                     command=lambda t=template: entry_var.set(t),
                     font=('Arial', 8), width=15).grid(row=row, column=col, padx=2, pady=2)
        
        def apply_label():
            label = entry_var.get().strip()
            if not label:
                messagebox.showwarning("Pusta etykieta", "Podaj etykietę!")
                return
            
            # Przypisz etykietę do wszystkich zaznaczonych punktów
            for point_id in self.selected_points:
                self.point_labels[str(point_id)] = label
            
            dialog.destroy()
            self.draw_map()
            self.toggle_lasso_mode()  # Wyłącz tryb lasso
            
            messagebox.showinfo("Przypisano",
                              f"Etykieta '{label}' przypisana do {len(self.selected_points)} punktów.\n\n"
                              f"Pamiętaj aby zapisać zmiany!")
        
        def cancel():
            dialog.destroy()
            self.draw_map()
        
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="✓ Przypisz",
                 command=apply_label,
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                 padx=20).pack(side=tk.LEFT, expand=True, padx=(0, 5))
        
        tk.Button(btn_frame, text="✗ Anuluj",
                 command=cancel,
                 bg='#757575', fg='white', font=('Arial', 10, 'bold'),
                 padx=20).pack(side=tk.RIGHT, expand=True, padx=(5, 0))
        
        entry.bind('<Return>', lambda e: apply_label())
    
    def delete_node(self):
        """Usuwa wybrany węzeł z natychmiastową aktualizacją widoku"""
        if not self.selected_point:
            messagebox.showwarning("Brak wyboru", "Najpierw wybierz punkt do usunięcia!")
            return
        
        node_id = self.selected_point
        
        # Usuń punkt ze ścieżek (natychmiast)
        for path in self.all_paths:
            path['points'] = [p for p in path['points'] if p['id'] != node_id]
        
        # Usuń puste ścieżki
        self.all_paths = [p for p in self.all_paths if len(p['points']) > 0]
        
        # Usuń połączenia z tym punktem
        self.all_connections = [
            c for c in self.all_connections 
            if c['from'] != node_id and c['to'] != node_id
        ]
        
        # Usuń etykietę jeśli istnieje
        if str(node_id) in self.point_labels:
            del self.point_labels[str(node_id)]
        
        # Reset wyboru
        self.selected_point = None
        self.selected_point_label['text'] = "Brak"
        self.current_label_text['text'] = "Brak etykiety"
        self.coords_label['text'] = "x: -, y: -"
        self.connections_label['text'] = "0"
        
        # Natychmiastowa aktualizacja widoku
        self.draw_map()
        
        self.info_label['text'] = f"✓ Usunięto węzeł {node_id} (pamiętaj zapisać zmiany)"
    
    def delete_lasso_mode(self):
        """Aktywuje tryb usuwania węzłów lassem"""
        if not self.map_data:
            messagebox.showwarning("Brak mapy", "Najpierw wczytaj mapę!")
            return
        
        self.delete_lasso_mode_active = not self.delete_lasso_mode_active
        
        if self.delete_lasso_mode_active:
            self.info_label['text'] = "🗑️ TRYB USUWANIA LASSEM: Narysuj obszar wokół węzłów do usunięcia"
            self.info_label['bg'] = '#FFCDD2'
            self.canvas['cursor'] = 'crosshair'
            
            # Zmień bindowanie canvas
            self.canvas.unbind('<Button-1>')
            self.canvas.bind('<Button-1>', self.delete_lasso_start)
            self.canvas.bind('<B1-Motion>', self.delete_lasso_draw)
            self.canvas.bind('<ButtonRelease-1>', self.delete_lasso_end)
            
            # Reset zaznaczenia
            self.lasso_points = []
            self.selected_points = []
            if self.lasso_polygon:
                self.canvas.delete(self.lasso_polygon)
                self.lasso_polygon = None
        else:
            self.info_label['text'] = "Kliknij na punkt aby dodać etykietę"
            self.info_label['bg'] = '#e3f2fd'
            self.canvas['cursor'] = 'hand2'
            
            # Przywróć normalne bindowanie
            self.canvas.unbind('<B1-Motion>')
            self.canvas.unbind('<ButtonRelease-1>')
            self.canvas.bind('<Button-1>', self.on_point_click)
            
            # Wyczyść lasso
            if self.lasso_polygon:
                self.canvas.delete(self.lasso_polygon)
                self.lasso_polygon = None
            self.lasso_points = []
    
    def delete_lasso_start(self, event):
        """Rozpoczyna rysowanie lasso do usuwania"""
        self.lasso_points = [(event.x, event.y)]
        if self.lasso_polygon:
            self.canvas.delete(self.lasso_polygon)
            self.lasso_polygon = None
    
    def delete_lasso_draw(self, event):
        """Rysuje lasso podczas przeciągania"""
        self.lasso_points.append((event.x, event.y))
        
        if self.lasso_polygon:
            self.canvas.delete(self.lasso_polygon)
        
        if len(self.lasso_points) > 2:
            # Rysuj polygon w kolorze czerwonym
            flat_points = [coord for point in self.lasso_points for coord in point]
            self.lasso_polygon = self.canvas.create_polygon(
                flat_points,
                outline='#D32F2F', width=3, fill='',
                dash=(5, 5), tags='delete_lasso'
            )
    
    def delete_lasso_end(self, event):
        """Kończy rysowanie lasso i usuwa punkty wewnątrz"""
        if len(self.lasso_points) < 3:
            return
        
        # Zamknij polygon
        self.lasso_points.append(self.lasso_points[0])
        
        # Znajdź punkty wewnątrz polygonu
        nodes_to_delete = []
        for path in self.all_paths:
            for point in path['points']:
                if self._point_in_polygon(point['x'], point['y'], self.lasso_points):
                    nodes_to_delete.append(point['id'])
        
        if self.lasso_polygon:
            self.canvas.delete(self.lasso_polygon)
            self.lasso_polygon = None
        
        if nodes_to_delete:
            # Potwierdź usunięcie
            result = messagebox.askyesno("Usuń węzły",
                                        f"Znaleziono {len(nodes_to_delete)} węzłów w zaznaczonym obszarze.\n\n"
                                        f"Czy na pewno chcesz usunąć wszystkie?\n\n"
                                        f"Węzły: {', '.join(map(str, nodes_to_delete[:10]))}"
                                        f"{'...' if len(nodes_to_delete) > 10 else ''}")
            
            if result:
                # Usuń wszystkie punkty
                for node_id in nodes_to_delete:
                    # Usuń punkt ze ścieżek
                    for path in self.all_paths:
                        path['points'] = [p for p in path['points'] if p['id'] != node_id]
                    
                    # Usuń połączenia z tym punktem
                    self.all_connections = [
                        c for c in self.all_connections 
                        if c['from'] != node_id and c['to'] != node_id
                    ]
                    
                    # Usuń etykietę jeśli istnieje
                    if str(node_id) in self.point_labels:
                        del self.point_labels[str(node_id)]
                
                # Usuń puste ścieżki
                self.all_paths = [p for p in self.all_paths if len(p['points']) > 0]
                
                # Natychmiastowa aktualizacja widoku
                self.draw_map()
                
                self.info_label['text'] = f"✓ Usunięto {len(nodes_to_delete)} węzłów (pamiętaj zapisać zmiany)"
                
                # Wyłącz tryb usuwania lassem
                self.delete_lasso_mode_active = False
                self.canvas['cursor'] = 'hand2'
                self.canvas.unbind('<B1-Motion>')
                self.canvas.unbind('<ButtonRelease-1>')
                self.canvas.bind('<Button-1>', self.on_point_click)
        else:
            messagebox.showinfo("Brak węzłów", "W zaznaczonym obszarze nie ma węzłów.")
        
        self.lasso_points = []
    
    def show_feedback(self):
        """Wyświetla okno z feedbackiem od użytkowników"""
        feedback_file = "route_feedback.json"
        
        if not os.path.exists(feedback_file):
            messagebox.showinfo("Brak feedbacku",
                              "Nie znaleziono pliku route_feedback.json\n\n"
                              "Feedback pojawi się po tym jak użytkownicy\n"
                              "przejdą trasę w aplikacji Navigator.")
            return
        
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
            
            if not feedbacks:
                messagebox.showinfo("Brak feedbacku",
                                  "Plik feedbacku jest pusty.\n\n"
                                  "Brak danych do wyświetlenia.")
                return
            
            # Utwórz okno feedbacku
            feedback_window = tk.Toplevel(self.root)
            feedback_window.title("Przegląd Feedbacku Użytkowników")
            feedback_window.geometry("900x600")
            feedback_window.transient(self.root)
            
            # Header
            tk.Label(feedback_window, text="📊 FEEDBACK OD UŻYTKOWNIKÓW",
                    bg='#673AB7', fg='white', font=('Arial', 14, 'bold'),
                    pady=15).pack(fill=tk.X)
            
            # Statystyki
            stats_frame = tk.Frame(feedback_window, bg='#F3E5F5', pady=10)
            stats_frame.pack(fill=tk.X, padx=10, pady=10)
            
            total = len(feedbacks)
            deviated = sum(1 for f in feedbacks if f.get('deviated', False))
            
            reasons = {}
            for f in feedbacks:
                reason = f.get('reason', 'unknown')
                reasons[reason] = reasons.get(reason, 0) + 1
            
            stats_text = f"Łącznie odpowiedzi: {total} | Zboczyli z trasy: {deviated} ({deviated*100//total if total else 0}%)"
            tk.Label(stats_frame, text=stats_text,
                    bg='#F3E5F5', font=('Arial', 11, 'bold'),
                    fg='#4A148C').pack()
            
            reasons_text = "Powody: " + " | ".join([f"{k}: {v}" for k, v in reasons.items()])
            tk.Label(stats_frame, text=reasons_text,
                    bg='#F3E5F5', font=('Arial', 9),
                    fg='#666').pack(pady=(5, 0))
            
            # Lista feedbacków
            list_frame = tk.Frame(feedback_window)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Scrollbar
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Text widget z formatowaniem
            text_widget = tk.Text(list_frame, yscrollcommand=scrollbar.set,
                                 font=('Courier', 9), wrap=tk.WORD)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Wypełnij feedbackami
            for i, fb in enumerate(feedbacks, 1):
                text_widget.insert(tk.END, f"\n{'='*90}\n", 'separator')
                text_widget.insert(tk.END, f"FEEDBACK #{i}\n", 'header')
                text_widget.insert(tk.END, f"{'='*90}\n", 'separator')
                
                timestamp = fb.get('timestamp', 'Brak daty')
                text_widget.insert(tk.END, f"Data: {timestamp}\n", 'info')
                
                deviated = fb.get('deviated', False)
                status = "❌ ZBOCZYŁ Z TRASY" if deviated else "✓ Zgodnie z trasą"
                text_widget.insert(tk.END, f"Status: {status}\n", 'status')
                
                reason = fb.get('reason', 'brak')
                reason_map = {
                    'crowded': '👥 Zbyt tłoczno',
                    'shorter': '⚡ Krótsza trasa',
                    'blocked': '🚫 Zablokowana',
                    'nonexistent': '❓ Nieistniejąca',
                    'other': '📝 Inny powód',
                    'exploring': '🗺️ Eksploracja'
                }
                text_widget.insert(tk.END, f"Powód: {reason_map.get(reason, reason)}\n", 'reason')
                
                suggested = fb.get('suggested_route', [])
                text_widget.insert(tk.END, f"Sugerowana trasa: {' → '.join(map(str, suggested))}\n", 'route')
                
                visited = fb.get('visited_nodes', [])
                text_widget.insert(tk.END, f"Faktyczna trasa:  {' → '.join(map(str, visited))}\n", 'route')
                
                path_len = fb.get('path_length', 0)
                text_widget.insert(tk.END, f"Długość ścieżki: {path_len} punktów\n", 'info')
                
                notes = fb.get('notes', '')
                if notes:
                    text_widget.insert(tk.END, f"Notatki: {notes}\n", 'notes')
                
                text_widget.insert(tk.END, "\n")
            
            # Konfiguruj tagi
            text_widget.tag_config('separator', foreground='#999')
            text_widget.tag_config('header', font=('Courier', 10, 'bold'), foreground='#673AB7')
            text_widget.tag_config('info', foreground='#666')
            text_widget.tag_config('status', font=('Courier', 9, 'bold'), foreground='#D32F2F')
            text_widget.tag_config('reason', foreground='#1976D2')
            text_widget.tag_config('route', font=('Courier', 8), foreground='#388E3C')
            text_widget.tag_config('notes', foreground='#F57C00', font=('Courier', 9, 'italic'))
            
            text_widget.config(state=tk.DISABLED)
            
            # Przycisk zamknij
            tk.Button(feedback_window, text="Zamknij",
                     command=feedback_window.destroy,
                     bg='#757575', fg='white',
                     font=('Arial', 10, 'bold'),
                     padx=20, pady=8).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać feedbacku:\n{e}")
    
    def auto_load_file(self):
        """Automatycznie wczytuje plik przy starcie"""
        if self.load_map():
            print("✓ Automatycznie wczytano mapę z gps_paths.json")
    
    def return_to_menu(self):
        """Zamyka aplikację i wraca do menu głównego"""
        import subprocess
        import sys
        import os
        
        result = messagebox.askyesno("Powrót do Menu",
                                     "Czy na pewno chcesz wrócić do menu głównego?\n\n"
                                     "Niezapisane zmiany mogą zostać utracone.")
        
        if result:
            # Uruchom menu
            script_dir = os.path.dirname(os.path.abspath(__file__))
            menu_path = os.path.join(script_dir, "menu.py")
            
            if os.path.exists(menu_path):
                if sys.platform == "win32":
                    subprocess.Popen([sys.executable, menu_path])
                else:
                    subprocess.Popen([sys.executable, menu_path])
            
            # Zamknij tę aplikację
            self.root.quit()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = MapManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
