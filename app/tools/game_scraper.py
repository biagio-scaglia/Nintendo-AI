"""
Script per estrarre informazioni sui giochi Nintendo da fonti web
e aggiungerle al database.
"""
import json
import requests
from pathlib import Path
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import time

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
GAME_DETAILS_PATH = BASE_DIR / "app" / "knowledge" / "game_details.json"
NINTENDO_GAMES_PATH = BASE_DIR / "app" / "db" / "nintendo_games.json"
SOURCES_PATH = BASE_DIR / "app" / "tools" / "sources.json"

# Fonti affidabili
TRUSTED_SOURCES = [
    "nintendo.com",
    "nintendo.it",
    "nintendo.co.jp",
    "fandom.com",
    "mariowiki.com",
    "zelda.fandom.com",
    "ssbwiki.com",
    "metroidwiki.org",
    "kirby.fandom.com",
    "nintendolife.com",
    "bulbapedia.bulbagarden.net",
    "serebii.net",
    "ign.com",
    "gamefaqs.gamespot.com",
    "giantbomb.com",
    "mobygames.com",
    "metacritic.com",
    "wikipedia.org",
    "nintendowiki.org",
    "fireemblemwiki.org",
    "xenoblade.fandom.com",
    "splatoonwiki.org",
    "zeldadungeon.net",
    "zeldawiki.wiki"
]

def load_sources() -> List[str]:
    """Carica la lista di fonti salvate."""
    if SOURCES_PATH.exists():
        with open(SOURCES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("sources", [])
    return []

def save_sources(sources: List[str]):
    """Salva la lista di fonti."""
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SOURCES_PATH, "w", encoding="utf-8") as f:
        json.dump({"sources": sources}, f, indent=2, ensure_ascii=False)

def is_trusted_source(url: str) -> bool:
    """Verifica se l'URL proviene da una fonte affidabile."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return any(trusted in domain for trusted in TRUSTED_SOURCES)

def extract_from_fandom_wiki(url: str) -> Optional[Dict]:
    """Estrae informazioni da una pagina Fandom/Wiki."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Estrai titolo
        title_elem = soup.find("h1", class_="page-header__title") or soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Estrai descrizione (primo paragrafo)
        desc_elem = soup.find("div", class_="mw-parser-output") or soup.find("div", id="content")
        description = ""
        if desc_elem:
            paragraphs = desc_elem.find_all("p")
            for p in paragraphs[:3]:
                text = p.get_text(strip=True)
                if len(text) > 50:
                    description = text[:500]
                    break
        
        # Estrai informazioni da infobox
        infobox = soup.find("table", class_="infobox") or soup.find("aside", class_="portable-infobox")
        platform = ""
        if infobox:
            platform_rows = infobox.find_all("tr")
            for row in platform_rows:
                header = row.find("th")
                if header and ("platform" in header.get_text().lower() or "piattaforma" in header.get_text().lower()):
                    data = row.find("td")
                    if data:
                        platform = data.get_text(strip=True)
                        break
        
        if not title:
            return None
        
        return {
            "title": title,
            "platform": platform or "Nintendo Switch",  # Default
            "description": description,
            "source_url": url
        }
    except Exception as e:
        print(f"Errore nell'estrazione da {url}: {e}")
        return None

