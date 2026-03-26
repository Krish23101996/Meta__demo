from env.models import EmailRecord, TaskDefinition


def build_task() -> TaskDefinition:
    return TaskDefinition(
        task_id="hard_security_breach",
        difficulty="hard",
        objective=(
            "Handle a potential security breach with missing indicators: classify "
            "critical security, request missing IOCs, route and escalate safely."
        ),
        email=EmailRecord(
            sender="security_alerts@example.com",
            subject="Possible credential stuffing detected",
            body=(
                "Login anomalies detected from multiple IP ranges. "
                "We suspect credential stuffing but IOC list is incomplete."
            ),
        ),
        expected_category="security",
        expected_priority="critical",
        require_assign=True,
        expected_assignee="security_incident_response",
        require_escalate=True,
        expected_escalation_target="security_incident_response",
        require_request_info=True,
        requires_close=True,
    )
