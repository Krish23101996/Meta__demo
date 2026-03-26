from __future__ import annotations

from env.models import TaskDefinition


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def score_task(task: TaskDefinition, env_state: dict) -> float:
    score = 0.0

    if env_state.get("category_correct", False):
        score += 0.30

    if env_state.get("priority_correct", False):
        score += 0.20

    if task.require_assign:
        if env_state.get("assigned_correct", False):
            score += 0.20
        elif env_state.get("assigned_any", False):
            score += 0.10
    else:
        score += 0.20

    if task.require_escalate:
        if env_state.get("escalated_correct", False):
            score += 0.20
        elif env_state.get("escalated_any", False):
            score += 0.10
    else:
        score += 0.20

    if not env_state.get("harmful_action", False):
        if env_state.get("closed_valid", False):
            score += 0.10
        elif env_state.get("closed_any", False):
            score += 0.05

    return _clamp(score, 0.0, 1.0)