def extract_from_nintendo_site(url: str) -> Optional[Dict]:
    """Estrae informazioni dal sito ufficiale Nintendo."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Titolo
        title_elem = soup.find("h1") or soup.find("title")
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Descrizione
        desc_elem = soup.find("div", class_="description") or soup.find("p", class_="description")
        description = desc_elem.get_text(strip=True)[:500] if desc_elem else ""
        
        # Piattaforma (di solito è nel path o nel breadcrumb)
        parsed = urlparse(url)
        platform = "Nintendo Switch"  # Default
        if "switch" in parsed.path.lower():
            platform = "Nintendo Switch"
        elif "wii-u" in parsed.path.lower() or "wiiu" in parsed.path.lower():
            platform = "Nintendo Wii U"
        elif "3ds" in parsed.path.lower():
            platform = "Nintendo 3DS"
        elif "ds" in parsed.path.lower():
            platform = "Nintendo DS"
        
        if not title:
            return None
        
        return {
            "title": title,
            "platform": platform,
            "description": description,
            "source_url": url
        }
    except Exception as e:
        print(f"Errore nell'estrazione da {url}: {e}")
        return None

def extract_game_info(url: str) -> Optional[Dict]:
    """Estrae informazioni da un URL di gioco."""
    if not is_trusted_source(url):
        print(f"⚠️ Fonte non verificata: {url}")
        response = input("Continuare comunque? (s/n): ")
        if response.lower() != "s":
            return None
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if "fandom.com" in domain or "wiki" in domain:
        return extract_from_fandom_wiki(url)
    elif "nintendo.com" in domain or "nintendo.it" in domain:
        return extract_from_nintendo_site(url)
    else:
        # Prova estrazione generica
        return extract_from_fandom_wiki(url)

def generate_keywords(title: str, description: str, platform: str) -> List[str]:
    """Genera keywords dal titolo e descrizione."""
    keywords = []
    
    # Aggiungi parole dal titolo
    title_words = re.findall(r'\b\w+\b', title.lower())
    keywords.extend([w for w in title_words if len(w) > 3])
    
    # Aggiungi piattaforma
    platform_lower = platform.lower()
    if "switch" in platform_lower:
        keywords.append("switch")
    elif "wii u" in platform_lower:
        keywords.append("wiiu")
    elif "3ds" in platform_lower:
        keywords.append("3ds")
    elif "ds" in platform_lower:
        keywords.append("ds")
    
    # Aggiungi generi comuni dalla descrizione
    desc_lower = description.lower()
    genre_keywords = {
        "action": ["azione", "action", "combat", "combattimento"],
        "adventure": ["avventura", "adventure", "explore", "esplorazione"],
        "rpg": ["rpg", "ruolo", "role"],
        "platform": ["platform", "platforming", "saltare", "jump"],
        "puzzle": ["puzzle", "rompicapo"],
        "racing": ["racing", "corse", "kart"],
        "strategy": ["strategia", "strategy", "tattico", "tactical"]
    }
    
    for genre, terms in genre_keywords.items():
        if any(term in desc_lower for term in terms):
            keywords.append(genre)
    
    return list(set(keywords))[:10]

def is_list_page(url: str) -> bool:
    """Verifica se l'URL è una pagina lista di giochi."""
    url_lower = url.lower()
    list_indicators = [
        "list_of",
        "category:",
        "/games",
        "/game",
        "elenco",
        "category"
    ]
    return any(indicator in url_lower for indicator in list_indicators)

def extract_game_links_from_list(url: str, max_links: int = 100) -> List[str]:
    """Estrae tutti i link ai giochi da una pagina lista."""
    game_links = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        parsed_base = urlparse(url)
        base_url = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # Cerca link in tabelle, liste, o div con classi comuni
        links = soup.find_all("a", href=True)
        
        for link in links:
            href = link.get("href", "")
            link_text = link.get_text(strip=True)
            
            # Ignora link vuoti o non rilevanti
            if not href or not link_text or len(link_text) < 3:
                continue
            
            # Costruisci URL completo
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = urljoin(base_url, href)
            else:
                full_url = urljoin(url, href)
            
            # Filtra link che sembrano essere giochi
            # Escludi link a categorie, liste, o pagine non-gioco
            exclude_patterns = [
                "list_of", "category:", "category/", "template:", "file:",
                "help:", "special:", "talk:", "user:", "wikipedia:", "wikimedia:",
                "#", "?", "javascript:", "mailto:", "tel:"
            ]
            
            if any(pattern in href.lower() for pattern in exclude_patterns):
                continue
            
            # Include solo link che sembrano essere pagine di giochi
            # (contengono parole chiave o sono da domini affidabili)
            if is_trusted_source(full_url) and len(link_text) > 5:
                # Evita duplicati
                if full_url not in game_links:
                    game_links.append(full_url)
            
            if len(game_links) >= max_links:
                break
        
        return game_links[:max_links]
    except Exception as e:
        print(f"Errore nell'estrazione link da {url}: {e}")
        return []

