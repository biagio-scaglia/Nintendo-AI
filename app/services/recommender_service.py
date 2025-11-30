import json
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher

GAMES_DB_PATH = Path(__file__).parent.parent / "db" / "nintendo_games.json"

_games_cache = None

def load_games() -> List[Dict]:
    global _games_cache
    if _games_cache is not None:
        return _games_cache
    
    try:
        with open(GAMES_DB_PATH, "r", encoding="utf-8") as f:
            _games_cache = json.load(f)
        return _games_cache
    except Exception as e:
        print(f"Error loading games database: {e}")
        return []

def filter_by_platform(games: List[Dict], platform: str) -> List[Dict]:
    if not platform:
        return games
    
    platform_lower = platform.lower()
    return [
        game for game in games
        if platform_lower in game.get("platform", "").lower()
    ]

def similarity_score(tag1: str, tag2: str) -> float:
    return SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()

def match_by_tags(games: List[Dict], tags: List[str]) -> Optional[Dict]:
    if not tags or not games:
        return None
    
    best_match = None
    best_score = 0.0
    
    for game in games:
        game_tags = [t.lower() for t in game.get("tags", [])]
        game_moods = [m.lower() for m in game.get("mood", [])]
        
        score = 0.0
        
        for user_tag in tags:
            user_tag_lower = user_tag.lower()
            
            for game_tag in game_tags:
                if user_tag_lower == game_tag:
                    score += 2.0
                elif user_tag_lower in game_tag or game_tag in user_tag_lower:
                    score += 1.5
                else:
                    sim = similarity_score(user_tag_lower, game_tag)
                    score += sim
            
            for game_mood in game_moods:
                # Supporta formato bilingue "english/italiano"
                mood_parts = game_mood.split("/")
                mood_english = mood_parts[0].lower() if mood_parts else ""
                mood_italian = mood_parts[1].lower() if len(mood_parts) > 1 else ""
                
                if user_tag_lower == mood_english or user_tag_lower == mood_italian:
                    score += 1.5
                elif user_tag_lower in mood_english or mood_english in user_tag_lower:
                    score += 1.0
                elif mood_italian and (user_tag_lower in mood_italian or mood_italian in user_tag_lower):
                    score += 1.0
                elif user_tag_lower in game_mood or game_mood in user_tag_lower:
                    score += 1.0
                else:
                    sim = similarity_score(user_tag_lower, mood_english)
                    if mood_italian:
                        sim = max(sim, similarity_score(user_tag_lower, mood_italian))
                    score += sim * 0.5
        
        if score > best_score:
            best_score = score
            best_match = game
    
    return best_match if best_score > 0.1 else None

def extract_platform_from_text(text: str) -> Optional[str]:
    text_lower = text.lower()
    platforms = {
        "switch": "Nintendo Switch",
        "wii u": "Nintendo Wii U",
        "wiiu": "Nintendo Wii U",
        "wii": "Nintendo Wii",
        "3ds": "Nintendo 3DS",
        "ds": "Nintendo DS"
    }
    
    for key, platform in platforms.items():
        if key in text_lower:
            return platform
    
    return None

def smart_recommend(games: List[Dict], tags: List[str], mood: Optional[List[str]] = None, user_text: str = "") -> Dict:
    all_tags = tags.copy()
    if mood:
        all_tags.extend(mood)
    
    platform = extract_platform_from_text(user_text)
    
    if platform:
        filtered_games = filter_by_platform(games, platform)
    else:
        filtered_games = games
    
    if not filtered_games:
        filtered_games = games
    
    match = match_by_tags(filtered_games, all_tags)
    
    if match:
        return match
    
    if filtered_games:
        return filtered_games[0]
    
    if games:
        return games[0]
    
    return {}

def get_similar_games(game: Dict, count: int = 3) -> List[Dict]:
    if not game:
        return []
    
    all_games = load_games()
    game_tags = set(t.lower() for t in game.get("tags", []))
    game_moods = set(m.lower() for m in game.get("mood", []))
    
    scored_games = []
    
    for g in all_games:
        if g.get("title") == game.get("title"):
            continue
        
        g_tags = set(t.lower() for t in g.get("tags", []))
        g_moods = set(m.lower() for m in g.get("mood", []))
        
        tag_overlap = len(game_tags & g_tags)
        mood_overlap = len(game_moods & g_moods)
        
        score = tag_overlap * 2 + mood_overlap
        
        if score > 0:
            scored_games.append((score, g))
    
    scored_games.sort(key=lambda x: x[0], reverse=True)
    
    return [g for _, g in scored_games[:count]]

