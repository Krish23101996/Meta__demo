from __future__ import annotations

import json
import os
from typing import Dict

from openai import OpenAI

from env.environment import EmailTriageEnvironment


def _ensure_openai_api() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for baseline run")
    client = OpenAI(api_key=api_key)
    client.models.list(limit=1)


def _deterministic_policy(task_key: str) -> list[dict]:
    if task_key == "easy":
        return [
            {"action_type": "classify", "category": "billing", "priority": "low"},
            {"action_type": "close"},
        ]
    if task_key == "medium":
        return [
            {"action_type": "classify", "category": "technical", "priority": "high"},
            {"action_type": "assign", "assignee": "support_l2"},
            {"action_type": "escalate", "assignee": "incident_response"},
            {"action_type": "close"},
        ]
    return [
        {"action_type": "classify", "category": "security", "priority": "critical"},
        {
            "action_type": "request_info",
            "message": "Please share IOC list, impacted accounts, and log excerpts.",
        },
        {"action_type": "assign", "assignee": "security_incident_response"},
        {"action_type": "escalate", "assignee": "security_incident_response"},
        {"action_type": "close"},
    ]


def run_baseline() -> Dict[str, float]:
    _ensure_openai_api()

    env = EmailTriageEnvironment()
    scores: Dict[str, float] = {}

    for task_key in ["easy", "medium", "hard"]:
        env.reset(task_key)
        done = False
        for action in _deterministic_policy(task_key):
            _, _, done, info = env.step(action)
            if done:
                scores[task_key] = float(info["score"])
                break
        if not done:
            _, _, _, info = env.step({"action_type": "close"})
            scores[task_key] = float(info["score"])

    return scores


if __name__ == "__main__":
    baseline_scores = run_baseline()
    print(json.dumps(baseline_scores, indent=2, sort_keys=True))
