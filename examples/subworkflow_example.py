"""
Example demonstrating sub-workflow execution and parallel processing
"""

import asyncio
from microflow import (
    Workflow, task, JSONStateStore,
    subworkflow, parallel_subworkflows,
    workflow_chain, if_node, conditional_task
)


# ========================================
# Data Processing Sub-workflows
# ========================================

def create_data_validation_workflow():
    """Sub-workflow for data validation"""

    @task(name="check_required_fields")
    def check_required_fields(ctx):
        required = ['user_id', 'email', 'data']
        missing = [field for field in required if not ctx.get(field)]

        if missing:
            return {
                "validation_status": "failed",
                "missing_fields": missing,
                "is_valid": False
            }
        else:
            return {
                "validation_status": "passed",
                "missing_fields": [],
                "is_valid": True
            }

    @task(name="validate_email_format")
    def validate_email_format(ctx):
        email = ctx.get("email", "")
        is_valid_email = "@" in email and "." in email  # Simple validation

        return {
            "email_valid": is_valid_email,
            "email_checked": True
        }

    @task(name="sanitize_data")
    def sanitize_data(ctx):
        data = ctx.get("data", {})
        # Simple sanitization
        sanitized = {k: str(v).strip() if isinstance(v, str) else v for k, v in data.items()}

        return {
            "data": sanitized,
            "data_sanitized": True
        }

    # Build validation workflow
    check_required_fields >> validate_email_format >> sanitize_data

    return Workflow([check_required_fields, validate_email_format, sanitize_data],
                   name="data_validation")


def create_notification_workflow():
    """Sub-workflow for sending notifications"""

    @task(name="send_email_notification")
    async def send_email_notification(ctx):
        user_id = ctx.get("user_id")
        print(f"📧 Sending email notification to user {user_id}")
        await asyncio.sleep(0.3)
        return {"email_sent": True}

    @task(name="send_sms_notification")
    async def send_sms_notification(ctx):
        user_id = ctx.get("user_id")
        print(f"📱 Sending SMS notification to user {user_id}")
        await asyncio.sleep(0.2)
        return {"sms_sent": True}

    @task(name="log_notifications")
    def log_notifications(ctx):
        notifications = []
        if ctx.get("email_sent"):
            notifications.append("email")
        if ctx.get("sms_sent"):
            notifications.append("sms")

        return {
            "notifications_logged": True,
            "notification_types": notifications
        }

    # Parallel notifications, then logging
    send_email_notification >> log_notifications
    send_sms_notification >> log_notifications

    return Workflow([send_email_notification, send_sms_notification, log_notifications],
                   name="notification_service")


def create_data_processing_workflow():
    """Sub-workflow for processing user data"""

    @task(name="calculate_user_score")
    def calculate_user_score(ctx):
        data = ctx.get("data", {})
        # Simple scoring algorithm
        score = sum(int(v) if str(v).isdigit() else 0 for v in data.values())
        return {"user_score": score}

    @task(name="determine_user_tier")
    def determine_user_tier(ctx):
        score = ctx.get("user_score", 0)

        if score >= 100:
            tier = "gold"
        elif score >= 50:
            tier = "silver"
        else:
            tier = "bronze"

        return {"user_tier": tier}

    @task(name="update_user_profile")
    async def update_user_profile(ctx):
        user_id = ctx.get("user_id")
        tier = ctx.get("user_tier")
        score = ctx.get("user_score")

        print(f"👤 Updating profile for user {user_id}: {tier} tier (score: {score})")
        await asyncio.sleep(0.4)

        return {"profile_updated": True}

    calculate_user_score >> determine_user_tier >> update_user_profile

    return Workflow([calculate_user_score, determine_user_tier, update_user_profile],
                   name="data_processing")


# ========================================
# Main Workflow Tasks
# ========================================

