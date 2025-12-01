import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "user_memory.json")

def load_memory() -> Dict:
    """Carica la memoria dell'utente dal file JSON"""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading memory: {e}")
    
    # Ritorna struttura vuota se non esiste o errore
    return {
        "user_name": "",
        "preferences": {
            "favorite_games": [],
            "favorite_genres": [],
            "favorite_platforms": [],
            "preferred_difficulty": [],
            "mood_preferences": []
        },
        "favorites": [],  # Lista di giochi salvati nei preferiti
        "mentioned_games": [],
        "provided_info": [],
        "conversation_history": [],
        "last_updated": None
    }

def save_memory(memory: Dict):
    """Salva la memoria dell'utente nel file JSON"""
    try:
        # Assicurati che la directory esista
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        
        memory["last_updated"] = datetime.now().isoformat()
        
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        
        logger.info("Memory saved successfully")
    except Exception as e:
        logger.error(f"Error saving memory: {e}")

def extract_game_names(text: str) -> List[str]:
    """Estrae nomi di giochi dal testo"""
    # Lista di giochi Nintendo comuni per matching
    common_games = [
        "zelda", "mario", "pokemon", "metroid", "kirby", "donkey kong",
        "animal crossing", "splatoon", "fire emblem", "xenoblade",
        "super smash bros", "mario kart", "luigi's mansion", "paper mario",
        "pikmin", "star fox", "f-zero", "earthbound", "mother",
        "mario sports mix", "mario sports", "mario party", "mario tennis"
    ]
    
    text_lower = text.lower()
    found_games = []
    
    # Cerca giochi comuni (match più lungo per primi)
    sorted_games = sorted(common_games, key=len, reverse=True)
    for game in sorted_games:
        if game in text_lower:
            # Estrai il nome completo dal testo originale mantenendo la capitalizzazione
            pattern = re.compile(re.escape(game), re.IGNORECASE)
            matches = pattern.finditer(text)
            for match in matches:
                start, end = match.span()
                # Prova a estrarre il nome completo (parole vicine)
                words = text[max(0, start-20):min(len(text), end+20)].split()
                # Cerca pattern "Mario Sports Mix" o simili
                game_name = text[max(0, start):min(len(text), end+30)].strip()
                # Pulisci il nome
                game_name = re.sub(r'^(salva|metti|aggiungi|segna)\s+', '', game_name, flags=re.IGNORECASE).strip()
                if game_name and len(game_name) > 2:
                    found_games.append(game_name)
    
    # Cerca pattern come "salva X" o "X" dopo verbi di salvataggio
    save_patterns = [
        r'(?:salva|metti|aggiungi|segna)\s+([A-Z][a-zA-Z\s]+?)(?:\s+nei|\s+ai|\s+come|$)',
        r'([A-Z][a-zA-Z\s]{3,}?)(?:\s+nei\s+preferiti|\s+ai\s+preferiti)',
    ]
    
    for pattern in save_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match and len(match.strip()) > 2:
                found_games.append(match.strip())
    
    # Rimuovi duplicati mantenendo l'ordine
    seen = set()
    unique_games = []
    for game in found_games:
        game_lower = game.lower()
        if game_lower not in seen:
            seen.add(game_lower)
            unique_games.append(game)
    
    return unique_games

def extract_preferences_from_text(text: str) -> Dict:
    """Estrae preferenze dall'input dell'utente"""
    text_lower = text.lower()
    preferences = {
        "genres": [],
        "platforms": [],
        "difficulty": [],
        "mood": []
    }
    
    # Generi
    genres = {
        "avventura": ["avventura", "adventure", "avventuroso"],
        "azione": ["azione", "action", "azione"],
        "rpg": ["rpg", "ruolo", "role playing"],
        "platform": ["platform", "platformer", "saltare"],
        "puzzle": ["puzzle", "rompicapo"],
        "racing": ["racing", "corse", "correre"],
        "strategia": ["strategia", "strategy", "tattico"]
    }
    
    for genre, keywords in genres.items():
        if any(kw in text_lower for kw in keywords):
            preferences["genres"].append(genre)
    
    # Piattaforme
    platforms = {
        "switch": ["switch", "nintendo switch"],
        "3ds": ["3ds", "3d s"],
        "wii u": ["wii u", "wiiu"],
        "wii": ["wii"],
        "ds": ["ds", "nintendo ds"]
    }
    
    for platform, keywords in platforms.items():
        if any(kw in text_lower for kw in keywords):
            preferences["platforms"].append(platform)
    
    # Difficoltà
    if any(word in text_lower for word in ["facile", "easy", "semplice", "principiante"]):
        preferences["difficulty"].append("facile")
    if any(word in text_lower for word in ["difficile", "hard", "sfida", "challenging"]):
        preferences["difficulty"].append("difficile")
    if any(word in text_lower for word in ["medio", "medium", "normale"]):
        preferences["difficulty"].append("medio")
    
    # Mood
    mood_keywords = {
        "rilassante": ["rilassante", "relax", "tranquillo", "calm"],
        "energico": ["energico", "energetic", "attivo"],
        "competitivo": ["competitivo", "competitive", "sfida"],
        "sociale": ["sociale", "social", "amici", "multiplayer"]
    }
    
    for mood, keywords in mood_keywords.items():
        if any(kw in text_lower for kw in keywords):
            preferences["mood"].append(mood)
    
    return preferences

