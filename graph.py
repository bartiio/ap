import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import heapq
import json
import os
from typing import Dict, List, Tuple

class GraphPathFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Znajdowanie najkrótszej ścieżki - Multi-Floor GPS Path Finder")
        self.root.geometry("1200x800")
        
        # Multi-floor support
        self.floors = {}  # Dane wszystkich pięter
        self.floor_transitions = []  # Przejścia między piętrami
        self.building_info = {}
        self.current_floor = "0"  # Piętro wyświetlane na wizualizacji
        
        # Legacy - dla pojedynczego piętra
        self.graph = {}
        self.positions = {}
        self.point_coords = {}
        self.shortest_path = None
        self.path_distance = 0
        self.selected_start = None
        self.selected_end = None
        self.selected_start_floor = None
        self.selected_end_floor = None
        
        self.setup_ui()
        
        # Auto-wczytaj plik przy starcie
        self.root.after(100, self.auto_load_file)
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Panel górny - przyciski i kontrolki
        top_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Wybór punktu startowego Z PIĘTREM
        tk.Label(top_frame, text="START:", bg='#f0f0f0',
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(10, 5))
        
        tk.Label(top_frame, text="Piętro:", bg='#f0f0f0',
                font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        self.start_floor_var = tk.StringVar(value="0")
        self.start_floor_combo = ttk.Combobox(top_frame, textvariable=self.start_floor_var,
                                         values=["0", "1", "2"], width=5, state='readonly')
        self.start_floor_combo.pack(side=tk.LEFT, padx=2)
        self.start_floor_combo.bind('<<ComboboxSelected>>', self.on_start_floor_changed)
        
        tk.Label(top_frame, text="Punkt:", bg='#f0f0f0',
                font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(top_frame, textvariable=self.start_var,
                                        width=8, state='readonly')
        self.start_combo.pack(side=tk.LEFT, padx=5)
        self.start_combo.bind('<<ComboboxSelected>>', self.on_start_selected)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Wybór punktu końcowego Z PIĘTREM
        tk.Label(top_frame, text="KONIEC:", bg='#f0f0f0',
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(10, 5))
        
        tk.Label(top_frame, text="Piętro:", bg='#f0f0f0',
                font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        self.end_floor_var = tk.StringVar(value="0")
        self.end_floor_combo = ttk.Combobox(top_frame, textvariable=self.end_floor_var,
                                       values=["0", "1", "2"], width=5, state='readonly')
        self.end_floor_combo.pack(side=tk.LEFT, padx=2)
        self.end_floor_combo.bind('<<ComboboxSelected>>', self.on_end_floor_changed)
        
        tk.Label(top_frame, text="Punkt:", bg='#f0f0f0',
                font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        self.end_var = tk.StringVar()
        self.end_combo = ttk.Combobox(top_frame, textvariable=self.end_var,
                                      width=8, state='readonly')
        self.end_combo.pack(side=tk.LEFT, padx=5)
        self.end_combo.bind('<<ComboboxSelected>>', self.on_end_selected)
        
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Przycisk znajdź ścieżkę
        self.find_btn = tk.Button(top_frame, text="🔍 Znajdź najkrótszą ścieżkę",
                                 command=self.find_shortest_path,
                                 bg='#2196F3', fg='white', font=('Arial', 11, 'bold'),
                                 padx=15, pady=8, state='disabled')
        self.find_btn.pack(side=tk.LEFT, padx=10)
        
        # Przycisk wyczyść
        tk.Button(top_frame, text="🗑️ Wyczyść", command=self.clear_visualization,
                 bg='#f44336', fg='white', font=('Arial', 11, 'bold'),
                 padx=15, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Separator
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Przycisk eksportu
        self.export_btn = tk.Button(top_frame, text="💾 Eksportuj ścieżkę", 
                                    command=self.export_shortest_path,
                                    bg='#FF9800', fg='white', font=('Arial', 11, 'bold'),
                                    padx=15, pady=8, state='disabled')
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Separator
        tk.Frame(top_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Przycisk powrotu
        tk.Button(top_frame, text="⬅️ Menu", 
                 command=self.return_to_menu,
                 bg='#607D8B', fg='white', font=('Arial', 9, 'bold'),
                 padx=10, pady=8).pack(side=tk.LEFT, padx=5)
        
        # Panel informacyjny
        info_frame = tk.Frame(self.root, bg='#e3f2fd', pady=8)
        info_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.info_label = tk.Label(info_frame, 
                                   text="Wczytaj plik JSON z grafem GPS aby rozpocząć",
                                   bg='#e3f2fd', font=('Arial', 10), fg='#1565c0')
        self.info_label.pack()
        
        # Panel wizualizacji
        self.canvas_frame = tk.Frame(self.root, bg='white')
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Placeholder dla matplotlib
        self.figure = None
        self.canvas = None
    
    def load_graph(self):
        """Wczytuje graf z pliku JSON (obsługa multi-floor)"""
        # Sprawdź czy istnieje plik testowy, jeśli nie - użyj standardowego
        if os.path.exists("test_multifloor.json"):
            filename = "test_multifloor.json"
        else:
            filename = "gps_paths.json"
        
        if not os.path.exists(filename):
            messagebox.showerror("Błąd", f"Nie znaleziono pliku {filename}!\nUtwórz mapę w Map Maker.")
            return False
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sprawdź czy to nowy format wielopiętrowy
            if 'floors' in data and 'building_info' in data:
                # Nowy format - multi-floor
                self.floors = data.get('floors', {})
                self.floor_transitions = data.get('floor_transitions', [])
                self.building_info = data.get('building_info', {})
                
                # Zbuduj jeden wielki graf zawierający wszystkie piętra
                self.build_multifloor_graph()
                
                # Zaktualizuj combobox pięter
                floor_list = list(self.floors.keys())
                if hasattr(self, 'start_floor_var'):
                    # Zaktualizuj dostępne wartości w comboboxach
                    self.start_floor_combo['values'] = floor_list
                    self.end_floor_combo['values'] = floor_list
                    
                    # Ustaw pierwsze piętro jako wybrane
                    first_floor = floor_list[0] if floor_list else "0"
                    self.start_floor_var.set(first_floor)
                    self.end_floor_var.set(first_floor)
                    self.selected_start_floor = first_floor
                    self.selected_end_floor = first_floor
                
                # Zaktualizuj listę punktów dla początkowego piętra
                self.update_point_lists()
                
                # Włącz przycisk
                self.find_btn['state'] = 'normal'
                
                total_points = sum(len(self.get_floor_graph(f)) for f in self.floors.keys())
                self.info_label['text'] = (f"✓ Budynek wielopiętrowy: {len(self.floors)} pięter, "
                                          f"{total_points} punktów, "
                                          f"{len(self.floor_transitions)} przejść")
                
                # Wizualizacja pierwszego piętra
                self.current_floor = list(self.floors.keys())[0] if self.floors else "0"
                self.visualize_graph()
                
                messagebox.showinfo("Wczytano",
                                  f"✓ Wczytano budynek wielopiętrowy\n\n"
                                  f"Piętra: {len(self.floors)}\n"
                                  f"Przejścia: {len(self.floor_transitions)}")
                return True
                
            else:
                # Stary format - single floor
                self.graph = {}
                self.positions = {}
                self.point_coords = {}
                self.shortest_path = None
                self.selected_start = None
                self.selected_end = None
                
                # Konwertuj na multi-floor
                self.floors = {
                    "0": {
                        "paths": data.get('paths', []),
                        "connections": data.get('connections', []),
                        "point_labels": data.get('point_labels', {})
                    }
                }
                self.floor_transitions = []
                self.building_info = {"name": "Budynek", "floors": ["0"]}
                
                # Zbuduj graf
                self.build_multifloor_graph()
                self.update_point_lists()
                
                self.find_btn['state'] = 'normal'
                self.info_label['text'] = f"✓ Wczytano mapę (stary format, 1 piętro)"
                self.visualize_graph()
                
                messagebox.showinfo("Wczytano", 
                                  "Wczytano mapę w starym formacie\n"
                                  "Zostanie zapisana jako wielopiętrowa")
                return True
            
        except FileNotFoundError:
            messagebox.showerror("Błąd", f"Nie znaleziono pliku!")
            return False
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas wczytywania:\n{e}")
            return False
            messagebox.showerror("Błąd", f"Błąd podczas wczytywania:\n{e}")
            return False
        
    def on_start_selected(self, event=None):
        """Obsługa wyboru punktu startowego"""
        self.selected_start = self.start_var.get()
        if self.selected_start and self.selected_end:
            self.visualize_graph()
    
    def on_end_selected(self, event=None):
        """Obsługa wyboru punktu końcowego"""
        self.selected_end = self.end_var.get()
        if self.selected_start and self.selected_end:
            self.visualize_graph()
    
    def on_start_floor_changed(self, event=None):
        """Zmiana piętra startowego - aktualizuj listę punktów"""
        floor = self.start_floor_var.get()
        self.selected_start_floor = floor  # Zapisz wybrane piętro
        if floor in self.floors:
            nodes = self.get_floor_nodes(floor)
            self.start_combo['values'] = nodes
            if nodes:
                self.start_var.set(nodes[0])
                self.selected_start = nodes[0]
            else:
                self.start_var.set('')
                self.selected_start = None
    
    def on_end_floor_changed(self, event=None):
        """Zmiana piętra końcowego - aktualizuj listę punktów"""
        floor = self.end_floor_var.get()
        self.selected_end_floor = floor  # Zapisz wybrane piętro
        if floor in self.floors:
            nodes = self.get_floor_nodes(floor)
            self.end_combo['values'] = nodes
            if nodes:
                self.end_var.set(nodes[0])
                self.selected_end = nodes[0]
            else:
                self.end_var.set('')
                self.selected_end = None
    
    def get_floor_nodes(self, floor):
        """Zwraca posortowaną listę węzłów dla danego piętra"""
        if floor not in self.floors:
            return []
        
        floor_data = self.floors[floor]
        nodes = set()
        
        # Zbierz ID punktów z paths
        for path in floor_data.get('paths', []):
            # path może być obiektem z 'points' albo listą
            if isinstance(path, dict) and 'points' in path:
                for point in path['points']:
                    if isinstance(point, dict) and 'id' in point:
                        nodes.add(str(point['id']))
            elif isinstance(path, list):
                # Stara struktura - path to lista punktów [x,y]
                pass
        
        # Jeśli nie znaleziono punktów w paths, zbierz z connections
        if not nodes:
            for conn in floor_data.get('connections', []):
                nodes.add(str(conn['from']))
                nodes.add(str(conn['to']))
        
        return sorted(nodes, key=lambda x: int(x) if x.isdigit() else 0)
    
    def get_floor_graph(self, floor):
        """Buduje graf dla konkretnego piętra"""
        graph = {}
        floor_data = self.floors.get(floor, {})
        
        # Dodaj krawędzie z connections
        for conn in floor_data.get('connections', []):
            node1 = str(conn['from'])
            node2 = str(conn['to'])
            dist = conn['distance']
            
            if node1 not in graph:
                graph[node1] = []
            if node2 not in graph:
                graph[node2] = []
            
            graph[node1].append((node2, dist))
            graph[node2].append((node1, dist))
        
        return graph
    
    def build_multifloor_graph(self):
        """Buduje jeden wielki graf zawierający wszystkie piętra + przejścia"""
        self.graph = {}
        self.positions = {}
        self.point_coords = {}
        
        # Dodaj wszystkie piętra
        for floor_id, floor_data in self.floors.items():
            # Zbierz punkty
            all_points = {}
            for path in floor_data.get('paths', []):
                # Obsługa nowego formatu: path ma 'points'
                if isinstance(path, dict) and 'points' in path:
                    for point in path['points']:
                        if isinstance(point, dict) and 'id' in point:
                            point_id = str(point['id'])
                            x = point.get('x', 0)
                            y = point.get('y', 0)
                            if x != 0 or y != 0:
                                all_points[point_id] = (x, y)
                                # Dodaj prefiks piętra dla unikalności
                                full_id = f"{floor_id}_{point_id}"
                                self.point_coords[full_id] = (x, y)
                # Obsługa starego formatu: path to lista współrzędnych
                elif isinstance(path, list):
                    pass  # Pomiń stary format
            
            # Dodaj połączenia na tym piętrze
            for conn in floor_data.get('connections', []):
                node1 = f"{floor_id}_{conn['from']}"
                node2 = f"{floor_id}_{conn['to']}"
                dist = conn['distance']
                self.add_edge(node1, node2, dist)
            
            # Pozycje dla wizualizacji
            max_y = max(y for x, y in all_points.values()) if all_points else 700
            for point_id, (x, y) in all_points.items():
                full_id = f"{floor_id}_{point_id}"
                self.positions[full_id] = (x, max_y - y)
        
        # Dodaj przejścia między piętrami
        for transition in self.floor_transitions:
            from_floor = transition['from_floor']
            to_floor = transition['to_floor']
            from_point = f"{from_floor}_{transition['from_point']}"
            to_point = f"{to_floor}_{transition['to_point']}"
            travel_time = transition.get('travel_time', 30)
            
            # Dodaj krawędź między piętrami
            self.add_edge(from_point, to_point, travel_time)
    
    def update_point_lists(self):
        """Aktualizuje listy punktów w comboboxach"""
        if not self.floors:
            return
        
        # Ustaw pierwsze piętro jako domyślne
        first_floor = list(self.floors.keys())[0]
        nodes = self.get_floor_nodes(first_floor)
        
        self.start_combo['values'] = nodes
        self.end_combo['values'] = nodes
        
        if nodes:
            self.start_var.set(nodes[0])
            self.end_var.set(nodes[-1] if len(nodes) > 1 else nodes[0])
    
    def add_edge(self, node1: str, node2: str, weight: float):
        """Dodaje krawędź między dwoma węzłami"""
        if node1 not in self.graph:
            self.graph[node1] = []
        if node2 not in self.graph:
            self.graph[node2] = []
        
        self.graph[node1].append((node2, weight))
        self.graph[node2].append((node1, weight))
    
    def find_shortest_path(self):
        """Znajduje najkrótszą ścieżkę między wybranymi punktami (multi-floor)"""
        start = self.start_var.get()
        end = self.end_var.get()
        start_floor = self.selected_start_floor
        end_floor = self.selected_end_floor
        
        if not start or not end:
            messagebox.showwarning("Brak wyboru", 
                                  "Wybierz punkt startowy i końcowy!")
            return
        
        # Konwertuj do prefixed format
        start_node = f"{start_floor}_{start}"
        end_node = f"{end_floor}_{end}"
        
        if start_node == end_node:
            messagebox.showwarning("Błąd", 
                                  "Punkt startowy i końcowy są takie same!")
            return
        
        # Znajdź ścieżkę
        path, distance = self.dijkstra(start_node, end_node)
        
        if path:
            self.shortest_path = path
            self.path_distance = distance
            
            # Włącz przycisk eksportu
            self.export_btn['state'] = 'normal'
            
            # Analizuj przejścia między piętrami
            floor_changes = self.analyze_floor_transitions(path)
            
            # Zaktualizuj informację
            info_text = (f"✓ Ścieżka: P{start_floor} pkt{start} → "
                        f"P{end_floor} pkt{end} | "
                        f"Dystans: {distance:.2f} | "
                        f"Kroki: {len(path) - 1}")
            if floor_changes:
                info_text += f" | Zmian pięter: {len(floor_changes)}"
            self.info_label['text'] = info_text
            
            # Pokaż wizualizację ze ścieżką
            self.visualize_graph()
            
            # Przygotuj komunikat z przejściami
            path_display = self.format_path_with_floors(path)
            message = f"Ścieżka znaleziona!\n\n{path_display}\n"
            message += f"\nDystans całkowity: {distance:.2f}\n"
            message += f"Liczba kroków: {len(path) - 1}"
            
            if floor_changes:
                message += f"\n\n🏢 Zmiany pięter ({len(floor_changes)}):"
                for change in floor_changes:
                    message += f"\n  {change}"
            
            messagebox.showinfo("Znaleziono ścieżkę!", message)
        else:
            messagebox.showerror("Brak ścieżki", 
                               f"Nie znaleziono ścieżki między punktem {start} (piętro {start_floor}) "
                               f"a {end} (piętro {end_floor})!\n"
                               "Sprawdź czy punkty są połączone lub istnieją przejścia między piętrami.")
    
    def dijkstra(self, start: str, end: str) -> Tuple[List[str], float]:
        """Algorytm Dijkstry do znajdowania najkrótszej ścieżki"""
        if start not in self.graph or end not in self.graph:
            return None, float('inf')
        
        # Kolejka priorytetowa: (dystans, węzeł, ścieżka)
        pq = [(0, start, [start])]
        visited = set()
        distances = {node: float('inf') for node in self.graph}
        distances[start] = 0
        
        while pq:
            current_dist, current_node, path = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            if current_node == end:
                return path, current_dist
            
            for neighbor, weight in self.graph[current_node]:
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    heapq.heappush(pq, (distance, neighbor, path + [neighbor]))
        
        return None, float('inf')
    
    def analyze_floor_transitions(self, path: List[str]) -> List[str]:
        """Analizuje ścieżkę i znajduje przejścia między piętrami"""
        transitions = []
        
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            
            # Pobierz floor_id z prefixed node ID
            current_floor = current_node.split('_')[0]
            next_floor = next_node.split('_')[0]
            
            # Sprawdź czy zmiana piętra
            if current_floor != next_floor:
                # Znajdź informacje o przejściu
                transition_info = self.find_transition_info(current_node, next_node)
                if transition_info:
                    floor_name_from = self.building_info.get('floor_names', {}).get(current_floor, f"Piętro {current_floor}")
                    floor_name_to = self.building_info.get('floor_names', {}).get(next_floor, f"Piętro {next_floor}")
                    
                    trans_type = transition_info['type']
                    trans_name = transition_info.get('name', '')
                    icon = "🪜" if trans_type == "stairs" else "🛗"
                    
                    transitions.append(
                        f"{icon} {trans_name}: {floor_name_from} → {floor_name_to}"
                    )
        
        return transitions
    
    def find_transition_info(self, from_node: str, to_node: str) -> dict:
        """Znajduje informacje o przejściu między węzłami"""
        from_floor, from_point = from_node.split('_')
        to_floor, to_point = to_node.split('_')
        
        for transition in self.floor_transitions:
            # Sprawdź czy to nasze przejście (w obu kierunkach)
            if (transition['from_floor'] == from_floor and 
                transition['to_floor'] == to_floor and
                str(transition['from_point']) == from_point and
                str(transition['to_point']) == to_point):
                return transition
            elif (transition['from_floor'] == to_floor and 
                  transition['to_floor'] == from_floor and
                  str(transition['from_point']) == to_point and
                  str(transition['to_point']) == from_point):
                return transition
        
        return None
    
    def format_path_with_floors(self, path: List[str]) -> str:
        """Formatuje ścieżkę z informacjami o piętrach"""
        if not path:
            return ""
        
        result = []
        current_floor = None
        
        for node in path:
            floor, point = node.split('_')
            
            # Dodaj nagłówek piętra gdy się zmienia
            if floor != current_floor:
                floor_name = self.building_info.get('floor_names', {}).get(floor, f"Piętro {floor}")
                result.append(f"\n🏢 {floor_name}:")
                current_floor = floor
            
            # Dodaj punkt z etykietą jeśli istnieje
            point_label = self.floors.get(floor, {}).get('point_labels', {}).get(point, "")
            if point_label:
                result.append(f"  • Punkt {point} ({point_label})")
            else:
                result.append(f"  • Punkt {point}")
        
        return '\n'.join(result)

    
    def export_shortest_path(self):
        """Eksportuje najkrótszą ścieżkę do pliku JSON (multi-floor)"""
        if not self.shortest_path:
            messagebox.showwarning("Brak ścieżki", 
                                  "Najpierw znajdź najkrótszą ścieżkę!")
            return
        
        # Zapisz do stałego pliku
        filename = "shortest_path.json"
        
        # Analizuj przejścia między piętrami
        floor_changes = self.analyze_floor_transitions(self.shortest_path)
        
        # Przygotuj dane do eksportu
        path_data = {
            "shortest_path": {
                "start_node": self.shortest_path[0],
                "end_node": self.shortest_path[-1],
                "path": self.shortest_path,
                "total_distance": round(self.path_distance, 2),
                "number_of_steps": len(self.shortest_path) - 1,
                "floor_transitions": floor_changes
            },
            "path_segments": [],
            "nodes_coordinates": {}
        }
        
        # Dodaj współrzędne wszystkich węzłów na ścieżce
        for node in self.shortest_path:
            if node in self.point_coords:
                x, y = self.point_coords[node]
                
                # Pobierz floor_id i point_id
                floor, point = node.split('_')
                floor_name = self.building_info.get('floor_names', {}).get(floor, f"Piętro {floor}")
                point_label = self.floors.get(floor, {}).get('point_labels', {}).get(point, "")
                
                path_data["nodes_coordinates"][node] = {
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "floor": floor,
                    "floor_name": floor_name,
                    "point_id": point,
                    "point_label": point_label
                }
        
        # Dodaj szczegóły segmentów ścieżki
        for i in range(len(self.shortest_path) - 1):
            node_from = self.shortest_path[i]
            node_to = self.shortest_path[i + 1]
            
            # Pobierz informacje o piętrach
            floor_from, point_from = node_from.split('_')
            floor_to, point_to = node_to.split('_')
            
            # Znajdź wagę krawędzi
            segment_distance = 0
            for neighbor, weight in self.graph[node_from]:
                if neighbor == node_to:
                    segment_distance = weight
                    break
            
            segment = {
                "from": node_from,
                "to": node_to,
                "distance": round(segment_distance, 2),
                "from_floor": floor_from,
                "to_floor": floor_to,
                "is_floor_transition": (floor_from != floor_to)
            }
            
            # Jeśli to przejście między piętrami, dodaj informacje
            if floor_from != floor_to:
                transition_info = self.find_transition_info(node_from, node_to)
                if transition_info:
                    segment["transition_type"] = transition_info['type']
                    segment["transition_name"] = transition_info.get('name', '')
            
            # Dodaj współrzędne jeśli dostępne
            if node_from in self.point_coords:
                segment["from_coords"] = {
                    "x": round(self.point_coords[node_from][0], 2),
                    "y": round(self.point_coords[node_from][1], 2)
                }
            if node_to in self.point_coords:
                segment["to_coords"] = {
                    "x": round(self.point_coords[node_to][0], 2),
                    "y": round(self.point_coords[node_to][1], 2)
                }
            
            path_data["path_segments"].append(segment)
        
        # Zapisz do pliku
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(path_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Eksport ukończony", 
                              f"Ścieżka zapisana do:\n{filename}\n\n"
                              f"Długość: {self.path_distance:.2f}\n"
                              f"Liczba węzłów: {len(self.shortest_path)}")
            
            self.info_label['text'] += f" | Wyeksportowano do: {filename.split('/')[-1]}"
            
        except Exception as e:
            messagebox.showerror("Błąd eksportu", f"Nie udało się zapisać pliku:\n{e}")
    
    def clear_visualization(self):
        """Czyści wizualizację i wybrane punkty"""
        self.shortest_path = None
        self.selected_start = None
        self.selected_end = None
        self.start_var.set('')
        self.end_var.set('')
        
        # Wyłącz przycisk eksportu
        self.export_btn['state'] = 'disabled'
        
        if self.graph:
            self.info_label['text'] = (f"Graf wczytany: {len(self.graph)} punktów | "
                                      "Wybierz punkty i znajdź ścieżkę")
            self.visualize_graph()
        else:
            self.info_label['text'] = "Wczytaj plik JSON z grafem GPS aby rozpocząć"
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
    
    def visualize_graph(self):
        """Wizualizacja grafu w oknie tkinter (multi-floor)"""
        if not self.graph:
            return
            
        # Usuń poprzedni canvas jeśli istnieje
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        # Utwórz nową figurę
        self.figure = plt.Figure(figsize=(12, 8), dpi=100)
        ax = self.figure.add_subplot(111)
        
        G = nx.Graph()
        
        # Określ które piętro pokazać
        current_floor = None
        if self.shortest_path:
            # Jeśli mamy ścieżkę, pokaż piętro startowe
            current_floor = self.shortest_path[0].split('_')[0]
        elif self.selected_start_floor:
            current_floor = self.selected_start_floor
        else:
            current_floor = "0"  # Domyślnie parter
        
        # Dodawanie krawędzi tylko z aktualnego piętra
        floor_nodes = set()
        for node, edges in self.graph.items():
            node_floor = node.split('_')[0]
            
            # Dodaj węzły z aktualnego piętra
            if node_floor == current_floor:
                floor_nodes.add(node)
                for neighbor, weight in edges:
                    neighbor_floor = neighbor.split('_')[0]
                    # Dodaj krawędź tylko jeśli oba węzły są na tym samym piętrze
                    if neighbor_floor == current_floor:
                        G.add_edge(node, neighbor, weight=weight)
        
        # Znajdź węzły przejść między piętrami na aktualnym piętrze
        transition_nodes = set()
        for transition in self.floor_transitions:
            if transition['from_floor'] == current_floor:
                trans_node = f"{transition['from_floor']}_{transition['from_point']}"
                if trans_node in floor_nodes:
                    transition_nodes.add(trans_node)
            if transition['to_floor'] == current_floor:
                trans_node = f"{transition['to_floor']}_{transition['to_point']}"
                if trans_node in floor_nodes:
                    transition_nodes.add(trans_node)
        
        # Użyj pozycji z pliku JSON (tylko dla węzłów z aktualnego piętra)
        pos = {node: self.positions[node] for node in floor_nodes if node in self.positions}
        
        if not pos and G.nodes():
            pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Rysowanie wszystkich krawędzi
        if G.edges():
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                  width=2, alpha=0.5, ax=ax)
        
        # Rysowanie węzłów przejść między piętrami
        if transition_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=list(transition_nodes),
                                  node_color='orange', node_size=500, 
                                  alpha=0.8, ax=ax, node_shape='s')  # kwadrat
        
        # Rysowanie wszystkich innych węzłów
        regular_nodes = [n for n in floor_nodes if n not in transition_nodes]
        if regular_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=regular_nodes,
                                  node_color='lightblue', 
                                  node_size=400, alpha=0.9, ax=ax)
        
        # Zaznacz wybrane punkty start/end (bez ścieżki)
        if self.selected_start and not self.shortest_path:
            start_node = f"{self.selected_start_floor}_{self.selected_start}"
            if start_node in pos:
                nx.draw_networkx_nodes(G, pos, nodelist=[start_node],
                                      node_color='lightgreen', node_size=600, ax=ax)
        
        if self.selected_end and not self.shortest_path:
            end_node = f"{self.selected_end_floor}_{self.selected_end}"
            if end_node in pos:
                nx.draw_networkx_nodes(G, pos, nodelist=[end_node],
                                      node_color='lightcoral', node_size=600, ax=ax)
        
        # Zaznaczanie najkrótszej ścieżki (tylko węzły z aktualnego piętra)
        if self.shortest_path and len(self.shortest_path) > 1:
            # Filtruj ścieżkę do węzłów na aktualnym piętrze
            path_on_floor = [n for n in self.shortest_path if n.split('_')[0] == current_floor]
            
            # Rysuj krawędzie ścieżki
            path_edges = []
            for i in range(len(self.shortest_path)-1):
                node1, node2 = self.shortest_path[i], self.shortest_path[i+1]
                floor1, floor2 = node1.split('_')[0], node2.split('_')[0]
                # Dodaj tylko krawędzie w obrębie piętra
                if floor1 == current_floor and floor2 == current_floor:
                    path_edges.append((node1, node2))
            
            if path_edges:
                nx.draw_networkx_edges(G, pos, edgelist=path_edges, 
                                      edge_color='red', width=4, ax=ax)
            
            # Zaznaczanie węzłów na ścieżce
            if path_on_floor:
                nx.draw_networkx_nodes(G, pos, nodelist=path_on_floor, 
                                      node_color='lightgreen', node_size=500, ax=ax)
            
            # Zaznaczanie punktu startowego i końcowego (jeśli są na tym piętrze)
            if self.shortest_path[0] in pos:
                nx.draw_networkx_nodes(G, pos, nodelist=[self.shortest_path[0]], 
                                      node_color='green', node_size=700, ax=ax)
            if self.shortest_path[-1] in pos:
                nx.draw_networkx_nodes(G, pos, nodelist=[self.shortest_path[-1]], 
                                      node_color='red', node_size=700, ax=ax)
            
            # Etykiety wag krawędzi (tylko dla ścieżki na tym piętrze)
            edge_labels = {}
            for n1, n2 in path_edges:
                for neighbor, weight in self.graph[n1]:
                    if neighbor == n2:
                        edge_labels[(n1, n2)] = f'{weight:.1f}'
                        break
            if edge_labels:
                nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, ax=ax)
        
        # Etykiety węzłów (tylko point_id bez floor prefix)
        labels = {node: node.split('_')[1] for node in pos.keys()}
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax)
        
        # Tytuł z informacją o piętrze
        floor_name = self.building_info.get('floor_names', {}).get(current_floor, f"Piętro {current_floor}")
        title = f"🏢 {floor_name}"
        if self.shortest_path:
            start_floor, start_point = self.shortest_path[0].split('_')
            end_floor, end_point = self.shortest_path[-1].split('_')
            title += f" | Ścieżka: P{start_floor} pkt{start_point} → P{end_floor} pkt{end_point}"
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.axis('off')
        
        # Dodaj canvas do okna tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    
    def auto_load_file(self):
        """Automatycznie wczytuje plik przy starcie"""
        if self.load_graph():
            print("✓ Automatycznie wczytano mapę z gps_paths.json")
    
    def return_to_menu(self):
        """Zamyka aplikację i wraca do menu głównego"""
        from tkinter import messagebox
        import subprocess
        import sys
        import os
        
        result = messagebox.askyesno("Powrót do Menu",
                                     "Czy na pewno chcesz wrócić do menu głównego?")
        
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
    app = GraphPathFinderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