@task(name="receive_user_data")
async def receive_user_data(ctx):
    """Simulate receiving user data"""
    user_id = ctx.get("user_id", "user123")
    print(f"📥 Receiving data for user: {user_id}")

    await asyncio.sleep(0.2)

    return {
        "email": f"{user_id}@example.com",
        "data": {
            "activity_score": 75,
            "engagement_score": 30,
            "completion_rate": 85
        },
        "timestamp": "2024-01-01T10:00:00Z",
        "data_received": True
    }


# Sub-workflow execution nodes
validation_step = subworkflow(
    workflow_source=create_data_validation_workflow,
    input_keys=["user_id", "email", "data"],
    output_keys=["is_valid", "validation_status", "data"],
    name="validation_subprocess"
)

processing_step = subworkflow(
    workflow_source=create_data_processing_workflow,
    input_keys=["user_id", "data"],
    output_keys=["user_score", "user_tier", "profile_updated"],
    name="processing_subprocess"
)

notification_step = subworkflow(
    workflow_source=create_notification_workflow,
    input_keys=["user_id", "user_tier"],
    name="notification_subprocess"
)


# Conditional processing based on validation
validation_check = if_node(
    condition="ctx.get('is_valid', False)",
    name="check_validation_result",
    true_route="valid",
    false_route="invalid"
)

@conditional_task(route="valid", condition_node="check_validation_result")
@task(name="proceed_with_processing")
def proceed_with_processing(ctx):
    print("✅ Data validation passed - proceeding with processing")
    return {"processing_approved": True}

@conditional_task(route="invalid", condition_node="check_validation_result")
@task(name="handle_invalid_data")
def handle_invalid_data(ctx):
    print(f"❌ Data validation failed: {ctx.get('validation_status')}")
    return {"processing_approved": False, "error_handled": True}


# ========================================
# Parallel Sub-workflow Example
# ========================================

@task(name="prepare_parallel_data")
def prepare_parallel_data(ctx):
    """Prepare data for parallel processing"""
    user_id = ctx.get("user_id")

    # Create different data sets for parallel processing
    datasets = [
        {"user_id": user_id, "data_type": "analytics", "data": {"views": 1000, "clicks": 150}},
        {"user_id": user_id, "data_type": "social", "data": {"likes": 50, "shares": 25}},
        {"user_id": user_id, "data_type": "behavioral", "data": {"sessions": 10, "duration": 300}}
    ]

    return {"parallel_datasets": datasets}


def create_analytics_processor():
    """Processor for analytics data"""
    @task(name="process_analytics")
    def process_analytics(ctx):
        data = ctx.get("data", {})
        ctr = data.get("clicks", 0) / data.get("views", 1)
        return {"ctr": ctr, "analytics_processed": True}

    return Workflow([process_analytics], name="analytics_processor")


def create_social_processor():
    """Processor for social data"""
    @task(name="process_social")
    def process_social(ctx):
        data = ctx.get("data", {})
        engagement = data.get("likes", 0) + data.get("shares", 0)
        return {"engagement_score": engagement, "social_processed": True}

    return Workflow([process_social], name="social_processor")


def create_behavioral_processor():
    """Processor for behavioral data"""
    @task(name="process_behavioral")
    def process_behavioral(ctx):
        data = ctx.get("data", {})
        avg_session = data.get("duration", 0) / data.get("sessions", 1)
        return {"avg_session_duration": avg_session, "behavioral_processed": True}

    return Workflow([process_behavioral], name="behavioral_processor")


parallel_processing = parallel_subworkflows(
    workflows=[
        {
            "source": create_analytics_processor,
            "name": "analytics_parallel",
            "input_keys": ["user_id", "data"],
            "context_mapping": {"parallel_datasets": "datasets"}
        },
        {
            "source": create_social_processor,
            "name": "social_parallel",
            "input_keys": ["user_id", "data"]
        },
        {
            "source": create_behavioral_processor,
            "name": "behavioral_parallel",
            "input_keys": ["user_id", "data"]
        }
    ],
    name="parallel_data_processing",
    max_concurrent=3
)


