# OpenEnv Email Triage Environment

This repository implements a production-style OpenEnv environment for **enterprise email triage and incident routing**.

## Real-world use case
Operations teams receive high volumes of billing, technical, and security emails. This environment simulates deterministic triage decisions:
- classify issue type and priority
- assign the right owner queue
- request missing information when needed
- escalate incidents safely
- close only when policy requirements are met

## Environment API
The environment class is `EmailTriageEnvironment` in `/home/runner/work/Meta__demo/Meta__demo/env/environment.py`.

Supported methods:
- `reset(task_name="easy")`
- `step(action)`
- `state()`

## Action space
Action schema (`Action` model):
- `action_type`: `classify | assign | request_info | close | escalate`
- `category` (for classify)
- `priority` (for classify)
- `assignee` (for assign/escalate)
- `message` (for request_info)

## Observation space
Observation schema (`Observation` model):
- `task_id`
- `objective`
- `email` (sender, subject, body)
- `allowed_actions`
- `previous_outcome`
- `progress` (`steps`, `max_steps`)

## Tasks
- **Easy:** clear billing refund request
- **Medium:** outage triage requiring classify + assign + escalate + close
- **Hard:** security breach triage requiring critical classification, info request, routing, escalation, and safe closure

## Grading and rewards
- Deterministic grader returns score in `[0.0, 1.0]`
- Partial credit for partially correct routing/escalation actions
- Intermediate rewards for correct actions
- Penalties for invalid actions and harmful/policy-violating closes

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Example usage
```python
from env.environment import EmailTriageEnvironment

env = EmailTriageEnvironment()
obs = env.reset("medium")
obs, reward, done, info = env.step({"action_type": "classify", "category": "technical", "priority": "high"})
print(reward, done, info)
```

## Baseline agent
Baseline runner in `/home/runner/work/Meta__demo/Meta__demo/scripts/run_baseline.py`:
- Reads `OPENAI_API_KEY`
- Verifies OpenAI access
- Runs deterministic task policy across all tasks
- Prints reproducible per-task scores

Run:
```bash
export OPENAI_API_KEY=your_key
python scripts/run_baseline.py
```

## Docker
Build and run:
```bash
docker build -t openenv-email-triage .
docker run --rm -e OPENAI_API_KEY=$OPENAI_API_KEY openenv-email-triage
```
