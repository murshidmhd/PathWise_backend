from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class UserContext(BaseModel):
    recommended_careers: list[str] = []
    primary_career: str = ""
    assessment_summary: str = ""


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[Message] = []
    summary: str = ""
    user_context: UserContext = UserContext()
    session_type: str = "chat"  # "chat" or "assessment"


class ChatResponse(BaseModel):
    reply: str
    summary: str = ""
    should_summarize: bool = False


class SummarizeRequest(BaseModel):
    conversation_history: list[Message]


class SummarizeResponse(BaseModel):
    summary: str
