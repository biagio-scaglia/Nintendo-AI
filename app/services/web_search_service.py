"""Servizio per ricerca web quando le informazioni non sono disponibili localmente"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple
import logging
import re
import urllib.parse

logger = logging.getLogger(__name__)

def normalize_game_name(game_name: str) -> str:
    """
    Normalizza il nome del gioco per gestire varianti comuni in modo generico.
    Gestisce apostrofi mancanti, punteggiatura, "&" vs "and", ecc.
    Es: "luigi mansion" -> "Luigi's Mansion", "mario and luigi" -> "Mario & Luigi"
    """
    game_lower = game_name.lower().strip()
    
    # Mappatura specifica per giochi con nomi particolari (solo per casi speciali)
    specific_mappings = {
        "luigi mansion": "Luigi's Mansion",
        "luigis mansion": "Luigi's Mansion",
        "luigi mansion 3": "Luigi's Mansion 3",
        "luigis mansion 3": "Luigi's Mansion 3",
        "luigi mansion dark moon": "Luigi's Mansion: Dark Moon",
        "luigis mansion dark moon": "Luigi's Mansion: Dark Moon",
        "luigi mansion 2": "Luigi's Mansion: Dark Moon",
        "luigis mansion 2": "Luigi's Mansion: Dark Moon",
        "super mario bros": "Super Mario Bros.",
        "super mario bros 3": "Super Mario Bros. 3",
        "the legend of zelda": "The Legend of Zelda",
        "zelda breath of the wild": "The Legend of Zelda: Breath of the Wild",
        "zelda tears of the kingdom": "The Legend of Zelda: Tears of the Kingdom",
        "zelda ocarina of time": "The Legend of Zelda: Ocarina of Time",
    }
    
    # Controlla mappature specifiche
    if game_lower in specific_mappings:
        return specific_mappings[game_lower]
    
    # Normalizzazione generica
    words = game_lower.split()
    normalized_words = []
    skip_next = False
    
    # Nomi propri comuni che possono avere apostrofi
    proper_names = ["luigi", "mario", "zelda", "link", "yoshi", "wario", "waluigi", "peach", "daisy", "rosalina", "bowser", "toad"]
    
    i = 0
    while i < len(words):
        if skip_next:
            skip_next = False
            i += 1
            continue
            
        word = words[i]
        
        # Gestisci "and" -> "&" per nomi come "Mario and Luigi"
        if word == "and" and i > 0 and i < len(words) - 1:
            # Controlla se è un caso comune come "mario and luigi"
            if words[i-1] in proper_names and words[i+1] in proper_names:
                normalized_words.append("&")
                i += 1
                continue
        
        # Gestisci apostrofi mancanti: "luigis" -> "Luigi's"
        # Pattern: nome + "s" (senza apostrofo) -> nome + "'s"
        found_apostrophe_fix = False
        for name in proper_names:
            if word == name + "s":
                # È un nome con 's' aggiunta senza apostrofo (es. "luigis")
                normalized_words.append(name.capitalize() + "'s")
                found_apostrophe_fix = True
                break
        
        if found_apostrophe_fix:
            i += 1
            continue
        
        # Gestisci pattern "nome s parola" -> "nome's parola" (es. "luigi s mansion")
        if i > 0 and i < len(words) - 1:
            prev_word = words[i-1]
            if word == "s" and prev_word in proper_names:
                # Pattern trovato: "nome s parola"
                # Rimuovi l'ultima parola aggiunta (il nome senza apostrofo) e aggiungi con apostrofo
                if normalized_words and normalized_words[-1].lower() == prev_word:
                    normalized_words[-1] = prev_word.capitalize() + "'s"
                else:
                    normalized_words.append(prev_word.capitalize() + "'s")
                skip_next = True  # Salta la parola "s"
                i += 1
                continue
        
        # Capitalizza la prima lettera di ogni parola
        if word:
            normalized_words.append(word.capitalize())
        
        i += 1
    
    result = " ".join(normalized_words)
    
    # Gestisci punteggiatura comune
    result = re.sub(r'\bBros\b', 'Bros.', result, flags=re.IGNORECASE)
    result = re.sub(r'\bVs\b', 'vs.', result, flags=re.IGNORECASE)
    
    # Rimuovi spazi multipli
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Se il risultato è troppo diverso dall'originale o vuoto, usa title case semplice
    if not result or len(result) < 3:
        return game_name.strip().title()
    
    return result

def format_game_name_for_fandom(game_name: str) -> str:
    """
    Formatta il nome del gioco per l'URL Fandom.
    Es: "Phoenix Wright: Ace Attorney - Trials and Tribulations" -> "Phoenix_Wright:_Ace_Attorney_-_Trials_and_Tribulations"
    Prima normalizza il nome per gestire varianti comuni.
    """
    # Normalizza prima
    normalized = normalize_game_name(game_name)
    # Sostituisci spazi con underscore, mantieni due punti, trattini e apostrofi
    formatted = normalized.replace(" ", "_")
    return formatted

def detect_fandom_game(game_name: str, query: str = "") -> Optional[Tuple[str, str]]:
    """
    Rileva se è un gioco Nintendo e restituisce (fandom_name, formatted_game_name).
    Es: ("aceattorney", "Phoenix_Wright:_Ace_Attorney_-_Trials_and_Tribulations")
    Prima normalizza il nome per gestire varianti comuni.
    """
    # Normalizza il nome del gioco prima di controllare i keyword
    normalized_game_name = normalize_game_name(game_name)
    game_lower = normalized_game_name.lower().strip()
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
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("aceattorney", formatted_name)
    if any(kw in combined for kw in ace_attorney_game_keywords):
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("aceattorney", formatted_name)
    
    # Zelda games
    zelda_game_keywords = [
        "the legend of zelda", "breath of the wild", "tears of the kingdom",
        "ocarina of time", "majora's mask", "wind waker", "twilight princess",
        "skyward sword", "a link to the past", "a link between worlds"
    ]
    if any(kw in combined for kw in zelda_game_keywords):
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("zelda", formatted_name)
    
    # Mario games
    mario_game_keywords = [
        "super mario", "mario kart", "mario party", "mario odyssey",
        "mario galaxy", "mario sunshine", "paper mario", "mario & luigi",
        "luigi mansion", "luigis mansion", "luigi's mansion",  # Aggiunto per Luigi's Mansion
        "mario bros", "mario world", "mario 64", "mario 3d"
    ]
    if any(kw in combined for kw in mario_game_keywords):
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("mario", formatted_name)
    
    # Pokemon games
    pokemon_game_keywords = [
        "pokemon", "pokémon", "red", "blue", "yellow", "gold", "silver",
        "ruby", "sapphire", "diamond", "pearl", "black", "white", "sun", "moon",
        "sword", "shield", "scarlet", "violet"
    ]
    if any(kw in combined for kw in pokemon_game_keywords):
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("pokemon", formatted_name)
    
    # Persona e Shin Megami Tensei games
    persona_smt_game_keywords = [
        "persona", "shin megami tensei", "megami tensei", "smt", "persona 3", "persona 4", "persona 5",
        "persona 5 royal", "persona 4 golden", "nocturne", "shin megami tensei v", "smt v",
        "shin megami tensei iii", "persona q", "persona q2"
    ]
    # Controlla anche se contiene "persona" o "shin megami tensei" o "smt" nel nome
    if ("persona" in game_lower or "shin megami tensei" in game_lower or "megami tensei" in game_lower or 
        ("smt" in game_lower and len(game_lower.split()) <= 3)):  # "smt" da solo o con poche parole
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("megamitensei", formatted_name)
    if any(kw in combined for kw in persona_smt_game_keywords):
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("megamitensei", formatted_name)
    
    # Kirby games
    if "kirby" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("kirby", formatted_name)
    
    # Donkey Kong games
    if "donkey kong" in game_lower or "diddy kong" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("donkeykong", formatted_name)
    
    # Animal Crossing games
    if "animal crossing" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("animalcrossing", formatted_name)
    
    # Star Fox games
    if "star fox" in game_lower or "starfox" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("starfox", formatted_name)
    
    # F-Zero games
    if "f-zero" in game_lower or "fzero" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("fzero", formatted_name)
    
    # Yoshi games
    if "yoshi" in game_lower and "mario" not in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("yoshi", formatted_name)
    
    # Wario games
    if "wario" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("wario", formatted_name)
    
    # Pikmin games
    if "pikmin" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("pikmin", formatted_name)
    
    # Splatoon games
    if "splatoon" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("splatoon", formatted_name)
    
    # Kid Icarus games
    if "kid icarus" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("kidicarus", formatted_name)
    
    # Game & Watch
    if "game & watch" in game_lower or "game and watch" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("gameandwatch", formatted_name)
    
    # Punch-Out!! games
    if "punch-out" in game_lower or "punch out" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("punch-out", formatted_name)
    
    # Rhythm Heaven games
    if "rhythm heaven" in game_lower:
        formatted_name = format_game_name_for_fandom(normalized_game_name)
        return ("rhythmheaven", formatted_name)
    
    # Nintendo consoles (nintendo.fandom.com)
    nintendo_console_keywords = [
        "nintendo switch", "nintendo switch 2", "nintendo switch lite", "nintendo switch oled",
        "wii u", "wii", "nintendo 3ds", "nintendo ds", "gamecube", "nintendo 64", "n64",
        "super nintendo", "snes", "nes", "game boy", "game boy advance", "game boy color"
    ]
    if any(kw in combined for kw in nintendo_console_keywords):
        formatted_name = format_game_name_for_fandom(game_name)
        return ("nintendo", formatted_name)
    
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
    
    # Persona e Shin Megami Tensei
    persona_smt_series_keywords = ["persona", "shin megami tensei", "megami tensei", "saga di persona", 
                                   "da persona", "in persona", "smt", "shin megami"]
    persona_smt_chars = [
        "joker", "yu narukami", "makoto yuki", "aigis", "yukari", "mitsuru", "akihiko", "ken",
        "yukiko", "chie", "rise", "naoto", "kanji", "teddie", "ann", "ryuji", "morgana",
        "yusuke", "makoto", "haru", "futaba", "goro", "kasumi", "sumire", "demifiend",
        "flynn", "nanashi", "nahobino", "minato", "kotone"
    ]
    if any(kw in query_lower for kw in persona_smt_series_keywords):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("megamitensei", char_name)
    
    if any(kw in combined for kw in persona_smt_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("megamitensei", char_name)
    
    # Kirby
    kirby_series_keywords = ["kirby", "saga di kirby", "da kirby"]
    kirby_chars = ["kirby", "meta knight", "king dedede", "bandana waddle dee", "adeleine", "ribbon"]
    # Mapping per nomi composti Kirby
    kirby_full_names = {
        "meta knight": "Meta Knight",
        "king dedede": "King Dedede",
        "bandana waddle dee": "Bandana Waddle Dee"
    }
    if any(kw in query_lower for kw in kirby_series_keywords) or any(kw in combined for kw in kirby_chars):
        char_name = entity_name.strip().lower()
        # Controlla se c'è un nome completo nel mapping
        if char_name in kirby_full_names:
            char_name = kirby_full_names[char_name]
        else:
            # Capitalizza ogni parola (title case)
            char_name = entity_name.strip().title()
        return ("kirby", char_name)
    
    # Donkey Kong
    donkey_kong_series_keywords = ["donkey kong", "saga di donkey kong", "da donkey kong"]
    donkey_kong_chars = ["donkey kong", "diddy kong", "dixie kong", "cranky kong", "funky kong", "k rool"]
    donkey_kong_full_names = {
        "donkey kong": "Donkey Kong",
        "diddy kong": "Diddy Kong",
        "dixie kong": "Dixie Kong",
        "cranky kong": "Cranky Kong",
        "funky kong": "Funky Kong",
        "k rool": "King K. Rool"
    }
    if any(kw in query_lower for kw in donkey_kong_series_keywords) or any(kw in combined for kw in donkey_kong_chars):
        char_name = entity_name.strip().lower()
        if char_name in donkey_kong_full_names:
            char_name = donkey_kong_full_names[char_name]
        else:
            char_name = entity_name.strip().title()
        return ("donkeykong", char_name)
    
    # Animal Crossing
    animal_crossing_series_keywords = ["animal crossing", "saga di animal crossing", "da animal crossing"]
    animal_crossing_chars = ["tom nook", "isabelle", "k.k. slider", "blathers", "celeste", "flick", "cj"]
    animal_crossing_full_names = {
        "tom nook": "Tom Nook",
        "k.k. slider": "K.K. Slider",
        "k.k slider": "K.K. Slider"
    }
    if any(kw in query_lower for kw in animal_crossing_series_keywords) or any(kw in combined for kw in animal_crossing_chars):
        char_name = entity_name.strip().lower()
        if char_name in animal_crossing_full_names:
            char_name = animal_crossing_full_names[char_name]
        else:
            char_name = entity_name.strip().title()
        return ("animalcrossing", char_name)
    
    # Star Fox
    star_fox_series_keywords = ["star fox", "starfox", "saga di star fox", "da star fox"]
    star_fox_chars = ["fox", "falco", "peppy", "slippy", "wolf", "leon", "pigma", "andross"]
    star_fox_full_names = {
        "fox": "Fox McCloud",
        "falco": "Falco Lombardi",
        "peppy": "Peppy Hare",
        "slippy": "Slippy Toad"
    }
    if any(kw in query_lower for kw in star_fox_series_keywords) or any(kw in combined for kw in star_fox_chars):
        char_name = entity_name.strip().lower()
        if char_name in star_fox_full_names:
            char_name = star_fox_full_names[char_name]
        else:
            char_name = entity_name.strip().title()
        return ("starfox", char_name)
    
    # F-Zero
    fzero_series_keywords = ["f-zero", "fzero", "saga di f-zero", "da f-zero"]
    fzero_chars = ["captain falcon", "samurai goroh", "pico", "black shadow"]
    fzero_full_names = {
        "captain falcon": "Captain Falcon",
        "samurai goroh": "Samurai Goroh",
        "black shadow": "Black Shadow"
    }
    if any(kw in query_lower for kw in fzero_series_keywords) or any(kw in combined for kw in fzero_chars):
        char_name = entity_name.strip().lower()
        if char_name in fzero_full_names:
            char_name = fzero_full_names[char_name]
        else:
            char_name = entity_name.strip().title()
        return ("fzero", char_name)
    
    # Yoshi (separato da Mario)
    yoshi_series_keywords = ["yoshi", "saga di yoshi", "da yoshi"]
    yoshi_chars = ["yoshi", "baby mario", "baby luigi", "poochy"]
    if any(kw in query_lower for kw in yoshi_series_keywords) or any(kw in combined for kw in yoshi_chars):
        # Solo se non è già rilevato come Mario
        if "mario" not in query_lower and "mario" not in entity_lower:
            char_name = entity_name.strip()
            char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
            return ("yoshi", char_name)
    
    # Wario
    wario_series_keywords = ["wario", "saga di wario", "da wario"]
    wario_chars = ["wario", "waluigi", "captain syrup", "ashley"]
    if any(kw in query_lower for kw in wario_series_keywords) or any(kw in combined for kw in wario_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("wario", char_name)
    
    # Pikmin
    pikmin_series_keywords = ["pikmin", "saga di pikmin", "da pikmin"]
    pikmin_chars = ["olimar", "louie", "alph", "brittany", "charlie", "pikmin"]
    if any(kw in query_lower for kw in pikmin_series_keywords) or any(kw in combined for kw in pikmin_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("pikmin", char_name)
    
    # Splatoon
    splatoon_series_keywords = ["splatoon", "saga di splatoon", "da splatoon"]
    splatoon_chars = ["inkling", "octoling", "marie", "callie", "pearl", "marina", "agent 3", "agent 4", "agent 8"]
    if any(kw in query_lower for kw in splatoon_series_keywords) or any(kw in combined for kw in splatoon_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("splatoon", char_name)
    
    # Kid Icarus
    kid_icarus_series_keywords = ["kid icarus", "saga di kid icarus", "da kid icarus"]
    kid_icarus_chars = ["pit", "palutena", "medusa", "viridi", "hades", "dark pit"]
    if any(kw in query_lower for kw in kid_icarus_series_keywords) or any(kw in combined for kw in kid_icarus_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("kidicarus", char_name)
    
    # Punch-Out!!
    punchout_series_keywords = ["punch-out", "punch out", "saga di punch-out", "da punch-out"]
    punchout_chars = ["little mac", "doc louis", "mike tyson", "glass joe", "king hippo"]
    if any(kw in query_lower for kw in punchout_series_keywords) or any(kw in combined for kw in punchout_chars):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("punch-out", char_name)
    
    # Rhythm Heaven
    rhythm_heaven_series_keywords = ["rhythm heaven", "saga di rhythm heaven", "da rhythm heaven"]
    if any(kw in query_lower for kw in rhythm_heaven_series_keywords):
        char_name = entity_name.strip()
        char_name = char_name[0].upper() + char_name[1:].lower() if len(char_name) > 1 else char_name.upper()
        return ("rhythmheaven", char_name)
    
    return None

def scrape_fandom_page(fandom_name: str, page_name: str, is_game: bool = False, deep_scrape: bool = False) -> Optional[tuple]:
    """
    Fa scraping di una pagina Fandom e estrae il contenuto principale e la prima immagine.
    Prova diverse varianti del nome se la prima non funziona.
    
    Args:
        fandom_name: Nome del fandom (es. "aceattorney", "zelda")
        page_name: Nome della pagina (personaggio o gioco già formattato)
        is_game: Se True, è un gioco (usa formattazione diversa)
        deep_scrape: Se True, estrae tutto il contenuto. Se False, limita a 15 paragrafi e 5 liste
    
    Returns:
        Tuple (content: str, image_url: Optional[str]) o None se non trovato
    """
    # Genera varianti del nome per provare diverse combinazioni
    # Per i giochi, prova anche varianti con/senza apostrofi, numeri, ecc.
    if is_game:
        # Per i giochi, prova diverse varianti per gestire errori di digitazione e varianti comuni
        base_name = page_name.replace("_", " ").replace("%27", "'")  # Decodifica base
        
        # Genera varianti intelligenti
        name_variants = []
        
        # 1. Nome originale formattato
        name_variants.append(page_name)
        
        # 2. Base con underscore
        name_variants.append(base_name.replace(" ", "_"))
        
        # 3. Varianti con/senza apostrofi
        if "'" in base_name or "'s" in base_name:
            # Con apostrofo
            name_variants.append(base_name.replace(" ", "_"))
            # Senza apostrofo
            name_variants.append(base_name.replace("'", "").replace(" ", "_"))
            # Apostrofo -> s (es. "Luigi's" -> "Luigis")
            name_variants.append(base_name.replace("'s", "s").replace("'", "").replace(" ", "_"))
            # Spazio prima di 's (es. "Luigi s" -> "Luigi's")
            name_variants.append(base_name.replace(" s ", "'s ").replace(" s", "'s").replace(" ", "_"))
        else:
            # Se non c'è apostrofo, prova ad aggiungerlo in posizioni comuni
            # Pattern: "nome s parola" -> "nome's parola" (es. "luigi s mansion" -> "luigi's mansion")
            words = base_name.split()
            for i in range(len(words) - 1):
                if words[i].lower() in ["luigi", "mario", "zelda", "link", "yoshi", "wario", "waluigi", "peach", "daisy", "rosalina"]:
                    if words[i+1].lower().startswith('s') and len(words[i+1]) > 1:
                        # C'è già una 's', prova con apostrofo
                        variant_words = words.copy()
                        variant_words[i] = variant_words[i] + "'s"
                        variant_words[i+1] = variant_words[i+1][1:]  # Rimuovi la 's'
                        name_variants.append("_".join(variant_words))
                    elif not words[i].endswith("'s") and not words[i].endswith("s"):
                        # Prova ad aggiungere 's
                        variant_words = words.copy()
                        variant_words[i] = variant_words[i] + "'s"
                        name_variants.append("_".join(variant_words))
        
        # 4. Varianti con punteggiatura
        # Gestisci "Bros" -> "Bros."
        if "bros" in base_name.lower():
            name_variants.append(base_name.replace("Bros", "Bros.").replace("bros", "Bros.").replace(" ", "_"))
            name_variants.append(base_name.replace("Bros.", "Bros").replace("bros.", "Bros").replace(" ", "_"))
        
        # 5. Varianti con "&" vs "and"
        if "&" in base_name:
            name_variants.append(base_name.replace("&", "and").replace(" ", "_"))
        if " and " in base_name.lower():
            name_variants.append(base_name.replace(" and ", "_&_").replace(" And ", "_&_").replace(" ", "_"))
        
        # 6. Title case varianti
        title_base = base_name.title()
        name_variants.append(title_base.replace(" ", "_"))
        if "'" in title_base:
            name_variants.append(title_base.replace("'", "").replace(" ", "_"))
            name_variants.append(title_base.replace("'s", "s").replace("'", "").replace(" ", "_"))
        
        # 7. URL encoding dell'apostrofo
        for variant in name_variants[:]:  # Copia la lista per iterare
            if "'" in variant:
                name_variants.append(variant.replace("'", "%27"))
        
        # Rimuovi duplicati mantenendo l'ordine
        seen = set()
        unique_variants = []
        for variant in name_variants:
            if variant and variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        name_variants = unique_variants
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
                            image_url = src.strip()  # Rimuovi whitespace e newline
                            # Se è un URL relativo, convertilo in assoluto
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            elif image_url.startswith('/'):
                                image_url = f'https://{fandom_name}.fandom.com' + image_url
                            # Rimuovi eventuali newline o spazi dall'URL
                            image_url = image_url.replace('\n', '').replace('\r', '').replace(' ', '')
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
                                            image_url = src.strip()  # Rimuovi whitespace e newline
                                            if image_url.startswith('//'):
                                                image_url = 'https:' + image_url
                                            elif image_url.startswith('/'):
                                                image_url = f'https://{fandom_name}.fandom.com' + image_url
                                            # Rimuovi eventuali newline o spazi dall'URL
                                            image_url = image_url.replace('\n', '').replace('\r', '').replace(' ', '')
                                            logger.info(f"Immagine trovata nella pagina: {image_url}")
                                            break
                                    except:
                                        pass
                                else:
                                    # Se non ha dimensioni specificate, prova comunque (ma solo se non è placeholder)
                                    image_url = src.strip()  # Rimuovi whitespace e newline
                                    if image_url.startswith('//'):
                                        image_url = 'https:' + image_url
                                    elif image_url.startswith('/'):
                                        image_url = f'https://{fandom_name}.fandom.com' + image_url
                                    # Rimuovi eventuali newline o spazi dall'URL
                                    image_url = image_url.replace('\n', '').replace('\r', '').replace(' ', '')
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
                    
                    # Estrai contenuto della pagina (limitato o completo in base a deep_scrape)
                    content_text = ""
                    
                    if deep_scrape:
                        # Estrai TUTTO il contenuto (per approfondimenti)
                        paragraphs = main_content.find_all('p')
                        for p in paragraphs:
                            # Rimuovi note e riferimenti dai paragrafi
                            for ref in p.find_all(['sup', 'span'], class_=re.compile(r'reference|cite')):
                                ref.decompose()
                            
                            text = p.get_text(separator=' ', strip=True)
                            # Filtra solo paragrafi troppo corti o non significativi
                            if len(text) > 50 and not re.match(r'^[\d\s\[\]()]+$', text):
                                content_text += text + " "
                        
                        # Estrai tutte le liste significative
                        lists = main_content.find_all(['ul', 'ol'])
                        for ul in lists:
                            # Evita liste di navigazione o riferimenti
                            if not ul.find_parent(['nav', 'aside', 'div'], class_=re.compile(r'nav|sidebar|reference')):
                                list_text = ul.get_text(separator=' ', strip=True)
                                if len(list_text) > 30:
                                    content_text += list_text + " "
                        
                        # Estrai anche i contenuti delle sezioni (h2, h3 con contenuto)
                        sections = main_content.find_all(['h2', 'h3'])
                        for section in sections:
                            section_title = section.get_text(strip=True)
                            next_sibling = section.find_next_sibling()
                            if next_sibling and section_title:
                                content_text += f"{section_title}. "
                                section_content = ""
                                current = next_sibling
                                count = 0
                                while current and count < 10:
                                    if current.name in ['h2', 'h3']:
                                        break
                                    if current.name in ['p', 'ul', 'ol']:
                                        text = current.get_text(separator=' ', strip=True)
                                        if len(text) > 30:
                                            section_content += text + " "
                                    current = current.find_next_sibling()
                                    count += 1
                                if section_content:
                                    content_text += section_content[:500] + " "
                    else:
                        # Estrai solo primi 15 paragrafi e 5 liste (default)
                        paragraphs = main_content.find_all('p', limit=15)
                        for p in paragraphs:
                            # Rimuovi note e riferimenti dai paragrafi
                            for ref in p.find_all(['sup', 'span'], class_=re.compile(r'reference|cite')):
                                ref.decompose()
                            
                            text = p.get_text(separator=' ', strip=True)
                            # Filtra paragrafi troppo corti o non significativi
                            if len(text) > 80 and not re.match(r'^[\d\s\[\]()]+$', text):
                                content_text += text + " "
                        
                        # Se non abbiamo abbastanza contenuto, prendi anche le liste
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
                    
                    # Rimuovi frasi incomplete o troppo corte
                    sentences = content_text.split('.')
                    cleaned_sentences = []
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 15:  # Solo frasi significative
                            cleaned_sentences.append(sentence)
                    content_text = '. '.join(cleaned_sentences)
                    if content_text and not content_text.endswith('.'):
                        content_text += '.'
                    
                    # Restituisci il contenuto estratto
                    if len(content_text) > 100:
                        scrape_type = "completo" if deep_scrape else "limitato"
                        logger.info(f"✅ Contenuto {scrape_type} estratto: {len(content_text)} caratteri")
                        if image_url:
                            logger.info(f"✅ Immagine trovata: {image_url}")
                        return (content_text, image_url)
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

def search_web_game_info(game_title: str, query: str = "", deep_scrape: bool = False) -> tuple:
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
        
        # PRIMA PRIORITÀ: Prova Fandom per PERSONAGGI (prima dei giochi, per evitare falsi positivi)
        fandom_info = detect_fandom_series(entity_name, query)
        if fandom_info:
            fandom_name, character_name = fandom_info
            logger.info(f"Rilevata serie Fandom: {fandom_name} per personaggio: {character_name}")
            
            fandom_result = scrape_fandom_page(fandom_name, character_name, is_game=False, deep_scrape=deep_scrape)
            if fandom_result:
                fandom_content, image_url = fandom_result
                logger.info(f"✅ Informazioni trovate su Fandom per {character_name}")
                return (fandom_content, image_url)
        
        # SECONDA PRIORITÀ: Prova Fandom per GIOCHI
        fandom_game_info = detect_fandom_game(entity_name, query)
        if fandom_game_info:
            fandom_name, formatted_game_name = fandom_game_info
            logger.info(f"Rilevato gioco Fandom: {fandom_name} - {formatted_game_name}")
            
            fandom_result = scrape_fandom_page(fandom_name, formatted_game_name, is_game=True, deep_scrape=deep_scrape)
            if fandom_result:
                fandom_content, image_url = fandom_result
                logger.info(f"✅ Informazioni trovate su Fandom per gioco: {formatted_game_name}")
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

def get_web_context(game_title: str, additional_query: str = "", deep_scrape: bool = False) -> Optional[str]:
    """
    Ottiene contesto da web per un gioco quando non disponibile localmente.
    Restituisce una stringa formattata con informazioni trovate.
    
    Args:
        game_title: Nome del gioco/personaggio
        additional_query: Query aggiuntiva per contesto
        deep_scrape: Se True, estrae tutto il contenuto. Se False, limita a 15 paragrafi e 5 liste
    """
    web_info, _ = search_web_game_info(game_title, additional_query, deep_scrape=deep_scrape)  # Ignora immagine nel contesto
    
    if web_info:
        return f"""
