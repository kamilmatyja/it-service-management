<!-- ai-generated: 100% - Generated using Gemini -->

# svcdesk - Technical Specification (Lab 1)

## 1. Overview
This document serves as the technical specification for the `svcdesk` API. It outlines the core system behaviors required by the business and resolves inherent contradictions found in the initial requirements document (R-01 through R-25). The system is a JSON-based RESTful API running on port 8080, managing IT service tickets with automated SLA tracking and priority assignment.

## 2. Business Rule Resolutions (C1, C2, C3)
The initial requirements presented conflicting logic. As a systems analyst, I have defined the following implementations to resolve these contradictions:

### 2.1 C1: SLA clock for P1 (Resolution: `wallclock`)
**Conflict:** Requirement R-13 states SLA clocks pause outside business hours, while R-14 states P1 tickets must be tracked around the clock (24/7).
**Implementation:** The API will use a **wall-clock** for all P1 tickets. When a P1 ticket is created, its acknowledgement target (15 minutes) and resolution target (4 hours) are calculated continuously, ignoring business hours or weekends. The `paused` state in `/sla` for P1 tickets will always be `false`. For tickets with priority P2, P3, and P4, the API will strictly apply the business-hours clock (Monday to Friday, 08:00 to 16:00, Europe/Warsaw).

### 2.2 C2: Closed tickets and reopening (Resolution: `immutable`)
**Conflict:** Requirement R-09 states a closed ticket is strictly immutable, while R-10 suggests a reporter may reopen a "resolved or closed" ticket within 7 days.
**Implementation:** The API will enforce the **immutable** rule for closed tickets. The `POST /tickets/{id}/reopen` endpoint will only accept tickets in the `resolved` state (provided they are within the 7-day window). If a client attempts to reopen a ticket that has already reached the `closed` state, the API will reject the request with a `409 Conflict` error. Customers must create a new ticket using the `related_to` field if further work is required on a closed issue.

### 2.3 C3: VIP reporters and the priority matrix (Resolution: `vip`)
**Conflict:** Requirement R-05 states priority must be derived *only* from the impact/urgency matrix, while R-06 requires VIP tickets to be at least P2.
**Implementation:** The API will honor the **vip** upgrade rule. During ticket creation (`POST /tickets`), the system will first calculate the base priority using the standard matrix (Impact 1-3, Urgency 1-3). If the resulting priority is P3 or P4, and the payload includes `reporter.vip: true`, the API will automatically elevate the final priority to `P2`. If the matrix yields P1 or P2, the priority remains unchanged. Any `priority` field explicitly sent by the client in the request body is entirely ignored.

## 3. General API Behavior
*   **State Machine:** Tickets must strictly follow the transition path: `new` -> `acknowledged` -> `in_progress` -> `resolved` -> `closed`. Any skipped step (e.g., resolving a new ticket directly) results in a `409 Conflict`.
*   **Timestamps:** All time-based calculations and responses will use RFC 3339 formatting with a `Z` offset indicating UTC.
*   **Test Clock Integration:** To facilitate automated testing, the API will respect the `X-Test-Clock` header to mock the "current time" for individual requests, but only when the `SVCDESK_TEST_CLOCK` environment variable is enabled.
*   **Persistence:** Ticket data must survive container restarts, utilizing a local SQLite database stored in a Docker volume.