def update_memory_from_conversation(user_message: str, ai_response: str, game_info: Optional[Dict] = None, recommended_game: Optional[Dict] = None):
    """Aggiorna la memoria basandosi sulla conversazione"""
    memory = load_memory()
    
    # Estrai giochi menzionati
    games_mentioned = extract_game_names(user_message + " " + ai_response)
    for game in games_mentioned:
        if game not in memory["mentioned_games"]:
            memory["mentioned_games"].append(game)
    
    # Aggiungi gioco raccomandato se presente
    if recommended_game and recommended_game.get("title"):
        game_title = recommended_game.get("title")
        if game_title not in memory["mentioned_games"]:
            memory["mentioned_games"].append(game_title)
    
    # Estrai preferenze dal messaggio dell'utente
    prefs = extract_preferences_from_text(user_message)
    
    # Aggiorna preferenze
    for genre in prefs["genres"]:
        if genre not in memory["preferences"]["favorite_genres"]:
            memory["preferences"]["favorite_genres"].append(genre)
    
    for platform in prefs["platforms"]:
        if platform not in memory["preferences"]["favorite_platforms"]:
            memory["preferences"]["favorite_platforms"].append(platform)
    
    for difficulty in prefs["difficulty"]:
        if difficulty not in memory["preferences"]["preferred_difficulty"]:
            memory["preferences"]["preferred_difficulty"].append(difficulty)
    
    for mood in prefs["mood"]:
        if mood not in memory["preferences"]["mood_preferences"]:
            memory["preferences"]["mood_preferences"].append(mood)
    
    # Salva informazioni fornite (se c'è game_info)
    if game_info:
        info_entry = {
            "title": game_info.get("title", ""),
            "platform": game_info.get("platform", ""),
            "timestamp": datetime.now().isoformat(),
            "description": game_info.get("description", "")[:200]  # Limita lunghezza
        }
        # Evita duplicati
        existing = [i for i in memory["provided_info"] if i.get("title") == info_entry["title"]]
        if not existing:
            memory["provided_info"].append(info_entry)
    
    # Salva ultima conversazione (solo ultimi 10 scambi per non appesantire)
    conversation_entry = {
        "user": user_message[:500],  # Limita lunghezza
        "ai": ai_response[:500],
        "timestamp": datetime.now().isoformat()
    }
    memory["conversation_history"].append(conversation_entry)
    # Mantieni solo ultimi 10 scambi
    if len(memory["conversation_history"]) > 10:
        memory["conversation_history"] = memory["conversation_history"][-10:]
    
    save_memory(memory)
    logger.info("Memory updated from conversation")

def get_personalization_context() -> str:
    """Genera un contesto di personalizzazione basato sulla memoria"""
    memory = load_memory()
    
    if not memory.get("mentioned_games") and not memory.get("preferences"):
        return ""  # Nessuna memoria, niente personalizzazione
    
    context_parts = []
    
    # Giochi menzionati/preferiti
    if memory.get("mentioned_games"):
        games = ", ".join(memory["mentioned_games"][:5])  # Max 5 giochi
        context_parts.append(f"🎮 Giochi menzionati/preferiti dall'utente: {games}")
    
    # Preferenze di genere
    if memory.get("preferences", {}).get("favorite_genres"):
        genres = ", ".join(memory["preferences"]["favorite_genres"])
        context_parts.append(f"📚 Generi preferiti: {genres}")
    
    # Piattaforme preferite
    if memory.get("preferences", {}).get("favorite_platforms"):
        platforms = ", ".join(memory["preferences"]["favorite_platforms"])
        context_parts.append(f"🎯 Piattaforme preferite: {platforms}")
    
    # Difficoltà preferita
    if memory.get("preferences", {}).get("preferred_difficulty"):
        difficulty = ", ".join(memory["preferences"]["preferred_difficulty"])
        context_parts.append(f"⚙️ Difficoltà preferita: {difficulty}")
    
    # Mood preferiti
    if memory.get("preferences", {}).get("mood_preferences"):
        moods = ", ".join(memory["preferences"]["mood_preferences"])
        context_parts.append(f"💭 Mood preferiti: {moods}")
    
    if context_parts:
        return "\n".join([
            "═══════════════════════════════════════════════════════════════",
            "📝 MEMORIA E PREFERENZE DELL'UTENTE",
            "═══════════════════════════════════════════════════════════════",
            "",
            "\n".join(context_parts),
            "",
            "⚠️ ISTRUZIONI PER LA PERSONALIZZAZIONE:",
            "- Usa queste informazioni per personalizzare le tue risposte",
            "- Riferisciti ai giochi già menzionati se rilevanti",
            "- Considera le preferenze dell'utente quando consigli giochi",
            "- Mostra che ricordi le conversazioni precedenti",
            "- Sii naturale: non elencare tutte le preferenze, usale nel contesto"
        ])
    
    return ""

