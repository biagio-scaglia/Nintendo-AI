from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import ChatRequest, ChatResponse, Game, GameInfo, GameInfoRequest, GameInfoResponse
from app.ai_engine_ollama import chat_nintendo_ai
from app.utils import validate_history, format_for_engine, classify_intent
from app.services.recommender_service import load_games, filter_by_platform, smart_recommend, get_similar_games
from app.services.info_service import get_game_info, search_game_info, get_context_for_ai
from app.services.web_search_service import get_web_context, get_web_game_info, get_web_image_url, extract_entity_name, detect_fandom_series
from app.services.user_memory_service import (
    update_memory_from_conversation, 
    get_personalization_context, 
    load_memory, 
    clear_memory,
    detect_save_favorite_intent,
    save_to_favorites,
    set_user_name,
    get_user_profile,
    generate_personality_report
)
from app.tools.wiki_agent import WikiAgent
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

# Inizializza WikiAgent
wiki_agent = WikiAgent(lang="it")

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
            "/games/platform/{platform}": "GET - Games by platform",
            "/memory": "GET - Get saved user memory",
            "/memory/clear": "POST - Clear user memory",
            "/profile": "GET - Get user profile",
            "/profile/name": "POST - Set user name",
            "/profile/report": "GET - Generate personality report",
            "/wiki/search": "POST - Search Wikipedia pages",
            "/wiki/page": "POST - Get Wikipedia page content",
            "/wiki/answer": "POST - Answer question using Wikipedia"
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
        
        # Controlla PRIMA se l'utente vuole solo salvare nei preferiti (senza altre domande)
        should_save_favorite = detect_save_favorite_intent(last_user_message)
        # Considera come richiesta singola se contiene solo parole relative al salvataggio
        save_only_phrases = ["segna tra i preferiti", "segna nei preferiti", "metti nei preferiti", 
                            "salva nei preferiti", "aggiungi ai preferiti", "salva questo", 
                            "metti questo", "segna questo"]
        is_only_save_request = should_save_favorite and any(phrase in last_user_message.lower() for phrase in save_only_phrases)
        
        intent = classify_intent(last_user_message)
        logger.info(f"Detected intent: {intent}")
        
        context = ""
        game_info = None
        recommended_game = None
        all_text = " ".join([m.get("content", "") for m in validated])
        
        # Per small_talk o domande generali, prova Wikipedia se sembra una domanda informativa
        if intent == "small_talk":
            # Rileva se è una domanda informativa generale (non su un gioco specifico)
            general_info_keywords = [
                "cos'è", "cosa è", "chi è", "quando", "dove", "perché", "come",
                "storia di", "storia del", "storia della", "origine", "nascita",
                "quando è nato", "quando è stato creato", "quando è uscito"
            ]
            is_general_info = any(keyword in last_user_message.lower() for keyword in general_info_keywords)
            
            if is_general_info and len(last_user_message.split()) > 3:  # Solo per domande abbastanza specifiche
                try:
                    logger.info(f"Small talk con domanda informativa, provo Wikipedia: {last_user_message}")
                    wiki_answer = wiki_agent.answer(last_user_message)
                    if "error" not in wiki_answer:
                        wiki_context = f"""📚 INFORMAZIONI DA WIKIPEDIA:

Pagina: {wiki_answer.get('matched_page', 'N/A')}
Riassunto: {wiki_answer.get('summary', '')}
"""
                        if wiki_answer.get('relevant_section'):
                            wiki_context += f"Sezione rilevante: {wiki_answer.get('relevant_section')}\n\n"
                        
                        full_text = wiki_answer.get('full_text', '')
                        if full_text:
                            wiki_context += f"Contenuto:\n{full_text[:1500]}"
                            if len(full_text) > 1500:
                                wiki_context += "\n\n[... contenuto troncato ...]"
                        
                        context = wiki_context
                        logger.info(f"✅ Informazioni trovate su Wikipedia per small talk")
                except Exception as wiki_error:
                    logger.warning(f"Wikipedia search failed for small talk: {wiki_error}")
        
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
                
                # Rileva se l'utente chiede approfondimenti
                deep_scrape_keywords = [
                    "approfondisci", "dimmi di più", "altre info", "altre informazioni",
                    "dimmi altro", "raccontami di più", "espandi", "più dettagli",
                    "più informazioni", "altro su", "altro riguardo"
                ]
                deep_scrape = any(keyword in last_user_message.lower() for keyword in deep_scrape_keywords)
                if deep_scrape:
                    logger.info("Richiesta di approfondimento rilevata, estraggo tutto il contenuto")
                
                game_info = None  # Inizializza prima del try
                try:
                    # Passa l'intera query come additional_query per mantenere il contesto (es. "in ace attorney")
                    web_context = get_web_context(last_user_message, last_user_message, deep_scrape=deep_scrape)
                    if web_context:
                        context = web_context
                        # Aggiungi istruzione per generare informazioni diverse
                        if deep_scrape:
                            context += "\n\n⚠️ ISTRUZIONE IMPORTANTE PER APPROFONDIMENTO:\n- L'utente ha già ricevuto informazioni su questo argomento\n- DEVI fornire informazioni DIVERSE e COMPLEMENTARI rispetto a quelle già date\n- Evita di ripetere le stesse informazioni già fornite\n- Concentrati su aspetti nuovi, dettagli aggiuntivi, curiosità, o prospettive diverse\n- Sii specifico e dettagliato con nuove informazioni"
                        # Crea GameInfo SOLO se c'è un'immagine da mostrare
                        try:
                            image_url = get_web_image_url(last_user_message, last_user_message, deep_scrape=deep_scrape)
                            # Pulisci l'URL da newline e spazi
                            if image_url:
                                image_url = image_url.strip().replace('\n', '').replace('\r', '').replace(' ', '')
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
                                logger.info(f"GameInfo image_url value: {game_info.image_url}")
                                logger.info(f"GameInfo JSON serialized: {game_info.model_dump()}")
                        except Exception as img_error:
                            logger.warning(f"Error getting image URL: {img_error}")
                            game_info = None
                    else:
                        game_info = None
                except Exception as e:
                    logger.warning(f"Web search failed for character query: {e}")
                    game_info = None
                
                # Fallback: Prova Wikipedia se Fandom non ha trovato nulla
                if not context:
                    try:
                        logger.info(f"Fandom non ha trovato risultati, provo Wikipedia per: {last_user_message}")
                        wiki_answer = wiki_agent.answer(last_user_message)
                        if "error" not in wiki_answer:
                            wiki_context = f"""📚 INFORMAZIONI DA WIKIPEDIA:

Pagina: {wiki_answer.get('matched_page', 'N/A')}
Riassunto: {wiki_answer.get('summary', '')}
"""
                            if wiki_answer.get('relevant_section'):
                                wiki_context += f"Sezione rilevante: {wiki_answer.get('relevant_section')}\n\n"
                            
                            # Aggiungi testo completo (limitato per non appesantire)
                            full_text = wiki_answer.get('full_text', '')
                            if full_text:
                                # Prendi i primi 2000 caratteri
                                wiki_context += f"Contenuto completo:\n{full_text[:2000]}"
                                if len(full_text) > 2000:
                                    wiki_context += "\n\n[... contenuto troncato ...]"
                            
                            context = wiki_context
                            logger.info(f"✅ Informazioni trovate su Wikipedia per: {last_user_message}")
                    except Exception as wiki_error:
                        logger.warning(f"Wikipedia search failed: {wiki_error}")
                        # Continua senza info web, l'AI userà la sua conoscenza
            else:
                # Per giochi, prova prima Fandom (più accurato), poi database locale
                logger.info(f"Game query detected, trying Fandom first for: {last_user_message}")
                
                # Rileva se l'utente chiede approfondimenti
                deep_scrape_keywords = [
                    "approfondisci", "dimmi di più", "altre info", "altre informazioni",
                    "dimmi altro", "raccontami di più", "espandi", "più dettagli",
                    "più informazioni", "altro su", "altro riguardo"
                ]
                deep_scrape = any(keyword in last_user_message.lower() for keyword in deep_scrape_keywords)
                if deep_scrape:
                    logger.info("Richiesta di approfondimento rilevata, estraggo tutto il contenuto")
                
                web_context = get_web_context(last_user_message, "", deep_scrape=deep_scrape)
                
                if web_context:
                    # Fandom ha trovato informazioni - usale come fonte principale
                    context = web_context
                    
                    # Se è una richiesta di approfondimento, aggiungi anche Wikipedia come fonte complementare
                    if deep_scrape:
                        try:
                            logger.info(f"Richiesta approfondimento: aggiungo Wikipedia come fonte complementare")
                            wiki_answer = wiki_agent.answer(last_user_message)
                            if "error" not in wiki_answer:
                                wiki_complement = f"""

📚 INFORMAZIONI COMPLEMENTARI DA WIKIPEDIA:

Pagina: {wiki_answer.get('matched_page', 'N/A')}
Riassunto: {wiki_answer.get('summary', '')}
"""
                                if wiki_answer.get('relevant_section'):
                                    wiki_complement += f"Sezione rilevante: {wiki_answer.get('relevant_section')}\n\n"
                                
                                full_text = wiki_answer.get('full_text', '')
                                if full_text:
                                    # Per approfondimenti, prendi una porzione più grande
                                    wiki_complement += f"Contenuto aggiuntivo:\n{full_text[:1500]}"
                                    if len(full_text) > 1500:
                                        wiki_complement += "\n\n[... contenuto troncato ...]"
                                
                                context += wiki_complement
                                logger.info(f"✅ Aggiunte informazioni complementari da Wikipedia")
                        except Exception as wiki_error:
                            logger.warning(f"Failed to get Wikipedia complement: {wiki_error}")
                    
                    # Aggiungi istruzione per generare informazioni diverse
                    if deep_scrape:
                        context += "\n\n⚠️ ISTRUZIONE IMPORTANTE PER APPROFONDIMENTO:\n- L'utente ha già ricevuto informazioni su questo argomento\n- DEVI fornire informazioni DIVERSE e COMPLEMENTARI rispetto a quelle già date\n- Evita di ripetere le stesse informazioni già fornite\n- Concentrati su aspetti nuovi, dettagli aggiuntivi, curiosità, o prospettive diverse\n- Sii specifico e dettagliato con nuove informazioni\n- Combina le informazioni da Fandom e Wikipedia per una risposta completa"
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
                    
                    # Se ancora non trovato, prova Wikipedia prima della ricerca web tradizionale
                    if not context:
                        try:
                            logger.info(f"Game not found in Fandom or local DB, trying Wikipedia for: {last_user_message}")
                            wiki_answer = wiki_agent.answer(last_user_message)
                            if "error" not in wiki_answer:
                                wiki_context = f"""📚 INFORMAZIONI DA WIKIPEDIA:

Pagina: {wiki_answer.get('matched_page', 'N/A')}
Riassunto: {wiki_answer.get('summary', '')}
"""
                                if wiki_answer.get('relevant_section'):
                                    wiki_context += f"Sezione rilevante: {wiki_answer.get('relevant_section')}\n\n"
                                
                                # Aggiungi testo completo (limitato)
                                full_text = wiki_answer.get('full_text', '')
                                if full_text:
                                    wiki_context += f"Contenuto completo:\n{full_text[:2000]}"
                                    if len(full_text) > 2000:
                                        wiki_context += "\n\n[... contenuto troncato ...]"
                                
                                context = wiki_context
                                logger.info(f"✅ Informazioni trovate su Wikipedia per gioco: {last_user_message}")
                                
                                # Crea GameInfo anche da Wikipedia se possibile
                                try:
                                    wiki_game_info = {
                                        "title": wiki_answer.get('matched_page', ''),
                                        "platform": "Nintendo",
                                        "description": wiki_answer.get('summary', '')[:400],
                                        "gameplay": wiki_answer.get('full_text', '')[:1000],
                                        "difficulty": "N/A",
                                        "modes": [],
                                        "keywords": []
                                    }
                                    game_info = GameInfo(**wiki_game_info)
                                    logger.info(f"Created GameInfo from Wikipedia")
                                except Exception as wiki_info_error:
                                    logger.warning(f"Failed to create GameInfo from Wikipedia: {wiki_info_error}")
                        except Exception as wiki_error:
                            logger.warning(f"Wikipedia search failed: {wiki_error}")
                        
                        # Ultimo fallback: ricerca web tradizionale
                        if not context:
                            logger.info(f"Wikipedia non ha trovato risultati, trying traditional web search")
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
                            # Pulisci l'URL da newline e spazi
                            if image_url:
                                image_url = image_url.strip().replace('\n', '').replace('\r', '').replace(' ', '')
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
        
        # Aggiungi contesto di personalizzazione dalla memoria
        personalization_context = get_personalization_context()
        if personalization_context:
            if context:
                context = context + "\n\n" + personalization_context
            else:
                context = personalization_context
        
        # Se è solo una richiesta di salvataggio, gestiscila direttamente senza chiamare l'AI
        if is_only_save_request:
            from app.services.user_memory_service import extract_game_names, load_memory
            memory = load_memory()
            
            # Prova a trovare il gioco da salvare
            games_in_message = extract_game_names(last_user_message)
            if not games_in_message and memory.get("provided_info"):
                last_info = memory["provided_info"][-1]
                games_in_message = [last_info.get("title", "")]
            
            if games_in_message:
                game_name_to_save = games_in_message[0]
                game_info_from_memory = None
                for info in memory.get("provided_info", []):
                    if info.get("title", "").lower() == game_name_to_save.lower():
                        game_info_from_memory = info
                        break
                
                saved_to_favorites = save_to_favorites(game_name_to_save, game_info_from_memory)
                if saved_to_favorites:
                    reply = f"✅ Ho salvato '{game_name_to_save}' nei tuoi preferiti! Puoi vederlo nella sezione Profilo."
                else:
                    reply = f"'{game_name_to_save}' è già nei tuoi preferiti!"
            else:
                reply = "Non ho trovato un gioco da salvare. Chiedimi prima informazioni su un gioco specifico!"
        else:
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
        
        # Controlla se l'utente vuole salvare nei preferiti (solo se non è già stato gestito)
        if not is_only_save_request:
            should_save_favorite = detect_save_favorite_intent(last_user_message)
            saved_to_favorites = False
            
            if should_save_favorite:
            # Prova a salvare il gioco corrente
            game_to_save = None
            game_name_to_save = None
            
            if game_info:
                game_to_save = game_info.model_dump() if hasattr(game_info, 'model_dump') else game_info.dict()
                game_name_to_save = game_info.title
                saved_to_favorites = save_to_favorites(game_name_to_save, game_to_save)
            elif recommended_game:
                game_to_save = recommended_game.model_dump() if hasattr(recommended_game, 'model_dump') else recommended_game.dict()
                game_name_to_save = recommended_game.title
                saved_to_favorites = save_to_favorites(game_name_to_save, game_to_save)
            else:
                # Se non c'è game_info nel contesto, prova a estrarre il nome del gioco dal messaggio
                # o cercarlo nella memoria recente
                from app.services.user_memory_service import extract_game_names, load_memory
                memory = load_memory()
                
                # Estrai nomi di giochi dal messaggio
                games_in_message = extract_game_names(last_user_message)
                
                # Cerca anche nei giochi menzionati di recente o nelle info fornite
                if not games_in_message and memory.get("provided_info"):
                    # Prendi l'ultimo gioco di cui si sono chiesti info
                    last_info = memory["provided_info"][-1]
                    games_in_message = [last_info.get("title", "")]
                
                if games_in_message:
                    game_name_to_save = games_in_message[0]
                    # Cerca info del gioco nella memoria
                    game_info_from_memory = None
                    for info in memory.get("provided_info", []):
                        if info.get("title", "").lower() == game_name_to_save.lower():
                            game_info_from_memory = info
                            break
                    
                    saved_to_favorites = save_to_favorites(game_name_to_save, game_info_from_memory)
            
                if saved_to_favorites:
                    # Aggiungi conferma alla risposta solo se non è già vuota o di errore
                    game_name = game_name_to_save or (game_info.title if game_info else (recommended_game.title if recommended_game else "questo gioco"))
                    if reply and "non sono riuscito" not in reply.lower():
                        reply = f"✅ Ho salvato '{game_name}' nei tuoi preferiti! Puoi vederlo nella sezione Profilo.\n\n{reply}"
                    else:
                        # Se la risposta è vuota o di errore, usa solo la conferma
                        reply = f"✅ Ho salvato '{game_name}' nei tuoi preferiti! Puoi vederlo nella sezione Profilo."
                elif should_save_favorite:
                    # Se voleva salvare ma non c'è un gioco da salvare
                    if reply and "non sono riuscito" not in reply.lower():
                        reply = "Non ho trovato un gioco da salvare nei preferiti. Chiedimi informazioni su un gioco specifico e poi chiedi di salvarlo!\n\n" + reply
                    else:
                        reply = "Non ho trovato un gioco da salvare nei preferiti. Chiedimi informazioni su un gioco specifico e poi chiedi di salvarlo!"
        
        # Salva informazioni nella memoria per personalizzazione futura
        try:
            game_info_dict = None
            if game_info:
                game_info_dict = game_info.model_dump() if hasattr(game_info, 'model_dump') else game_info.dict()
            
            recommended_game_dict = None
            if recommended_game:
                recommended_game_dict = recommended_game.model_dump() if hasattr(recommended_game, 'model_dump') else recommended_game.dict()
            
            update_memory_from_conversation(
                user_message=last_user_message,
                ai_response=reply,
                game_info=game_info_dict,
                recommended_game=recommended_game_dict
            )
            logger.info("Memory updated successfully")
        except Exception as mem_error:
            logger.warning(f"Error updating memory: {mem_error}")
            # Non bloccare la risposta se c'è un errore nella memoria
        
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

