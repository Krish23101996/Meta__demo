# DESIGN: OpenEnv Email Triage Environment

## Phase 1 — Real-World Problem Selection

### Chosen problem
**Enterprise Email Triage and Incident Routing**.

This is a practical operations problem: teams receive support/security/compliance emails and must classify urgency, assign ownership, and choose safe handling actions.

---

## Environment Definition

### Environment objective
Given an incoming email queue and policy constraints, the agent should take safe and useful triage actions that maximize task completion quality while minimizing risky handling.

Primary objective:
1. Correctly classify category and priority.
2. Route to the right owner/team when needed.
3. Avoid harmful actions (e.g., closing critical incidents).
4. Complete triage workflow with deterministic scoring.

### Action space
Agent emits one structured action at a time:
- `classify`: assign category and priority to current email
- `assign`: route email to a specific queue/team
- `request_info`: ask sender for missing information
- `close`: close email when resolution criteria are met
- `escalate`: escalate to incident/security/compliance queue

Action fields:
- `action_type` (required)
- `category` (optional for classify)
- `priority` (optional for classify)
- `assignee` (optional for assign/escalate)
- `message` (optional for request_info)

### Observation space
Each step returns a deterministic observation containing:
- Current task id and goal text
- Current email metadata and body
- Allowed actions
- Previous action outcome
- Progress summary (processed count, pending count)

### State representation
Internal state tracks:
- Active task definition
- Queue pointer / current email
- Action history
- Derived facts (classification set, assigned, escalated, closed)
- Running reward total and invalid action count
- Done flag and final score when terminal

---

## Task Design

### Easy task (single-step)
**Scenario:** One billing email with clear intent.
- Expected: classify as `billing`, `low`, then close.
- Low ambiguity and short email.

### Medium task (multi-step)
**Scenario:** Customer support outage hint requiring triage and assignment.
- Expected: classify `technical`, set `high`, assign to `support_l2`, then escalate if outage keywords present.
- Requires multiple coherent actions in sequence.

### Hard task (complex reasoning)
**Scenario:** Potential security breach with missing metadata and compliance implications.
- Expected: classify `security` with `critical`, request_info for missing indicators, assign/escalate to `security_incident_response`, avoid premature close.
- Requires balancing urgency, safety, and policy.

---

## Grader Logic (Deterministic 0.0–1.0)

Scoring is deterministic and rule-based:
- Start at `0.0`
- Add weighted component scores:
  - Classification correctness: `0.30`
  - Priority correctness: `0.20`
  - Routing/assignment correctness: `0.20`
  - Proper escalation behavior: `0.20`
  - Safe completion behavior (no harmful close): `0.10`
- Clamp to `[0.0, 1.0]`

Partial scoring:
- Category correct but priority wrong => keep classification points only.
- Correct escalation target but delayed action => partial escalation points.
- If invalid action emitted, subtract fixed penalty and continue.

No randomness is used anywhere in grading.

---

## Reward Strategy

### Intermediate rewards
Per-step shaping rewards:
- `+0.20` for correct classify action
- `+0.15` for correct assignment
- `+0.20` for correct escalation
- `+0.10` for useful request_info when required
- `+0.10` for valid close at proper stage

### Penalties
- `-0.15` invalid action schema or unsupported action
- `-0.20` policy violation (e.g., close before mandatory escalation)
- `-0.30` harmful action (closing critical security incident)

Terminal reward:
- Add final grader score at episode completion to align step-level shaping with final objective.

All rewards are deterministic and based solely on task config + action history.

---

## Determinism and Safety

- No random task generation; all tasks are static fixtures.
- Grader and reward logic rely only on deterministic comparisons.
- Harmful actions receive explicit negative reward and affect final grade.

