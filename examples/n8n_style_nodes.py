"""
Example demonstrating n8n-style nodes: IF, SWITCH, HTTP, and sub-workflows
"""

import asyncio
from microflow import (
    Workflow, task, JSONStateStore,
    if_node, switch_node, conditional_task,
    http_get, http_post, BearerAuth,
    subworkflow
)


# Sample data fetching task
@task(name="fetch_user_data", max_retries=1)
async def fetch_user_data(ctx):
    """Simulate fetching user data"""
    user_id = ctx.get("user_id", "user123")

    # Simulate API response
    await asyncio.sleep(0.5)

    return {
        "user": {
            "id": user_id,
            "name": "John Doe",
            "email": "john@example.com",
            "status": "active",
            "subscription": "premium",
            "credits": 150
        }
    }


# Create conditional nodes
check_user_status = if_node(
    condition="ctx['user']['status'] == 'active'",
    name="check_user_active",
    true_route="active",
    false_route="inactive"
)

route_by_subscription = switch_node(
    expression="ctx['user']['subscription']",
    cases={
        'free': 'handle_free',
        'premium': 'handle_premium',
        'enterprise': 'handle_enterprise'
    },
    default_route='handle_unknown',
    name="route_subscription"
)

check_credits = if_node(
    condition="ctx['user']['credits'] >= 100",
    name="check_sufficient_credits",
    true_route="sufficient",
    false_route="insufficient"
)


# Conditional tasks based on routing
@conditional_task(route="active", condition_node="check_user_active")
@task(name="process_active_user")
async def process_active_user(ctx):
    """Process active user"""
    print(f"Processing active user: {ctx['user']['name']}")
    return {"processing_status": "active_user_processed"}


@conditional_task(route="inactive", condition_node="check_user_active")
@task(name="handle_inactive_user")
async def handle_inactive_user(ctx):
    """Handle inactive user"""
    print(f"User {ctx['user']['name']} is inactive - sending reactivation email")
    return {"processing_status": "reactivation_sent"}


@conditional_task(route="handle_premium", condition_node="route_subscription")
@task(name="premium_benefits")
async def premium_benefits(ctx):
    """Apply premium benefits"""
    print(f"Applying premium benefits for {ctx['user']['name']}")
    return {
        "benefits_applied": True,
        "discount": 0.2,
        "priority_support": True
    }


@conditional_task(route="handle_free", condition_node="route_subscription")
@task(name="free_tier_limits")
async def free_tier_limits(ctx):
    """Apply free tier limitations"""
    print(f"Applying free tier limits for {ctx['user']['name']}")
    return {
        "benefits_applied": True,
        "discount": 0.0,
        "priority_support": False,
        "usage_limit": 100
    }


@conditional_task(route="sufficient", condition_node="check_sufficient_credits")
@task(name="proceed_with_operation")
async def proceed_with_operation(ctx):
    """Proceed with operation when credits are sufficient"""
    print(f"User has {ctx['user']['credits']} credits - proceeding")
    return {"operation_approved": True}


@conditional_task(route="insufficient", condition_node="check_sufficient_credits")
@task(name="request_payment")
async def request_payment(ctx):
    """Request payment when credits are insufficient"""
    print(f"User has only {ctx['user']['credits']} credits - requesting payment")
    return {"payment_required": True, "required_credits": 100}


# HTTP request nodes
send_notification = http_post(
    url="https://api.example.com/notifications",
    json_data={
        "user_id": "ctx.user.id",
        "message": "Your account has been processed",
        "type": "info"
    },
    auth=BearerAuth("fake_api_token"),
    name="send_notification",
    max_retries=2
)

# For demo, let's create a mock HTTP task instead of real HTTP
@task(name="mock_http_notification")
async def mock_http_notification(ctx):
    """Mock HTTP notification for demo"""
    print(f"📧 Sending notification to {ctx['user']['email']}")
    await asyncio.sleep(0.3)
    return {
        "notification_sent": True,
        "notification_id": "notif_12345"
    }


