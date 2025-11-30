import json
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher

KNOWLEDGE_DB_PATH = Path(__file__).parent / "game_details.json"

_knowledge_cache = None

def load_knowledge() -> List[Dict]:
    global _knowledge_cache
    if _knowledge_cache is not None:
        return _knowledge_cache
    
    try:
        with open(KNOWLEDGE_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _knowledge_cache = data.get("games", [])
        return _knowledge_cache
    except Exception as e:
        print(f"Error loading knowledge database: {e}")
        return []

def similarity_score(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def search_games(query: str, top_k: int = 5) -> List[Dict]:
    games = load_knowledge()
    if not games or not query:
        return []
    
    query_lower = query.lower()
    query_words = set(word for word in query_lower.split() if len(word) > 2)
    scored_games = []
    
    for game in games:
        score = 0.0
        
        title = game.get("title", "").lower()
        keywords = [k.lower() for k in game.get("keywords", [])]
        
        if query_lower in title:
            score += 10.0
            scored_games.append((score, game))
            continue
        
        if any(word in title for word in query_words):
            score += 5.0
        
        title_sim = similarity_score(query_lower, title)
        if title_sim > 0.5:
            score += title_sim * 8.0
        
        for keyword in keywords:
            if query_lower in keyword or keyword in query_lower:
                score += 3.0
                break
            if any(word in keyword for word in query_words):
                score += 1.5
        
        if score > 2.0:
            scored_games.append((score, game))
    
    scored_games.sort(key=lambda x: x[0], reverse=True)
    
    return [game for _, game in scored_games[:top_k]]

def retrieve_info(game_title: str) -> Optional[Dict]:
    games = load_knowledge()
    if not games:
        return None
    
    game_title_lower = game_title.lower()
    
    for game in games:
        title = game.get("title", "").lower()
        if game_title_lower == title or game_title_lower in title or title in game_title_lower:
            return game
        
        title_sim = similarity_score(game_title_lower, title)
        if title_sim > 0.8:
            return game
    
    results = search_games(game_title, top_k=1)
    if results:
        return results[0]
    
    return None

def get_context_for_query(query: str, max_games: int = 1) -> str:
    results = search_games(query, top_k=max_games)
    
    if not results:
        return ""
    
    game = results[0]
    title = game.get("title", "")
    platform = game.get("platform", "")
    description = game.get("description", "")[:300]
    gameplay = game.get("gameplay", "")[:200]
    difficulty = game.get("difficulty", "")
    modes = ", ".join(game.get("modes", []))
    
    context = f"Titolo: {title}\nPiattaforma: {platform}\nDescrizione: {description}\nGameplay: {gameplay}\nDifficoltà: {difficulty}\nModalità: {modes}"
    
    return context

