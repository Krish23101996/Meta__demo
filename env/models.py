from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ActionType = Literal["classify", "assign", "request_info", "close", "escalate"]
CategoryType = Literal["billing", "technical", "security", "compliance", "general"]
PriorityType = Literal["low", "medium", "high", "critical"]


class EmailRecord(BaseModel):
    sender: str
    subject: str
    body: str


class TaskDefinition(BaseModel):
    task_id: str
    difficulty: Literal["easy", "medium", "hard"]
    objective: str
    email: EmailRecord
    expected_category: CategoryType
    expected_priority: PriorityType
    require_assign: bool = False
    expected_assignee: Optional[str] = None
    require_escalate: bool = False
    expected_escalation_target: Optional[str] = None
    require_request_info: bool = False
    requires_close: bool = True


class Action(BaseModel):
    action_type: ActionType
    category: Optional[CategoryType] = None
    priority: Optional[PriorityType] = None
    assignee: Optional[str] = None
    message: Optional[str] = None


class Observation(BaseModel):
    task_id: str
    objective: str
    email: EmailRecord
    allowed_actions: List[ActionType]
    previous_outcome: str
    progress: Dict[str, int]


class Reward(BaseModel):
    value: float = Field(ge=-1.0, le=2.0)
    reason: str
    done: bool
