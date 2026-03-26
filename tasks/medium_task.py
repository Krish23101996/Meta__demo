from env.models import EmailRecord, TaskDefinition


def build_task() -> TaskDefinition:
    return TaskDefinition(
        task_id="medium_outage_triage",
        difficulty="medium",
        objective=(
            "Triage potential service outage: classify correctly, assign to L2, "
            "and escalate to incident queue before closure."
        ),
        email=EmailRecord(
            sender="ops_manager@example.com",
            subject="Intermittent 502 errors in checkout",
            body=(
                "We are seeing intermittent 502 errors in checkout across regions. "
                "Impact appears high and ongoing."
            ),
        ),
        expected_category="technical",
        expected_priority="high",
        require_assign=True,
        expected_assignee="support_l2",
        require_escalate=True,
        expected_escalation_target="incident_response",
        require_request_info=False,
        requires_close=True,
    )
