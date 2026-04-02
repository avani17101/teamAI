from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Task(BaseModel):
    id: Optional[str] = None
    description: str
    owner: str
    deadline: str
    status: str = "pending"
    meeting_id: Optional[str] = None
    created_at: Optional[str] = None


class Decision(BaseModel):
    id: Optional[str] = None
    description: str
    meeting_id: Optional[str] = None


class Risk(BaseModel):
    id: Optional[str] = None
    description: str
    severity: str  # high | medium | low
    meeting_id: Optional[str] = None


class ExtractionResult(BaseModel):
    tasks: List[Task] = []
    decisions: List[Decision] = []
    risks: List[Risk] = []


class Meeting(BaseModel):
    id: Optional[str] = None
    title: str
    transcript: str
    summary: Optional[str] = None
    extraction: Optional[ExtractionResult] = None
    created_at: Optional[str] = None


class MeetingUploadRequest(BaseModel):
    title: str
    transcript: str
    department: str = "engineering"
    auto_sync_notion: bool = True   # False = return tasks for HITL review, don't create in Notion
    debug_mode: bool = False        # True = skip emails, don't tag people in Notion (just names)


class NotionSyncRequest(BaseModel):
    meeting_id: str
    task_ids: List[str]   # only these task IDs will be synced to Notion
    department: str = "engineering"
    meeting_title: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    department: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    used_openclaw: bool = False


class ExecuteActionRequest(BaseModel):
    action: str  # "create_task" | "update_task" | "notify"
    payload: dict


class TaskUpdateRequest(BaseModel):
    status: str


class FullTaskUpdateRequest(BaseModel):
    """Full task update - all fields optional, only provided fields are updated."""
    description: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TeamMemberRequest(BaseModel):
    name: str
    role: str = ""
    role_details: str = ""  # Detailed role description
    responsibilities: str = ""  # Key responsibilities for better task assignment
    department: str = ""
    email: str = ""
    telegram_handle: str = ""


class OrgContextRequest(BaseModel):
    department: str
    mission: str
    notion_database_id: str = ""
    notion_page_id: str = ""


class NotificationRequest(BaseModel):
    department: str
    days_ahead: int = 3
