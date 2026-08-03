"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LogEntryBase(BaseModel):
    timestamp: Optional[str] = None
    activity: str
    type: str  # LOG, TODO, TASK
    follow_up: Optional[str] = None
    status: Optional[str] = None
    reference_id: Optional[int] = None
    eta: Optional[str] = None


class LogEntryCreate(LogEntryBase):
    pass


class LogEntryUpdate(BaseModel):
    timestamp: Optional[str] = None
    activity: Optional[str] = None
    type: Optional[str] = None
    follow_up: Optional[str] = None
    status: Optional[str] = None
    reference_id: Optional[int] = None
    eta: Optional[str] = None


class LogEntryResponse(LogEntryBase):
    id: int
    created_at: str
    updated_at: str
    tags: list[dict] = []

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"


class TagResponse(TagCreate):
    id: int

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: int
    report_type: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    content: str
    generated_at: str

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    report_type: str  # weekly, comprehensive, overdue, next_steps, patterns
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    year: Optional[int] = None
    week_number: Optional[int] = None
    custom_notes: Optional[str] = None


class DashboardStats(BaseModel):
    total_entries: int
    total_logs: int
    total_todos: int
    total_tasks: int
    pending_tasks: int
    assigned_tasks: int
    ongoing_tasks: int
    completed_tasks: int
    overdue_tasks: int


class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: str
    timeout: Optional[int] = 60
    max_tokens: Optional[int] = 4096


class AppConfig(BaseModel):
    app: dict
    llm: dict
    ui: dict
    import_settings: Optional[dict] = None