def auto_extract_from_sources(sources: List[str], max_games_per_source: int = 50, delay: float = 1.0):
    """Estrae automaticamente giochi da tutte le fonti fornite."""
    all_games = []
    processed_urls = set()
    
    print(f"\n🚀 Inizio estrazione automatica da {len(sources)} fonti...")
    print("=" * 70)
    
    for idx, source_url in enumerate(sources, 1):
        print(f"\n[{idx}/{len(sources)}] Processando: {source_url}")
        
        try:
            if is_list_page(source_url):
                print("  📋 Rilevata pagina lista, estraggo link ai giochi...")
                game_links = extract_game_links_from_list(source_url, max_links=max_games_per_source)
                print(f"  ✅ Trovati {len(game_links)} link ai giochi")
                
                for link_idx, game_url in enumerate(game_links, 1):
                    if game_url in processed_urls:
                        continue
                    
                    print(f"    [{link_idx}/{len(game_links)}] Estraggo: {game_url[:60]}...")
                    
                    game_data = extract_game_info(game_url)
                    if game_data and game_data.get("title"):
                        game_data["source_url"] = game_url
                        all_games.append(game_data)
                        processed_urls.add(game_url)
                        print(f"      ✅ Estratto: {game_data.get('title')}")
                    
                    time.sleep(delay)  # Rispetta il server
            else:
                # Prova a estrarre come pagina singola
                print("  📄 Pagina singola, estraggo informazioni...")
                game_data = extract_game_info(source_url)
                if game_data and game_data.get("title"):
                    game_data["source_url"] = source_url
                    all_games.append(game_data)
                    processed_urls.add(source_url)
                    print(f"  ✅ Estratto: {game_data.get('title')}")
                
                time.sleep(delay)
        
        except Exception as e:
            print(f"  ❌ Errore: {e}")
            continue
    
    print(f"\n✅ Estrazione completata! Trovati {len(all_games)} giochi.")
    return all_games

def add_game_to_database(game_data: Dict, auto_fill: bool = False, silent: bool = False):
    """Aggiunge un gioco al database."""
    # Carica game_details.json
    with open(GAME_DETAILS_PATH, "r", encoding="utf-8") as f:
        details_data = json.load(f)
    
    games = details_data.get("games", [])
    
    # Verifica se esiste già
    title_lower = game_data.get("title", "").lower()
    for existing in games:
        if existing.get("title", "").lower() == title_lower:
            if not silent:
                print(f"⚠️ Gioco '{game_data.get('title')}' già presente nel database.")
                response = input("Sovrascrivere? (s/n): ")
                if response.lower() != "s":
                    return False
            games.remove(existing)
            break
    
    # Completa i dati mancanti
    if auto_fill or not game_data.get("gameplay"):
        if not silent:
            print(f"\n📝 Completa le informazioni per: {game_data.get('title')}")
        if not game_data.get("gameplay"):
            if silent:
                # Genera gameplay base dalla descrizione
                desc = game_data.get("description", "")
                game_data["gameplay"] = desc[:300] if desc else "Gameplay da definire"
            else:
                gameplay = input("Gameplay (descrizione meccaniche): ")
                game_data["gameplay"] = gameplay
        if not game_data.get("difficulty"):
            game_data["difficulty"] = "Media"  # Default
        if not game_data.get("modes"):
            game_data["modes"] = ["Single Player"]  # Default
    
    # Genera keywords se mancanti
    if not game_data.get("keywords"):
        game_data["keywords"] = generate_keywords(
            game_data.get("title", ""),
            game_data.get("description", ""),
            game_data.get("platform", "")
        )
    
    # Rimuovi source_url prima di salvare
    game_data.pop("source_url", None)
    
    # Aggiungi al database
    games.append(game_data)
    details_data["games"] = games
    
    # Salva
    with open(GAME_DETAILS_PATH, "w", encoding="utf-8") as f:
        json.dump(details_data, f, indent=2, ensure_ascii=False)
    
    # Aggiungi anche a nintendo_games.json (formato semplificato)
    with open(NINTENDO_GAMES_PATH, "r", encoding="utf-8") as f:
        nintendo_games = json.load(f)
    
    # Estrai tags e mood dai keywords
    tags = game_data.get("keywords", [])[:5]
    mood = []  # Potrebbe essere estratto dalla descrizione in futuro
    
    nintendo_game = {
        "title": game_data.get("title"),
        "platform": game_data.get("platform"),
        "tags": tags,
        "mood": mood
    }
    
    # Verifica se esiste già
    for existing in nintendo_games:
        if existing.get("title", "").lower() == title_lower:
            nintendo_games.remove(existing)
            break
    
    nintendo_games.append(nintendo_game)
    
    with open(NINTENDO_GAMES_PATH, "w", encoding="utf-8") as f:
        json.dump(nintendo_games, f, indent=2, ensure_ascii=False)
    
    if not silent:
        print(f"✅ Gioco '{game_data.get('title')}' aggiunto al database!")
    return True

