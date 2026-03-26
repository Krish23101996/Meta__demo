from env.models import EmailRecord, TaskDefinition


def build_task() -> TaskDefinition:
    return TaskDefinition(
        task_id="easy_billing_refund",
        difficulty="easy",
        objective="Classify and complete a straightforward billing request safely.",
        email=EmailRecord(
            sender="customer_a@example.com",
            subject="Refund request for duplicate invoice",
            body=(
                "Hi support, I was charged twice for INV-7782. "
                "Please refund the duplicate charge."
            ),
        ),
        expected_category="billing",
        expected_priority="low",
        require_assign=False,
        require_escalate=False,
        require_request_info=False,
        requires_close=True,
    )
