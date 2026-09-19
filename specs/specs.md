<!-- ai-generated: 100% - Generated using Gemini CLI for API specification -->

# Specification for svcdesk API (Lab 1)

This document outlines the API specifications for the svcdesk ticketing system, resolving the inherent contradictions in the initial requirements document.

## C1: SLA clock for P1 (Resolution: wallclock)
For P1 (Critical) tickets, time is of the essence. The SLA clock for P1 tickets will run 24/7 using the wall-clock approach. It will not pause outside of business hours. P1 tickets must be acknowledged within 15 minutes and resolved within 4 hours, regardless of whether they are reported on Monday morning or Friday night. For P2-P4, the standard business-hours clock (Monday-Friday, 08:00-16:00 Europe/Warsaw) applies.

## C2: Closed tickets and reopening (Resolution: reopen)
Users must be able to reopen tickets if a fix fails, even if the ticket was marked as closed. Therefore, the system allows the `reopen` action from both the `resolved` state AND the `closed` state. This action is permitted strictly within a 7-day window after the resolution or closure timestamp. Reopening a ticket returns its state to `in_progress`.

## C3: VIP reporters and the priority matrix (Resolution: vip)
VIP reporters require expedited support. The priority matrix will compute the initial priority based on impact and urgency. However, if `reporter.vip` is true and the computed priority is P3 or P4, the system will automatically upgrade the priority to P2. A computed P1 remains P1.

## General Endpoints
- `GET /health`: Healthcheck endpoint.
- `POST /tickets`: Create a new ticket.
- `GET /tickets`: List tickets with optional filters.
- `GET /tickets/{id}`: Fetch ticket details.
- `GET /tickets/{id}/sla`: Fetch SLA status (breached/paused).
- Transitions: `POST /tickets/{id}/ack`, `/start`, `/resolve`, `/close`, `/reopen`.