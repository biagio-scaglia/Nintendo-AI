from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse, Game, GameInfo, GameInfoRequest, GameInfoResponse
from app.ai_engine_ollama import chat_nintendo_ai
from app.utils import validate_history, format_for_engine, classify_intent
from app.services.recommender_service import load_games, filter_by_platform, smart_recommend, get_similar_games
from app.services.info_service import get_game_info, search_game_info, get_context_for_ai
import uvicorn
import logging
import re
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nintendo AI Recommender",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_tags_from_response(response: str) -> list:
    words = response.lower().split()
    common_tags = [
        "adventure", "action", "rpg", "platform", "puzzle", "racing",
        "fighting", "strategy", "simulation", "relaxing", "competitive",
        "multiplayer", "single-player", "open-world", "exploration",
        "story", "casual", "challenging", "fun", "colorful", "cute",
        "epic", "nostalgic", "retro", "modern", "social", "party"
    ]
    
    found_tags = []
    for word in words:
        word_clean = re.sub(r'[^\w]', '', word)
        if word_clean in common_tags:
            found_tags.append(word_clean)
    
    return list(set(found_tags))[:5]

@app.get("/")
async def root():
    return {
        "message": "Nintendo AI Recommender API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "POST - Chat with Nintendo Game Advisor",
            "/game/info": "POST - Get game information",
            "/games/list": "GET - List all games",
            "/games/platform/{platform}": "GET - Games by platform"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    logger.info(f"Chat request received. History length: {len(payload.history)}")
    
    try:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in payload.history]
        
        validated = validate_history(history_dicts)
        logger.info(f"Validated history length: {len(validated)}")
        
        last_user_message = ""
        if validated:
            last_user_msg = [m for m in validated if m.get("role") == "user"]
            if last_user_msg:
                last_user_message = last_user_msg[-1].get("content", "")
        
        intent = classify_intent(last_user_message)
        logger.info(f"Detected intent: {intent}")
        
        context = ""
        game_info = None
        
        if intent == "info_request":
            context = get_context_for_ai(last_user_message)
            if context:
                search_results = search_game_info(last_user_message, top_k=1)
                if search_results:
                    try:
                        game_info_data = search_results[0]
                        game_info = GameInfo(**game_info_data)
                    except:
                        pass
        
        formatted = format_for_engine(validated)
        reply = chat_nintendo_ai(formatted, context=context)
        
        tags = extract_tags_from_response(reply)
        all_text = " ".join([m.get("content", "") for m in validated])
        
        recommended_game = None
        if intent == "recommendation_request" or not game_info:
            games = load_games()
            recommended = smart_recommend(games, tags, user_text=all_text)
            
            if recommended:
                recommended_game = Game(
                    title=recommended.get("title", ""),
                    platform=recommended.get("platform", ""),
                    tags=recommended.get("tags", []),
                    mood=recommended.get("mood", [])
                )
        
        logger.info("Chat response generated successfully")
        
        return ChatResponse(reply=reply, recommended_game=recommended_game, info=game_info)
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise


@app.get("/games/list", response_model=list[Game])
async def list_games():
    logger.info("Games list request received")
    games = load_games()
    return [Game(**game) for game in games]

@app.get("/games/platform/{platform}", response_model=list[Game])
async def games_by_platform(platform: str):
    logger.info(f"Games by platform request: {platform}")
    games = load_games()
    filtered = filter_by_platform(games, platform)
    return [Game(**game) for game in filtered]

@app.post("/game/info", response_model=GameInfoResponse)
async def game_info_endpoint(payload: GameInfoRequest):
    logger.info(f"Game info request: {payload.query}")
    
    try:
        game_data = get_game_info(payload.query)
        
        if game_data:
            game_info = GameInfo(**game_data)
            return GameInfoResponse(game=game_info)
        else:
            search_results = search_game_info(payload.query, top_k=1)
            if search_results:
                game_info = GameInfo(**search_results[0])
                return GameInfoResponse(game=game_info)
            else:
                return GameInfoResponse(game=None)
    
    except Exception as e:
        logger.error(f"Error getting game info: {str(e)}", exc_info=True)
        return GameInfoResponse(game=None)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
