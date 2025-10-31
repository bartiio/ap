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
        self.root.title("Znajdowanie najkrótszej ścieżki - GPS Path Finder")
        self.root.geometry("1200x800")
        
        self.graph = {}
        self.positions = {}
        self.point_coords = {}
        self.shortest_path = None
        self.path_distance = 0
        self.selected_start = None
        self.selected_end = None
        
        self.setup_ui()
        
        # Auto-wczytaj plik przy starcie
        self.root.after(100, self.auto_load_file)
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Panel górny - przyciski i kontrolki
        top_frame = tk.Frame(self.root, bg='#f0f0f0', pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Wybór punktu startowego
        tk.Label(top_frame, text="Punkt START:", bg='#f0f0f0',
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(top_frame, textvariable=self.start_var,
                                        width=8, state='readonly')
        self.start_combo.pack(side=tk.LEFT, padx=5)
        self.start_combo.bind('<<ComboboxSelected>>', self.on_start_selected)
        
        # Wybór punktu końcowego
        tk.Label(top_frame, text="Punkt KONIEC:", bg='#f0f0f0',
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.end_var = tk.StringVar()
        self.end_combo = ttk.Combobox(top_frame, textvariable=self.end_var,
                                      width=8, state='readonly')
        self.end_combo.pack(side=tk.LEFT, padx=5)
        self.end_combo.bind('<<ComboboxSelected>>', self.on_end_selected)
        
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
        """Wczytuje graf z pliku JSON"""
        filename = "gps_paths.json"
        
        if not os.path.exists(filename):
            messagebox.showerror("Błąd", f"Nie znaleziono pliku {filename}!\nUtwórz mapę w Map Maker.")
            return False
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Wyczyść poprzednie dane
            self.graph = {}
            self.positions = {}
            self.point_coords = {}
            self.shortest_path = None
            self.selected_start = None
            self.selected_end = None
            
            # Wczytaj punkty i ich współrzędne
            all_points = {}
            for path in data['paths']:
                for point in path['points']:
                    point_id = str(point['id'])
                    if point['x'] != 0 or point['y'] != 0:  # Pomijaj puste punkty
                        all_points[point_id] = (point['x'], point['y'])
                        self.point_coords[point_id] = (point['x'], point['y'])
            
            # Wczytaj połączenia (krawędzie)
            for connection in data['connections']:
                node1 = str(connection['from'])
                node2 = str(connection['to'])
                distance = connection['distance']
                
                # Dodaj tylko jeśli oba punkty istnieją
                if node1 in all_points and node2 in all_points:
                    self.add_edge(node1, node2, distance)
            
            # Ustaw pozycje dla wizualizacji (odwróć Y bo matplotlib ma odwrotną oś)
            max_y = max(y for x, y in all_points.values()) if all_points else 700
            self.positions = {
                node: (x, max_y - y) 
                for node, (x, y) in all_points.items()
            }
            
            if not self.graph:
                messagebox.showwarning("Pusty graf", 
                                      "Graf jest pusty!\nNarysuj ścieżki w mapmaker_new.py i zapisz je.")
                return
            
            # Zaktualizuj listę węzłów w comboboxach
            nodes = sorted(self.graph.keys(), key=lambda x: int(x))
            self.start_combo['values'] = nodes
            self.end_combo['values'] = nodes
            
            # Włącz przycisk znajdowania ścieżki
            self.find_btn['state'] = 'normal'
            
            # Zaktualizuj informację
            conn_count = sum(len(edges) for edges in self.graph.values()) // 2
            self.info_label['text'] = (f"✓ Wczytano graf: {len(self.graph)} punktów, "
                                      f"{conn_count} połączeń")
            
            # Pokaż wizualizację
            self.visualize_graph()
            return True
            
        except FileNotFoundError:
            messagebox.showerror("Błąd", f"Nie znaleziono pliku!")
            return False
        except Exception as e:
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
    
    def add_edge(self, node1: str, node2: str, weight: float):
        """Dodaje krawędź między dwoma węzłami"""
        if node1 not in self.graph:
            self.graph[node1] = []
        if node2 not in self.graph:
            self.graph[node2] = []
        
        self.graph[node1].append((node2, weight))
        self.graph[node2].append((node1, weight))
    
    def find_shortest_path(self):
        """Znajduje najkrótszą ścieżkę między wybranymi punktami"""
        start = self.start_var.get()
        end = self.end_var.get()
        
        if not start or not end:
            messagebox.showwarning("Brak wyboru", 
                                  "Wybierz punkt startowy i końcowy!")
            return
        
        if start == end:
            messagebox.showwarning("Błąd", 
                                  "Punkt startowy i końcowy są takie same!")
            return
        
        # Znajdź ścieżkę
        path, distance = self.dijkstra(start, end)
        
        if path:
            self.shortest_path = path
            self.path_distance = distance
            
            # Włącz przycisk eksportu
            self.export_btn['state'] = 'normal'
            
            # Zaktualizuj informację
            self.info_label['text'] = (f"✓ Najkrótsza ścieżka: {start} → {end} | "
                                      f"Długość: {distance:.2f} | "
                                      f"Liczba przejść: {len(path) - 1}")
            
            # Pokaż wizualizację ze ścieżką
            self.visualize_graph()
            
            messagebox.showinfo("Znaleziono ścieżkę!", 
                              f"Ścieżka: {' → '.join(path)}\n"
                              f"Długość: {distance:.2f} jednostek\n"
                              f"Liczba przejść: {len(path) - 1}")
        else:
            messagebox.showerror("Brak ścieżki", 
                               f"Nie znaleziono ścieżki między punktem {start} a {end}!\n"
                               "Sprawdź czy punkty są połączone.")
    
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
    
    def export_shortest_path(self):
        """Eksportuje najkrótszą ścieżkę do pliku JSON"""
        if not self.shortest_path:
            messagebox.showwarning("Brak ścieżki", 
                                  "Najpierw znajdź najkrótszą ścieżkę!")
            return
        
        # Zapisz do stałego pliku
        filename = "shortest_path.json"
        
        # Przygotuj dane do eksportu
        path_data = {
            "shortest_path": {
                "start_node": self.shortest_path[0],
                "end_node": self.shortest_path[-1],
                "path": self.shortest_path,
                "total_distance": round(self.path_distance, 2),
                "number_of_steps": len(self.shortest_path) - 1
            },
            "path_segments": [],
            "nodes_coordinates": {}
        }
        
        # Dodaj współrzędne wszystkich węzłów na ścieżce
        for node in self.shortest_path:
            if node in self.point_coords:
                x, y = self.point_coords[node]
                path_data["nodes_coordinates"][node] = {
                    "x": round(x, 2),
                    "y": round(y, 2)
                }
        
        # Dodaj szczegóły segmentów ścieżki
        for i in range(len(self.shortest_path) - 1):
            node_from = self.shortest_path[i]
            node_to = self.shortest_path[i + 1]
            
            # Znajdź wagę krawędzi
            segment_distance = 0
            for neighbor, weight in self.graph[node_from]:
                if neighbor == node_to:
                    segment_distance = weight
                    break
            
            segment = {
                "from": node_from,
                "to": node_to,
                "distance": round(segment_distance, 2)
            }
            
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
        """Wizualizacja grafu w oknie tkinter"""
        if not self.graph:
            return
            
        # Usuń poprzedni canvas jeśli istnieje
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        
        # Utwórz nową figurę
        self.figure = plt.Figure(figsize=(12, 8), dpi=100)
        ax = self.figure.add_subplot(111)
        
        G = nx.Graph()
        
        # Dodawanie krawędzi do grafu NetworkX
        for node, edges in self.graph.items():
            for neighbor, weight in edges:
                G.add_edge(node, neighbor, weight=weight)
        
        # Użyj pozycji z pliku JSON
        pos = self.positions if self.positions else nx.spring_layout(G, k=2, iterations=50)
        
        # Rysowanie wszystkich krawędzi
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              width=2, alpha=0.5, ax=ax)
        
        # Rysowanie wszystkich węzłów
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                              node_size=400, alpha=0.9, ax=ax)
        
        # Zaznacz wybrane punkty start/end (bez ścieżki)
        if self.selected_start and not self.shortest_path:
            nx.draw_networkx_nodes(G, pos, nodelist=[self.selected_start],
                                  node_color='lightgreen', node_size=600, ax=ax)
        
        if self.selected_end and not self.shortest_path:
            nx.draw_networkx_nodes(G, pos, nodelist=[self.selected_end],
                                  node_color='lightcoral', node_size=600, ax=ax)
        
        # Zaznaczanie najkrótszej ścieżki
        if self.shortest_path and len(self.shortest_path) > 1:
            path_edges = [(self.shortest_path[i], self.shortest_path[i+1]) 
                         for i in range(len(self.shortest_path)-1)]
            nx.draw_networkx_edges(G, pos, edgelist=path_edges, 
                                  edge_color='red', width=4, ax=ax)
            
            # Zaznaczanie węzłów na ścieżce
            nx.draw_networkx_nodes(G, pos, nodelist=self.shortest_path, 
                                  node_color='lightgreen', node_size=500, ax=ax)
            
            # Zaznaczanie punktu startowego i końcowego
            nx.draw_networkx_nodes(G, pos, nodelist=[self.shortest_path[0]], 
                                  node_color='green', node_size=700, ax=ax)
            nx.draw_networkx_nodes(G, pos, nodelist=[self.shortest_path[-1]], 
                                  node_color='red', node_size=700, ax=ax)
            
            # Etykiety wag krawędzi (tylko dla ścieżki)
            edge_labels = {}
            for i in range(len(self.shortest_path) - 1):
                n1, n2 = self.shortest_path[i], self.shortest_path[i+1]
                for neighbor, weight in self.graph[n1]:
                    if neighbor == n2:
                        edge_labels[(n1, n2)] = f'{weight:.1f}'
                        break
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8, ax=ax)
        
        # Etykiety węzłów
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax)
        
        title = "Graf ze ścieżkami GPS"
        if self.shortest_path:
            title += f" | Najkrótsza ścieżka: {self.shortest_path[0]} → {self.shortest_path[-1]}"
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
