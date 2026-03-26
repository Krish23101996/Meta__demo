from __future__ import annotations

from typing import Dict, Tuple

from env.models import Action, Observation, Reward, TaskDefinition
from grader.grader import score_task
from tasks.easy_task import build_task as build_easy_task
from tasks.hard_task import build_task as build_hard_task
from tasks.medium_task import build_task as build_medium_task


class EmailTriageEnvironment:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskDefinition] = {
            "easy": build_easy_task(),
            "medium": build_medium_task(),
            "hard": build_hard_task(),
        }
        self._allowed_actions = ["classify", "assign", "request_info", "close", "escalate"]
        self._max_steps = 12
        self.reset("easy")

    def reset(self, task_name: str = "easy") -> Observation:
        if task_name not in self._tasks:
            raise ValueError(f"Unknown task '{task_name}'. Expected one of {list(self._tasks.keys())}")

        self._task = self._tasks[task_name]
        self._history = []
        self._steps = 0
        self._done = False
        self._score = 0.0
        self._total_reward = 0.0
        self._state = {
            "category_correct": False,
            "priority_correct": False,
            "assigned_any": False,
            "assigned_correct": False,
            "escalated_any": False,
            "escalated_correct": False,
            "requested_info": False,
            "closed_any": False,
            "closed_valid": False,
            "harmful_action": False,
            "invalid_actions": 0,
            "policy_violations": 0,
            "task": self._task.task_id,
        }
        return self._observation("Environment reset")

    def _observation(self, previous_outcome: str) -> Observation:
        return Observation(
            task_id=self._task.task_id,
            objective=self._task.objective,
            email=self._task.email,
            allowed_actions=self._allowed_actions,
            previous_outcome=previous_outcome,
            progress={"steps": self._steps, "max_steps": self._max_steps},
        )

    def state(self) -> dict:
        return {
            "task": self._task.model_dump(),
            "steps": self._steps,
            "done": self._done,
            "score": self._score,
            "total_reward": round(self._total_reward, 4),
            "history": list(self._history),
            "flags": dict(self._state),
        }

    def step(self, action: Action | dict) -> Tuple[Observation, Reward, bool, dict]:
        if self._done:
            obs = self._observation("Episode already completed")
            reward = Reward(value=0.0, reason="no-op-after-done", done=True)
            return obs, reward, True, {"score": self._score}

        self._steps += 1

        try:
            parsed = action if isinstance(action, Action) else Action.model_validate(action)
        except Exception:
            self._state["invalid_actions"] += 1
            r = self._apply_reward(-0.15, "invalid-action-schema")
            done = self._check_termination()
            return self._observation("Invalid action schema"), r, done, {"score": self._score}

        reward_delta = 0.0
        outcome = "action-processed"

        if parsed.action_type == "classify":
            if parsed.category is None or parsed.priority is None:
                self._state["invalid_actions"] += 1
                reward_delta -= 0.15
                outcome = "invalid-classify-missing-fields"
            else:
                if parsed.category == self._task.expected_category:
                    self._state["category_correct"] = True
                if parsed.priority == self._task.expected_priority:
                    self._state["priority_correct"] = True

                if self._state["category_correct"] and self._state["priority_correct"]:
                    reward_delta += 0.20
                    outcome = "correct-classification"
                elif self._state["category_correct"] or self._state["priority_correct"]:
                    reward_delta += 0.10
                    outcome = "partial-classification"
                else:
                    outcome = "incorrect-classification"

        elif parsed.action_type == "assign":
            if not parsed.assignee:
                self._state["invalid_actions"] += 1
                reward_delta -= 0.15
                outcome = "invalid-assign-missing-assignee"
            else:
                self._state["assigned_any"] = True
                if parsed.assignee == self._task.expected_assignee:
                    self._state["assigned_correct"] = True
                    reward_delta += 0.15
                    outcome = "correct-assignment"
                else:
                    reward_delta += 0.05
                    outcome = "partial-assignment"

        elif parsed.action_type == "escalate":
            if not parsed.assignee:
                self._state["invalid_actions"] += 1
                reward_delta -= 0.15
                outcome = "invalid-escalate-missing-target"
            else:
                self._state["escalated_any"] = True
                if parsed.assignee == self._task.expected_escalation_target:
                    self._state["escalated_correct"] = True
                    reward_delta += 0.20
                    outcome = "correct-escalation"
                else:
                    reward_delta += 0.10
                    outcome = "partial-escalation"

        elif parsed.action_type == "request_info":
            if not parsed.message:
                self._state["invalid_actions"] += 1
                reward_delta -= 0.15
                outcome = "invalid-request-info-missing-message"
            else:
                self._state["requested_info"] = True
                if self._task.require_request_info:
                    reward_delta += 0.10
                    outcome = "useful-request-info"
                else:
                    reward_delta += 0.02
                    outcome = "optional-request-info"

        elif parsed.action_type == "close":
            self._state["closed_any"] = True
            missing_requirements = self._missing_close_requirements()
            if self._task.expected_priority == "critical" and missing_requirements:
                self._state["harmful_action"] = True
                reward_delta -= 0.30
                outcome = "harmful-close-critical-incident"
            elif missing_requirements:
                self._state["policy_violations"] += 1
                reward_delta -= 0.20
                outcome = f"policy-violation-close-before-{','.join(missing_requirements)}"
            else:
                self._state["closed_valid"] = True
                reward_delta += 0.10
                outcome = "valid-close"

        self._history.append(parsed.model_dump())
        reward = self._apply_reward(reward_delta, outcome)
        done = self._check_termination()
        return self._observation(outcome), reward, done, {"score": self._score}

    def _missing_close_requirements(self) -> list[str]:
        missing = []
        if not self._state["category_correct"] or not self._state["priority_correct"]:
            missing.append("classification")
        if self._task.require_assign and not self._state["assigned_correct"]:
            missing.append("assignment")
        if self._task.require_escalate and not self._state["escalated_correct"]:
            missing.append("escalation")
        if self._task.require_request_info and not self._state["requested_info"]:
            missing.append("request_info")
        return missing

    def _apply_reward(self, delta: float, reason: str) -> Reward:
        self._total_reward += delta
        return Reward(value=round(delta, 4), reason=reason, done=self._done)

    def _check_termination(self) -> bool:
        closed = self._state["closed_valid"]
        timed_out = self._steps >= self._max_steps
        if closed or timed_out:
            self._done = True
            self._score = round(score_task(self._task, self._state), 4)
            self._total_reward += self._score
        return self._done
