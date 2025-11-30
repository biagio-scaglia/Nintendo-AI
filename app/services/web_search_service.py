"""Servizio per ricerca web quando le informazioni non sono disponibili localmente"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import logging
import re

logger = logging.getLogger(__name__)

def search_web_game_info(game_title: str, query: str = "") -> Optional[str]:
    """
    Cerca informazioni su un gioco Nintendo su internet.
    Restituisce una stringa con informazioni trovate o None.
    """
    try:
        # Costruisci query di ricerca
        search_query = f"{game_title} Nintendo game" if not query else f"{game_title} {query} Nintendo"
        
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

