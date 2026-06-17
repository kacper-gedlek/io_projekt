# Projekt: Bezdotykowa rejestracja obecności

## Opis projektu

Projekt dotyczy realizacji systemu integrującego czytniki kart RFID (standard Mifare) z modułem obecności **Attendance** (`mod_attendance`) na platformie **Moodle**. Repozytorium zawiera kod źródłowy backendu pośredniczącego w komunikacji i wykonującego zapytania bezpośrednio na bazie danych Moodle.

Backend został zaimplementowany w języku Python z użyciem frameworka **FastAPI** oraz biblioteki **SQLAlchemy** (ORM). Aplikacja obsługuje zarówno bazę danych MySQL/MariaDB (poprzez sterownik `pymysql`), jak i PostgreSQL (`psycopg2`), co pozwala na łatwe wdrożenie w istniejących środowiskach uczelnianych.

---

## Zakres funkcjonalności backendu

System udostępnia zestaw punktów końcowych (API endpoints) zabezpieczonych kluczem dostępu (`X-API-Key`), które realizują kluczowe wymagania projektowe:

1. **Identyfikacja użytkowników (`GET /api/users/check/{card_uid}`)**
   Odpytuje bazę Moodle i sprawdza, czy odczytany UID karty (przechowywany w polu `idnumber` tabeli `mdl_user`) jest przypisany do aktywnego konta.
2. **Pobieranie kursów prowadzącego (`GET /api/lecturer/{card_uid}/courses`)**
   Umożliwia zalogowanie wykładowcy za pomocą karty RFID i pobranie listy kursów, w których posiada on przypisaną rolę nauczyciela (`teacher` / `editingteacher`).
3. **Zarządzanie sesjami zajęć (`GET /api/courses/{course_id}/sessions`)**
   Pobiera zdefiniowane w Moodle sesje obecności dla wskazanego przedmiotu z możliwością wyświetlenia sesji z bieżącego dnia, wybranej daty lub całej historii.
4. **Rejestracja obecności (`POST /api/attendance/register`)**
   Zapisuje fakt obecności studenta bezpośrednio w strukturach tabel Moodle. Wyszukuje status oznaczający obecność (domyślnie oznaczony jako "P" lub mający najwyższą wagę oceny) i tworzy odpowiedni rekord w logach wtyczki `mod_attendance`.

---

## Struktura plików w projekcie

```text
io_projekt/
│
├── app/                  # Pakiet główny aplikacji
│   ├── config.py         # Wczytywanie konfiguracji (zmienne środowiskowe z pliku .env)
│   ├── database.py       # Konfiguracja silnika bazodanowego (SQLAlchemy engine, sesje)
│   ├── models.py         # Definicja modeli ORM odzwierciedlających tabele Moodle (mdl_user, mdl_course, itp.)
│   ├── crud.py           # Zapytania i operacje na bazie danych (logika biznesowa)
│   └── main.py           # Konfiguracja FastAPI, definicje tras, walidacja i obsługa błędów
│
├── .env                # Lokalny plik konfiguracyjny (baza danych, klucz zabezpieczający)
├── requirements.txt    # Wymagane pakiety Pythona
├── test_api.py         # Skrypt z testami integracyjnymi
└── README.md           # Niniejsza dokumentacja
```

---

## Instrukcja uruchomienia i konfiguracji

### 1. Przygotowanie środowiska wirtualnego
W katalogu głównym projektu należy utworzyć i aktywować środowisko wirtualne Pythona:

```bash
# Utworzenie venv
python -m venv venv

# Aktywacja (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Aktywacja (Windows CMD)
.\venv\Scripts\activate.bat

# Aktywacja (Linux/macOS)
source venv/bin/activate
```

Następnie należy zainstalować wymagane pakiety:
```bash
pip install -r requirements.txt
```

### 2. Konfiguracja połączeń (Plik .env)
Przed pierwszym uruchomieniem należy stworzyć plik `.env` w głównym katalogu projektu i zdefiniować parametry połączenia z bazą danych Moodle oraz klucz zabezpieczający API:

```env
# Adres URL bazy danych Moodle (przykład dla MySQL):
DATABASE_URL=

# Klucz wymagany w nagłówku X-API-Key przy każdym zapytaniu do API:
API_KEY=

# Konfiguracja serwera
HOST=
PORT=
```

### 3. Uruchomienie aplikacji
Aby uruchomić serwer deweloperski, należy wykonać polecenie:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Dokumentacja interaktywna (Swagger UI) wygenerowana automatycznie przez FastAPI jest dostępna pod lokalnym adresem:
**[http://localhost:8001/docs](http://localhost:8001/docs)**

---

## Testowanie aplikacji

Aby potwierdzić poprawność integracji z bazą Moodle i prawidłowe zachowanie wszystkich punktów końcowych, przygotowany został zestaw testów automatycznych. Testy wykorzystują bazę danych SQLite w pamięci (mock) i symulują pełen scenariusz: od weryfikacji tożsamości po zapisanie obecności studenta w bazie.

Uruchomienie testów:
```bash
python test_api.py
```

---

## Materiały referencyjne i źródła

Podczas analizy struktury bazy danych Moodle oraz planowania integracji z mikrokontrolerami korzystaliśmy z poniższych źródeł:

### Integracja i Moodle
* [Boringowl - Flask](https://boringowl.io/tag/flask) & [SQLAlchemy](https://boringowl.io/tag/sql-alchemy) (wzorce architektury bazodanowej)
* Repozytorium wtyczki [moodle_mod_attendance](https://github.com/danmarsden/moodle-mod_attendance/tree/MOODLE_311_STABLE)
* Dokumentacja sterownika [mysql-connector-python](https://pypi.org/project/mysql-connector-python/)