🌐 INFORMAZIONI TROVATE SU INTERNET PER "{game_title}":

{web_info}

⚠️ NOTA: Queste informazioni provengono da ricerche web e potrebbero non essere completamente accurate.
Usa queste informazioni con cautela e menziona all'utente che sono informazioni generali trovate online.
"""
    return None

def get_web_image_url(game_title: str, query: str = "", deep_scrape: bool = False) -> Optional[str]:
    """
    Ottiene l'URL dell'immagine da Fandom per un personaggio/gioco.
    """
    _, image_url = search_web_game_info(game_title, query, deep_scrape=deep_scrape)
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
                # Rimuovi eventuali frasi successive come "in ace attorney", "della saga", "da kirby", ecc.
                # Prendi tutto fino a queste frasi (per mantenere nomi composti come "meta knight")
                entity = entity.split(" in ")[0].split(" della ")[0].split(" da ")[0].split(" di ")[0]
                # Rimuovi punteggiatura finale
                entity = entity.rstrip("?.,!;:")
                entity = entity.strip()
                # Se l'entità ha più parole, restituiscila tutta (per nomi composti)
                if entity:
                    return entity
    
    # Se non trova frasi, prova a estrarre le prime parole (fino a 3 per nomi composti)
    words = query_lower.split()
    if words:
        # Prendi fino a 3 parole per supportare nomi composti come "meta knight", "king dedede"
        entity = " ".join(words[:3]).rstrip("?.,!;:")
        return entity.strip()
    
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

