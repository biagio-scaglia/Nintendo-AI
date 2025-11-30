# 🎮 Nintendo AI Game Advisor

Sistema intelligente di raccomandazione giochi Nintendo basato su AI, con API REST e app Flutter mobile.

## ✨ Caratteristiche

- 🤖 **AI-Powered Recommendations**: Consigli personalizzati basati su umore e preferenze
- 💬 **Chat Interattiva**: Interfaccia conversazionale per scoprire giochi Nintendo
- 📱 **App Flutter**: Applicazione mobile cross-platform (Android/iOS) con visualizzazione strutturata
- 🔍 **Ricerca Intelligente**: Sistema RAG per informazioni dettagliate sui giochi
- 🌐 **Integrazione Fandom**: Scraping completo da wiki Fandom per informazioni accurate su giochi e personaggi
- 🖼️ **Immagini Personaggi**: Estrazione automatica di immagini da Fandom per personaggi Nintendo
- 📄 **Scraping Intelligente**: Estrae 15 paragrafi e 5 liste di default per risposte concise
- 🔍 **Approfondimento su Richiesta**: Chiedi "approfondisci" o "dimmi di più" per estrarre tutto il contenuto dalla stessa pagina
- 🧠 **Sintesi AI**: L'AI sintetizza automaticamente il contenuto estratto per risposte complete e ben formattate
- ⚡ **Risposte Veloci**: Modalità ottimizzata per messaggi colloquiali (small_talk) con tempi di risposta ridotti
- 🎯 **42 Giochi Nintendo**: Database completo con tags e mood bilingue (IT/EN)
- 👤 **Info Personaggi**: Supporto completo per domande su personaggi Nintendo con immagini
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
5. **Integrazione Fandom**: Per giochi e personaggi, cerca automaticamente su Fandom per informazioni accurate
6. **Scraping Intelligente**: Estrae 15 paragrafi e 5 liste di default per risposte concise e veloci
7. **Approfondimento su Richiesta**: Se chiedi "approfondisci" o "dimmi di più", estrae tutto il contenuto dalla stessa pagina
8. **Sintesi AI**: L'AI sintetizza automaticamente il contenuto estratto per generare risposte complete e ben formattate
9. **Estrazione Immagini**: Recupera immagini da Fandom per personaggi quando disponibili
10. **Modalità Ottimizzata**: Usa parametri veloci per messaggi colloquiali (small_talk) per risposte rapide
11. **Visualizzazione Strutturata**: Le informazioni vengono mostrate in card colorate nel frontend con immagini

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
- **`app/services/web_search_service.py`**: Scraping Fandom e ricerca web per giochi/personaggi non nel DB
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

## 🌐 Integrazione Fandom

Il sistema include scraping diretto da wiki Fandom per informazioni accurate e aggiornate:

### Serie Supportate

**Giochi e Personaggi:**
- 🎮 **Ace Attorney** → `aceattorney.fandom.com`
- 🗡️ **The Legend of Zelda** → `zelda.fandom.com`
- 🍄 **Super Mario** → `mario.fandom.com`
- ⚡ **Pokémon** → `pokemon.fandom.com`
- 👾 **Metroid** → `metroid.fandom.com`
- ⚔️ **Fire Emblem** → `fireemblem.fandom.com`
- 🌌 **Xenoblade Chronicles** → `xenoblade.fandom.com`
- ⭐ **Kirby** → `kirby.fandom.com`
- 🦍 **Donkey Kong** → `donkeykong.fandom.com`
- 🏝️ **Animal Crossing** → `animalcrossing.fandom.com`
- 🦊 **Star Fox** → `starfox.fandom.com`
- 🏎️ **F-Zero** → `fzero.fandom.com`
- 🥚 **Yoshi** → `yoshi.fandom.com`
- 💰 **Wario** → `wario.fandom.com`
- 🌱 **Pikmin** → `pikmin.fandom.com`
- 🎨 **Splatoon** → `splatoon.fandom.com`
- 🏛️ **Kid Icarus** → `kidicarus.fandom.com`
- 🎮 **Game & Watch** → `gameandwatch.fandom.com`
- 🥊 **Punch-Out!!** → `punch-out.fandom.com`
- 🎵 **Rhythm Heaven** → `rhythmheaven.fandom.com`
- 🎭 **Persona / Shin Megami Tensei** → `megamitensei.fandom.com`

**Console Nintendo:**
- 🎮 **Console Nintendo** → `nintendo.fandom.com` (Switch, Wii U, 3DS, DS, GameCube, N64, SNES, NES, Game Boy, ecc.)

### Funzionalità

- ✅ **Scraping Intelligente**: Estrae 15 paragrafi e 5 liste di default per risposte concise
- ✅ **Approfondimento su Richiesta**: Chiedi "approfondisci" o "dimmi di più" per estrarre tutto il contenuto dalla stessa pagina
- ✅ **Sintesi AI**: L'AI sintetizza automaticamente il contenuto estratto per generare risposte complete e ben formattate
- ✅ **Estrazione Immagini**: Recupera automaticamente la prima immagine significativa del personaggio/gioco
- ✅ **Normalizzazione Nomi**: Gestisce automaticamente varianti comuni (es. "luigi mansion" → "Luigi's Mansion")
- ✅ **Varianti URL**: Prova automaticamente diverse varianti di URL per trovare la pagina corretta anche con errori di digitazione
- ✅ **Rilevamento Automatico**: Riconosce automaticamente la serie dalla query (es. "chi è meta knight?" → Kirby)
- ✅ **Nomi Composti**: Supporta nomi composti come "Meta Knight", "King Dedede", "Captain Falcon"
- ✅ **Priorità Personaggi**: Rileva prima i personaggi, poi i giochi per evitare falsi positivi
- ✅ **Fallback Intelligente**: Se Fandom non è disponibile, usa ricerca web tradizionale

### Esempi di Query Supportate

- "chi è Meta Knight?" → `https://kirby.fandom.com/wiki/Meta_Knight`
- "mi parli di Godot da Ace Attorney?" → `https://aceattorney.fandom.com/wiki/Godot`
- "Persona 5" → `https://megamitensei.fandom.com/wiki/Persona_5`
- "Nintendo Switch" → `https://nintendo.fandom.com/wiki/Nintendo_Switch`
- "chi è Tom Nook?" → `https://animalcrossing.fandom.com/wiki/Tom_Nook`

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
- **Nessun timeout**: Il sistema aspetta finché Ollama non risponde (anche se lento)
- **Logging tempi**: Tutti i tempi di risposta vengono loggati nel terminale
- **Modalità fast**: Messaggi colloquiali come "ciao" hanno risposte ottimizzate (5-10 sec invece di 30-40 sec)
- **Immagini Fandom**: Le immagini dei personaggi vengono estratte automaticamente da Fandom quando disponibili

## 📄 Licenza

Questo progetto è open source e disponibile per uso personale ed educativo.

## 🤝 Contribuire

Contributi sono benvenuti! Sentiti libero di aprire issue o pull request.

---

**Buon gaming! 🎮✨**
