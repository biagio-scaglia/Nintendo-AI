# 🎮 Nintendo AI Game Advisor

Sistema intelligente di raccomandazione giochi Nintendo basato su AI, con API REST e app Flutter mobile.

## ✨ Caratteristiche

- 🤖 **AI-Powered Recommendations**: Consigli personalizzati basati su umore e preferenze
- 💬 **Chat Interattiva**: Interfaccia conversazionale per scoprire giochi Nintendo
- 📱 **App Flutter**: Applicazione mobile cross-platform (Android/iOS) con visualizzazione strutturata
- 🔍 **Ricerca Intelligente**: Sistema RAG per informazioni dettagliate sui giochi
- 🌐 **Ricerca Web Integrata**: Cerca automaticamente su internet giochi e personaggi non nel database
- 🎯 **42 Giochi Nintendo**: Database completo con tags e mood bilingue (IT/EN)
- 👤 **Info Personaggi**: Supporto per domande su personaggi Nintendo (es. "chi è yoshi?")
- 📊 **Card Informative**: Visualizzazione strutturata di informazioni giochi e personaggi nel frontend

## 🏗️ Architettura

```
nintendo_ai/
├── app/                    # Backend FastAPI
│   ├── main.py            # API REST server
│   ├── ai_engine_ollama.py  # Integrazione Ollama
│   ├── db/                # Database giochi
│   ├── knowledge/         # Sistema RAG
│   ├── services/          # Servizi di raccomandazione
│   └── tools/             # Utilità e scraper
├── flutter_app/           # App mobile Flutter
└── requirements.txt       # Dipendenze Python
```

## 🚀 Quick Start

### Prerequisiti

- Python 3.8+
- Flutter SDK 3.10.1+ (per l'app mobile)
- [Ollama](https://ollama.ai/) installato e in esecuzione

### 1. Installa Ollama e il Modello

```bash
# Installa Ollama da https://ollama.ai/

# Scarica un modello (consigliato)
ollama pull qwen3:8b
# oppure
ollama pull llama3.2
```

### 2. Setup Backend API

```bash
# Installa dipendenze Python
pip install -r requirements.txt

# Avvia il server API
python -m app.main
```

Il server sarà disponibile su `http://localhost:8000`

### 3. Setup App Flutter (Opzionale)

```bash
cd flutter_app

# Installa dipendenze
flutter pub get

# Configura l'URL API in lib/services/nintendo_api_service.dart
# - Android Emulator: http://10.0.2.2:8000
# - iOS Simulator: http://localhost:8000
# - Dispositivo fisico: http://TUO_IP:8000

# Esegui l'app
flutter run
```

## 📡 API Endpoints

### Chat
```http
POST /chat
Content-Type: application/json

{
  "history": [
    {"role": "user", "content": "Consigliami un gioco per quando sono stanco"}
  ]
}
```

### Lista Giochi
```http
GET /games/list
```

### Giochi per Piattaforma
```http
GET /games/platform/{platform}
```

### Informazioni Gioco
```http
POST /game/info
Content-Type: application/json

{
  "query": "Zelda Breath of the Wild"
}
```

## 🎯 Come Funziona

1. **Analisi Umore**: L'AI analizza il messaggio dell'utente per estrarre mood e preferenze
2. **Raccomandazione**: Confronta i tag estratti con il database di 42 giochi Nintendo
3. **Matching Intelligente**: Trova il gioco con la migliore corrispondenza
4. **Risposta Contestuale**: Se richiesto, recupera informazioni dettagliate dal sistema RAG
5. **Ricerca Web**: Se un gioco o personaggio non è nel database, cerca automaticamente su internet
6. **Visualizzazione Strutturata**: Le informazioni vengono mostrate in card colorate nel frontend

## 🗄️ Database Giochi

Il sistema include **42 giochi Nintendo** con:
- Tags descrittivi (genere, gameplay, stile)
- Mood bilingue (italiano/inglese) per matching inclusivo
- Informazioni dettagliate (gameplay, difficoltà, modalità)
- Supporto per Switch, Wii U, Wii, 3DS, DS

## 🔧 Configurazione

### Modificare il Modello Ollama

In `app/ai_engine_ollama.py`:
```python
MODEL_NAME = "qwen3:8b"  # Cambia con il tuo modello preferito
```

Il sistema rileva automaticamente i modelli disponibili in Ollama.

### Configurare l'URL API (Flutter)

In `flutter_app/lib/services/nintendo_api_service.dart`:
```dart
static const String baseUrl = 'http://localhost:8000';
```

## 📦 Dipendenze

### Backend
- `fastapi` - Framework web
- `uvicorn` - Server ASGI
- `pydantic` - Validazione dati
- `requests` - Client HTTP per Ollama
- `beautifulsoup4` - Web scraping (opzionale)

### Flutter
- `http` - Client HTTP
- `provider` - State management

## 🛠️ Sviluppo

### Struttura Backend

- **`app/main.py`**: Server FastAPI principale con logica di routing query
- **`app/ai_engine_ollama.py`**: Integrazione con Ollama e pulizia markdown
- **`app/services/recommender_service.py`**: Logica di raccomandazione
- **`app/services/info_service.py`**: Sistema RAG per info giochi
- **`app/services/web_search_service.py`**: Ricerca web per giochi/personaggi non nel DB
- **`app/knowledge/rag_engine.py`**: Motore di ricerca semantica
- **`app/db/nintendo_games.json`**: Database giochi con tags/mood
- **`app/knowledge/game_details.json`**: Dettagli completi giochi

### Struttura Flutter

- **`lib/main.dart`**: Entry point
- **`lib/screens/chat_screen.dart`**: UI chat
- **`lib/providers/chat_provider.dart`**: State management
- **`lib/services/nintendo_api_service.dart`**: Client API
- **`lib/models/`**: Modelli dati

## 🐛 Troubleshooting

### Ollama non raggiungibile
```bash
# Verifica che Ollama sia in esecuzione
ollama list

# Riavvia Ollama se necessario
```

### Errore connessione API (Flutter)
- Verifica che l'API sia in esecuzione su `localhost:8000`
- Per Android emulator usa `10.0.2.2:8000`
- Per dispositivi fisici usa l'IP locale del computer

### Modello non trovato
```bash
# Installa un modello
ollama pull qwen3:8b

# Verifica modelli disponibili
ollama list
```

## 🌐 Ricerca Web

Il sistema include ricerca web automatica per:
- **Giochi non nel database**: Cerca informazioni su giochi Nintendo non presenti localmente
- **Personaggi**: Supporta domande su personaggi Nintendo (es. "chi è yoshi?", "cos'è link?")
- **Info generali**: Fornisce data di uscita, piattaforme, sviluppatore, descrizione generale

**Limitazioni**: Il sistema fornisce solo informazioni generali sui giochi. Non risponde a:
- Guide su come battere livelli
- Strategie di gioco specifiche
- Walkthrough o soluzioni puzzle
- Trucchi o cheat codes

## 📝 Note

- Il sistema usa **solo Ollama** (nessun modello locale)
- I mood sono in formato bilingue per supportare italiano e inglese
- L'API supporta CORS per richieste cross-origin
- Il database include giochi per Switch, Wii U, Wii, 3DS, DS
- Le risposte vengono pulite automaticamente da formattazione markdown
- Il frontend mostra card informative per giochi raccomandati e informazioni strutturate

## 📄 Licenza

Questo progetto è open source e disponibile per uso personale ed educativo.

## 🤝 Contribuire

Contributi sono benvenuti! Sentiti libero di aprire issue o pull request.

---

**Buon gaming! 🎮✨**
