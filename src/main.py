# ai-generated: 100% - Generated using Gemini, implemented DORA metrics and edge cases

import os
import uuid
from datetime import datetime, timezone, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any, Set, Tuple
from fastapi import FastAPI, Request, Depends, Body
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator

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

# --- Lab 1 Pydantic Models ---

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

# --- Lab 2 Pydantic Models ---

class MetricWindow(BaseModel):
    model_config = ConfigDict(extra='ignore')
    from_: str = Field(alias="from")
    to: str

class DoraMetricsRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')
    window: MetricWindow
    events: List[Dict[str, Any]]

# --- Helpers ---

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

def parse_iso(dt_str: str) -> datetime:
    if dt_str.endswith('Z'):
        dt_str = dt_str[:-1] + '+00:00'
    return datetime.fromisoformat(dt_str)

def calc_median(values: List[float]) -> Optional[int]:
    if not values:
        return None
    values.sort()
    n = len(values)
    if n % 2 == 1:
        return int(round(values[n // 2]))
    else:
        return int(round((values[n // 2 - 1] + values[n // 2]) / 2.0))

def calc_ratio(num: float, den: float) -> Optional[float]:
    if den == 0:
        return None
    return round(num / den, 6)

# --- Lab 1 Business Logic Helpers ---
# (Pominięte szczegóły implementacji z Lab 1, pozostają bez zmian)
def get_next_business_opening(dt: datetime) -> datetime:
    waw = ZoneInfo("Europe/Warsaw")
    dt = dt.astimezone(waw)
    local_date = dt.date()
    local_time = dt.time()
    if dt.weekday() >= 5:
        days_ahead = 7 - dt.weekday()
        return datetime.combine(local_date + timedelta(days=days_ahead), time(8, 0), tzinfo=waw)
    if local_time < time(8, 0):
        return datetime.combine(local_date, time(8, 0), tzinfo=waw)
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
    matrix = {
        (1, 1): "P1", (1, 2): "P2", (1, 3): "P3",
        (2, 1): "P2", (2, 2): "P3", (2, 3): "P4",
        (3, 1): "P3", (3, 2): "P4", (3, 3): "P4",
    }
    prio = matrix[(impact, urgency)]
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

    if priority == "P1":
        ack_due = now + timedelta(minutes=15)
        res_due = now + timedelta(hours=4)
    elif priority == "P2":
        ack_due = add_business_hours(now, 1)
        res_due = add_business_hours(now, 8)
    elif priority == "P3":
        ack_due = add_business_hours(now, 4)
        res_due = add_business_hours(now, 24)
    else:
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

    if t.acknowledged_at:
        ack_breached = t.acknowledged_at > t.sla.ack_due_at
    else:
        ack_breached = now > t.sla.ack_due_at

    if t.state in ("resolved", "closed"):
        resolve_breached = t.resolved_at > t.sla.resolve_due_at
    else:
        resolve_breached = now > t.sla.resolve_due_at

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
    if t.state == "resolved":
        if now > t.resolved_at + timedelta(days=7):
            raise ErrorResponseException(409, "reopen_window_expired", "7-day window passed")
        t.state = "in_progress"
        t.resolved_at = None
        t.closed_at = None
        return t
    raise ErrorResponseException(409, "invalid_transition", "Cannot reopen")

# --- Lab 2: DORA Endpoints ---

@app.get("/dora/ticket-events")
async def export_ticket_events():
    events = []
    for t in tickets_db.values():
        if t.created_at:
            events.append({"ticket_id": t.id, "at": t.created_at, "phase": "created", "priority": t.priority, "state": "new"})
        if t.acknowledged_at:
            events.append({"ticket_id": t.id, "at": t.acknowledged_at, "phase": "acknowledged", "priority": t.priority, "state": "acknowledged"})
        if t.resolved_at:
            events.append({"ticket_id": t.id, "at": t.resolved_at, "phase": "resolved", "priority": t.priority, "state": "resolved"})
        if t.closed_at:
            events.append({"ticket_id": t.id, "at": t.closed_at, "phase": "closed", "priority": t.priority, "state": "closed"})

    events.sort(key=lambda x: (x["at"], x["ticket_id"]))

    # Convert dates to ISO 8601 strings
    for e in events:
        e["at"] = e["at"].isoformat().replace("+00:00", "Z")

    return events

@app.post("/dora/metrics")
async def calculate_dora_metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise ErrorResponseException(400, "validation", "Invalid JSON")

    if not isinstance(body, dict) or "window" not in body or "events" not in body:
        raise ErrorResponseException(400, "validation", "Missing window or events")
    if not isinstance(body["events"], list):
        raise ErrorResponseException(400, "validation", "Events must be a list")

    try:
        w_from = parse_iso(body["window"]["from"])
        w_to = parse_iso(body["window"]["to"])
        if w_to <= w_from:
            raise ErrorResponseException(400, "validation", "to must be after from")
    except Exception:
        raise ErrorResponseException(400, "validation", "Invalid window format")

    # De-duplicate events by event_id (first occurrence wins)
    events_by_id = {}
    for ev in body["events"]:
        try:
            ev["at_dt"] = parse_iso(ev["at"])
            eid = ev["event_id"]
            if eid not in events_by_id:
                events_by_id[eid] = ev
        except Exception:
            raise ErrorResponseException(400, "validation", "Malformed event")

    commits = {}
    deployments = {}
    incidents = {}

    for ev in events_by_id.values():
        if ev["type"] == "commit":
            commits[ev["sha"]] = ev
        elif ev["type"] == "deployment":
            deployments[ev["deployment_id"]] = ev
        elif ev["type"] == "incident":
            inc_id = ev["incident_id"]
            if inc_id not in incidents:
                incidents[inc_id] = {"id": inc_id, "opened": None, "resolved": None, "deployments": []}
            if ev["phase"] == "opened":
                incidents[inc_id]["opened"] = ev["at_dt"]
                incidents[inc_id]["deployments"].extend(ev.get("deployments", []))
            elif ev["phase"] == "resolved":
                incidents[inc_id]["resolved"] = ev["at_dt"]

    # Validate well-formedness
    for ev in deployments.values():
        for sha in ev.get("commits", []):
            if sha not in commits:
                raise ErrorResponseException(400, "validation", f"Unknown commit sha: {sha}")
        cb = ev.get("caused_by")
        if cb and cb not in incidents:
            raise ErrorResponseException(400, "validation", f"Unknown incident id: {cb}")

    for ev in commits.values():
        rev = ev.get("reverts")
        cid = ev.get("change_id")
        if rev and rev not in commits:
            raise ErrorResponseException(400, "validation", f"Unknown revert sha: {rev}")
        if rev is None and cid is None:
            raise ErrorResponseException(400, "validation", "Commit must have change_id")
        if rev is not None and cid is not None:
            raise ErrorResponseException(400, "validation", "Revert cannot have change_id")

    for inc in incidents.values():
        for d_id in inc.get("deployments", []):
            if d_id not in deployments:
                raise ErrorResponseException(400, "validation", f"Unknown deployment id: {d_id}")

    # Process Commits (E2 - revert chains)
    revert_chains_collapsed = 0
    change_first_commit = {}

    def resolve_change_id(sha: str, visited: Set[str]) -> Optional[str]:
        if sha in visited: return None # prevent infinite loop
        visited.add(sha)
        c = commits.get(sha)
        if not c: return None
        if c.get("reverts"):
            return resolve_change_id(c["reverts"], visited)
        return c.get("change_id")

    for sha, c in commits.items():
        if c.get("reverts"):
            revert_chains_collapsed += 1

        cid = resolve_change_id(sha, set())
        c["resolved_change_id"] = cid

        if cid:
            if cid not in change_first_commit or c["at_dt"] < change_first_commit[cid]:
                change_first_commit[cid] = c["at_dt"]

    # Process Deployments
    sorted_deployments = sorted(deployments.values(), key=lambda x: x["at_dt"])

    prod_deployments = []
    for d in sorted_deployments:
        if d.get("environment") == "production":
            prod_deployments.append(d)

    seen_shas_in_prod = set()
    seen_changes_in_prod = set()

    lead_time_pairs_values = []
    negative_lead_time_pairs = 0
    commits_never_on_main = set()
    deployments_without_commits = 0
    rework_deployments = 0

    true_lead_time_values = []
    changes_delivered_in_window = 0

    for d in prod_deployments:
        d_is_success = (d["outcome"] == "success")
        d_in_window = (w_from <= d["at_dt"] < w_to)

        if d_in_window and d.get("unplanned") and d.get("caused_by"):
            rework_deployments += 1

        if not d.get("commits") and d_in_window:
            deployments_without_commits += 1

        for sha in d.get("commits", []):
            c = commits[sha]

            if c.get("branch") != "main":
                commits_never_on_main.add(sha)

            if d_is_success:
                # E1 / R-08 Lead Time Pairs
                if sha not in seen_shas_in_prod:
                    seen_shas_in_prod.add(sha)
                    if d_in_window:
                        lt = (d["at_dt"] - c["at_dt"]).total_seconds()
                        if lt < 0:
                            negative_lead_time_pairs += 1
                            lt = 0
                        lead_time_pairs_values.append(lt)

                # R-17 Ground Truth Lead Time
                cid = c.get("resolved_change_id")
                if cid and cid not in seen_changes_in_prod:
                    seen_changes_in_prod.add(cid)
                    if d_in_window:
                        changes_delivered_in_window += 1
                        tlt = (d["at_dt"] - change_first_commit[cid]).total_seconds()
                        if tlt < 0:
                            tlt = 0
                        true_lead_time_values.append(tlt)

    prod_deps_in_window = [d for d in prod_deployments if w_from <= d["at_dt"] < w_to]
    total_prod_deps = len(prod_deps_in_window)
    successful_deps = sum(1 for d in prod_deps_in_window if d["outcome"] == "success")
    failed_deps = sum(1 for d in prod_deps_in_window if d["outcome"] == "failure")

    # Process Incidents and Recovery Time (E5, E6)
    recovery_times = []
    open_failures = 0

    for d in prod_deps_in_window:
        if d["outcome"] == "failure":
            # Find covering incident
            covering_inc = None
            for inc in incidents.values():
                if inc["opened"] and d["deployment_id"] in inc.get("deployments", []):
                    if covering_inc is None:
                        covering_inc = inc
                    else:
                        if inc["opened"] < covering_inc["opened"]:
                            covering_inc = inc
                        elif inc["opened"] == covering_inc["opened"] and inc["id"] < covering_inc["id"]:
                            covering_inc = inc

            if covering_inc and covering_inc.get("resolved"):
                rt = (covering_inc["resolved"] - d["at_dt"]).total_seconds()
                if rt < 0: rt = 0
                recovery_times.append(rt)
            else:
                open_failures += 1

    # Overlapping incidents (E6)
    overlapping_incident_pairs = 0
    inc_list = list(incidents.values())
    for i in range(len(inc_list)):
        for j in range(i + 1, len(inc_list)):
            incA = inc_list[i]
            incB = inc_list[j]
            if not incA["opened"] or not incB["opened"]: continue

            endA = incA["resolved"] if incA["resolved"] else w_to
            endB = incB["resolved"] if incB["resolved"] else w_to

            if incA["opened"] < endB and incB["opened"] < endA:
                overlapping_incident_pairs += 1

    # Final calculations
    window_days = (w_to - w_from).total_seconds() / 86400.0
    df = calc_ratio(total_prod_deps, window_days) if total_prod_deps > 0 else 0.0
    cfr = calc_ratio(failed_deps, total_prod_deps) if total_prod_deps > 0 else None
    drr = calc_ratio(rework_deployments, total_prod_deps) if total_prod_deps > 0 else None

    # Count unique changes
    all_changes = set(c.get("resolved_change_id") for c in commits.values() if c.get("resolved_change_id"))

    response = {
        "spec_version": "1.0.0",
        "window": {"from": body["window"]["from"], "to": body["window"]["to"]},
        "deployment_frequency_per_day": df,
        "change_lead_time_seconds_p50": calc_median(lead_time_pairs_values),
        "failed_deployment_recovery_time_seconds_p50": calc_median(recovery_times),
        "change_fail_rate": cfr,
        "deployment_rework_rate": drr,
        "counts": {
            "deployments": total_prod_deps,
            "successful_deployments": successful_deps,
            "failed_deployments": failed_deps,
            "recovered_failures": len(recovery_times),
            "open_failures": open_failures,
            "rework_deployments": rework_deployments,
            "lead_time_pairs": len(lead_time_pairs_values),
            "changes": len(all_changes)
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": deployments_without_commits,
            "commits_never_on_main": len(commits_never_on_main),
            "revert_chains_collapsed": revert_chains_collapsed,
            "overlapping_incident_pairs": overlapping_incident_pairs
        },
        "ground_truth": {
            "changes_delivered": changes_delivered_in_window,
            "true_change_lead_time_seconds_p50": calc_median(true_lead_time_values)
        }
    }

    return response