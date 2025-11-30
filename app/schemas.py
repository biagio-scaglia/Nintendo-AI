from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class Game(BaseModel):
    title: str
    platform: str
    tags: List[str]
    mood: List[str]

class GameInfo(BaseModel):
    title: str
    platform: str
    description: str
    gameplay: str
    difficulty: str
    modes: List[str]
    keywords: List[str]

class ChatRequest(BaseModel):
    history: List[Message]

class ChatResponse(BaseModel):
    reply: str
    recommended_game: Optional[Game] = None
    info: Optional[GameInfo] = None

class GameInfoRequest(BaseModel):
    query: str

class GameInfoResponse(BaseModel):
    game: Optional[GameInfo] = None

