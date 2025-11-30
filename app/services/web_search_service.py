"""Servizio per ricerca web quando le informazioni non sono disponibili localmente"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
import logging
import re
import urllib.parse

logger = logging.getLogger(__name__)

def detect_fandom_series(entity_name: str, query: str = "") -> Optional[Tuple[str, str]]:
    """
    Rileva la serie Nintendo e restituisce (fandom_name, character_name).
    Es: ("aceattorney", "Godot"), ("zelda", "Mipha")
    """
    entity_lower = entity_name.lower().strip()
    query_lower = query.lower() if query else ""
    combined = f"{entity_lower} {query_lower}".lower()
    
    # Ace Attorney - controlla prima nella query per serie esplicite
    ace_attorney_series_keywords = ["ace attorney", "phoenix wright", "saga di ace attorney", 
                                    "da ace attorney", "in ace attorney"]
    ace_attorney_chars = ["godot", "maya fey", "miles edgeworth", "apollo justice", "franziska", 
                         "dahlia", "iris", "trucy", "athena", "phoenix", "edgeworth", "gumshoe"]
    
    # Se la query menziona esplicitamente Ace Attorney, usa quella serie
    if any(kw in query_lower for kw in ace_attorney_series_keywords):
        char_name = entity_name.strip()
        # Capitalizza correttamente (prima lettera maiuscola, resto minuscolo)
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("aceattorney", char_name)
    
    # Altrimenti controlla se il personaggio è di Ace Attorney
    if any(kw in combined for kw in ace_attorney_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("aceattorney", char_name)
    
    # Zelda
    zelda_series_keywords = ["zelda", "the legend of zelda", "saga di zelda", "da zelda"]
    zelda_chars = ["link", "ganon", "ganondorf", "mipha", "urbosa", "revali", "daruk", 
                   "sidon", "impa", "paya", "riju", "yunobo", "tulin", "princess zelda", 
                   "hyrule", "sheikah", "gerudo", "zora", "rito", "goron"]
    if any(kw in query_lower for kw in zelda_series_keywords) or any(kw in combined for kw in zelda_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("zelda", char_name)
    
    # Mario
    mario_series_keywords = ["mario", "super mario", "saga di mario", "da mario"]
    mario_chars = ["luigi", "peach", "daisy", "rosalina", "yoshi", "wario", "waluigi", 
                   "toad", "bowser", "koopa", "donkey kong", "diddy kong"]
    if any(kw in query_lower for kw in mario_series_keywords) or any(kw in combined for kw in mario_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("mario", char_name)
    
    # Pokemon
    pokemon_series_keywords = ["pokemon", "pokémon", "saga di pokemon", "da pokemon"]
    pokemon_chars = ["pikachu", "charizard", "mewtwo", "ash", "misty", "brock", "trainer", "gym leader"]
    if any(kw in query_lower for kw in pokemon_series_keywords) or any(kw in combined for kw in pokemon_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("pokemon", char_name)
    
    # Metroid
    metroid_series_keywords = ["metroid", "saga di metroid", "da metroid"]
    metroid_chars = ["samus", "ridley", "mother brain"]
    if any(kw in query_lower for kw in metroid_series_keywords) or any(kw in combined for kw in metroid_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("metroid", char_name)
    
    # Fire Emblem
    fire_emblem_series_keywords = ["fire emblem", "saga di fire emblem", "da fire emblem"]
    fire_emblem_chars = ["marth", "ike", "lucina", "robin", "corrin", "byleth"]
    if any(kw in query_lower for kw in fire_emblem_series_keywords) or any(kw in combined for kw in fire_emblem_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("fireemblem", char_name)
    
    # Xenoblade
    xenoblade_series_keywords = ["xenoblade", "saga di xenoblade", "da xenoblade"]
    xenoblade_chars = ["shulk", "rex", "pyra", "mythra"]
    if any(kw in query_lower for kw in xenoblade_series_keywords) or any(kw in combined for kw in xenoblade_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("xenoblade", char_name)
    
    return None

def scrape_fandom_page(fandom_name: str, character_name: str) -> Optional[str]:
    """
    Fa scraping di una pagina Fandom e estrae il contenuto principale.
    Prova diverse varianti del nome se la prima non funziona.
    """
    # Prova diverse varianti del nome
    name_variants = [
        character_name,  # Nome originale
        character_name.replace(" ", "_"),  # Con underscore
        character_name.title(),  # Title case
        character_name.title().replace(" ", "_"),  # Title case con underscore
    ]
    
    for char_url in name_variants:
        try:
            # Costruisci l'URL Fandom
            url = f"https://{fandom_name}.fandom.com/wiki/{urllib.parse.quote(char_url)}"
            
            logger.info(f"Tentativo di accesso a Fandom: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Rimuovi elementi non necessari
                for element in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                    element.decompose()
                
                # Cerca il contenuto principale della pagina
                # Fandom usa diverse strutture, proviamo vari selettori
                content_selectors = [
                    'div.mw-parser-output',
                    'div#content',
                    'article',
                    'div.page-content'
                ]
                
                content_text = ""
                for selector in content_selectors:
                    content_div = soup.select_one(selector)
                    if content_div:
                        # Estrai solo i paragrafi principali (evita infobox, tabelle, ecc.)
                        paragraphs = content_div.find_all('p', limit=10)  # Primi 10 paragrafi
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if len(text) > 50:  # Solo paragrafi significativi
                                content_text += text + " "
                        
                        if len(content_text) > 200:  # Abbiamo abbastanza contenuto
                            break
                
                # Se non abbiamo trovato abbastanza contenuto, prova a prendere tutto il testo principale
                if len(content_text) < 200:
                    main_content = soup.find('div', class_='mw-parser-output') or soup.find('div', id='content')
                    if main_content:
                        # Rimuovi infobox e altri elementi laterali
                        for infobox in main_content.find_all(['aside', 'table', 'div'], class_=re.compile(r'infobox|sidebar')):
                            infobox.decompose()
                        
                        content_text = main_content.get_text(separator=' ', strip=True)
                
                # Pulisci il testo
                content_text = re.sub(r'\s+', ' ', content_text)  # Rimuovi spazi multipli
                content_text = content_text.strip()
                
                if len(content_text) > 100:
                    logger.info(f"✅ Contenuto Fandom estratto: {len(content_text)} caratteri")
                    return content_text[:2000]  # Limita a 2000 caratteri
                else:
                    logger.warning(f"Contenuto Fandom troppo corto: {len(content_text)} caratteri")
                    # Prova la prossima variante
                    continue
                    
            elif response.status_code == 404:
                logger.warning(f"Pagina Fandom non trovata (404): {url}, provo variante successiva...")
                continue  # Prova la prossima variante
            else:
                logger.warning(f"Errore HTTP {response.status_code} per {url}, provo variante successiva...")
                continue  # Prova la prossima variante
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout durante l'accesso a Fandom: {url}, provo variante successiva...")
            continue  # Prova la prossima variante
        except Exception as e:
            logger.warning(f"Errore durante lo scraping di Fandom per {url}: {str(e)}, provo variante successiva...")
            continue  # Prova la prossima variante
    
    # Se nessuna variante ha funzionato
    logger.warning(f"Nessuna variante del nome ha funzionato per {character_name} su {fandom_name}.fandom.com")
    return None

def search_web_game_info(game_title: str, query: str = "") -> Optional[str]:
    """
    Cerca informazioni su un gioco/personaggio Nintendo su internet.
    Prima prova Fandom, poi fallback su DuckDuckGo/Google.
    Restituisce una stringa con informazioni trovate o None.
    """
    try:
        # Estrai il nome dell'entità
        entity_name = extract_entity_name(game_title)
        if not entity_name:
            entity_name = game_title.strip()
        
        # PRIMA PRIORITÀ: Prova Fandom
        fandom_info = detect_fandom_series(entity_name, query)
        if fandom_info:
            fandom_name, character_name = fandom_info
            logger.info(f"Rilevata serie Fandom: {fandom_name} per personaggio: {character_name}")
            
            fandom_content = scrape_fandom_page(fandom_name, character_name)
            if fandom_content:
                logger.info(f"✅ Informazioni trovate su Fandom per {character_name}")
                return fandom_content
        
        # FALLBACK: Se Fandom non funziona, usa DuckDuckGo/Google
        logger.info(f"Fandom non disponibile, uso ricerca tradizionale per: {entity_name}")
        
        # Costruisci query di ricerca più specifica
        base_query = entity_name.strip()
        
        # Rileva se è un personaggio di Zelda
        zelda_chars = ["zelda", "link", "ganon", "ganondorf", "mipha", "urbosa", "revali", "daruk", "sidon", "impa", "paya", "riju", "yunobo", "tulin"]
        mario_chars = ["mario", "luigi", "peach", "daisy", "rosalina", "yoshi", "wario", "waluigi", "toad", "bowser", "koopa"]
        pokemon_chars = ["pikachu", "charizard", "mewtwo", "ash", "misty", "brock"]
        
        if any(char in base_query.lower() for char in zelda_chars):
            base_query = f"{base_query} Zelda character Nintendo"
        elif any(char in base_query.lower() for char in mario_chars):
            base_query = f"{base_query} Mario character Nintendo"
        elif any(char in base_query.lower() for char in pokemon_chars):
            base_query = f"{base_query} Pokemon character Nintendo"
        else:
            base_query = f"{base_query} Nintendo"
        
        if not query:
            search_query = f"{base_query} character game"
        else:
            search_query = f"{base_query} {query}"
        
        # Usa DuckDuckGo Instant Answer API
        api_url = "https://api.duckduckgo.com/"
        params = {
            'q': search_query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('AbstractText'):
                abstract = data.get('AbstractText', '')
                abstract_lower = abstract.lower()
                if any(keyword in abstract_lower for keyword in ['nintendo', 'switch', 'wii', '3ds', 'game', 'zelda', 'mario', 'pokemon', 'character', 'princess', 'principessa']):
                    if len(abstract) > 50:
                        return abstract[:500]
            
            if data.get('RelatedTopics'):
                for topic in data.get('RelatedTopics', [])[:3]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        text = topic.get('Text', '')
                        text_lower = text.lower()
                        if any(keyword in text_lower for keyword in ['nintendo', 'switch', 'wii', '3ds', 'game', 'zelda', 'mario', 'pokemon', 'character']):
                            if len(text) > 50:
                                return text[:500]
        
        # Fallback finale: ricerca Google
        try:
            google_url = "https://www.google.com/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {'q': search_query}
            response = requests.get(google_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                snippets = soup.find_all('span', class_='aCOpRe') or soup.find_all('div', class_='VwiC3b') or soup.find_all('span', class_='st')
                for snippet in snippets[:3]:
                    text = snippet.get_text(strip=True)
                    if text and len(text) > 50:
                        text_lower = text.lower()
                        if any(keyword in text_lower for keyword in ['nintendo', 'zelda', 'mario', 'pokemon', 'character', 'game', 'princess', 'principessa']):
                            return text[:500]
        except:
            pass
        
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

