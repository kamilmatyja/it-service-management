# ai-generated: 100% - Generated using Gemini

import os
import uuid
from datetime import datetime, timezone, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, ConfigDict, field_serializer

app = FastAPI()

# In-memory store for Lab 1
tickets_db: Dict[str, 'Ticket'] = {}

# --- Custom Exception Handling ---

class ErrorResponseException(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message

@app.exception_handler(ErrorResponseException)
async def custom_error_handler(request: Request, exc: ErrorResponseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation", "message": "Validation failed"}}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = "not_found" if exc.status_code == 404 else "error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": exc.detail}}
    )

# --- Pydantic Models ---

class Reporter(BaseModel):
    model_config = ConfigDict(extra='ignore')
    name: str = Field(min_length=1, max_length=100)
    email: Optional[str] = None
    vip: bool = False

class TicketCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    reporter: Reporter
    impact: int = Field(strict=True, ge=1, le=3)
    urgency: int = Field(strict=True, ge=1, le=3)
    related_to: Optional[str] = None

class SLA(BaseModel):
    ack_due_at: datetime
    resolve_due_at: datetime

    @field_serializer('ack_due_at', 'resolve_due_at')
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat().replace("+00:00", "Z")

class Ticket(BaseModel):
    id: str
    title: str
    description: str
    reporter: Reporter
    impact: int
    urgency: int
    priority: str
    state: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    related_to: Optional[str] = None
    sla: SLA

    @field_serializer('created_at', 'acknowledged_at', 'resolved_at', 'closed_at')
    def serialize_dt(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        return dt.isoformat().replace("+00:00", "Z")

# --- Test Clock Dependency ---

def get_now(request: Request) -> datetime:
    use_test_clock = os.environ.get("SVCDESK_TEST_CLOCK", "").lower() in ("1", "true")
    if use_test_clock:
        header = request.headers.get("x-test-clock")
        if header:
            try:
                if header.endswith('Z'):
                    header = header[:-1] + '+00:00'
                dt = datetime.fromisoformat(header)
                if dt.tzinfo is None:
                    raise ValueError("Naive timestamp not allowed")
                return dt
            except ValueError:
                raise ErrorResponseException(422, "validation", "Invalid X-Test-Clock format")
    return datetime.now(timezone.utc)

# --- Business Logic Helpers ---

def get_next_business_opening(dt: datetime) -> datetime:
    waw = ZoneInfo("Europe/Warsaw")
    dt = dt.astimezone(waw)
    local_date = dt.date()
    local_time = dt.time()

    # If weekend, move to Monday 08:00
    if dt.weekday() >= 5:
        days_ahead = 7 - dt.weekday()
        return datetime.combine(local_date + timedelta(days=days_ahead), time(8, 0), tzinfo=waw)

    # If weekday before 08:00
    if local_time < time(8, 0):
        return datetime.combine(local_date, time(8, 0), tzinfo=waw)

    # If weekday after or exactly at 16:00
    if local_time >= time(16, 0):
        days_ahead = 3 if dt.weekday() == 4 else 1
        return datetime.combine(local_date + timedelta(days=days_ahead), time(8, 0), tzinfo=waw)

    return dt

def add_business_hours(start_dt: datetime, add_hours: int) -> datetime:
    waw = ZoneInfo("Europe/Warsaw")
    current_dt = start_dt.astimezone(waw)
    current_dt = get_next_business_opening(current_dt)

    remaining_seconds = add_hours * 3600

    while remaining_seconds > 0:
        closing_time = datetime.combine(current_dt.date(), time(16, 0), tzinfo=waw)
        seconds_to_close = int((closing_time - current_dt).total_seconds())

        if remaining_seconds <= seconds_to_close:
            current_dt += timedelta(seconds=remaining_seconds)
            remaining_seconds = 0
        else:
            remaining_seconds -= seconds_to_close
            days_ahead = 3 if current_dt.weekday() == 4 else 1
            next_date = current_dt.date() + timedelta(days=days_ahead)
            current_dt = datetime.combine(next_date, time(8, 0), tzinfo=waw)

    return current_dt.astimezone(timezone.utc)

def compute_priority(impact: int, urgency: int, vip: bool) -> str:
    # Priority Matrix
    matrix = {
        (1, 1): "P1", (1, 2): "P2", (1, 3): "P3",
        (2, 1): "P2", (2, 2): "P3", (2, 3): "P4",
        (3, 1): "P3", (3, 2): "P4", (3, 3): "P4",
    }
    prio = matrix[(impact, urgency)]

    # C3 = vip: VIP tickets at P3 or P4 upgrade to P2
    if vip and prio in ("P3", "P4"):
        prio = "P2"

    return prio

# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok", "service": "svcdesk"}

@app.post("/tickets", status_code=201, response_model=Ticket)
async def create_ticket(ticket_in: TicketCreate, now: datetime = Depends(get_now)):
    priority = compute_priority(ticket_in.impact, ticket_in.urgency, ticket_in.reporter.vip)

    # C1 = wallclock for P1, business hours for others
    if priority == "P1":
        ack_due = now + timedelta(minutes=15)
        res_due = now + timedelta(hours=4)
    elif priority == "P2":
        ack_due = add_business_hours(now, 1)
        res_due = add_business_hours(now, 8)
    elif priority == "P3":
        ack_due = add_business_hours(now, 4)
        res_due = add_business_hours(now, 24)
    else: # P4
        ack_due = add_business_hours(now, 8)
        res_due = add_business_hours(now, 72)

    ticket_id = str(uuid.uuid4())
    ticket = Ticket(
        id=ticket_id,
        title=ticket_in.title,
        description=ticket_in.description,
        reporter=ticket_in.reporter,
        impact=ticket_in.impact,
        urgency=ticket_in.urgency,
        priority=priority,
        state="new",
        created_at=now,
        related_to=ticket_in.related_to,
        sla=SLA(ack_due_at=ack_due, resolve_due_at=res_due)
    )

    tickets_db[ticket_id] = ticket
    return ticket

@app.get("/tickets", response_model=List[Ticket])
async def list_tickets(state: Optional[str] = None, priority: Optional[str] = None):
    res = []
    for t in tickets_db.values():
        if state and t.state != state:
            continue
        if priority and t.priority != priority:
            continue
        res.append(t)
    return res

@app.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")
    return tickets_db[ticket_id]

@app.get("/tickets/{ticket_id}/sla")
async def get_ticket_sla(ticket_id: str, now: datetime = Depends(get_now)):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")

    t = tickets_db[ticket_id]

    # Evaluate Ack breach
    if t.acknowledged_at:
        ack_breached = t.acknowledged_at > t.sla.ack_due_at
    else:
        ack_breached = now > t.sla.ack_due_at

    # Evaluate Resolve breach
    if t.state in ("resolved", "closed"):
        resolve_breached = t.resolved_at > t.sla.resolve_due_at
    else:
        resolve_breached = now > t.sla.resolve_due_at

    # Evaluate paused (P1 wallclock is never paused)
    paused = False
    if t.priority != "P1" and t.state not in ("resolved", "closed"):
        waw_now = now.astimezone(ZoneInfo("Europe/Warsaw"))
        if waw_now.weekday() >= 5 or waw_now.time() < time(8, 0) or waw_now.time() >= time(16, 0):
            paused = True

    return {
        "priority": t.priority,
        "ack_due_at": t.sla.ack_due_at.isoformat().replace("+00:00", "Z"),
        "resolve_due_at": t.sla.resolve_due_at.isoformat().replace("+00:00", "Z"),
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused
    }

# --- State Machine Transitions ---

@app.post("/tickets/{ticket_id}/ack", response_model=Ticket)
async def ack_ticket(ticket_id: str, now: datetime = Depends(get_now)):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")
    t = tickets_db[ticket_id]
    if t.state != "new":
        raise ErrorResponseException(409, "invalid_transition", "Cannot acknowledge")
    t.state = "acknowledged"
    t.acknowledged_at = now
    return t

@app.post("/tickets/{ticket_id}/start", response_model=Ticket)
async def start_ticket(ticket_id: str, now: datetime = Depends(get_now)):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")
    t = tickets_db[ticket_id]
    if t.state != "acknowledged":
        raise ErrorResponseException(409, "invalid_transition", "Cannot start")
    t.state = "in_progress"
    return t

@app.post("/tickets/{ticket_id}/resolve", response_model=Ticket)
async def resolve_ticket(ticket_id: str, now: datetime = Depends(get_now)):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")
    t = tickets_db[ticket_id]
    if t.state != "in_progress":
        raise ErrorResponseException(409, "invalid_transition", "Cannot resolve")
    t.state = "resolved"
    t.resolved_at = now
    return t

@app.post("/tickets/{ticket_id}/close", response_model=Ticket)
async def close_ticket(ticket_id: str, now: datetime = Depends(get_now)):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")
    t = tickets_db[ticket_id]
    if t.state != "resolved":
        raise ErrorResponseException(409, "invalid_transition", "Cannot close")
    t.state = "closed"
    t.closed_at = now
    return t

@app.post("/tickets/{ticket_id}/reopen", response_model=Ticket)
async def reopen_ticket(ticket_id: str, now: datetime = Depends(get_now)):
    if ticket_id not in tickets_db:
        raise ErrorResponseException(404, "not_found", "Ticket not found")
    t = tickets_db[ticket_id]

    # C2 = immutable: reopen only allowed from 'resolved', and only within 7 days
    if t.state == "resolved":
        if now > t.resolved_at + timedelta(days=7):
            raise ErrorResponseException(409, "reopen_window_expired", "7-day window passed")

        t.state = "in_progress"
        t.resolved_at = None
        t.closed_at = None
        return t

    # Any other state (including 'closed') is invalid under C2 = immutable
    raise ErrorResponseException(409, "invalid_transition", "Cannot reopen")