def batch_add_games(games: List[Dict], silent: bool = True):
    """Aggiunge multipli giochi al database in batch."""
    added = 0
    skipped = 0
    
    for game in games:
        if add_game_to_database(game, auto_fill=True, silent=silent):
            added += 1
        else:
            skipped += 1
    
    return added, skipped

def main():
    """Funzione principale per aggiungere giochi."""
    print("=" * 70)
    print("🎮 Nintendo Game Database Scraper")
    print("=" * 70)
    print()
    
    # Carica e salva fonti (tutti i link forniti dall'utente)
    sources = [
        "https://www.nintendo.com",
        "https://www.nintendo.it",
        "https://www.nintendo.co.jp",
        "https://www.nintendo.fandom.com",
        "https://mariowiki.com",
        "https://mariowiki.it",
        "https://zelda.fandom.com",
        "https://zelda.fandom.com/wiki/List_of_The_Legend_of_Zelda_media",
        "https://www.ssbwiki.com",
        "https://strategywiki.org/wiki/Category:Nintendo",
        "https://www.metroidwiki.org",
        "https://www.kirby.fandom.com",
        "https://nintendolife.com/games",
        "https://nintendoeverything.com",
        "https://www.smashbros.com",
        "https://www.pokemon.com",
        "https://bulbapedia.bulbagarden.net",
        "https://www.pokewiki.de",
        "https://www.serebii.net",
        "https://ludomedia.it/nintendo-switch/elenco-alfabetico-giochi",
        "https://www.ign.com/wikis",
        "https://gamefaqs.gamespot.com",
        "https://www.giantbomb.com",
        "https://www.mobygames.com",
        "https://www.metacritic.com",
        "https://www.gameinformer.com",
        "https://en.wikipedia.org/wiki/List_of_Nintendo_64_games",
        "https://en.wikipedia.org/wiki/List_of_GameCube_games",
        "https://en.wikipedia.org/wiki/List_of_Wii_games",
        "https://en.wikipedia.org/wiki/List_of_Wii_U_games",
        "https://en.wikipedia.org/wiki/List_of_Nintendo_Switch_games",
        "https://en.wikipedia.org/wiki/List_of_Nintendo_DS_games",
        "https://en.wikipedia.org/wiki/List_of_Nintendo_3DS_games",
        "https://en.wikipedia.org/wiki/List_of_Game_Boy_Advance_games",
        "https://en.wikipedia.org/wiki/List_of_Game_Boy_Color_games",
        "https://en.wikipedia.org/wiki/List_of_Game_Boy_games",
        "https://en.wikipedia.org/wiki/List_of_Virtual_Boy_games",
        "https://nintendowiki.org",
        "https://fireemblemwiki.org",
        "https://xenoblade.fandom.com",
        "https://donkeykong.fandom.com",
        "https://yoshi.fandom.com",
        "https://pikmin.fandom.com",
        "https://arms.nintendo.com",
        "https://splatoonwiki.org",
        "https://wiisports.fandom.com",
        "https://starfox.fandom.com",
        "https://fzero.fandom.com",
        "https://goldensun.fandom.com",
        "https://warioware.fandom.com",
        "https://warioland.fandom.com",
        "https://earthbound.fandom.com",
        "https://mario.fandom.com/wiki/List_of_Mario_games",
        "https://wikirby.com",
        "https://nintendosoup.com",
        "https://nintendoenthusiast.com",
        "https://switchbrew.org",
        "https://serenesforest.net",
        "https://www.mariocastle.it",
        "https://zeldadungeon.net",
        "https://zeldawiki.wiki",
        "https://kirby.fandom.com/wiki/List_of_Kirby_games"
    ]
    
    save_sources(sources)
    print(f"✅ {len(sources)} fonti salvate come riferimento.")
    print()
    
    while True:
        print("Opzioni:")
        print("1. Aggiungi gioco da URL")
        print("2. Aggiungi gioco manualmente")
        print("3. Estrazione automatica da tutte le fonti")
        print("4. Esci")
        choice = input("\nScelta: ")
        
        if choice == "1":
            url = input("\nIncolla l'URL della pagina del gioco: ").strip()
            if not url:
                continue
            
            print("\n🔍 Estrazione informazioni...")
            game_data = extract_game_info(url)
            
            if game_data:
                print(f"\n✅ Informazioni estratte:")
                print(f"   Titolo: {game_data.get('title')}")
                print(f"   Piattaforma: {game_data.get('platform')}")
                print(f"   Descrizione: {game_data.get('description', '')[:100]}...")
                
                auto = input("\nCompletare automaticamente i campi mancanti? (s/n): ")
                add_game_to_database(game_data, auto_fill=(auto.lower() == "s"))
            else:
                print("❌ Impossibile estrarre informazioni dall'URL.")
        
        elif choice == "2":
            print("\n📝 Inserimento manuale:")
            game_data = {
                "title": input("Titolo: ").strip(),
                "platform": input("Piattaforma: ").strip() or "Nintendo Switch",
                "description": input("Descrizione: ").strip(),
                "gameplay": input("Gameplay: ").strip(),
                "difficulty": input("Difficoltà (Bassa/Media/Alta): ").strip() or "Media",
                "modes": [m.strip() for m in input("Modalità (separate da virgola): ").split(",")],
                "keywords": [k.strip() for k in input("Keywords (separate da virgola): ").split(",")]
            }
            
            if game_data["title"]:
                add_game_to_database(game_data, auto_fill=False)
        
        elif choice == "3":
            print("\n🤖 Estrazione automatica da tutte le fonti")
            print("⚠️ Questo processo può richiedere molto tempo...")
            confirm = input("Continuare? (s/n): ")
            if confirm.lower() == "s":
                max_per_source = input("Max giochi per fonte (default 50): ").strip()
                max_per_source = int(max_per_source) if max_per_source.isdigit() else 50
                
                extracted_games = auto_extract_from_sources(sources, max_games_per_source=max_per_source)
                
                if extracted_games:
                    print(f"\n💾 Aggiungo {len(extracted_games)} giochi al database...")
                    added, skipped = batch_add_games(extracted_games, silent=True)
                    print(f"\n✅ Completato! Aggiunti: {added}, Saltati: {skipped}")
                else:
                    print("\n⚠️ Nessun gioco estratto.")
        
        elif choice == "4":
            break
        
        print()

if __name__ == "__main__":
    main()

