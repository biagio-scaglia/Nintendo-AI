from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse, Game, GameInfo, GameInfoRequest, GameInfoResponse
from app.ai_engine_ollama import chat_nintendo_ai
from app.utils import validate_history, format_for_engine, classify_intent
from app.services.recommender_service import load_games, filter_by_platform, smart_recommend, get_similar_games
from app.services.info_service import get_game_info, search_game_info, get_context_for_ai
from app.services.web_search_service import get_web_context, get_web_game_info, get_web_image_url, extract_entity_name, detect_fandom_series
import uvicorn
import logging
import re
import json
import time

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

def extract_mood_from_text(text: str) -> list:
    """Estrae mood e tags dall'input dell'utente per la raccomandazione"""
    text_lower = text.lower()
    mood_keywords = {
        # Mood positivi
        "felice": ["felice", "happy", "contento", "gioioso", "allegro", "euforico"],
        "energico": ["energico", "energetic", "attivo", "vivace", "dinamico"],
        "stanco": ["stanco", "tired", "affaticato", "spossato", "esausto"],
        "rilassante": ["rilassante", "relax", "tranquillo", "calm", "pacifico", "sereno"],
        "avventuroso": ["avventura", "adventure", "esplorare", "explore", "scoprire"],
        "competitivo": ["competitivo", "competitive", "sfida", "challenge", "gara"],
        "sociale": ["sociale", "social", "amici", "friends", "multiplayer", "insieme"],
        "nostalgico": ["nostalgico", "nostalgic", "retro", "classico", "vintage"],
        "emotivo": ["emotivo", "emotional", "sentimentale", "storia", "story"],
        "epico": ["epico", "epic", "grandioso", "imponente", "spettacolare"],
        # Mood negativi/neutri
        "triste": ["triste", "sad", "depresso", "giù", "down"],
        "stressato": ["stressato", "stressed", "ansioso", "nervoso", "preoccupato"],
        "annoiato": ["annoiato", "bored", "noioso", "tedioso"]
    }
    
    found_moods = []
    for mood, keywords in mood_keywords.items():
        if any(kw in text_lower for kw in keywords):
            found_moods.append(mood)
    
    # Estrai anche tags generici
    tags = extract_tags_from_response(text)
    
    return found_moods + tags

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
        recommended_game = None
        all_text = " ".join([m.get("content", "") for m in validated])
        
        # Se è una richiesta di informazioni, cerca il gioco specifico
        if intent == "info_request":
            # Distingui tra richieste su personaggi e richieste su giochi
            is_character_query = any(phrase in last_user_message.lower() for phrase in [
                "chi è", "cos'è", "cosa è", "chi e", "cos e", "cosa e",
                "mi parli di", "parlami di", "dimmi di", "raccontami di",
                "info su", "informazioni su", "che cos'è", "che cosa è"
            ])
            
            if is_character_query:
                # Per personaggi, vai direttamente a web (non cercare nel database giochi)
                logger.info(f"Character query detected, searching web for: {last_user_message}")
                game_info = None  # Inizializza prima del try
                try:
                    # Passa l'intera query come additional_query per mantenere il contesto (es. "in ace attorney")
                    web_context = get_web_context(last_user_message, last_user_message)
                    if web_context:
                        context = web_context
                        # Crea GameInfo SOLO se c'è un'immagine da mostrare
                        try:
                            image_url = get_web_image_url(last_user_message, last_user_message)
                            # Filtra immagini placeholder o base64 vuote
                            if image_url and not image_url.startswith('data:image') and len(image_url) > 20:
                                # Crea GameInfo minimale solo con immagine per il frontend
                                entity_name = extract_entity_name(last_user_message)
                                if not entity_name:
                                    entity_name = last_user_message.strip()
                                game_info = GameInfo(
                                    title=entity_name.title(),
                                    platform="Nintendo",
                                    description="",
                                    gameplay="",
                                    difficulty="N/A",
                                    modes=[],
                                    keywords=[],
                                    image_url=image_url
                                )
                                logger.info(f"Created GameInfo with image for character: {entity_name}")
                        except Exception as img_error:
                            logger.warning(f"Error getting image URL: {img_error}")
                            game_info = None
                    else:
                        game_info = None
                except Exception as e:
                    logger.warning(f"Web search failed for character query: {e}")
                    game_info = None
                    # Continua senza info web, l'AI userà la sua conoscenza
            else:
                # Per giochi, prova prima Fandom (più accurato), poi database locale
                logger.info(f"Game query detected, trying Fandom first for: {last_user_message}")
                web_context = get_web_context(last_user_message, "")
                
                if web_context:
                    # Fandom ha trovato informazioni - usale come fonte principale
                    context = web_context
                    logger.info(f"✅ Using Fandom as primary source for game info")
                else:
                    # Fallback: cerca nel database locale
                    context = get_context_for_ai(last_user_message)
                    if context:
                        search_results = search_game_info(last_user_message, top_k=1)
                        if search_results:
                            try:
                                game_info_data = search_results[0]
                                game_info = GameInfo(**game_info_data)
                                logger.info(f"Found game info in local database: {game_info_data.get('title')}")
                            except Exception as e:
                                logger.warning(f"Failed to create GameInfo from local: {e}")
                    
                    # Se ancora non trovato, prova ricerca web tradizionale
                    if not context:
                        logger.info(f"Game not found in Fandom or local DB, trying traditional web search")
                        web_context = get_web_context(last_user_message, "")
                        if web_context:
                            context = web_context
                
                # Crea GameInfo strutturato da web per il frontend
                # Verifica se è un personaggio controllando se detect_fandom_series trova qualcosa
                try:
                    entity_name = extract_entity_name(last_user_message)
                    if not entity_name:
                        entity_name = last_user_message.strip()
                    is_character = detect_fandom_series(entity_name, last_user_message) is not None
                except Exception as e:
                    logger.warning(f"Error detecting character: {e}")
                    entity_name = last_user_message.strip()
                    is_character = False
                
                if not game_info and web_context:
                    if is_character:
                        # È un personaggio - crea GameInfo con immagine se disponibile
                        try:
                            image_url = get_web_image_url(last_user_message, last_user_message)
                            if image_url and not image_url.startswith('data:image') and len(image_url) > 20:
                                game_info = GameInfo(
                                    title=entity_name.title(),
                                    platform="Nintendo",
                                    description="",
                                    gameplay="",
                                    difficulty="N/A",
                                    modes=[],
                                    keywords=[],
                                    image_url=image_url
                                )
                                logger.info(f"Created GameInfo with image for character: {entity_name}")
                            else:
                                game_info = None
                        except Exception as img_error:
                            logger.warning(f"Error getting image for character: {img_error}")
                            game_info = None
                    else:
                        # È un gioco - crea GameInfo completo
                        web_game_info = get_web_game_info(last_user_message, "")
                        if web_game_info:
                            try:
                                game_info = GameInfo(**web_game_info)
                                logger.info(f"Created GameInfo from web for game query")
                            except Exception as e:
                                logger.warning(f"Failed to create GameInfo from web: {e}")
        
        # Se è una richiesta di raccomandazione, trova il gioco PRIMA di generare la risposta
        elif intent == "recommendation_request":
            # Estrai mood e tags dall'input dell'utente
            user_mood_tags = extract_mood_from_text(all_text)
            games = load_games()
            recommended = smart_recommend(games, user_mood_tags, user_text=all_text)
            
            if recommended:
                recommended_game = Game(
                    title=recommended.get("title", ""),
                    platform=recommended.get("platform", ""),
                    tags=recommended.get("tags", []),
                    mood=recommended.get("mood", [])
                )
                
                # Ottieni informazioni dettagliate sul gioco raccomandato
                game_details = get_game_info(recommended.get("title", ""))
                if game_details:
                    context = f"""🎮 GIOCO RACCOMANDATO PER L'UTENTE: {recommended.get('title', '')}

Piattaforma: {recommended.get('platform', '')}
Tags: {', '.join(recommended.get('tags', []))}
Mood: {', '.join(recommended.get('mood', []))}

DESCRIZIONE:
{game_details.get('description', '')}

GAMEPLAY:
{game_details.get('gameplay', '')}

Difficoltà: {game_details.get('difficulty', 'N/A')}
Modalità: {', '.join(game_details.get('modes', []))}

⚠️ ISTRUZIONI CRITICHE:
- DEVI menzionare "{recommended.get('title', '')}" nella tua risposta
- Spiega PERCHÉ questo gioco è perfetto per l'utente basandoti sul suo umore: {', '.join(user_mood_tags) if user_mood_tags else 'generale'}
- Sii entusiasta, specifico e coinvolgente
- Usa le informazioni sopra per dare dettagli concreti sul gameplay
- Non essere vago o generico!
- Se l'utente non ha specificato la console, chiedigliela per essere più preciso"""
                else:
                    # Se non trovato localmente, prova ricerca web
                    web_info = get_web_context(recommended.get('title', ''), "")
                    if web_info:
                        context = f"""🎮 GIOCO RACCOMANDATO PER L'UTENTE: {recommended.get('title', '')}

Piattaforma: {recommended.get('platform', '')}
Tags: {', '.join(recommended.get('tags', []))}
Mood: {', '.join(recommended.get('mood', []))}

{web_info}

⚠️ ISTRUZIONI CRITICHE:
- DEVI menzionare "{recommended.get('title', '')}" nella tua risposta
- Spiega PERCHÉ questo gioco è perfetto per l'utente basandoti sul suo umore: {', '.join(user_mood_tags) if user_mood_tags else 'generale'}
- Usa le informazioni web sopra se rilevanti
- Sii entusiasta, specifico e coinvolgente
- Se l'utente non ha specificato la console, chiedigliela per essere più preciso"""
                        # Crea GameInfo anche da web per il frontend
                        web_game_info = get_web_game_info(recommended.get('title', ''), "")
                        if web_game_info:
                            try:
                                # Usa piattaforma dal recommended se disponibile
                                if recommended.get('platform'):
                                    web_game_info['platform'] = recommended.get('platform')
                                game_info = GameInfo(**web_game_info)
                            except Exception as e:
                                logger.warning(f"Failed to create GameInfo from web for recommendation: {e}")
                    else:
                        context = f"""🎮 GIOCO RACCOMANDATO PER L'UTENTE: {recommended.get('title', '')}

Piattaforma: {recommended.get('platform', '')}
Tags: {', '.join(recommended.get('tags', []))}
Mood: {', '.join(recommended.get('mood', []))}

⚠️ ISTRUZIONI CRITICHE:
- DEVI menzionare "{recommended.get('title', '')}" nella tua risposta
- Spiega PERCHÉ questo gioco è perfetto per l'utente basandoti sul suo umore: {', '.join(user_mood_tags) if user_mood_tags else 'generale'}
- Sii entusiasta, specifico e coinvolgente
- Se l'utente non ha specificato la console, chiedigliela per essere più preciso"""
        
        formatted = format_for_engine(validated)
        
        try:
            start_time = time.time()
            logger.info("⏱️  Inizio generazione risposta AI...")
            # Per small_talk, usa parametri più veloci (risposte più brevi)
            is_small_talk = intent == "small_talk"
            reply = chat_nintendo_ai(formatted, context=context, fast_mode=is_small_talk)
            elapsed_time = time.time() - start_time
            logger.info(f"⏱️  Tempo totale per generare la risposta: {elapsed_time:.2f} secondi ({elapsed_time/60:.2f} minuti)")
            
            # Se la risposta è vuota, usa un messaggio di fallback
            if not reply or len(reply.strip()) == 0:
                logger.warning("⚠️ Risposta vuota ricevuta da Ollama, uso messaggio di fallback")
                if intent == "small_talk":
                    reply = "Ciao! Sono qui per aiutarti con i giochi Nintendo! 🎮 Come posso aiutarti oggi?"
                elif intent == "recommendation_request":
                    reply = "Mi dispiace, non sono riuscito a generare una raccomandazione. Potresti provare a descrivere meglio il tipo di gioco che cerchi?"
                elif intent == "info_request":
                    reply = "Mi dispiace, non sono riuscito a recuperare le informazioni richieste. Potresti riprovare con una domanda più specifica?"
                else:
                    reply = "Mi dispiace, c'è stato un problema nella generazione della risposta. Potresti riprovare?"
        except Exception as e:
            elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"Error in AI response generation dopo {elapsed_time:.2f} secondi: {e}")
            reply = "Mi dispiace, c'è stato un errore nella generazione della risposta. Puoi riprovare con una domanda diversa sui giochi Nintendo?"
        
        # NON cercare giochi raccomandati automaticamente se non esplicitamente richiesto
        # I giochi raccomandati vengono mostrati SOLO quando l'intent è "recommendation_request"
        # Questo evita di mostrare card non inerenti quando l'utente chiede solo informazioni
        
        logger.info("Chat response generated successfully")
        logger.info(f"Returning response with info: {game_info is not None}, recommended_game: {recommended_game is not None}")
        
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