@task(name="aggregate_parallel_results")
def aggregate_parallel_results(ctx):
    """Aggregate results from parallel processing"""
    results = ctx.get("parallel_results", [])
    successful = [r for r in results if r.get("subworkflow_success")]

    print(f"📊 Parallel processing completed: {len(successful)}/{len(results)} successful")

    aggregate = {"parallel_processing_summary": {
        "total_workflows": len(results),
        "successful": len(successful),
        "success_rate": len(successful) / len(results) if results else 0
    }}

    # Merge specific results
    for result in successful:
        if "ctr" in result:
            aggregate["click_through_rate"] = result["ctr"]
        if "engagement_score" in result:
            aggregate["social_engagement"] = result["engagement_score"]
        if "avg_session_duration" in result:
            aggregate["session_duration"] = result["avg_session_duration"]

    return aggregate


def create_subworkflow_demo():
    """Create a workflow demonstrating sub-workflow capabilities"""

    # Build main workflow
    receive_user_data >> validation_step
    validation_step >> validation_check

    # Conditional branches
    validation_check >> proceed_with_processing
    validation_check >> handle_invalid_data

    # Main processing (only if validation passed)
    proceed_with_processing >> processing_step
    processing_step >> notification_step

    # Parallel processing demo
    receive_user_data >> prepare_parallel_data
    prepare_parallel_data >> parallel_processing
    parallel_processing >> aggregate_parallel_results

    all_tasks = [
        receive_user_data,
        validation_step,
        validation_check,
        proceed_with_processing,
        handle_invalid_data,
        processing_step,
        notification_step,
        prepare_parallel_data,
        parallel_processing,
        aggregate_parallel_results
    ]

    return Workflow(all_tasks, name="subworkflow_demo")


async def main():
    """Run the sub-workflow demonstration"""
    print("=== Sub-workflow and Parallel Processing Demo ===\n")

    store = JSONStateStore("./data")

    # Test scenarios
    test_cases = [
        {
            "name": "Valid User Data",
            "context": {"user_id": "valid_user_001"}
        },
        {
            "name": "Invalid User Data (missing email)",
            "context": {"user_id": "invalid_user_002", "skip_email": True}
        }
    ]

    for i, test_case in enumerate(test_cases):
        print(f"\n🔄 Running Test Case {i+1}: {test_case['name']}")
        print("=" * 60)

        workflow = create_subworkflow_demo()
        run_id = f"subworkflow_demo_{i+1:03d}"

        # Modify behavior for invalid data test
        if "Invalid" in test_case['name']:
            original_receive = receive_user_data.spec.fn

            async def invalid_receive(ctx):
                result = await original_receive(ctx)
                if ctx.get("skip_email"):
                    del result["email"]  # Make data invalid
                return result

            receive_user_data.spec.fn = invalid_receive

        try:
            final_ctx = await workflow.run(
                run_id=run_id,
                store=store,
                initial_ctx=test_case['context']
            )

            print(f"\n✅ Test Case {i+1} completed!")
            print(f"Validation: {final_ctx.get('validation_status', 'unknown')}")
            print(f"Processing approved: {final_ctx.get('processing_approved', False)}")
            print(f"User tier: {final_ctx.get('user_tier', 'unknown')}")
            print(f"Profile updated: {final_ctx.get('profile_updated', False)}")
            print(f"Parallel success rate: {final_ctx.get('parallel_processing_summary', {}).get('success_rate', 0):.1%}")

        except Exception as e:
            print(f"❌ Test Case {i+1} failed: {e}")

    print(f"\n📋 Sub-workflow execution details saved to: {store.data_dir}/runs/")
    print("\n💡 Key Features Demonstrated:")
    print("   ✓ Sub-workflow execution with context mapping")
    print("   ✓ Conditional execution based on validation results")
    print("   ✓ Parallel sub-workflow processing")
    print("   ✓ Error handling and graceful failures")
    print("   ✓ Data aggregation from multiple sources")


if __name__ == "__main__":
    asyncio.run(main())