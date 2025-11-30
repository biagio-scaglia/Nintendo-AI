"""Servizio per ricerca web quando le informazioni non sono disponibili localmente"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
import logging
import re
import urllib.parse

logger = logging.getLogger(__name__)

def format_game_name_for_fandom(game_name: str) -> str:
    """
    Formatta il nome del gioco per l'URL Fandom.
    Es: "Phoenix Wright: Ace Attorney - Trials and Tribulations" -> "Phoenix_Wright:_Ace_Attorney_-_Trials_and_Tribulations"
    """
    # Sostituisci spazi con underscore, mantieni due punti e trattini
    formatted = game_name.replace(" ", "_")
    return formatted

def detect_fandom_game(game_name: str, query: str = "") -> Optional[Tuple[str, str]]:
    """
    Rileva se è un gioco Nintendo e restituisce (fandom_name, formatted_game_name).
    Es: ("aceattorney", "Phoenix_Wright:_Ace_Attorney_-_Trials_and_Tribulations")
    """
    game_lower = game_name.lower().strip()
    query_lower = query.lower() if query else ""
    combined = f"{game_lower} {query_lower}".lower()
    
    # Ace Attorney games
    ace_attorney_game_keywords = [
        "phoenix wright", "ace attorney", "trials and tribulations", "justice for all",
        "apollo justice", "dual destinies", "spirit of justice", "investigations",
        "the great ace attorney", "adventures", "resolve", "turnabout", "gyakuten saiban"
    ]
    # Controlla anche se contiene "ace attorney" o "phoenix wright" nel nome
    if "ace attorney" in game_lower or "phoenix wright" in game_lower:
        formatted_name = format_game_name_for_fandom(game_name)
        return ("aceattorney", formatted_name)
    if any(kw in combined for kw in ace_attorney_game_keywords):
        formatted_name = format_game_name_for_fandom(game_name)
        return ("aceattorney", formatted_name)
    
    # Zelda games
    zelda_game_keywords = [
        "the legend of zelda", "breath of the wild", "tears of the kingdom",
        "ocarina of time", "majora's mask", "wind waker", "twilight princess",
        "skyward sword", "a link to the past", "a link between worlds"
    ]
    if any(kw in combined for kw in zelda_game_keywords):
        formatted_name = format_game_name_for_fandom(game_name)
        return ("zelda", formatted_name)
    
    # Mario games
    mario_game_keywords = [
        "super mario", "mario kart", "mario party", "mario odyssey",
        "mario galaxy", "mario sunshine", "paper mario", "mario & luigi"
    ]
    if any(kw in combined for kw in mario_game_keywords):
        formatted_name = format_game_name_for_fandom(game_name)
        return ("mario", formatted_name)
    
    # Pokemon games
    pokemon_game_keywords = [
        "pokemon", "pokémon", "red", "blue", "yellow", "gold", "silver",
        "ruby", "sapphire", "diamond", "pearl", "black", "white", "sun", "moon",
        "sword", "shield", "scarlet", "violet"
    ]
    if any(kw in combined for kw in pokemon_game_keywords):
        formatted_name = format_game_name_for_fandom(game_name)
        return ("pokemon", formatted_name)
    
    return None

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
    
    # Mapping per nomi completi dei personaggi (nome corto -> nome completo su Fandom)
    ace_attorney_full_names = {
        "gumshoe": "Dick Gumshoe",
        "phoenix": "Phoenix Wright",
        "edgeworth": "Miles Edgeworth",
        "maya": "Maya Fey",
        "apollo": "Apollo Justice",
        "franziska": "Franziska von Karma",
        "dahlia": "Dahlia Hawthorne",
        "iris": "Iris",
        "trucy": "Trucy Wright",
        "athena": "Athena Cykes"
    }
    
    # Se la query menziona esplicitamente Ace Attorney, usa quella serie
    if any(kw in query_lower for kw in ace_attorney_series_keywords):
        char_name = entity_name.strip()
        # Controlla se c'è un nome completo nel mapping
        if char_name.lower() in ace_attorney_full_names:
            char_name = ace_attorney_full_names[char_name.lower()]
        else:
            # Capitalizza correttamente (prima lettera maiuscola, resto minuscolo)
            char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("aceattorney", char_name)
    
    # Altrimenti controlla se il personaggio è di Ace Attorney
    if any(kw in combined for kw in ace_attorney_chars):
        char_name = entity_name.strip()
        # Controlla se c'è un nome completo nel mapping
        if char_name.lower() in ace_attorney_full_names:
            char_name = ace_attorney_full_names[char_name.lower()]
        else:
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

def scrape_fandom_page(fandom_name: str, page_name: str, is_game: bool = False) -> Optional[tuple]:
    """
    Fa scraping di una pagina Fandom e estrae il contenuto principale e la prima immagine.
    Prova diverse varianti del nome se la prima non funziona.
    
    Args:
        fandom_name: Nome del fandom (es. "aceattorney", "zelda")
        page_name: Nome della pagina (personaggio o gioco già formattato)
        is_game: Se True, è un gioco (usa formattazione diversa)
    
    Returns:
        Tuple (content: str, image_url: Optional[str]) o None se non trovato
    """
    # Per i giochi, usa il nome già formattato, per i personaggi prova varianti
    if is_game:
        name_variants = [page_name]  # I giochi hanno già il formato corretto
    else:
        # Prova diverse varianti del nome per personaggi
        name_variants = [
            page_name,  # Nome originale
            page_name.replace(" ", "_"),  # Con underscore
            page_name.title(),  # Title case
            page_name.title().replace(" ", "_"),  # Title case con underscore
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
                
                # Estrai la prima immagine PRIMA di rimuovere gli elementi
                image_url = None
                
                # Cerca immagini nell'infobox (spesso contiene l'immagine principale)
                infobox = soup.find('aside', class_=re.compile(r'infobox|portable-infobox'))
                if infobox:
                    img = infobox.find('img')
                    if img and img.get('src'):
                        src = img.get('src')
                        # Filtra placeholder, base64 vuoti, e immagini troppo piccole
                        if (src and 
                            not src.startswith('data:image') and 
                            not '1x1' in src.lower() and
                            not 'pixel' in src.lower() and
                            len(src) > 20):
                            image_url = src
                            # Se è un URL relativo, convertilo in assoluto
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            elif image_url.startswith('/'):
                                image_url = f'https://{fandom_name}.fandom.com' + image_url
                            logger.info(f"Immagine trovata nell'infobox: {image_url}")
                
                # Se non trovata nell'infobox, cerca nella pagina principale
                if not image_url:
                    main_content_temp = soup.find('div', class_='mw-parser-output') or soup.find('div', id='content')
                    if main_content_temp:
                        # Cerca la prima immagine significativa (non icone, non piccole)
                        images = main_content_temp.find_all('img')
                        for img in images:
                            src = img.get('src', '')
                            # Evita immagini troppo piccole, icone, o decorative
                            width = img.get('width', '')
                            height = img.get('height', '')
                            if (src and 
                                not src.startswith('data:image') and 
                                not '1x1' in src.lower() and
                                not 'pixel' in src.lower() and
                                len(src) > 20 and
                                not any(skip in src.lower() for skip in ['icon', 'logo', 'button', 'arrow', 'thumb'])):
                                # Preferisci immagini più grandi
                                if width and height:
                                    try:
                                        w = int(str(width).replace('px', ''))
                                        h = int(str(height).replace('px', ''))
                                        if w > 100 and h > 100:  # Almeno 100x100px
                                            image_url = src
                                            if image_url.startswith('//'):
                                                image_url = 'https:' + image_url
                                            elif image_url.startswith('/'):
                                                image_url = f'https://{fandom_name}.fandom.com' + image_url
                                            logger.info(f"Immagine trovata nella pagina: {image_url}")
                                            break
                                    except:
                                        pass
                                else:
                                    # Se non ha dimensioni specificate, prova comunque (ma solo se non è placeholder)
                                    image_url = src
                                    if image_url.startswith('//'):
                                        image_url = 'https:' + image_url
                                    elif image_url.startswith('/'):
                                        image_url = f'https://{fandom_name}.fandom.com' + image_url
                                    logger.info(f"Immagine trovata nella pagina (senza dimensioni): {image_url}")
                                    break
                
                # Rimuovi elementi non necessari (nav, header, footer, script, style, infobox, tabelle, note, riferimenti)
                for element in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style', 
                                             'table', 'div'], class_=re.compile(r'infobox|sidebar|navbox|reference|notelist|mw-references-wrap')):
                    element.decompose()
                
                # Rimuovi anche sezioni non rilevanti
                for section in soup.find_all(['div', 'section'], class_=re.compile(r'toc|table-of-contents|catlinks|printfooter')):
                    section.decompose()
                
                # Cerca il contenuto principale della pagina
                main_content = soup.find('div', class_='mw-parser-output')
                if not main_content:
                    main_content = soup.find('div', id='content')
                if not main_content:
                    main_content = soup.find('article')
                
                if main_content:
                    # Rimuovi ulteriori elementi non necessari dal contenuto principale
                    for unwanted in main_content.find_all(['aside', 'table', 'div', 'section'], 
                                                       class_=re.compile(r'infobox|sidebar|navbox|reference|notelist|toc|catlinks|printfooter|gallery')):
                        unwanted.decompose()
                    
                    # Rimuovi anche link esterni e note a piè di pagina
                    for ref in main_content.find_all(['sup', 'span'], class_=re.compile(r'reference|cite')):
                        ref.decompose()
                    
                    # Estrai paragrafi principali in ordine (primi 15 per più accuratezza)
                    paragraphs = main_content.find_all('p', limit=15)
                    content_text = ""
                    
                    for p in paragraphs:
                        # Rimuovi note e riferimenti dai paragrafi
                        for ref in p.find_all(['sup', 'span'], class_=re.compile(r'reference|cite')):
                            ref.decompose()
                        
                        text = p.get_text(separator=' ', strip=True)
                        # Filtra paragrafi troppo corti o non significativi
                        if len(text) > 80 and not re.match(r'^[\d\s\[\]()]+$', text):  # Evita paragrafi solo numeri/simboli
                            content_text += text + " "
                    
                    # Se non abbiamo abbastanza contenuto dai paragrafi, prendi anche le liste
                    if len(content_text) < 300:
                        lists = main_content.find_all(['ul', 'ol'], limit=5)
                        for ul in lists:
                            # Evita liste di navigazione o riferimenti
                            if not ul.find_parent(['nav', 'aside', 'div'], class_=re.compile(r'nav|sidebar|reference')):
                                list_text = ul.get_text(separator=' ', strip=True)
                                if len(list_text) > 50:
                                    content_text += list_text + " "
                    
                    # Pulisci il testo finale in modo più accurato
                    content_text = re.sub(r'\[\d+\]', '', content_text)  # Rimuovi riferimenti numerici [1], [2], ecc.
                    content_text = re.sub(r'\[edit\]', '', content_text, flags=re.IGNORECASE)  # Rimuovi link [edit]
                    content_text = re.sub(r'\[citation needed\]', '', content_text, flags=re.IGNORECASE)  # Rimuovi [citation needed]
                    content_text = re.sub(r'See also:.*?\.', '', content_text, flags=re.IGNORECASE | re.DOTALL)  # Rimuovi "See also:" sections
                    content_text = re.sub(r'Main article:.*?\.', '', content_text, flags=re.IGNORECASE | re.DOTALL)  # Rimuovi "Main article:" links
                    content_text = re.sub(r'\s+', ' ', content_text)  # Rimuovi spazi multipli
                    content_text = re.sub(r'\.{2,}', '.', content_text)  # Rimuovi punti multipli
                    content_text = content_text.strip()
                    
                    # Rimuovi frasi incomplete o troppo corte all'inizio/fine
                    sentences = content_text.split('.')
                    cleaned_sentences = []
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 20:  # Solo frasi significative
                            cleaned_sentences.append(sentence)
                    content_text = '. '.join(cleaned_sentences)
                    if content_text and not content_text.endswith('.'):
                        content_text += '.'
                    
                    if len(content_text) > 150:
                        logger.info(f"✅ Contenuto Fandom estratto: {len(content_text)} caratteri")
                        if image_url:
                            logger.info(f"✅ Immagine trovata: {image_url}")
                        return (content_text[:3000], image_url)  # Restituisce tupla (contenuto, image_url)
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
    logger.warning(f"Nessuna variante del nome ha funzionato per {page_name} su {fandom_name}.fandom.com")
    return None

def search_web_game_info(game_title: str, query: str = "") -> tuple:
    """
    Cerca informazioni su un gioco/personaggio Nintendo su internet.
    Prima prova Fandom, poi fallback su DuckDuckGo/Google.
    Restituisce una tupla (contenuto: str, image_url: Optional[str]) o (None, None) se non trovato.
    """
    try:
        # Estrai il nome dell'entità
        entity_name = extract_entity_name(game_title)
        if not entity_name:
            entity_name = game_title.strip()
        
        # PRIMA PRIORITÀ: Prova Fandom per GIOCHI
        fandom_game_info = detect_fandom_game(entity_name, query)
        if fandom_game_info:
            fandom_name, formatted_game_name = fandom_game_info
            logger.info(f"Rilevato gioco Fandom: {fandom_name} - {formatted_game_name}")
            
            fandom_result = scrape_fandom_page(fandom_name, formatted_game_name, is_game=True)
            if fandom_result:
                fandom_content, image_url = fandom_result
                logger.info(f"✅ Informazioni trovate su Fandom per gioco: {formatted_game_name}")
                return (fandom_content, image_url)
        
        # SECONDA PRIORITÀ: Prova Fandom per PERSONAGGI
        fandom_info = detect_fandom_series(entity_name, query)
        if fandom_info:
            fandom_name, character_name = fandom_info
            logger.info(f"Rilevata serie Fandom: {fandom_name} per personaggio: {character_name}")
            
            fandom_result = scrape_fandom_page(fandom_name, character_name, is_game=False)
            if fandom_result:
                fandom_content, image_url = fandom_result
                logger.info(f"✅ Informazioni trovate su Fandom per {character_name}")
                return (fandom_content, image_url)
        
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
                            return (text[:500], None)  # Restituisce tupla (contenuto, None per immagine)
        except:
            pass
        
        return (None, None)
        
    except Exception as e:
        logger.warning(f"Errore nella ricerca web per {game_title}: {str(e)}")
        return (None, None)

def get_web_context(game_title: str, additional_query: str = "") -> Optional[str]:
    """
    Ottiene contesto da web per un gioco quando non disponibile localmente.
    Restituisce una stringa formattata con informazioni trovate.
    """
    web_info, _ = search_web_game_info(game_title, additional_query)  # Ignora immagine nel contesto
    
    if web_info:
        return f"""
