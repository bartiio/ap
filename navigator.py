import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math
import datetime
import os
from typing import Dict, List, Tuple, Optional

class GPSNavigator:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS Navigator - Nawigacja wielopiętrowa")
        self.root.geometry("1000x800")
        
        # Multi-floor support
        self.floors = {}  # Dane wszystkich pięter
        self.floor_transitions = []  # Przejścia między piętrami
        self.building_info = {}
        self.current_floor = "0"  # Aktualne piętro użytkownika
        self.route_floor = "0"  # Piętro pokazywane na mapie (dla trasy)
        
        # Dane (legacy dla pojedynczego piętra)
        self.all_paths = []
        self.all_connections = []
        self.shortest_path = []
        self.path_segments = []
        self.nodes_coords = {}
        self.point_labels = {}  # Etykiety punktów (ID -> nazwa)
        
        # Stan użytkownika
        self.user_position = None
        self.current_path_index = 0
        self.is_drawing = False
        self.drawn_path = []
        self.proximity_threshold = 30  # Odległość w pikselach do uznania że użytkownik dotarł
        
        # Ścieżki użytkowników do aktualizacji mapy
        self.user_paths_history = []  # Lista wszystkich przejść użytkowników
        self.current_user_path = []  # Aktualna ścieżka użytkownika
        self.map_filename = None  # Nazwa pliku z mapą
        
        # Kierunek ruchu użytkownika (do nawigacji względnej)
        self.user_direction = None  # Kąt w radianach
        self.last_positions = []  # Ostatnie kilka pozycji do obliczenia kierunku
        
        # Kontrola zgodności z trasą
        self.route_deviation_threshold = 50  # Odległość od trasy uznawana za odstępstwo
        self.deviated_from_route = False  # Czy użytkownik zboczył z trasy
        self.visited_nodes = []  # Węzły które użytkownik faktycznie odwiedził
        
        # Tryb wolnej eksploracji
        self.free_exploration_mode = False
        
        # Alerty dla przejść między piętrami
        self.floor_transition_alert_shown = False
        self.next_transition = None  # Następne przejście na trasie
        
        self.setup_ui()
        
        # Automatycznie wczytaj pliki przy starcie
        self.root.after(100, self.auto_load_files)
    
    def auto_load_files(self):
        """Automatycznie wczytuje pliki gps_paths.json i shortest_path.json"""
        # Wczytaj mapę
        if self.load_map():
            # Jeśli mapa OK, spróbuj wczytać trasę
            self.load_route()
    
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Panel górny - przyciski
        top_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(top_frame, text="📂 Wczytaj mapę (GPS paths)", 
                 command=self.load_map,
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="🎯 Wczytaj trasę (Shortest path)", 
                 command=self.load_route,
                 bg='#2196F3', fg='white', font=('Arial', 10, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(top_frame, text="🚶 Rozpocznij nawigację", 
                 command=self.start_navigation,
                 bg='#FF5722', fg='white', font=('Arial', 10, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="�️ Wolna eksploracja", 
                 command=self.start_free_exploration,
                 bg='#9C27B0', fg='white', font=('Arial', 10, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_frame, text="�🗑️ Wyczyść pozycję", 
                 command=self.clear_user_path,
                 bg='#f44336', fg='white', font=('Arial', 10, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Label(top_frame, text="Auto-update mapy:", 
                bg='#f0f0f0', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        self.auto_update_var = tk.BooleanVar(value=True)
        tk.Checkbutton(top_frame, text="Włączone", variable=self.auto_update_var,
                      bg='#f0f0f0', font=('Arial', 9, 'bold'),
                      activebackground='#f0f0f0').pack(side=tk.LEFT)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Wybór piętra
        tk.Label(top_frame, text="🏢 Piętro:", 
                bg='#f0f0f0', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.floor_var = tk.StringVar(value="0")
        self.floor_combo = ttk.Combobox(top_frame, textvariable=self.floor_var,
                                        values=["0"], width=15, state='readonly')
        self.floor_combo.pack(side=tk.LEFT, padx=5)
        self.floor_combo.bind('<<ComboboxSelected>>', self.on_floor_changed)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(top_frame, text="⬅️ Menu", 
                 command=self.return_to_menu,
                 bg='#607D8B', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Panel ustawień
        settings_frame = tk.Frame(self.root, bg='#e8f5e9', pady=8)
        settings_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(settings_frame, text="Próg bliskości (px):", 
                bg='#e8f5e9', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        self.threshold_var = tk.IntVar(value=30)
        threshold_slider = tk.Scale(settings_frame, from_=10, to=100, 
                                   orient=tk.HORIZONTAL, variable=self.threshold_var,
                                   length=150, command=self.update_threshold)
        threshold_slider.pack(side=tk.LEFT, padx=5)
        
        self.threshold_label = tk.Label(settings_frame, text="30 px", 
                                       bg='#e8f5e9', font=('Arial', 9, 'bold'))
        self.threshold_label.pack(side=tk.LEFT, padx=5)
        
        tk.Frame(settings_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        tk.Label(settings_frame, text="Próbkowanie ścieżki (co N-ty punkt):", 
                bg='#e8f5e9', font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        self.sampling_var = tk.IntVar(value=50)
        sampling_slider = tk.Scale(settings_frame, from_=20, to=100, 
                                   orient=tk.HORIZONTAL, variable=self.sampling_var,
                                   length=150, command=self.update_sampling)
        sampling_slider.pack(side=tk.LEFT, padx=5)
        
        self.sampling_label = tk.Label(settings_frame, text="co 50", 
                                       bg='#e8f5e9', font=('Arial', 9, 'bold'))
        self.sampling_label.pack(side=tk.LEFT, padx=5)
        
        # Panel informacyjny - nawigacja
        self.nav_frame = tk.Frame(self.root, bg='#1976D2', pady=15)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.nav_label = tk.Label(self.nav_frame, 
                                 text="Wczytaj mapę i trasę aby rozpocząć nawigację",
                                 bg='#1976D2', fg='white', 
                                 font=('Arial', 14, 'bold'))
        self.nav_label.pack()
        
        self.distance_label = tk.Label(self.nav_frame, 
                                      text="",
                                      bg='#1976D2', fg='#BBDEFB', 
                                      font=('Arial', 11))
        self.distance_label.pack()
        
        # Panel canvas
        canvas_container = tk.Frame(self.root, bg='white')
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas do rysowania
        self.canvas = tk.Canvas(canvas_container, bg='white', 
                               cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Legenda
        legend_frame = tk.Frame(self.root, bg='#f5f5f5', pady=5)
        legend_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Label(legend_frame, text="● Szare linie: Mapa", 
                bg='#f5f5f5', fg='gray', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="● Czerwona linia: Trasa do przejścia", 
                bg='#f5f5f5', fg='red', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="● Niebieska linia: Twoja pozycja", 
                bg='#f5f5f5', fg='blue', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="🟢 Start", 
                bg='#f5f5f5', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="🔴 Cel", 
                bg='#f5f5f5', font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
    def update_threshold(self, value):
        """Aktualizuje próg bliskości"""
        self.proximity_threshold = int(value)
        self.threshold_label['text'] = f"{value} px"
    
    def update_sampling(self, value):
        """Aktualizuje częstotliwość próbkowania"""
        self.sampling_label['text'] = f"co {value}"
        
    def load_map(self):
        """Automatycznie wczytuje mapę z gps_paths.json (multi-floor support)"""
        filename = "gps_paths.json"
        
        if not os.path.exists(filename):
            messagebox.showerror("Błąd", 
                               f"Nie znaleziono pliku: {filename}\n\n"
                               f"Utwórz mapę w Map Maker najpierw.")
            return False
        
        self.map_filename = filename
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sprawdź czy to nowy format wielopiętrowy
            if 'floors' in data and 'building_info' in data:
                # Nowy format - multi-floor
                self.floors = data.get('floors', {})
                self.floor_transitions = data.get('floor_transitions', [])
                self.building_info = data.get('building_info', {})
                
                # Ustaw domyślne piętro
                floor_list = list(self.floors.keys())
                if floor_list:
                    self.current_floor = floor_list[0]
                    self.route_floor = floor_list[0]
                    
                    # Zaktualizuj combobox
                    floor_names = [f"{f} - {self.building_info.get('floor_names', {}).get(f, f'Piętro {f}')}" 
                                  for f in floor_list]
                    self.floor_combo['values'] = floor_names
                    self.floor_combo.set(floor_names[0])
                    
                    # Wczytaj dane aktualnego piętra
                    self.load_floor_data(self.current_floor)
                
                print(f"✓ Wczytano budynek wielopiętrowy: {filename}")
                print(f"  Piętra: {len(self.floors)}")
                print(f"  Przejścia: {len(self.floor_transitions)}")
                
                self.draw_map()
                return True
            else:
                # Stary format - single floor
                self.all_paths = data.get('paths', [])
                self.all_connections = data.get('connections', [])
                self.point_labels = data.get('point_labels', {})
                
                # Konwertuj na multi-floor
                self.floors = {
                    "0": {
                        "paths": self.all_paths,
                        "connections": self.all_connections,
                        "point_labels": self.point_labels
                    }
                }
                self.floor_transitions = []
                self.building_info = {"name": "Budynek", "floors": ["0"], "floor_names": {"0": "Parter"}}
                self.current_floor = "0"
                
                print(f"✓ Wczytano mapę (stary format): {filename}")
                print(f"  Ścieżki: {len(self.all_paths)}")
                print(f"  Połączenia: {len(self.all_connections)}")
                
                self.draw_map()
                return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać mapy:\n{e}")
            return False
    
    def load_floor_data(self, floor_id):
        """Wczytuje dane konkretnego piętra do zmiennych roboczych"""
        if floor_id not in self.floors:
            return
        
        floor_data = self.floors[floor_id]
        self.all_paths = floor_data.get('paths', [])
        self.all_connections = floor_data.get('connections', [])
        self.point_labels = floor_data.get('point_labels', {})
    
    def on_floor_changed(self, event=None):
        """Obsługa zmiany wybranego piętra"""
        selected = self.floor_combo.get()
        if not selected:
            return
        
        # Wyciągnij ID piętra (przed " - ")
        floor_id = selected.split(' - ')[0]
        
        if floor_id in self.floors:
            self.current_floor = floor_id
            self.route_floor = floor_id
            self.load_floor_data(floor_id)
            
            # Przerysuj mapę
            self.canvas.delete('all')
            self.draw_map()
            
            # Jeśli jest trasa, przerysuj ją dla nowego piętra
            if self.shortest_path:
                self.draw_route()
    
    def load_route(self):
        """Automatycznie wczytuje trasę z shortest_path.json (multi-floor support)"""
        filename = "shortest_path.json"
        
        if not os.path.exists(filename):
            messagebox.showwarning("Brak trasy", 
                                  f"Nie znaleziono pliku: {filename}\n\n"
                                  f"Użyj Graph Analyzer aby wygenerować trasę.")
            return False
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            path_data = data.get('shortest_path', {})
            self.shortest_path = path_data.get('path', [])
            self.path_segments = data.get('path_segments', [])
            self.nodes_coords = data.get('nodes_coordinates', {})
            
            if not self.shortest_path:
                messagebox.showwarning("Pusta trasa", "Nie znaleziono trasy w pliku!")
                return False
            
            # Wykryj przejścia między piętrami na trasie
            floor_transitions_on_route = path_data.get('floor_transitions', [])
            
            # Określ piętro startowe (pierwsze piętro na trasie)
            if self.shortest_path and '_' in self.shortest_path[0]:
                start_floor = self.shortest_path[0].split('_')[0]
                self.current_floor = start_floor
                self.route_floor = start_floor
                
                # Ustaw combobox na właściwe piętro
                floor_list = list(self.floors.keys())
                if start_floor in floor_list:
                    idx = floor_list.index(start_floor)
                    floor_names = self.floor_combo['values']
                    if idx < len(floor_names):
                        self.floor_combo.set(floor_names[idx])
                        self.load_floor_data(start_floor)
            
            # Przygotuj ładne nazwy tras (obsługa multi-floor ID)
            start_id = self.shortest_path[0]
            end_id = self.shortest_path[-1]
            
            # Usuń prefix piętra jeśli istnieje
            start_point = start_id.split('_')[-1] if '_' in start_id else start_id
            end_point = end_id.split('_')[-1] if '_' in end_id else end_id
            
            start_label = self.point_labels.get(start_point, f"Punkt {start_point}")
            end_label = self.point_labels.get(end_point, f"Punkt {end_point}")
            
            print(f"✓ Automatycznie wczytano trasę: {filename}")
            print(f"  Start: {start_label} (węzeł: {start_id})")
            print(f"  Cel: {end_label} (węzeł: {end_id})")
            print(f"  Punkty: {len(self.shortest_path)}")
            if floor_transitions_on_route:
                print(f"  Zmiany pięter: {len(floor_transitions_on_route)}")
                for trans in floor_transitions_on_route:
                    print(f"    • {trans}")
            
            self.draw_route()
            return True
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wczytać trasy:\n{e}")
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def draw_map(self):
        """Rysuje mapę wszystkich ścieżek"""
        if not self.all_paths:
            return
        
        # Rysuj wszystkie połączenia jako szare linie
        for connection in self.all_connections:
            # Znajdź współrzędne punktów
            from_id = str(connection['from'])
            to_id = str(connection['to'])
            
            from_coords = self.find_point_coords(from_id)
            to_coords = self.find_point_coords(to_id)
            
            if from_coords and to_coords:
                self.canvas.create_line(
                    from_coords[0], from_coords[1],
                    to_coords[0], to_coords[1],
                    fill='lightgray', width=2, tags='map'
                )
    
    def find_point_coords(self, point_id: str) -> Optional[Tuple[float, float]]:
        """Znajduje współrzędne punktu po ID"""
        for path in self.all_paths:
            for point in path['points']:
                if str(point['id']) == point_id:
                    return (point['x'], point['y'])
        return None
    
    def draw_route(self):
        """Rysuje trasę do przejścia (tylko punkty z aktualnego piętra)"""
        if not self.nodes_coords:
            return
        
        # Usuń poprzednią trasę
        self.canvas.delete('route')
        self.canvas.delete('markers')
        self.canvas.delete('floor_transition_marker')
        
        # Filtruj punkty do aktualnego piętra
        route_on_floor = []
        for node in self.shortest_path:
            if '_' in node:
                node_floor = node.split('_')[0]
                if node_floor == self.route_floor:
                    route_on_floor.append(node)
            else:
                # Stary format bez prefiksu piętra
                route_on_floor.append(node)
        
        # Rysuj trasę jako czerwoną linię (tylko w obrębie piętra)
        for i in range(len(self.shortest_path) - 1):
            node_from = self.shortest_path[i]
            node_to = self.shortest_path[i + 1]
            
            # Sprawdź czy oba punkty są na tym samym piętrze
            if '_' in node_from and '_' in node_to:
                floor_from = node_from.split('_')[0]
                floor_to = node_to.split('_')[0]
                
                # Rysuj tylko jeśli oba na aktualnym piętrze
                if floor_from == self.route_floor and floor_to == self.route_floor:
                    if node_from in self.nodes_coords and node_to in self.nodes_coords:
                        from_coords = self.nodes_coords[node_from]
                        to_coords = self.nodes_coords[node_to]
                        
                        self.canvas.create_line(
                            from_coords['x'], from_coords['y'],
                            to_coords['x'], to_coords['y'],
                            fill='red', width=5, tags='route'
                        )
            else:
                # Stary format
                if node_from in self.nodes_coords and node_to in self.nodes_coords:
                    from_coords = self.nodes_coords[node_from]
                    to_coords = self.nodes_coords[node_to]
                    
                    self.canvas.create_line(
                        from_coords['x'], from_coords['y'],
                        to_coords['x'], to_coords['y'],
                        fill='red', width=5, tags='route'
                    )
        
        # Zaznacz punkty (tylko z aktualnego piętra)
        for i, node in enumerate(self.shortest_path):
            # Sprawdź czy punkt jest na aktualnym piętrze
            if '_' in node:
                node_floor = node.split('_')[0]
                if node_floor != self.route_floor:
                    continue
                node_id = node.split('_')[1]
            else:
                node_id = node
            
            if node in self.nodes_coords:
                coords = self.nodes_coords[node]
                x, y = coords['x'], coords['y']
                
                # Pobierz etykietę jeśli istnieje
                label = self.point_labels.get(node_id, f"#{node_id}")
                
                # Sprawdź czy to punkt przejścia między piętrami
                is_transition = self.is_floor_transition_point(node, i)
                
                if i == 0:  # Start
                    self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                          fill='green', outline='darkgreen',
                                          width=2, tags='markers')
                    self.canvas.create_text(x, y-20, text=f'START\n{label}',
                                          fill='green', font=('Arial', 9, 'bold'),
                                          tags='markers')
                elif i == len(self.shortest_path) - 1:  # Cel
                    self.canvas.create_oval(x-10, y-10, x+10, y+10,
                                          fill='red', outline='darkred',
                                          width=2, tags='markers')
                    self.canvas.create_text(x, y-20, text=f'CEL\n{label}',
                                          fill='red', font=('Arial', 9, 'bold'),
                                          tags='markers')
                elif is_transition:  # Punkt przejścia między piętrami
                    self.canvas.create_rectangle(x-12, y-12, x+12, y+12,
                                                fill='purple', outline='darkviolet',
                                                width=3, tags='floor_transition_marker')
                    trans_icon = "🪜" if is_transition == "stairs" else "🛗"
                    self.canvas.create_text(x, y-18, text=f'{trans_icon}\n{label}',
                                          fill='purple', font=('Arial', 9, 'bold'),
                                          tags='floor_transition_marker')
                else:  # Punkt pośredni
                    self.canvas.create_oval(x-6, y-6, x+6, y+6,
                                          fill='orange', outline='darkorange',
                                          width=2, tags='markers')
                    # Pokazuj etykietę dla punktów pośrednich jeśli istnieje
                    if node_id in self.point_labels:
                        self.canvas.create_text(x, y-12, text=label,
                                              fill='orange', font=('Arial', 7),
                                              tags='markers')
    
    def is_floor_transition_point(self, node, node_index):
        """Sprawdza czy punkt jest przejściem między piętrami"""
        if node_index >= len(self.shortest_path) - 1:
            return False
        
        current_node = self.shortest_path[node_index]
        next_node = self.shortest_path[node_index + 1]
        
        if '_' in current_node and '_' in next_node:
            current_floor = current_node.split('_')[0]
            next_floor = next_node.split('_')[0]
            
            if current_floor != next_floor:
                # Znajdź typ przejścia
                for segment in self.path_segments:
                    if (segment.get('from') == current_node and 
                        segment.get('to') == next_node and
                        segment.get('is_floor_transition', False)):
                        return segment.get('transition_type', 'stairs')
                return 'stairs'  # Domyślnie schody
        
        return False
    
    def start_navigation(self):
        """Rozpoczyna nawigację"""
        if not self.shortest_path or not self.nodes_coords:
            messagebox.showwarning("Brak danych", 
                                  "Najpierw wczytaj mapę i trasę!")
            return
        
        # Reset stanu
        self.current_path_index = 0
        self.drawn_path = []
        self.user_position = None
        self.canvas.delete('user_path')
        self.canvas.delete('user_marker')
        self.deviated_from_route = False
        self.visited_nodes = []
        
        # Podłącz eventy myszy
        self.canvas.bind('<ButtonPress-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.draw_user_path)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        
        # Przygotuj nazwę początkowego punktu
        first_point = self.shortest_path[0]
        first_label = self.point_labels.get(first_point, f"punkt {first_point}")
        
        self.nav_label['text'] = "🚶 Rysuj swoją pozycję myszką (przeciągnij)"
        self.distance_label['text'] = f"Idź do: {first_label}"
        
        messagebox.showinfo("Nawigacja rozpoczęta", 
                          "Rysuj swoją ścieżkę myszką!\n\n"
                          "System będzie śledzić Twoją pozycję i dawać wskazówki.")
    
    def start_free_exploration(self):
        """Rozpoczyna wolną eksplorację bez nawigacji"""
        if not self.all_paths:
            messagebox.showwarning("Brak mapy", 
                                  "Najpierw wczytaj mapę!")
            return
        
        # Aktywuj tryb wolnej eksploracji
        self.free_exploration_mode = True
        
        # Reset stanu
        self.current_path_index = 0
        self.drawn_path = []
        self.user_position = None
        self.canvas.delete('user_path')
        self.canvas.delete('user_marker')
        self.deviated_from_route = False
        self.visited_nodes = []
        self.shortest_path = []  # Brak trasy do podążania
        
        # Podłącz eventy myszy
        self.canvas.bind('<ButtonPress-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.draw_user_path)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        
        # Zmień kolor tła nawigacji
        self.nav_frame['bg'] = '#9C27B0'
        self.nav_label['bg'] = '#9C27B0'
        self.distance_label['bg'] = '#9C27B0'
        
        self.nav_label['text'] = "🗺️ WOLNA EKSPLORACJA - Odkrywaj nowe trasy!"
        self.distance_label['text'] = "Rysuj swoją ścieżkę myszką - tworzysz nową trasę"
        
        messagebox.showinfo("Wolna eksploracja", 
                          "🗺️ Tryb wolnej eksploracji aktywowany!\n\n"
                          "Rysuj swoją ścieżkę myszką bez wskazówek nawigacyjnych.\n"
                          "Twoja trasa zostanie dodana do mapy.\n\n"
                          "To świetny sposób na odkrywanie nowych połączeń!")
    
    def start_drawing(self, event):
        """Rozpoczyna rysowanie ścieżki użytkownika"""
        self.is_drawing = True
        self.user_position = (event.x, event.y)
        self.drawn_path = [(event.x, event.y)]
        self.current_user_path = [(event.x, event.y)]
    
    def draw_user_path(self, event):
        """Rysuje ścieżkę użytkownika"""
        if not self.is_drawing:
            return
        
        # Dodaj punkt do ścieżki
        x, y = event.x, event.y
        
        if self.drawn_path:
            prev_x, prev_y = self.drawn_path[-1]
            
            # Rysuj linię
            self.canvas.create_line(prev_x, prev_y, x, y,
                                  fill='blue', width=4, tags='user_path')
        
        self.drawn_path.append((x, y))
        self.current_user_path.append((x, y))
        self.user_position = (x, y)
        
        # Aktualizuj kierunek ruchu użytkownika
        self.last_positions.append((x, y))
        if len(self.last_positions) > 10:  # Zachowaj ostatnie 10 pozycji
            self.last_positions.pop(0)
        
        # Oblicz kierunek z ostatnich pozycji
        if len(self.last_positions) >= 5:
            # Weź pierwszą i ostatnią pozycję z ostatnich 5
            old_pos = self.last_positions[-5]
            new_pos = self.last_positions[-1]
            
            dx = new_pos[0] - old_pos[0]
            dy = new_pos[1] - old_pos[1]
            
            # Oblicz kąt ruchu użytkownika (w radianach)
            if abs(dx) > 1 or abs(dy) > 1:  # Tylko jeśli jest ruch
                self.user_direction = math.atan2(dy, dx)
        
        # Sprawdź nawigację
        self.check_navigation()
    
    def stop_drawing(self, event):
        """Kończy rysowanie ścieżki użytkownika"""
        self.is_drawing = False
        
        # Zaznacz aktualną pozycję
        self.canvas.delete('user_marker')
        if self.user_position:
            x, y = self.user_position
            self.canvas.create_oval(x-8, y-8, x+8, y+8,
                                  fill='blue', outline='darkblue',
                                  width=2, tags='user_marker')
        
        # W trybie wolnej eksploracji - zakończ i zapisz trasę
        if self.free_exploration_mode and len(self.current_user_path) > 5:
            result = messagebox.askyesno("Zakończ eksplorację",
                                        f"Utworzono trasę z {len(self.current_user_path)} punktów.\n\n"
                                        f"Czy chcesz zapisać tę trasę do mapy?")
            if result:
                self.update_map_with_user_path()
                messagebox.showinfo("Zapisano!", 
                                  "Twoja nowa trasa została dodana do mapy! 🗺️\n\n"
                                  "Możesz teraz rozpocząć kolejną eksplorację.")
            
            # Reset trybu
            self.free_exploration_mode = False
            self.nav_frame['bg'] = '#1976D2'
            self.nav_label['bg'] = '#1976D2'
            self.distance_label['bg'] = '#1976D2'
            self.nav_label['text'] = "Eksploracja zakończona"
            self.distance_label['text'] = ""
    
    def check_navigation(self):
        """Sprawdza postęp nawigacji i daje wskazówki"""
        if not self.user_position:
            return
        
        # W trybie wolnej eksploracji - tylko pokazuj informacje o eksploracji
        if self.free_exploration_mode:
            path_length = len(self.current_user_path)
            self.distance_label['text'] = f"🗺️ Utworzono {path_length} punktów trasy"
            return
        
        # PRIORYTET 1: Sprawdź czy użytkownik dotarł do KOŃCOWEGO celu (ostatni punkt)
        final_target = self.shortest_path[-1] if self.shortest_path else None
        
        if final_target and final_target in self.nodes_coords:
            final_coords = self.nodes_coords[final_target]
            final_x, final_y = final_coords['x'], final_coords['y']
            user_x, user_y = self.user_position
            
            final_distance = math.sqrt((final_x - user_x)**2 + (final_y - user_y)**2)
            
            # Jeśli użytkownik dotarł do końcowego celu (nawet inną trasą)
            if final_distance <= self.proximity_threshold:
                # Oznacz jako odwiedzony
                if final_target not in self.visited_nodes:
                    self.visited_nodes.append(final_target)
                
                # KONIEC NAWIGACJI
                self.current_path_index = len(self.shortest_path)  # Ustaw na koniec
                
                self.nav_label['text'] = "🎉 GRATULACJE! Dotarłeś do celu!"
                self.distance_label['text'] = ""
                
                # Sprawdź czy użytkownik poszedł sugerowaną trasą
                self.check_route_compliance()
                return
        
        # PRIORYTET 1.5: Sprawdź czy zbliża się przejście między piętrami
        if self.current_path_index < len(self.shortest_path) - 1:
            current_node = self.shortest_path[self.current_path_index]
            next_node = self.shortest_path[self.current_path_index + 1]
            
            # Sprawdź czy następny krok to zmiana piętra
            if '_' in current_node and '_' in next_node:
                current_floor = current_node.split('_')[0]
                next_floor = next_node.split('_')[0]
                
                if current_floor != next_floor:
                    # To jest przejście między piętrami!
                    if current_node in self.nodes_coords:
                        trans_coords = self.nodes_coords[current_node]
                        trans_x, trans_y = trans_coords['x'], trans_coords['y']
                        user_x, user_y = self.user_position
                        
                        trans_distance = math.sqrt((trans_x - user_x)**2 + (trans_y - user_y)**2)
                        
                        # Jeśli blisko przejścia
                        if trans_distance <= self.proximity_threshold * 1.5:  # Większy próg dla alertu
                            trans_type = self.get_transition_type(current_node, next_node)
                            trans_icon = "🪜" if trans_type == "stairs" else "🛗"
                            floor_from_name = self.building_info.get('floor_names', {}).get(current_floor, f"Piętro {current_floor}")
                            floor_to_name = self.building_info.get('floor_names', {}).get(next_floor, f"Piętro {next_floor}")
                            
                            self.nav_label['text'] = f"⚠️ {trans_icon} Zmiana piętra! {floor_from_name} → {floor_to_name}"
                            self.distance_label['text'] = f"Przejdź przez {trans_type} ({trans_distance:.1f} px)"
                            
                            # Po dotarciu do punktu przejścia - zaproponuj zmianę piętra
                            if trans_distance <= self.proximity_threshold:
                                if not self.floor_transition_alert_shown:
                                    self.floor_transition_alert_shown = True
                                    
                                    # WAŻNE: Oznacz punkt przejścia jako odwiedzony PRZED zmianą piętra
                                    if current_node not in self.visited_nodes:
                                        self.visited_nodes.append(current_node)
                                        print(f"✓ Punkt przejścia odwiedzony: {current_node}")
                                    
                                    result = messagebox.askyesno(
                                        "Zmiana piętra",
                                        f"Dotarłeś do przejścia między piętrami!\n\n"
                                        f"{trans_icon} Typ: {trans_type}\n"
                                        f"Z: {floor_from_name}\n"
                                        f"Do: {floor_to_name}\n\n"
                                        f"Czy chcesz przełączyć widok na {floor_to_name}?"
                                    )
                                    
                                    if result:
                                        # Przejdź do następnego punktu (na nowym piętrze)
                                        self.current_path_index += 1
                                        
                                        # Zmień piętro
                                        self.current_floor = next_floor
                                        self.route_floor = next_floor
                                        
                                        # Zaktualizuj combobox
                                        floor_list = list(self.floors.keys())
                                        if next_floor in floor_list:
                                            idx = floor_list.index(next_floor)
                                            floor_names = self.floor_combo['values']
                                            if idx < len(floor_names):
                                                self.floor_combo.set(floor_names[idx])
                                        
                                        # Wczytaj dane nowego piętra
                                        self.load_floor_data(next_floor)
                                        
                                        # Wyczyść pozycję użytkownika na nowym piętrze
                                        self.user_position = None
                                        self.canvas.delete('user_marker')
                                        self.canvas.delete('user_path')
                                        
                                        # Przerysuj mapę
                                        self.canvas.delete('all')
                                        self.draw_map()
                                        self.draw_route()
                                        
                                        # Reset alertu
                                        self.floor_transition_alert_shown = False
                                        
                                        messagebox.showinfo("Piętro zmienione", 
                                                          f"Jesteś teraz na: {floor_to_name}\n\n"
                                                          f"Zacznij rysować swoją pozycję na nowym piętrze\n"
                                                          f"aby kontynuować nawigację do celu!")
                                        return
                            return
        
        # PRIORYTET 2: Sprawdź postęp na sugerowanej trasie (punkty pośrednie)
        if self.current_path_index >= len(self.shortest_path):
            return
        
        # Pobierz aktualny cel na sugerowanej trasie
        current_target = self.shortest_path[self.current_path_index]
        
        if current_target not in self.nodes_coords:
            return
        
        target_coords = self.nodes_coords[current_target]
        target_x, target_y = target_coords['x'], target_coords['y']
        user_x, user_y = self.user_position
        
        # Oblicz odległość do bieżącego punktu pośredniego
        distance = math.sqrt((target_x - user_x)**2 + (target_y - user_y)**2)
        
        # Sprawdź czy użytkownik dotarł do punktu pośredniego
        if distance <= self.proximity_threshold:
            self.current_path_index += 1
            
            # Zapisz odwiedzony węzeł
            if current_target not in self.visited_nodes:
                self.visited_nodes.append(current_target)
            
            # Usuń osiągnięty punkt
            self.canvas.delete('markers')
            self.draw_route()
            
            # Sprawdź czy to był ostatni punkt
            if self.current_path_index >= len(self.shortest_path):
                self.nav_label['text'] = "🎉 GRATULACJE! Dotarłeś do celu!"
                self.distance_label['text'] = ""
                self.check_route_compliance()
                return
            else:
                # Następny punkt pośredni
                next_target = self.shortest_path[self.current_path_index]
                next_label = self.point_labels.get(next_target, f"punkt {next_target}")
                self.nav_label['text'] = f"✓ Dobra robota! Teraz idź do: {next_label}"
                return
        
        # PRIORYTET 3: Nawigacja - wskazówki jak dojść do punktu
        # Sprawdź czy użytkownik nie zboczył z trasy
        deviation_status = self.check_route_deviation()
        
        # Jeśli użytkownik przeciera nowe szlaki, nie dawaj wskazówek nawigacyjnych
        if deviation_status == "exploring":
            target_label = self.point_labels.get(final_target if final_target else current_target, 
                                                 f"punkt {final_target if final_target else current_target}")
            self.nav_label['text'] = f"🗺️ Przecierasz nowe szlaki! (Cel: {target_label})"
            return
        
        # Wskazówki kierunkowe względem kierunku ruchu użytkownika
        dx = target_x - user_x
        dy = target_y - user_y
        
        # Określ kierunek (względny lub absolutny)
        if self.user_direction is not None:
            direction = self.get_relative_direction(dx, dy)
        else:
            # Jeśli nie znamy kierunku użytkownika, użyj kierunków absolutnych
            direction = self.get_absolute_direction(dx, dy)
        
        # Przygotuj nazwę celu
        target_label = self.point_labels.get(current_target, f"punkt {current_target}")
        
        self.nav_label['text'] = f"🧭 {direction} do: {target_label}"
        self.distance_label['text'] = f"Odległość: {distance:.1f} px (próg: {self.proximity_threshold} px)"
    
    def check_route_deviation(self):
        """Sprawdza czy użytkownik zboczył z sugerowanej trasy
        
        Returns:
            str: "exploring" jeśli przeciera nowe szlaki, "deviated" jeśli zboczył, None jeśli na trasie
        """
        if not self.user_position or self.deviated_from_route:
            return None
        
        # Sprawdź odległość od najbliższego punktu na sugerowanej trasie
        min_distance = float('inf')
        
        for node in self.shortest_path:
            if node not in self.nodes_coords:
                continue
            
            coords = self.nodes_coords[node]
            nx, ny = coords['x'], coords['y']
            ux, uy = self.user_position
            
            dist = math.sqrt((nx - ux)**2 + (ny - uy)**2)
            if dist < min_distance:
                min_distance = dist
        
        # Jeśli użytkownik jest daleko od trasy
        if min_distance > self.route_deviation_threshold:
            self.deviated_from_route = True
            
            # Jeśli BARDZO daleko (2x próg), to przeciera nowe szlaki
            exploration_threshold = self.route_deviation_threshold * 2
            if min_distance > exploration_threshold:
                self.distance_label['text'] = "🗺️ PRZECIERASZ NOWE SZLAKI!"
                return "exploring"
            else:
                self.distance_label['text'] += " ⚠️ ODSTĘPSTWO OD TRASY"
                return "deviated"
        
        return None
    
    def check_route_compliance(self):
        """Sprawdza czy użytkownik przeszedł sugerowaną trasą i pyta o powód jeśli nie"""
        # Sprawdź czy użytkownik odwiedził wszystkie punkty z sugerowanej trasy (w kolejności)
        expected_nodes = self.shortest_path
        visited_nodes = self.visited_nodes
        
        # Sprawdź czy użytkownik odwiedził wszystkie punkty pośrednie
        all_nodes_visited = all(node in visited_nodes for node in expected_nodes)
        
        # Znajdź brakujące punkty
        missing_nodes = [node for node in expected_nodes if node not in visited_nodes]
        
        # Sprawdź czy użytkownik odwiedził je w tej samej kolejności
        in_correct_order = True
        last_expected_index = -1
        
        for expected_node in expected_nodes:
            try:
                visited_index = visited_nodes.index(expected_node)
                if visited_index < last_expected_index:
                    in_correct_order = False
                    break
                last_expected_index = visited_index
            except ValueError:
                # Węzeł nie został odwiedzony
                in_correct_order = False
                break
        
        # Jeśli użytkownik zboczył, nie odwiedził wszystkich punktów, lub nie w kolejności
        if self.deviated_from_route or not all_nodes_visited or not in_correct_order:
            # Pokaż dialog z pytaniem o powód
            print(f"  Wykryto odstępstwo:")
            print(f"    Zboczył z trasy: {self.deviated_from_route}")
            print(f"    Wszystkie punkty odwiedzone: {all_nodes_visited}")
            print(f"    Poprawna kolejność: {in_correct_order}")
            print(f"    Brakujące punkty: {missing_nodes}")
            print(f"    Oczekiwane: {expected_nodes}")
            print(f"    Odwiedzone: {visited_nodes}")
            
            # Sprawdź czy brakujący punkt to tylko punkt przejścia na poprzednim piętrze
            if len(missing_nodes) == 1 and '_' in missing_nodes[0]:
                missing_node = missing_nodes[0]
                # Sprawdź czy to punkt przejścia
                is_transition = False
                for i, node in enumerate(expected_nodes):
                    if node == missing_node and i < len(expected_nodes) - 1:
                        next_node = expected_nodes[i + 1]
                        if '_' in next_node:
                            missing_floor = missing_node.split('_')[0]
                            next_floor = next_node.split('_')[0]
                            if missing_floor != next_floor:
                                is_transition = True
                                print(f"    ℹ️ Brakujący punkt {missing_node} to punkt przejścia między piętrami")
                                # Automatycznie dodaj ten punkt jako odwiedzony
                                self.visited_nodes.append(missing_node)
                                print(f"    ✓ Automatycznie oznaczono {missing_node} jako odwiedzony")
                                
                                # Sprawdź ponownie
                                all_nodes_visited = all(node in self.visited_nodes for node in expected_nodes)
                                if all_nodes_visited:
                                    print(f"  ✓ Po korekcie: wszystkie punkty odwiedzone")
                                    # Nie pokazuj dialogu odstępstwa
                                    if self.auto_update_var.get():
                                        self.update_map_with_user_path()
                                    messagebox.showinfo("Sukces!", 
                                                      "🎉 Gratulacje!\n\nDotarłeś do celu!\n\n"
                                                      "Twoja trasa została dodana do mapy.")
                                    return
            
            self.ask_deviation_reason()
        else:
            # Użytkownik przeszedł dokładnie sugerowaną trasą
            print(f"  ✓ Użytkownik przeszedł zgodnie z trasą")
            
            # Aktualizuj mapę
            if self.auto_update_var.get():
                self.update_map_with_user_path()
            
            messagebox.showinfo("Sukces!", 
                              "🎉 Gratulacje!\n\nDotarłeś do celu zgodnie z trasą!\n\n"
                              "Twoja trasa została dodana do mapy.")
    
    def ask_deviation_reason(self):
        """Pyta użytkownika o powód odstępstwa od trasy"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self.root)
        dialog.title("Odstępstwo od sugerowanej trasy")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centruj okno
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Nagłówek
        header_frame = tk.Frame(dialog, bg='#FF9800', pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, 
                text="⚠️ Zauważyliśmy odstępstwo od trasy",
                bg='#FF9800', fg='white',
                font=('Arial', 14, 'bold')).pack()
        
        tk.Label(header_frame,
                text="Pomóż nam ulepszyć nawigację",
                bg='#FF9800', fg='white',
                font=('Arial', 10)).pack()
        
        # Treść
        content_frame = tk.Frame(dialog, bg='white', pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content_frame,
                text="Dotarłeś do celu, ale nie podążałeś sugerowaną trasą.\n"
                     "Dlaczego wybrałeś inną drogę?",
                bg='white',
                font=('Arial', 11),
                wraplength=450,
                justify=tk.LEFT).pack(pady=10, padx=20)
        
        # Pokaż trasę sugerowaną i rzeczywistą z etykietami
        expected_route = " → ".join([self.point_labels.get(n, f"#{n}") for n in self.shortest_path[:5]])
        if len(self.shortest_path) > 5:
            expected_route += " → ..."
        
        tk.Label(content_frame,
                text=f"Sugerowana: {expected_route}",
                bg='#FFF3E0',
                font=('Arial', 9, 'italic'),
                fg='#E65100',
                wraplength=450,
                justify=tk.LEFT,
                padx=10, pady=5).pack(pady=(0, 10), padx=20, fill=tk.X)
        
        # Zmienna do przechowania wyboru
        reason_var = tk.StringVar(value="")
        
        # Opcje do wyboru
        reasons = [
            ("🚶 Zatłoczony korytarz - zbyt wielu ludzi na sugerowanej trasie", "crowded"),
            ("⚡ Znalazłem krótszą drogę niż sugerowana", "shorter"),
            ("🚧 Sugerowana droga była zablokowana lub niedostępna", "blocked"),
            ("❌ Sugerowana droga nie istnieje lub jest nieprawidłowa", "nonexistent"),
            ("🔀 Znam lepszą trasę (inna przyczyna)", "other"),
            ("🎯 Lubię zwiedzać - po prostu eksploracja", "exploring")
        ]
        
        for text, value in reasons:
            rb = tk.Radiobutton(content_frame,
                              text=text,
                              variable=reason_var,
                              value=value,
                              bg='white',
                              font=('Arial', 10),
                              wraplength=430,
                              justify=tk.LEFT,
                              activebackground='#e3f2fd',
                              pady=5)
            rb.pack(anchor=tk.W, padx=30, pady=3)
        
        # Pole tekstowe dla dodatkowych uwag
        tk.Label(content_frame,
                text="Dodatkowe uwagi (opcjonalnie):",
                bg='white',
                font=('Arial', 9, 'italic')).pack(anchor=tk.W, padx=30, pady=(10, 2))
        
        notes_text = tk.Text(content_frame, height=3, width=50, font=('Arial', 9))
        notes_text.pack(padx=30, pady=5)
        
        # Przyciski
        button_frame = tk.Frame(dialog, bg='#f5f5f5', pady=10)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        def submit_feedback():
            reason = reason_var.get()
            notes = notes_text.get("1.0", tk.END).strip()
            
            if not reason:
                messagebox.showwarning("Brak wyboru", 
                                      "Proszę wybrać powód odstępstwa od trasy.",
                                      parent=dialog)
                return
            
            # Jeśli to tylko eksploracja, nie zapisuj feedbacku
            if reason == "exploring":
                dialog.destroy()
                
                # Aktualizuj mapę jeśli włączone
                if self.auto_update_var.get():
                    self.update_map_with_user_path()
                
                messagebox.showinfo("Dziękujemy!", 
                                  "🎉 Gratulacje! Dotarłeś do celu!\n\n"
                                  "Miłego zwiedzania! 🗺️\n\n"
                                  "Twoja trasa została dodana do mapy.")
                return
            
            # Zapisz feedback (dla innych powodów)
            self.save_route_feedback(reason, notes)
            
            # Zamknij dialog
            dialog.destroy()
            
            # Aktualizuj mapę jeśli włączone
            if self.auto_update_var.get():
                self.update_map_with_user_path()
            
            messagebox.showinfo("Dziękujemy!", 
                              "🎉 Gratulacje! Dotarłeś do celu!\n\n"
                              "Dziękujemy za feedback - pomoże nam ulepszyć nawigację.\n\n"
                              "Twoja trasa została dodana do mapy.")
        
        def skip_feedback():
            dialog.destroy()
            
            # Aktualizuj mapę jeśli włączone
            if self.auto_update_var.get():
                self.update_map_with_user_path()
            
            messagebox.showinfo("Sukces!", 
                              "🎉 Gratulacje!\n\nDotarłeś do celu!\n\n"
                              "Twoja trasa została dodana do mapy.")
        
        tk.Button(button_frame, text="✓ Wyślij feedback", 
                 command=submit_feedback,
                 bg='#4CAF50', fg='white',
                 font=('Arial', 10, 'bold'),
                 padx=20, pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Pomiń", 
                 command=skip_feedback,
                 bg='#9E9E9E', fg='white',
                 font=('Arial', 10),
                 padx=20, pady=8).pack(side=tk.LEFT, padx=10)
    
    def save_route_feedback(self, reason: str, notes: str):
        """Zapisuje feedback użytkownika o trasie"""
        feedback_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "suggested_route": self.shortest_path,
            "visited_nodes": self.visited_nodes,
            "deviated": self.deviated_from_route,
            "reason": reason,
            "notes": notes,
            "path_length": len(self.current_user_path)
        }
        
        # Zapisz do pliku JSON
        import os
        feedback_file = "route_feedback.json"
        
        try:
            # Wczytaj istniejące feedbacki
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    all_feedback = json.load(f)
            else:
                all_feedback = []
            
            # Dodaj nowy feedback
            all_feedback.append(feedback_data)
            
            # Zapisz
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(all_feedback, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Feedback zapisany do {feedback_file}")
            print(f"  Powód: {reason}")
            if notes:
                print(f"  Uwagi: {notes}")
            
        except Exception as e:
            print(f"✗ Błąd zapisu feedbacku: {e}")
    
    def get_relative_direction(self, dx: float, dy: float) -> str:
        """Określa kierunek względem aktualnego kierunku ruchu użytkownika"""
        # Kąt do celu (absolutny)
        target_angle = math.atan2(dy, dx)
        
        # Różnica między kierunkiem ruchu a kierunkiem do celu
        angle_diff = target_angle - self.user_direction
        
        # Normalizuj do zakresu -π do π
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # Konwertuj na stopnie dla łatwiejszej analizy
        angle_diff_deg = math.degrees(angle_diff)
        
        # Określ kierunek względny
        if -22.5 <= angle_diff_deg <= 22.5:
            return "Idź prosto do przodu ⬆️"
        elif 22.5 < angle_diff_deg <= 67.5:
            return "Skręć lekko w prawo ↗️"
        elif 67.5 < angle_diff_deg <= 112.5:
            return "Skręć w prawo ➡️"
        elif 112.5 < angle_diff_deg <= 157.5:
            return "Zawróć w prawo ↪️"
        elif angle_diff_deg > 157.5 or angle_diff_deg < -157.5:
            return "Zawróć / idź w przeciwnym kierunku 🔄"
        elif -157.5 <= angle_diff_deg < -112.5:
            return "Zawróć w lewo ↩️"
        elif -112.5 <= angle_diff_deg < -67.5:
            return "Skręć w lewo ⬅️"
        elif -67.5 <= angle_diff_deg < -22.5:
            return "Skręć lekko w lewo ↖️"
        else:
            return "Idź do przodu ⬆️"
    
    def get_absolute_direction(self, dx: float, dy: float) -> str:
        """Określa kierunek geograficzny (gdy nie znamy kierunku użytkownika)"""
        angle = math.atan2(dy, dx) * 180 / math.pi
        
        # Normalizuj kąt (0-360)
        if angle < 0:
            angle += 360
        
        # Określ kierunek
        if 22.5 <= angle < 67.5:
            return "Idź na POŁUDNIOWY-WSCHÓD ↘️"
        elif 67.5 <= angle < 112.5:
            return "Idź na POŁUDNIE ⬇️"
        elif 112.5 <= angle < 157.5:
            return "Idź na POŁUDNIOWY-ZACHÓD ↙️"
        elif 157.5 <= angle < 202.5:
            return "Idź na ZACHÓD ⬅️"
        elif 202.5 <= angle < 247.5:
            return "Idź na PÓŁNOCNY-ZACHÓD ↖️"
        elif 247.5 <= angle < 292.5:
            return "Idź na PÓŁNOC ⬆️"
        elif 292.5 <= angle < 337.5:
            return "Idź na PÓŁNOCNY-WSCHÓD ↗️"
        else:
            return "Idź na WSCHÓD ➡️"
    
    def get_direction(self, dx: float, dy: float) -> str:
        """Stara funkcja - pozostawiona dla kompatybilności"""
        return self.get_absolute_direction(dx, dy)
    
    def merge_user_path_with_existing(self, user_points_coords, existing_points):
        """Łączy punkty użytkownika z istniejącymi punktami (jak 'Połącz korytarze')"""
        merge_threshold = 40  # Ten sam próg co w mapmaker
        
        merged_points = []
        merged_to_existing = {}  # Mapowanie: index punktu użytkownika -> istniejący punkt
        
        # Dla każdego punktu użytkownika sprawdź czy jest blisko istniejącego
        for i, (ux, uy) in enumerate(user_points_coords):
            closest_existing = None
            min_dist = float('inf')
            
            # Znajdź najbliższy istniejący punkt
            for existing in existing_points:
                if existing['x'] == 0 and existing['y'] == 0:
                    continue
                    
                dist = math.sqrt((existing['x'] - ux)**2 + (existing['y'] - uy)**2)
                
                if dist <= merge_threshold and dist < min_dist:
                    min_dist = dist
                    closest_existing = existing
            
            if closest_existing:
                # Użyj istniejącego punktu
                merged_to_existing[i] = closest_existing['id']
                merged_points.append((closest_existing['x'], closest_existing['y']))
            else:
                # Zachowaj oryginalny punkt użytkownika
                merged_points.append((ux, uy))
        
        return merged_points, merged_to_existing
    
    def simplify_user_path_points(self, points_coords):
        """Upraszcza punkty ścieżki użytkownika grupując bliskie punkty"""
        if len(points_coords) <= 2:
            return points_coords
        
        merge_threshold = 40
        simplified = []
        used_indices = set()
        
        for i, (x1, y1) in enumerate(points_coords):
            if i in used_indices:
                continue
            
            # Znajdź klaster bliskich punktów
            cluster = [(x1, y1)]
            used_indices.add(i)
            
            for j, (x2, y2) in enumerate(points_coords):
                if j <= i or j in used_indices:
                    continue
                
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if dist <= merge_threshold:
                    cluster.append((x2, y2))
                    used_indices.add(j)
            
            # Średnia pozycja klastra
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            avg_y = sum(p[1] for p in cluster) / len(cluster)
            simplified.append((avg_x, avg_y))
        
        return simplified
    
    def update_map_with_user_path(self):
        """Aktualizuje oryginalną mapę GPS o ścieżkę użytkownika"""
        if not self.map_filename or not self.current_user_path:
            return
        
        try:
            # Wczytaj aktualną mapę
            with open(self.map_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Użyj wartości z suwaka próbkowania
            sampling_rate = self.sampling_var.get()
            
            # Co N-ty punkt z narysowanej ścieżki (kontrolowane suwakiem)
            sampled_indices = range(0, len(self.current_user_path), sampling_rate)
            sampled_path = [self.current_user_path[i] for i in sampled_indices]
            
            # Zawsze dodaj ostatni punkt
            if len(self.current_user_path) > 0 and self.current_user_path[-1] not in sampled_path:
                sampled_path.append(self.current_user_path[-1])
            
            # Filtruj punkty które są za blisko siebie
            filtered_path = []
            min_distance = 30
            
            for point in sampled_path:
                if not filtered_path:
                    filtered_path.append(point)
                else:
                    last_point = filtered_path[-1]
                    dist = math.sqrt((point[0] - last_point[0])**2 + (point[1] - last_point[1])**2)
                    if dist >= min_distance:
                        filtered_path.append(point)
            
            sampled_path = filtered_path
            
            print(f"  Oryginalnych punktów: {len(self.current_user_path)}")
            print(f"  Po próbkowaniu co {sampling_rate}: {len([self.current_user_path[i] for i in sampled_indices])}")
            print(f"  Po filtrowaniu (min {min_distance}px): {len(sampled_path)}")
            
            # NOWA FUNKCJONALNOŚĆ: Połącz korytarze (2 razy)
            # Zbierz wszystkie istniejące punkty
            existing_points = []
            for path in data['paths']:
                for point in path['points']:
                    if point['x'] != 0 or point['y'] != 0:
                        existing_points.append(point)
            
            # 1. Połącz ścieżkę użytkownika z istniejącymi punktami
            print(f"  Łączenie z istniejącymi punktami...")
            merged_with_existing, merged_map = self.merge_user_path_with_existing(sampled_path, existing_points)
            print(f"  Po połączeniu z mapą: {len(merged_with_existing)} punktów, {len(merged_map)} zmapowanych")
            
            # 2. Uprość wewnętrzne punkty ścieżki użytkownika (grupuj bliskie)
            print(f"  Upraszczanie wewnętrznych punktów...")
            final_path = self.simplify_user_path_points(merged_with_existing)
            print(f"  Po uproszczeniu: {len(final_path)} punktów")
            
            # Konwertuj finalne punkty na format JSON
            # Sprawdź które punkty zostały zmapowane na istniejące
            new_path_id = len(data['paths']) + 1
            point_id_start = max([p['id'] for path in data['paths'] for p in path['points']], default=0) + 1
            
            reused_points = {}  # ID istniejącego punktu -> lista indeksów użytkownika
            new_points = []
            
            for i, (x, y) in enumerate(final_path):
                # Sprawdź czy ten punkt jest bardzo blisko istniejącego (ponowna weryfikacja)
                matched_existing = None
                for existing in existing_points:
                    if existing['x'] == 0 and existing['y'] == 0:
                        continue
                    dist = math.sqrt((existing['x'] - x)**2 + (existing['y'] - y)**2)
                    if dist < 5:  # Bardzo blisko = ten sam punkt
                        matched_existing = existing['id']
                        break
                
                if matched_existing:
                    # Reużyj istniejący punkt
                    if matched_existing not in reused_points:
                        reused_points[matched_existing] = []
                    reused_points[matched_existing].append(i)
                else:
                    # Utwórz nowy punkt
                    new_points.append({
                        'id': point_id_start + len(new_points),
                        'x': round(x, 2),
                        'y': round(y, 2)
                    })
            
            # Dodaj nową ścieżkę TYLKO jeśli są nowe punkty do dodania
            if new_points:
                new_path = {
                    'id': new_path_id,
                    'points': new_points,
                    'color': 'blue'  # Ścieżki użytkowników w kolorze niebieskim
                }
                data['paths'].append(new_path)
                
                # Dodaj połączenia między punktami w nowej ścieżce
                for i in range(len(new_points) - 1):
                    point1 = new_points[i]
                    point2 = new_points[i + 1]
                    
                    distance = math.sqrt((point2['x'] - point1['x'])**2 + 
                                       (point2['y'] - point1['y'])**2)
                    
                    data['connections'].append({
                        'from': point1['id'],
                        'to': point2['id'],
                        'distance': round(distance, 2)
                    })
                
                # Połącz nową ścieżkę z istniejącymi punktami (tylko początki/końce)
                self.connect_to_existing_points(data, new_points)
            
            # Zapisz zaktualizowaną mapę
            with open(self.map_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Zaktualizuj lokalną kopię
            self.all_paths = data['paths']
            self.all_connections = data['connections']
            
            added_msg = f"dodano {len(new_points)} nowych punktów"
            reused_msg = f"reużyto {len(reused_points)} istniejących" if reused_points else ""
            
            print(f"✓ Mapa zaktualizowana: {added_msg}")
            if reused_msg:
                print(f"  {reused_msg}")
            
        except Exception as e:
            print(f"✗ Błąd aktualizacji mapy: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showwarning("Błąd aktualizacji", 
                                 f"Nie udało się zaktualizować mapy:\n{e}")
    
    def connect_to_existing_points(self, data, new_points):
        """Łączy nową ścieżkę z istniejącymi punktami - gwarantuje połączenia"""
        # Zbierz wszystkie istniejące punkty (oprócz nowo dodanych)
        existing_points = []
        for path in data['paths'][:-1]:  # Ostatnia ścieżka to właśnie dodana
            for point in path['points']:
                if point['x'] != 0 or point['y'] != 0:
                    existing_points.append(point)
        
        if not new_points or not existing_points:
            return
        
        def find_and_connect(target_point, point_type, initial_threshold=60):
            """Znajduje i łączy punkt z istniejącymi - z fallbackiem na większy promień"""
            connections_made = 0
            thresholds = [initial_threshold, 100, 150, 200]  # Próbuj coraz większe promienie
            
            for threshold in thresholds:
                # Znajdź wszystkie punkty w promieniu threshold
                candidates = []
                for existing in existing_points:
                    dist = math.sqrt((existing['x'] - target_point['x'])**2 + 
                                   (existing['y'] - target_point['y'])**2)
                    if dist <= threshold:
                        candidates.append((existing, dist))
                
                if candidates:
                    # Sortuj po odległości i połącz z 1-3 najbliższymi
                    candidates.sort(key=lambda x: x[1])
                    max_connections = min(3, len(candidates))  # Max 3 połączenia
                    
                    for existing, dist in candidates[:max_connections]:
                        # Sprawdź czy to połączenie już nie istnieje
                        connection_exists = any(
                            (c['from'] == target_point['id'] and c['to'] == existing['id']) or
                            (c['from'] == existing['id'] and c['to'] == target_point['id'])
                            for c in data['connections']
                        )
                        
                        if not connection_exists:
                            data['connections'].append({
                                'from': target_point['id'],
                                'to': existing['id'],
                                'distance': round(dist, 2)
                            })
                            connections_made += 1
                            print(f"  Połączono {point_type} z punktem {existing['id']} (odległość: {dist:.1f}px, próg: {threshold}px)")
                    
                    break  # Znaleziono połączenia, wyjdź z pętli progów
            
            if connections_made == 0:
                print(f"  ⚠ Nie znaleziono połączenia dla {point_type} (sprawdzono do {thresholds[-1]}px)")
            
            return connections_made
        
        # Połącz początek nowej ścieżki
        start_point = new_points[0]
        find_and_connect(start_point, "początku", initial_threshold=60)
        
        # Połącz koniec nowej ścieżki
        end_point = new_points[-1]
        find_and_connect(end_point, "końca", initial_threshold=60)
    
    def clear_user_path(self):
        """Czyści tylko ścieżkę użytkownika"""
        self.canvas.delete('user_path')
        self.canvas.delete('user_marker')
        self.drawn_path = []
        self.current_user_path = []
        self.user_position = None
        self.current_path_index = 0
        self.is_drawing = False
        self.user_direction = None
        self.last_positions = []
        self.deviated_from_route = False
        self.visited_nodes = []
        
        # Reset trybu wolnej eksploracji
        if self.free_exploration_mode:
            self.free_exploration_mode = False
            self.nav_frame['bg'] = '#1976D2'
            self.nav_label['bg'] = '#1976D2'
            self.distance_label['bg'] = '#1976D2'
        
        # Przygotuj nazwę punktu startowego
        first_point = self.shortest_path[0] if self.shortest_path else None
        first_label = self.point_labels.get(first_point, f"punkt {first_point}") if first_point else ""
        
        if self.shortest_path:
            self.nav_label['text'] = "🚶 Rysuj swoją pozycję myszką (przeciągnij)"
            self.distance_label['text'] = f"Idź do: {first_label}" if first_label else ""
        else:
            self.nav_label['text'] = "Wczytaj mapę i trasę aby rozpocząć nawigację"
            self.distance_label['text'] = ""
    
    def get_transition_type(self, from_node, to_node):
        """Zwraca typ przejścia między piętrami (stairs/elevator)"""
        for segment in self.path_segments:
            if (segment.get('from') == from_node and 
                segment.get('to') == to_node and
                segment.get('is_floor_transition', False)):
                trans_type = segment.get('transition_type', 'stairs')
                if trans_type == 'stairs':
                    return 'schody'
                elif trans_type == 'elevator':
                    return 'winda'
                return trans_type
        return 'schody'  # Domyślnie
    
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
    app = GPSNavigator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