@app.get("/memory")
async def get_memory():
    """Restituisce la memoria salvata dell'utente"""
    try:
        memory = load_memory()
        return memory
    except Exception as e:
        logger.error(f"Error getting memory: {str(e)}", exc_info=True)
        return {"error": "Failed to load memory"}

@app.post("/memory/clear")
async def clear_user_memory():
    """Cancella tutta la memoria dell'utente"""
    try:
        clear_memory()
        return {"message": "Memory cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}", exc_info=True)
        return {"error": "Failed to clear memory"}

@app.post("/profile/name")
async def set_profile_name(name_data: dict):
    """Imposta il nome utente"""
    try:
        user_name = name_data.get("name", "").strip()
        if not user_name:
            return {"error": "Name cannot be empty"}
        set_user_name(user_name)
        return {"message": "Name set successfully", "name": user_name}
    except Exception as e:
        logger.error(f"Error setting name: {str(e)}", exc_info=True)
        return {"error": "Failed to set name"}

@app.get("/profile")
async def get_profile():
    """Ottiene il profilo completo dell'utente"""
    try:
        profile = get_user_profile()
        return profile
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        return {"error": "Failed to get profile"}

@app.get("/profile/report")
async def get_personality_report():
    """Genera un resoconto della personalità dell'utente"""
    try:
        report = generate_personality_report()
        return {"report": report}
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        return {"error": "Failed to generate report"}

