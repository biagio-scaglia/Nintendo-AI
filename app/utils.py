from typing import List, Dict, Any

def sanitize_user_input(text: str) -> str:
    """
    Protegge l'AI da tentativi di prompt injection e manipolazione.
    NON filtra contenuti NSFW, solo tentativi di jailbreak.
    """
    # Parole chiave per prompt injection e jailbreak
    banned = [
        "ignore previous", "change your role", "system:", "you are now", 
        "forget", "disregard", "override", "jailbreak", "dan mode",
        "you are a", "act as", "pretend to be", "roleplay as",
        "forget all", "ignore all", "new instructions", "new rules"
    ]
    lowered = text.lower()
    
    if any(b in lowered for b in banned):
        return "Parlami dei giochi Nintendo che ti piacciono."
    
    return text

def classify_intent(user_message: str) -> str:
    message_lower = user_message.lower()
    
    info_keywords = [
        "chi è", "cos'è", "cosa è", "come funziona", "che modalità", "trama", 
        "gameplay", "difficoltà", "spiegami", "dimmi", "raccontami", 
        "parlami di", "mi parli di", "parlarmi di", "info su", "informazioni", "caratteristiche", 
        "meccaniche", "storia", "plot", "modalità di gioco", "come si gioca"
    ]
    
    recommend_keywords = [
        "consigliami", "voglio giocare", "cosa mi consigli", "suggeriscimi",
        "raccomandami", "cosa dovrei", "quale gioco", "che gioco", 
        "mi serve", "cerco", "vorrei", "mi piace"
    ]
    
    for keyword in info_keywords:
        if keyword in message_lower:
            return "info_request"
    
    for keyword in recommend_keywords:
        if keyword in message_lower:
            return "recommendation_request"
    
    return "small_talk"

def validate_history(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    validated = []
    for msg in history:
        if isinstance(msg, dict):
            role = str(msg.get("role", "user")).strip().lower()
            content = str(msg.get("content", "")).strip()
            
            if role not in ["user", "assistant", "system"]:
                role = "user"
            
            if content:
                if role == "user":
                    content = sanitize_user_input(content)
                
                validated.append({
                    "role": role,
                    "content": content
                })
    return validated

def format_for_engine(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return history