def clear_memory():
    """Cancella tutta la memoria dell'utente"""
    try:
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
        logger.info("Memory cleared")
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")

def detect_save_favorite_intent(user_message: str) -> bool:
    """Rileva se l'utente vuole salvare qualcosa nei preferiti"""
    message_lower = user_message.lower()
    save_keywords = [
        "segna nei preferiti", "salva nei preferiti", "aggiungi ai preferiti",
        "metti nei preferiti", "aggiungi preferiti", "salva preferito",
        "segna come preferito", "salva questo", "aggiungi questo",
        "voglio salvare", "salvami", "preferiti"
    ]
    return any(keyword in message_lower for keyword in save_keywords)

def save_to_favorites(game_title: str, game_info: Optional[Dict] = None):
    """Salva un gioco nei preferiti"""
    memory = load_memory()
    
    if "favorites" not in memory:
        memory["favorites"] = []
    
    # Controlla se già esiste
    existing = [f for f in memory["favorites"] if f.get("title", "").lower() == game_title.lower()]
    if existing:
        logger.info(f"Game {game_title} already in favorites")
        return False
    
    favorite_entry = {
        "title": game_title,
        "timestamp": datetime.now().isoformat(),
        "platform": game_info.get("platform", "") if game_info else "",
        "description": game_info.get("description", "")[:150] if game_info else "",
    }
    
    memory["favorites"].append(favorite_entry)
    save_memory(memory)
    logger.info(f"Saved {game_title} to favorites")
    return True

def set_user_name(name: str):
    """Imposta il nome utente"""
    memory = load_memory()
    memory["user_name"] = name.strip()
    save_memory(memory)
    logger.info(f"User name set to: {name}")

def get_user_profile() -> Dict:
    """Ottiene il profilo completo dell'utente"""
    memory = load_memory()
    return {
        "user_name": memory.get("user_name", ""),
        "favorites": memory.get("favorites", []),
        "preferences": memory.get("preferences", {}),
        "mentioned_games": memory.get("mentioned_games", []),
        "total_conversations": len(memory.get("conversation_history", [])),
    }

def generate_personality_report() -> str:
    """Genera un resoconto della personalità dell'utente basato sulle conversazioni"""
    memory = load_memory()
    
    if not memory.get("conversation_history") and not memory.get("favorites"):
        return "Non ci sono ancora abbastanza dati per generare un resoconto. Inizia a chattare e salva alcuni giochi nei preferiti!"
    
    report_parts = []
    
    # Analisi preferiti
    favorites = memory.get("favorites", [])
    if favorites:
        report_parts.append(f"🎮 Hai salvato {len(favorites)} giochi nei preferiti:")
        for fav in favorites[:5]:
            report_parts.append(f"   • {fav.get('title', 'Sconosciuto')}")
    
    # Analisi generi preferiti
    genres = memory.get("preferences", {}).get("favorite_genres", [])
    if genres:
        report_parts.append(f"\n📚 I tuoi generi preferiti: {', '.join(genres)}")
    
    # Analisi mood
    moods = memory.get("preferences", {}).get("mood_preferences", [])
    if moods:
        report_parts.append(f"\n💭 Preferisci giochi: {', '.join(moods)}")
    
    # Analisi piattaforme
    platforms = memory.get("preferences", {}).get("favorite_platforms", [])
    if platforms:
        report_parts.append(f"\n🎯 Le tue piattaforme preferite: {', '.join(platforms)}")
    
    # Analisi difficoltà
    difficulty = memory.get("preferences", {}).get("preferred_difficulty", [])
    if difficulty:
        report_parts.append(f"\n⚙️ Preferisci difficoltà: {', '.join(difficulty)}")
    
    # Analisi conversazioni
    conversations = len(memory.get("conversation_history", []))
    if conversations > 0:
        report_parts.append(f"\n💬 Hai avuto {conversations} conversazioni con l'assistente")
    
    # Conclusione
    if not report_parts:
        return "Non ci sono ancora abbastanza dati per generare un resoconto."
    
    report = "\n".join(report_parts)
    report += "\n\n✨ Continua a esplorare giochi e salva quelli che ti piacciono per un resoconto più dettagliato!"
    
    return report