@app.post("/profile/name")
async def set_profile_name(name_data: dict):
    """Imposta il nome utente"""
    try:
        user_name = name_data.get("name", "").strip()
        if not user_name:
            return {"error": "Name cannot be empty"}
        set_user_name(user_name)
        return {"message": "Name set successfully", "name": user_name}
    except Exception as e:
        logger.error(f"Error setting name: {str(e)}", exc_info=True)
        return {"error": "Failed to set name"}

@app.get("/profile")
async def get_profile():
    """Ottiene il profilo completo dell'utente"""
    try:
        profile = get_user_profile()
        return profile
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        return {"error": "Failed to get profile"}

@app.get("/profile/report")
async def get_personality_report():
    """Genera un resoconto della personalità dell'utente"""
    try:
        report = generate_personality_report()
        return {"report": report}
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        return {"error": "Failed to generate report"}

@app.post("/wiki/search")
async def wiki_search(query_data: dict):
    """Cerca pagine su Wikipedia"""
    try:
        query = query_data.get("query", "").strip()
        if not query:
            return {"error": "Query cannot be empty"}
        
        results = wiki_agent.search(query)
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching Wikipedia: {str(e)}", exc_info=True)
        return {"error": "Failed to search Wikipedia"}

@app.post("/wiki/page")
async def wiki_page(title_data: dict):
    """Ottieni una pagina Wikipedia completa"""
    try:
        title = title_data.get("title", "").strip()
        if not title:
            return {"error": "Title cannot be empty"}
        
        page_data = wiki_agent.get_page(title)
        return page_data
    except Exception as e:
        logger.error(f"Error getting Wikipedia page: {str(e)}", exc_info=True)
        return {"error": "Failed to get Wikipedia page"}

@app.post("/wiki/answer")
async def wiki_answer(question_data: dict):
    """Rispondi a una domanda usando Wikipedia"""
    try:
        question = question_data.get("question", "").strip()
        if not question:
            return {"error": "Question cannot be empty"}
        
        answer = wiki_agent.answer(question)
        return answer
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}", exc_info=True)
        return {"error": "Failed to answer question"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
