import tkinter as tk
from tkinter import messagebox
import math
import json

class GPSPathSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Symulator Ścieżek GPS - Symulacja chodzenia po obszarze")
        
        # Parametry
        self.point_radius = 4
        self.path_distance = 15  # Dystans między punktami GPS
        self.merge_distance = 30  # Dystans do łączenia ścieżek
        
        self.points = []  # Wszystkie punkty GPS
        self.edges = []  # Połączenia między punktami
        self.paths = []  # Ścieżki użytkowników
        self.current_path = []  # Aktualnie rysowana ścieżka
        self.next_id = 1
        self.next_path_id = 1
        
        self.is_drawing = False
        self.last_point = None
        self.colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#16a085']
        
        self.create_control_panel()
        self.create_canvas()
        
        # Status bar
        self.status_label = tk.Label(
            root, 
            text="Ścieżki: 0 | Punkty GPS: 0 | Przeciągnij myszą aby narysować ścieżkę",
            font=('Arial', 10),
            bg='#e0e0e0',
            pady=5
        )
        self.status_label.pack(fill=tk.X)
    
    def create_control_panel(self):
        """Panel kontrolny"""
        control_frame = tk.Frame(self.root, bg='#e8e8e8', pady=10)
        control_frame.pack(fill=tk.X)
        
        # Gęstość punktów
        tk.Label(control_frame, text="Gęstość:", bg='#e8e8e8', font=('Arial', 10)).pack(side=tk.LEFT, padx=(20, 5))
        self.density_var = tk.IntVar(value=self.path_distance)
        tk.Scale(control_frame, from_=5, to=40, orient=tk.HORIZONTAL, 
                variable=self.density_var, command=self.update_density, length=100).pack(side=tk.LEFT, padx=5)
        
        # Łączenie ścieżek
        tk.Label(control_frame, text="Łączenie:", bg='#e8e8e8', font=('Arial', 10)).pack(side=tk.LEFT, padx=(10, 5))
        self.merge_var = tk.IntVar(value=self.merge_distance)
        tk.Scale(control_frame, from_=10, to=80, orient=tk.HORIZONTAL,
                variable=self.merge_var, command=self.update_merge, length=100).pack(side=tk.LEFT, padx=5)
        
        # Przyciski
        tk.Button(control_frame, text="🔀 Połącz korytarze", command=self.merge_parallel_paths,
                 font=('Arial', 10, 'bold'), bg='#9b59b6', fg='white', padx=10).pack(side=tk.LEFT, padx=10)
        tk.Button(control_frame, text="📊 Statystyki", command=self.show_stats,
                 font=('Arial', 10, 'bold'), bg='#95e1d3', fg='black', padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="💾 Zapisz", command=self.save_graph,
                 font=('Arial', 10, 'bold'), bg='#4ecdc4', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="🗑️ Wyczyść", command=self.clear_all,
                 font=('Arial', 10, 'bold'), bg='#ff6b6b', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Frame(control_frame, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Button(control_frame, text="⬅️ Menu", command=self.return_to_menu,
                 font=('Arial', 9, 'bold'), bg='#607D8B', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
    
    def create_canvas(self):
        """Tworzy canvas"""
        self.canvas_width = 900
        self.canvas_height = 700
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height,
                               bg='#f0f0f0', cursor='crosshair')
        self.canvas.pack(pady=10)
        
        self.canvas.create_text(self.canvas_width // 2, 30,
            text="PRZECIĄGNIJ MYSZĄ ABY SYMULOWAĆ CHODZENIE I ZBIERANIE DANYCH GPS",
            font=('Arial', 12, 'bold'), fill='#333', tags='instruction')
        
        self.canvas.create_text(self.canvas_width // 2, 60,
            text="Każda linia = ślad GPS jednego użytkownika | Bliskieścieżki łączą się automatycznie",
            font=('Arial', 10), fill='#666', tags='instruction')
        
        self.canvas.bind('<ButtonPress-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.draw_path)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
    
    def update_density(self, value):
        self.path_distance = int(value)
    
    def update_merge(self, value):
        old_merge = self.merge_distance
        self.merge_distance = int(value)
        if len(self.paths) > 1 and old_merge != self.merge_distance:
            self.recalculate_connections()
    
    def calculate_distance(self, p1, p2):
        """Odległość między punktami"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def start_drawing(self, event):
        """Rozpoczęcie rysowania nowej ścieżki"""
        if event.y < 100:  # Nie rysuj na instrukcjach
            return
        
        self.is_drawing = True
        self.current_path = []
        self.last_point = (event.x, event.y)
        
        # Dodaj pierwszy punkt
        self.add_point(event.x, event.y)
    
    def draw_path(self, event):
        """Rysowanie ścieżki podczas przeciągania"""
        if not self.is_drawing or event.y < 100:
            return
        
        if self.last_point:
            dist = self.calculate_distance(self.last_point, (event.x, event.y))
            
            if dist >= self.path_distance:
                self.add_point(event.x, event.y)
                self.last_point = (event.x, event.y)
    
    def add_point(self, x, y):
        """Dodaje punkt GPS"""
        point_id = self.next_id
        path_id = self.next_path_id
        color = self.colors[(path_id - 1) % len(self.colors)]
        
        # Rysuj punkt
        self.canvas.create_oval(x - self.point_radius, y - self.point_radius,
                               x + self.point_radius, y + self.point_radius,
                               fill=color, outline=color, width=2, tags=f'path_{path_id}')
        
        # Połącz z poprzednim punktem w tej samej ścieżce
        if len(self.current_path) > 0:
            prev = self.current_path[-1]
            prev_point = next((p for p in self.points if p[2] == prev), None)
            if prev_point:
                dist = self.calculate_distance((x, y), (prev_point[0], prev_point[1]))
                self.canvas.create_line(prev_point[0], prev_point[1], x, y,
                                       fill=color, width=3, tags=f'path_{path_id}')
                self.edges.append((prev, point_id, dist))
        
        self.points.append((x, y, point_id, path_id))
        self.current_path.append(point_id)
        self.next_id += 1
    
    def stop_drawing(self, event):
        """Zakończenie rysowania ścieżki"""
        if not self.is_drawing:
            return
        
        self.is_drawing = False
        
        if len(self.current_path) > 0:
            self.paths.append({
                'id': self.next_path_id,
                'points': self.current_path.copy(),
                'color': self.colors[(self.next_path_id - 1) % len(self.colors)]
            })
            self.next_path_id += 1
        
        self.current_path = []
        self.last_point = None
        self.update_status()
    
    def recalculate_connections(self):
        """Przelicza połączenia między ścieżkami"""
        # Usuń krawędzie między ścieżkami
        new_edges = []
        for id1, id2, dist in self.edges:
            p1 = next((p for p in self.points if p[2] == id1), None)
            p2 = next((p for p in self.points if p[2] == id2), None)
            
            if p1 and p2 and p1[3] == p2[3]:  # Ta sama ścieżka
                new_edges.append((id1, id2, dist))
        
        self.edges = new_edges
        
        # Przelicz nowe połączenia
        for i, (x1, y1, id1, path_id1) in enumerate(self.points):
            for x2, y2, id2, path_id2 in self.points[i+1:]:
                if path_id1 == path_id2:
                    continue
                
                dist = self.calculate_distance((x1, y1), (x2, y2))
                
                if dist <= self.merge_distance:
                    edge_exists = any((e[0] == id1 and e[1] == id2) or 
                                    (e[0] == id2 and e[1] == id1) for e in self.edges)
                    
                    if not edge_exists:
                        self.edges.append((id1, id2, dist))
        
        self.update_status()
    
    def clear_all(self):
        """Czyści wszystko"""
        if len(self.points) == 0:
            return
        
        if messagebox.askyesno("Potwierdzenie", "Usunąć wszystkie ścieżki?"):
            self.canvas.delete('all')
            
            # Odtwórz instrukcje
            self.canvas.create_text(self.canvas_width // 2, 30,
                text="PRZECIĄGNIJ MYSZĄ ABY SYMULOWAĆ CHODZENIE I ZBIERANIE DANYCH GPS",
                font=('Arial', 12, 'bold'), fill='#333', tags='instruction')
            
            self.canvas.create_text(self.canvas_width // 2, 60,
                text="Każda linia = ślad GPS jednego użytkownika | Użyj 'Połącz korytarze' aby uprościć",
                font=('Arial', 10), fill='#666', tags='instruction')
            
            # WAŻNE: Przywróć bindowania zdarzeń
            self.canvas.bind('<ButtonPress-1>', self.start_drawing)
            self.canvas.bind('<B1-Motion>', self.draw_path)
            self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
            
            # Wyczyść dane
            self.points.clear()
            self.edges.clear()
            self.paths.clear()
            self.current_path.clear()
            self.next_id = 1
            self.next_path_id = 1
            self.update_status()
    
    def save_graph(self):
        """Zapisuje graf do JSON"""
        if len(self.points) == 0:
            messagebox.showwarning("Brak danych", "Nie ma danych do zapisania!")
            return
        
        graph_data = {
            'paths': [
                {
                    'id': path['id'],
                    'points': [
                        {'id': pid, 'x': next((p[0] for p in self.points if p[2] == pid), 0),
                         'y': next((p[1] for p in self.points if p[2] == pid), 0)}
                        for pid in path['points']
                    ],
                    'color': path['color']
                }
                for path in self.paths
            ],
            'connections': [
                {'from': id1, 'to': id2, 'distance': round(dist, 2)}
                for id1, id2, dist in self.edges
            ],
            'settings': {
                'point_density': self.path_distance,
                'merge_distance': self.merge_distance
            }
        }
        
        filename = 'gps_paths.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Zapisano", 
            f"Ścieżki GPS zapisane do:\n{filename}\n\n"
            f"Ścieżki: {len(self.paths)}\n"
            f"Punkty GPS: {len(self.points)}\n"
            f"Połączenia: {len(self.edges)}")
    
    def show_stats(self):
        """Statystyki"""
        if len(self.points) == 0:
            messagebox.showinfo("Statystyki", "Brak danych!")
            return
        
        # Połączenia w ramach ścieżek vs między ścieżkami
        within_path = 0
        cross_path = 0
        
        for id1, id2, dist in self.edges:
            p1 = next((p for p in self.points if p[2] == id1), None)
            p2 = next((p for p in self.points if p[2] == id2), None)
            
            if p1 and p2:
                if p1[3] == p2[3]:
                    within_path += 1
                else:
                    cross_path += 1
        
        # Analiza skrzyżowań
        intersections = []
        for x, y, pid, _ in self.points:
            connections = sum(1 for e in self.edges if pid in (e[0], e[1]))
            if connections > 2:
                intersections.append((pid, connections))
        
        avg_path_length = len(self.points) / len(self.paths) if self.paths else 0
        
        stats = f"""
═══════════════════════════════════════
      STATYSTYKI ŚCIEŻEK GPS
═══════════════════════════════════════

👥 Liczba ścieżek (użytkowników): {len(self.paths)}
📍 Całkowita liczba punktów GPS: {len(self.points)}
📊 Średnia długość ścieżki: {avg_path_length:.1f} punktów

POŁĄCZENIA:
  🔗 W ramach ścieżek: {within_path}
  🌉 Między ścieżkami: {cross_path}
  📏 Razem: {len(self.edges)}

SKRZYŻOWANIA:
  🔴 Liczba skrzyżowań: {len(intersections)}
  {('  Max. połączeń: ' + str(max(c for _, c in intersections)) if intersections else '')}

USTAWIENIA:
  • Gęstość punktów: {self.path_distance} px
  • Dystans łączenia: {self.merge_distance} px
        """
        
        messagebox.showinfo("Statystyki", stats)
    
    def update_status(self):
        """Aktualizuje status"""
        self.status_label.config(
            text=f"Ścieżki: {len(self.paths)} | Punkty GPS: {len(self.points)} | "
                 f"Połączenia: {len(self.edges)} | Przeciągnij myszą aby dodać kolejną ścieżkę"
        )
    
    def merge_parallel_paths(self):
        """Łączy równoległe ścieżki (ten sam korytarz, różni użytkownicy)"""
        if len(self.paths) < 2:
            messagebox.showinfo("Info", "Potrzeba co najmniej 2 ścieżek!")
            return
        
        if len(self.points) == 0:
            messagebox.showinfo("Info", "Brak punktów!")
            return
        
        merge_threshold = 40  # Maksymalny dystans do uznania za ten sam korytarz
        original_count = len(self.points)
        
        # Grupuj punkty które są blisko siebie
        merged_points = {}  # stary_id -> nowy_id
        new_points_list = []
        used_points = set()
        new_point_id = 1
        
        for i, (x1, y1, id1, path1) in enumerate(self.points):
            if id1 in used_points:
                continue
            
            # Znajdź wszystkie bliskie punkty (również z tej samej ścieżki)
            cluster = [(x1, y1, id1, path1)]
            used_points.add(id1)
            
            for j, (x2, y2, id2, path2) in enumerate(self.points):
                if id2 in used_points:
                    continue
                
                dist = self.calculate_distance((x1, y1), (x2, y2))
                
                if dist <= merge_threshold:
                    cluster.append((x2, y2, id2, path2))
                    used_points.add(id2)
            
            # Oblicz średnią pozycję klastra
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            avg_y = sum(p[1] for p in cluster) / len(cluster)
            
            # Przypisz nowe ID wszystkim punktom w klastrze
            for _, _, old_id, old_path in cluster:
                merged_points[old_id] = new_point_id
            
            # Zachowaj informację o ścieżce pierwszego punktu w klastrze
            new_points_list.append((avg_x, avg_y, new_point_id, cluster[0][3]))
            new_point_id += 1
        
        # Przelicz krawędzie z nowymi ID
        new_edges = []
        edge_set = set()  # Unikaj duplikatów
        
        for id1, id2, dist in self.edges:
            new_id1 = merged_points.get(id1)
            new_id2 = merged_points.get(id2)
            
            if new_id1 is None or new_id2 is None:
                continue
            
            if new_id1 == new_id2:  # Nie dodawaj self-loops
                continue
            
            # Utwórz unikalny klucz (mniejsze ID zawsze pierwsze)
            edge_key = (min(new_id1, new_id2), max(new_id1, new_id2))
            
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                
                p1 = next((p for p in new_points_list if p[2] == new_id1), None)
                p2 = next((p for p in new_points_list if p[2] == new_id2), None)
                
                if p1 and p2:
                    new_dist = self.calculate_distance((p1[0], p1[1]), (p2[0], p2[1]))
                    new_edges.append((new_id1, new_id2, new_dist))
        
        # Aktualizuj dane
        old_points = len(self.points)
        self.points = new_points_list
        self.edges = new_edges
        
        # Przerysuj
        self.redraw_graph()
        
        merged = old_points - len(self.points)
        messagebox.showinfo("Połączono korytarze",
            f"Scalono {merged} punktów\n"
            f"Pozostało {len(self.points)} unikalnych lokalizacji\n\n"
            f"Ścieżki w tym samym miejscu zostały połączone!")
        
        self.update_status()
    
    def redraw_graph(self):
        """Przerysowuje cały graf"""
        self.canvas.delete('all')
        
        # Odtwórz instrukcje
        self.canvas.create_text(self.canvas_width // 2, 30,
            text="PRZECIĄGNIJ MYSZĄ ABY SYMULOWAĆ CHODZENIE I ZBIERANIE DANYCH GPS",
            font=('Arial', 12, 'bold'), fill='#333', tags='instruction')
        
        self.canvas.create_text(self.canvas_width // 2, 60,
            text="Każda linia = ślad GPS jednego użytkownika | Użyj 'Połącz korytarze' aby uprościć",
            font=('Arial', 10), fill='#666', tags='instruction')
        
        # Przywróć bindowania zdarzeń (WAŻNE!)
        self.canvas.bind('<ButtonPress-1>', self.start_drawing)
        self.canvas.bind('<B1-Motion>', self.draw_path)
        self.canvas.bind('<ButtonRelease-1>', self.stop_drawing)
        
        # Rysuj krawędzie - tylko ciągłe linie (bez przerywanych)
        for id1, id2, dist in self.edges:
            p1 = next((p for p in self.points if p[2] == id1), None)
            p2 = next((p for p in self.points if p[2] == id2), None)
            
            if p1 and p2:
                # Wszystkie linie jako ciągłe zielone
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                       fill='#2ecc71', width=3)
        
        # Rysuj punkty
        for x, y, point_id, path_id in self.points:
            # Oblicz liczbę połączeń
            connections = sum(1 for e in self.edges if point_id in (e[0], e[1]))
            
            # Wielkość zależy od liczby połączeń
            radius = self.point_radius + connections * 2
            
            # Kolor zależy od typu punktu
            if connections > 2:
                color = '#e74c3c'  # Czerwony dla skrzyżowań
            else:
                color = '#3498db'  # Niebieski dla zwykłych
            
            self.canvas.create_oval(x - radius, y - radius,
                                   x + radius, y + radius,
                                   fill=color, outline='#2c3e50', width=2)
            
            # Numer połączeń dla skrzyżowań
            if connections > 2:
                self.canvas.create_text(x, y, text=str(connections),
                                       font=('Arial', 8, 'bold'), fill='white')
    
    def return_to_menu(self):
        """Zamyka aplikację i wraca do menu głównego"""
        from tkinter import messagebox
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
    app = GPSPathSimulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
