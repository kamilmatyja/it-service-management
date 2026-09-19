---
svcdesk_decisions:
  C1: wallclock      # wallclock | business
  C2: immutable      # reopen | immutable
  C3: vip            # matrix | vip
---
<!-- ai-generated: 20% - I choose wariants, AI generated -->

# Decisions

## C1 - SLA clock for P1

**Decision:** We implemented the wall-clock approach for P1 tickets, meaning their SLA targets run continuously 24/7 without any pauses.

**Rejected alternative:** Using the business-hours clock for P1 tickets, which would pause the SLA tracking over the weekend and outside of standard working hours.

**Reason:** A P1 ticket indicates that work has stopped for the entire organisation. Pausing the clock over the weekend would misrepresent the critical nature of the outage and delay the emergency response.

**Service owner:** IT Operations Director, because they are responsible for ensuring critical organizational systems are running 24/7 and managing the budgets for on-call engineers.

**Customer outcome:** The organisation gets immediate, around-the-clock attention for critical outages. Emergency tickets will not sit ignored until Monday morning while the business loses money.

## C2 - Closed tickets and reopening

**Decision:** Closed tickets are strictly immutable and cannot be reopened by the reporter or the agent under any circumstances.

**Rejected alternative:** Allowing a closed ticket to be reopened within a 7-day window, returning it to the in-progress state.

**Reason:** Reaching the "closed" state means the reporter has already confirmed the fix. If the issue reoccurs after closure, it is technically a new incident. It should be tracked separately using the `related_to` field to maintain accurate resolution metrics.

**Service owner:** Service Desk Manager, because they are responsible for the accuracy of incident resolution metrics, reporting, and the daily workflow of the desk agents.

**Customer outcome:** The organisation benefits from highly accurate reporting on how many distinct incidents actually occurred. Customers receive dedicated attention on a fresh ticket rather than resurrecting a closed one.

## C3 - VIP reporters and the priority matrix

**Decision:** Tickets reported by VIP users that are initially calculated as P3 or P4 by the matrix are automatically upgraded to P2.

**Rejected alternative:** Strictly following the priority matrix for everyone, which would treat VIP reporters exactly the same as standard users.

**Reason:** Executives and key stakeholders often report issues that seem low impact technically but have extremely high business visibility. Upgrading them ensures their requests do not languish in the standard queue, avoiding political friction.

**Service owner:** Chief Information Officer (CIO), as they manage executive stakeholder relationships and define the acceptable service level agreements for top-tier management.

**Customer outcome:** VIP reporters receive expedited resolution for their issues, preventing executive frustration. While standard users might see slight delays, the overall business leadership remains productive.