from typing import Dict, Optional, List
from app.knowledge.rag_engine import retrieve_info, search_games, get_context_for_query

def get_game_info(title: str) -> Optional[Dict]:
    game = retrieve_info(title)
    if game:
        return {
            "title": game.get("title", ""),
            "platform": game.get("platform", ""),
            "description": game.get("description", ""),
            "gameplay": game.get("gameplay", ""),
            "difficulty": game.get("difficulty", ""),
            "modes": game.get("modes", []),
            "keywords": game.get("keywords", [])
        }
    return None

def search_game_info(query: str, top_k: int = 3) -> List[Dict]:
    results = search_games(query, top_k=top_k)
    
    formatted_results = []
    for game in results:
        formatted_results.append({
            "title": game.get("title", ""),
            "platform": game.get("platform", ""),
            "description": game.get("description", ""),
            "gameplay": game.get("gameplay", ""),
            "difficulty": game.get("difficulty", ""),
            "modes": game.get("modes", []),
            "keywords": game.get("keywords", [])
        })
    
    return formatted_results

def get_context_for_ai(query: str) -> str:
    return get_context_for_query(query, max_games=1)

