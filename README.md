# 🗺️ GPS Navigation System

Kompleksowy system nawigacji GPS z funkcjami tworzenia map, znajdowania najkrótszej ścieżki, nawigacji w czasie rzeczywistym oraz zarządzania punktami zainteresowania.

## 📋 Opis

System składa się z 5 zintegrowanych aplikacji:

### 1. 🧭 **Navigator** (navigator.py)
- Nawigacja w czasie rzeczywistym
- Symulacja chodzenia po mapie (rysowanie myszką)
- Automatyczne wykrywanie odstępstw od trasy
- System feedbacku użytkownika
- Automatyczna aktualizacja mapy na podstawie przejść użytkowników
- **Nie wymaga hasła**

### 2. 🗺️ **Map Maker** (mapmaker_new.py)
- Tworzenie map przez rysowanie ścieżek
- Automatyczne wykrywanie skrzyżowań
- Łączenie równoległych korytarzy
- Eksport do JSON
- **Wymaga hasła administratora: `admin`**

### 3. 📊 **Graph Analyzer** (graph.py)
- Algorytm Dijkstry do znajdowania najkrótszej ścieżki
- Wizualizacja grafu z matplotlib
- Eksport trasy do JSON
- **Wymaga hasła administratora: `admin`**

### 4. 🏷️ **Map Manager** (map_manager.py)
- Dodawanie etykiet do punktów (nazwy sal, toalet, wind, etc.)
- Wyrównywanie punktów do siatki
- Usuwanie węzłów
- Grupowe zaznaczanie (lasso)
- Przeglądanie feedbacku użytkowników
- **Wymaga hasła administratora: `admin`**

### 5. 🏠 **Menu** (menu.py)
- Główne menu z autoryzacją
- Uruchamianie wszystkich aplikacji
- System uprawnień

## 🚀 Instalacja

### Wymagania
- Python 3.7+
- tkinter (zazwyczaj wbudowany w Python)
- Biblioteki z requirements.txt

### Kroki instalacji

1. **Sklonuj repozytorium:**
```bash
git clone https://github.com/TWOJE_USERNAME/gps-navigation-system.git
cd gps-navigation-system
```

2. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

3. **Uruchom aplikację:**
```bash
python menu.py
```

## 📦 Struktura projektu

```
ap/
├── menu.py              # Główne menu z autoryzacją
├── navigator.py         # Nawigacja w czasie rzeczywistym
├── mapmaker_new.py      # Tworzenie map
├── graph.py             # Analiza ścieżek i Dijkstra
├── map_manager.py       # Zarządzanie etykietami
├── gps_paths.json       # Plik z mapą (auto-generowany)
├── shortest_path.json   # Plik z trasą (auto-generowany)
├── route_feedback.json  # Feedback użytkowników (auto-generowany)
├── requirements.txt     # Zależności Python
├── README.md           # Ten plik
└── .gitignore          # Ignorowane pliki
```

## 🎮 Jak używać

### Pierwszy raz:

1. **Uruchom Menu:**
   ```bash
   python menu.py
   ```

2. **Utwórz mapę (Map Maker):**
   - Hasło: `admin`
   - Przeciągnij myszą aby narysować ścieżki
   - Użyj "Połącz korytarze" aby uprościć mapę
   - Zapisz jako `gps_paths.json`

3. **Znajdź trasę (Graph Analyzer):**
   - Hasło: `admin`
   - Mapa wczyta się automatycznie
   - Wybierz punkt START i KONIEC
   - Kliknij "Znajdź najkrótszą ścieżkę"
   - Eksportuj do `shortest_path.json`

4. **Dodaj etykiety (Map Manager):**
   - Hasło: `admin`
   - Kliknij na punkty i dodawaj nazwy (np. "Sala 101")
   - Zapisz zmiany

5. **Nawiguj (Navigator):**
   - Bez hasła
   - Wszystko wczyta się automatycznie
   - Przeciągnij myszą aby symulować chodzenie
   - System poinformuje Cię o odchyleniach od trasy

### Kolejne uruchomienia:

Wystarczy uruchomić `python menu.py` - wszystkie pliki wczytają się automatycznie!

## 🔑 Autoryzacja

**Hasło administratora:** `admin`

Zmień hasło w pliku `menu.py` (linia 172):
```python
if password == "admin":  # Zmień "admin" na swoje hasło
```

## 📊 Format plików JSON

### gps_paths.json (mapa)
```json
{
  "paths": [...],
  "connections": [...],
  "point_labels": {
    "1": "Wejście główne",
    "5": "Sala 101"
  }
}
```

### shortest_path.json (trasa)
```json
{
  "shortest_path": {
    "path": ["1", "2", "3"],
    "total_distance": 150.5
  }
}
```

### route_feedback.json (feedback)
```json
[
  {
    "timestamp": "2025-10-31 10:30:00",
    "reason": "shorter_route",
    "notes": "Skrót przez parking"
  }
]
```

## 🛠️ Rozwój projektu

### Planowane funkcje:
- [ ] Import map z plików CAD/PDF
- [ ] Eksport map do obrazów
- [ ] Wiele pięter/poziomów
- [ ] Integracja z prawdziwym GPS
- [ ] Aplikacja mobilna
- [ ] Baza danych zamiast JSON

### Jak współtworzyć:
1. Fork repozytorium
2. Stwórz branch (`git checkout -b feature/NowaFunkcja`)
3. Commit zmian (`git commit -m 'Dodano nową funkcję'`)
4. Push do brancha (`git push origin feature/NowaFunkcja`)
5. Otwórz Pull Request

## 🐛 Znane problemy

- Wielkie pliki JSON mogą spowalniać aplikację
- Lasso mode wymaga precyzyjnego rysowania
- Autoryzacja jest podstawowa (tylko hasło)

## 📝 Licencja

MIT License - możesz swobodnie używać i modyfikować

## 👤 Autor

Bartosz K.

## 🙏 Podziękowania

Dziękuję za korzystanie z GPS Navigation System!

---

**Potrzebujesz pomocy?** Otwórz Issue na GitHubie!