🌐 INFORMAZIONI TROVATE SU INTERNET PER "{game_title}":

{web_info}

⚠️ NOTA: Queste informazioni provengono da ricerche web e potrebbero non essere completamente accurate.
Usa queste informazioni con cautela e menziona all'utente che sono informazioni generali trovate online.
"""
    return None

def get_web_image_url(game_title: str, query: str = "") -> Optional[str]:
    """
    Ottiene l'URL dell'immagine da Fandom per un personaggio/gioco.
    """
    _, image_url = search_web_game_info(game_title, query)
    return image_url

def extract_entity_name(query: str) -> str:
    """
    Estrae il nome dell'entità (gioco/personaggio) dalla query.
    Es: "chi è yoshi?" -> "yoshi"
    Es: "mi parli di godot in ace attorney" -> "godot"
    """
    query_lower = query.lower().strip()
    
    # Rimuovi frasi comuni
    phrases_to_remove = [
        "chi è", "cos'è", "cosa è", "chi e", "cos e", "cosa e",
        "dimmi di", "parlami di", "mi parli di", "info su", "informazioni su",
        "raccontami di", "spiegami", "che cos'è", "che cosa è", "dimmi informazioni su"
    ]
    
    for phrase in phrases_to_remove:
        if phrase in query_lower:
            # Estrai tutto dopo la frase
            parts = query_lower.split(phrase, 1)
            if len(parts) > 1:
                entity = parts[1].strip()
                # Rimuovi eventuali frasi successive come "in ace attorney", "della saga", ecc.
                # Prendi solo la prima parte (il nome del personaggio)
                entity = entity.split(" in ")[0].split(" della ")[0].split(" da ")[0].split(" di ")[0]
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
    
    web_info, image_url = search_web_game_info(clean_name, query)
    
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
        "keywords": [],  # Potremmo estrarli ma per ora vuoto
        "image_url": image_url  # URL dell'immagine da Fandom
    }