# Sub-workflow example
def create_audit_workflow():
    """Create a simple audit workflow"""

    @task(name="log_user_action")
    def log_action(ctx):
        print(f"🔍 AUDIT: User {ctx.get('user_id')} - Status: {ctx.get('processing_status')}")
        return {"audit_logged": True, "log_id": f"log_{ctx.get('user_id')}"}

    @task(name="update_metrics")
    def update_metrics(ctx):
        print(f"📊 METRICS: Updated for user {ctx.get('user_id')}")
        return {"metrics_updated": True}

    log_action >> update_metrics
    return Workflow([log_action, update_metrics], name="audit_workflow")


audit_subworkflow = subworkflow(
    workflow_source=create_audit_workflow,
    input_keys=["user_id", "processing_status", "user"],
    name="audit_subprocess"
)


def create_n8n_style_workflow():
    """Create a workflow demonstrating n8n-style nodes"""

    # Build the workflow DAG
    fetch_user_data >> check_user_status

    # Active user path
    check_user_status >> process_active_user
    process_active_user >> route_by_subscription

    # Inactive user path
    check_user_status >> handle_inactive_user

    # Subscription routing
    route_by_subscription >> premium_benefits
    route_by_subscription >> free_tier_limits

    # Credits check for both subscription types
    premium_benefits >> check_credits
    free_tier_limits >> check_credits

    # Credit-based routing
    check_credits >> proceed_with_operation
    check_credits >> request_payment

    # Notifications
    proceed_with_operation >> mock_http_notification
    request_payment >> mock_http_notification
    handle_inactive_user >> mock_http_notification

    # Audit trail
    mock_http_notification >> audit_subworkflow

    # All tasks in the workflow
    all_tasks = [
        fetch_user_data,
        check_user_status,
        process_active_user,
        handle_inactive_user,
        route_by_subscription,
        premium_benefits,
        free_tier_limits,
        check_credits,
        proceed_with_operation,
        request_payment,
        mock_http_notification,
        audit_subworkflow
    ]

    return Workflow(all_tasks, name="n8n_style_demo")


async def main():
    """Run the n8n-style workflow example"""
    print("=== N8N-Style Workflow Demo ===\n")

    # Test scenarios
    test_cases = [
        {
            "name": "Active Premium User with Credits",
            "context": {"user_id": "premium_user_001"}
        },
        {
            "name": "Active Free User with Low Credits",
            "context": {"user_id": "free_user_002"}
        }
    ]

    store = JSONStateStore("./data")

    for i, test_case in enumerate(test_cases):
        print(f"\n🔄 Running Test Case {i+1}: {test_case['name']}")
        print("=" * 60)

        workflow = create_n8n_style_workflow()
        run_id = f"n8n_demo_{i+1:03d}"

        try:
            # Modify test case for different scenarios
            if "Low Credits" in test_case['name']:
                # Override the fetch_user_data for low credits scenario
                original_fetch = fetch_user_data.spec.fn

                async def low_credits_fetch(ctx):
                    result = await original_fetch(ctx)
                    result['user']['credits'] = 50  # Low credits
                    result['user']['subscription'] = 'free'  # Free tier
                    return result

                fetch_user_data.spec.fn = low_credits_fetch

            # Run workflow
            final_ctx = await workflow.run(
                run_id=run_id,
                store=store,
                initial_ctx=test_case['context']
            )

            print(f"\n✅ Test Case {i+1} completed successfully!")
            print(f"Final status: {final_ctx.get('processing_status')}")
            print(f"Operation approved: {final_ctx.get('operation_approved', False)}")
            print(f"Payment required: {final_ctx.get('payment_required', False)}")
            print(f"Notification sent: {final_ctx.get('notification_sent', False)}")
            print(f"Audit logged: {final_ctx.get('audit_logged', False)}")

        except Exception as e:
            print(f"❌ Test Case {i+1} failed: {e}")

    print(f"\n📋 Workflow runs saved to: {store.data_dir}/runs/")


if __name__ == "__main__":
    asyncio.run(main())