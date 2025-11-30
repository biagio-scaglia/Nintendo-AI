"""Servizio per ricerca web quando le informazioni non sono disponibili localmente"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
import re

logger = logging.getLogger(__name__)

def search_web_game_info(game_title: str, query: str = "") -> Optional[str]:
    """
    Cerca informazioni su un gioco/personaggio Nintendo su internet.
    Restituisce una stringa con informazioni trovate o None.
    """
    try:
        # Costruisci query di ricerca - includi info generali (uscita, piattaforma)
        base_query = f"{game_title} Nintendo"
        if not query:
            # Aggiungi termini per info generali (data uscita, piattaforma, sviluppatore)
            search_query = f"{base_query} release date platform developer"
        else:
            search_query = f"{base_query} {query}"
        
        # Usa DuckDuckGo Instant Answer API (più affidabile)
        api_url = "https://api.duckduckgo.com/"
        params = {
            'q': search_query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(api_url, params=params, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            
            # Prova a estrarre AbstractText
            if data.get('AbstractText'):
                abstract = data.get('AbstractText', '')
                if any(keyword in abstract.lower() for keyword in ['nintendo', 'switch', 'wii', '3ds', 'game']):
                    return abstract[:500]
            
            # Se non c'è AbstractText, prova con RelatedTopics
            if data.get('RelatedTopics'):
                for topic in data.get('RelatedTopics', [])[:2]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        text = topic.get('Text', '')
                        if any(keyword in text.lower() for keyword in ['nintendo', 'switch', 'wii', '3ds', 'game']):
                            return text[:500]
        
        # Fallback: ricerca Google (semplice, senza API key)
        # Nota: questo è un fallback base, potrebbe non funzionare sempre
        try:
            google_url = "https://www.google.com/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {'q': search_query}
            response = requests.get(google_url, params=params, headers=headers, timeout=8)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Cerca snippet nei risultati
                snippets = soup.find_all('span', class_='aCOpRe')
                for snippet in snippets[:2]:
                    text = snippet.get_text(strip=True)
                    if text and len(text) > 50:
                        return text[:500]
        except:
            pass  # Ignora errori nel fallback
        
        return None
        
    except Exception as e:
        logger.warning(f"Errore nella ricerca web per {game_title}: {str(e)}")
        return None

def get_web_context(game_title: str, additional_query: str = "") -> Optional[str]:
    """
    Ottiene contesto da web per un gioco quando non disponibile localmente.
    Restituisce una stringa formattata con informazioni trovate.
    """
    web_info = search_web_game_info(game_title, additional_query)
    
    if web_info:
        return f"""
🌐 INFORMAZIONI TROVATE SU INTERNET PER "{game_title}":

{web_info}

⚠️ NOTA: Queste informazioni provengono da ricerche web e potrebbero non essere completamente accurate.
Usa queste informazioni con cautela e menziona all'utente che sono informazioni generali trovate online.
"""
    return None

def extract_entity_name(query: str) -> str:
    """
    Estrae il nome dell'entità (gioco/personaggio) dalla query.
    Es: "chi è yoshi?" -> "yoshi"
    """
    query_lower = query.lower().strip()
    
    # Rimuovi frasi comuni
    phrases_to_remove = [
        "chi è", "cos'è", "cosa è", "chi e", "cos e", "cosa e",
        "dimmi di", "parlami di", "info su", "informazioni su",
        "raccontami di", "spiegami", "che cos'è", "che cosa è"
    ]
    
    for phrase in phrases_to_remove:
        if phrase in query_lower:
            # Estrai tutto dopo la frase
            parts = query_lower.split(phrase, 1)
            if len(parts) > 1:
                entity = parts[1].strip()
                # Rimuovi punteggiatura finale
                entity = entity.rstrip("?.,!;:")
                return entity.strip()
    
    # Se non trova frasi, prova a estrarre la prima parola significativa
    words = query_lower.split()
    if words:
        return words[0].rstrip("?.,!;:")
    
    return query_lower

def search_game_image(game_title: str) -> Optional[str]:
    """
    Funzionalità immagini rimossa - restituisce sempre None.
    """
    return None

def get_web_game_info(game_title: str, query: str = "") -> Optional[Dict]:
    """
    Cerca informazioni su un gioco/personaggio su internet e restituisce un dict strutturato
    simile a GameInfo per essere passato al frontend.
    """
    # Estrai il nome pulito dall'input
    clean_name = extract_entity_name(game_title)
    if not clean_name:
        clean_name = game_title
    
    web_info = search_web_game_info(clean_name, query)
    
    if not web_info:
        return None
    
    # Estrai piattaforma se menzionata (solo per giochi)
    platform = "Nintendo"  # Default più generico per personaggi
    if "switch" in web_info.lower():
        platform = "Nintendo Switch"
    elif "wii u" in web_info.lower() or "wiiu" in web_info.lower():
        platform = "Nintendo Wii U"
    elif "3ds" in web_info.lower():
        platform = "Nintendo 3DS"
    elif "wii" in web_info.lower() and "wii u" not in web_info.lower():
        platform = "Nintendo Wii"
    elif "ds" in web_info.lower() and "3ds" not in web_info.lower():
        platform = "Nintendo DS"
    
    # Usa il nome pulito come titolo
    title = clean_name.title() if clean_name else game_title
    
    # Crea un dict strutturato simile a GameInfo
    return {
        "title": title,
        "platform": platform,
        "description": web_info[:400] if len(web_info) > 400 else web_info,  # Descrizione più lunga
        "gameplay": web_info,  # Usa tutto il testo come gameplay
        "difficulty": "N/A",  # Non disponibile da web
        "modes": [],  # Non disponibile da web
        "keywords": []  # Potremmo estrarli ma per ora vuoto
    }

