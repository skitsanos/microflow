"""
Comprehensive example demonstrating all the new node types:
Shell, File Operations, Data Transformation, Timing, and Notifications
"""

import asyncio
import json
from pathlib import Path
from microflow import (
    Workflow, task, JSONStateStore,

    # Shell nodes
    shell_command, python_script, git_command,

    # File operation nodes
    write_file, read_file, copy_file, list_directory,

    # Data transformation nodes
    json_parse, json_stringify, csv_parse, data_filter, data_transform,

    # Timing nodes
    delay, wait_for_condition,

    # Conditional nodes
    if_node, conditional_task,

    # Notification nodes (mock for demo)
    simple_email
)


# ========================================
# Setup Tasks
# ========================================

@task(name="create_demo_data")
async def create_demo_data(ctx):
    """Create sample data for the demo"""
    print("📊 Creating demo data...")

    # Sample user data
    users = [
        {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "score": 85, "department": "Engineering"},
        {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "score": 92, "department": "Marketing"},
        {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "score": 78, "department": "Engineering"},
        {"id": 4, "name": "Diana Prince", "email": "diana@example.com", "score": 95, "department": "Sales"},
        {"id": 5, "name": "Eve Wilson", "email": "eve@example.com", "score": 88, "department": "Engineering"}
    ]

    # Sample system metrics
    metrics = {
        "timestamp": "2024-01-01T10:00:00Z",
        "cpu_usage": 65.2,
        "memory_usage": 78.5,
        "disk_usage": 45.8,
        "active_users": len(users),
        "status": "healthy"
    }

    return {
        "users": users,
        "metrics": metrics,
        "demo_ready": True
    }


# ========================================
# Shell Command Demo
# ========================================

# Get system information
get_system_info = shell_command(
    command="uname -a && date && whoami",
    name="get_system_info"
)

# List current directory contents
list_files = shell_command(
    command="ls -la",
    name="list_current_files"
)

# Get Git status (if in a git repo)
check_git_status = git_command(
    git_args=["status", "--porcelain"],
    name="check_git_status"
)


# ========================================
# File Operations Demo
# ========================================

# Write users data to JSON file
write_users_json = write_file(
    file_path="./data/demo_users.json",
    content='{users_json}',  # Will be populated from context
    create_dirs=True,
    name="write_users_file"
)

# Write metrics to JSON file
write_metrics_json = write_file(
    file_path="./data/demo_metrics.json",
    content='{metrics_json}',
    create_dirs=True,
    name="write_metrics_file"
)

# Read back the users file
read_users_back = read_file(
    file_path="./data/demo_users.json",
    name="read_users_back"
)

# List data directory contents
list_data_dir = list_directory(
    dir_path="./data",
    pattern="*.json",
    file_info=True,
    name="list_data_files"
)

# Copy users file to backup
backup_users_file = copy_file(
    source_path="./data/demo_users.json",
    dest_path="./data/demo_users_backup.json",
    name="backup_users_file"
)


# ========================================
# Data Transformation Demo
# ========================================

# Parse JSON from file content
parse_users_json = json_parse(
    json_key="file_content",
    output_key="parsed_users",
    name="parse_users_json"
)

# Filter users by department
filter_engineering_users = data_filter(
    data_key="users",
    filter_condition="item['department'] == 'Engineering'",
    output_key="engineering_users",
    name="filter_engineering_users"
)

# Transform users to add grade
add_user_grades = data_transform(
    data_key="engineering_users",
    transform_expression="{'id': item['id'], 'name': item['name'], 'score': item['score'], 'grade': 'A' if item['score'] >= 90 else 'B' if item['score'] >= 80 else 'C'}",
    output_key="graded_users",
    name="add_user_grades"
)

# Generate CSV data
generate_csv_report = csv_parse(
    csv_key="users_csv_string",
    output_key="users_csv_data",
    name="generate_csv_report"
)


# ========================================
# Conditional Logic Demo
# ========================================

# Check if system metrics are healthy
check_system_health = if_node(
    condition="ctx['metrics']['cpu_usage'] < 80 and ctx['metrics']['memory_usage'] < 85",
    name="check_system_health",
    true_route="healthy",
    false_route="unhealthy"
)

@conditional_task(route="healthy", condition_node="check_system_health")
@task(name="handle_healthy_system")
async def handle_healthy_system(ctx):
    """Handle healthy system status"""
    print("✅ System is healthy!")
    return {"system_status": "healthy", "action_taken": "monitoring"}

@conditional_task(route="unhealthy", condition_node="check_system_health")
@task(name="handle_unhealthy_system")
async def handle_unhealthy_system(ctx):
    """Handle unhealthy system status"""
    print("⚠️ System needs attention!")
    return {"system_status": "unhealthy", "action_taken": "alert_sent"}


# ========================================
# Timing Demo
# ========================================

# Add a delay between operations
processing_delay = delay(
    seconds=1.0,
    name="processing_delay"
)

# Wait for a condition (simulated)
wait_for_processing = wait_for_condition(
    condition_expression="ctx.get('demo_ready', False)",
    check_interval=0.5,
    max_wait_time=5.0,
    name="wait_for_demo_ready"
)


# ========================================
# Helper Tasks for Demo
# ========================================

@task(name="prepare_json_strings")
def prepare_json_strings(ctx):
    """Prepare JSON strings for file writing"""
    users_json = json.dumps(ctx["users"], indent=2)
    metrics_json = json.dumps(ctx["metrics"], indent=2)

    # Create a simple CSV string
    users_csv = "id,name,email,score,department\n"
    for user in ctx["users"]:
        users_csv += f"{user['id']},{user['name']},{user['email']},{user['score']},{user['department']}\n"

    return {
        "users_json": users_json,
        "metrics_json": metrics_json,
        "users_csv_string": users_csv
    }

@task(name="mock_email_notification")
async def mock_email_notification(ctx):
    """Mock email notification for demo"""
    status = ctx.get("system_status", "unknown")
    user_count = len(ctx.get("engineering_users", []))

    print(f"📧 Mock Email Sent:")
    print(f"   To: admin@example.com")
    print(f"   Subject: System Report - Status: {status}")
    print(f"   Body: Engineering team has {user_count} members")
    print(f"   System CPU: {ctx.get('metrics', {}).get('cpu_usage', 'N/A')}%")

    await asyncio.sleep(0.2)  # Simulate email sending

    return {
        "email_sent": True,
        "email_status": status,
        "notification_time": "2024-01-01T10:05:00Z"
    }

@task(name="generate_final_report")
def generate_final_report(ctx):
    """Generate a summary report of all operations"""
    print("\n" + "="*60)
    print("📋 MICROFLOW EXTENDED NODES DEMO REPORT")
    print("="*60)

    # System info
    if ctx.get("shell_stdout"):
        print(f"🖥️  System: {ctx['shell_stdout'].split()[0] if ctx['shell_stdout'] else 'Unknown'}")

    # File operations
    file_count = len(ctx.get("dir_files", []))
    print(f"📁 Files created: {file_count}")

    # Data processing
    total_users = len(ctx.get("users", []))
    eng_users = len(ctx.get("engineering_users", []))
    print(f"👥 Total users: {total_users}, Engineering: {eng_users}")

    # System health
    system_status = ctx.get("system_status", "unknown")
    print(f"🔍 System status: {system_status}")

    # Notifications
    email_sent = ctx.get("email_sent", False)
    print(f"📧 Email notification: {'✅ Sent' if email_sent else '❌ Failed'}")

    print("="*60)
    print("✅ Demo completed successfully!")

    return {
        "report_generated": True,
        "summary": {
            "total_users": total_users,
            "engineering_users": eng_users,
            "files_created": file_count,
            "system_status": system_status,
            "email_sent": email_sent
        }
    }


def create_extended_demo_workflow():
    """Create a comprehensive workflow demonstrating all node types"""

    # Build the workflow DAG

    # 1. Setup and data creation
    create_demo_data >> prepare_json_strings
    create_demo_data >> wait_for_processing

    # 2. Shell operations
    wait_for_processing >> get_system_info
    get_system_info >> list_files
    list_files >> check_git_status

    # 3. File operations
    prepare_json_strings >> write_users_json
    prepare_json_strings >> write_metrics_json
    write_users_json >> read_users_back
    write_users_json >> backup_users_file
    write_metrics_json >> list_data_dir

    # 4. Data transformation
    read_users_back >> parse_users_json
    parse_users_json >> filter_engineering_users
    filter_engineering_users >> add_user_grades

    # 5. System health check
    create_demo_data >> processing_delay
    processing_delay >> check_system_health
    check_system_health >> handle_healthy_system
    check_system_health >> handle_unhealthy_system

    # 6. Final reporting and notifications
    add_user_grades >> mock_email_notification
    handle_healthy_system >> mock_email_notification
    handle_unhealthy_system >> mock_email_notification
    list_data_dir >> generate_final_report
    mock_email_notification >> generate_final_report

    # All tasks in the workflow
    all_tasks = [
        create_demo_data,
        prepare_json_strings,
        wait_for_processing,
        get_system_info,
        list_files,
        check_git_status,
        write_users_json,
        write_metrics_json,
        read_users_back,
        backup_users_file,
        list_data_dir,
        parse_users_json,
        filter_engineering_users,
        add_user_grades,
        processing_delay,
        check_system_health,
        handle_healthy_system,
        handle_unhealthy_system,
        mock_email_notification,
        generate_final_report
    ]

    return Workflow(all_tasks, name="extended_nodes_demo")


async def main():
    """Run the extended nodes demonstration"""
    print("=== Microflow Extended Nodes Demo ===\n")
    print("This demo showcases:")
    print("🐚 Shell/Process execution")
    print("📁 File operations")
    print("🔄 Data transformations")
    print("⏰ Timing and delays")
    print("📧 Notifications")
    print("🔀 Conditional logic")
    print("\n" + "="*50)

    workflow = create_extended_demo_workflow()
    store = JSONStateStore("./data")

    try:
        print("\n🚀 Starting workflow execution...\n")

        final_ctx = await workflow.run(
            run_id="extended_demo_001",
            store=store,
            initial_ctx={
                "demo_name": "Extended Nodes Demo",
                "demo_version": "1.0",
                "demo_timestamp": "2024-01-01T10:00:00Z"
            }
        )

        print(f"\n🎉 Demo completed successfully!")
        print(f"📊 Final summary: {final_ctx.get('summary', {})}")

        # Show run information
        run_info = store.get_run_info("extended_demo_001")
        successful_tasks = [name for name, info in run_info['tasks'].items() if info['status'] == 'success']
        failed_tasks = [name for name, info in run_info['tasks'].items() if info['status'] == 'error']

        print(f"\n📈 Execution Statistics:")
        print(f"   ✅ Successful tasks: {len(successful_tasks)}")
        print(f"   ❌ Failed tasks: {len(failed_tasks)}")
        print(f"   ⏱️  Total execution time: {run_info['finished'] - run_info['started']:.2f}s")

        if failed_tasks:
            print(f"\n⚠️  Failed tasks: {', '.join(failed_tasks)}")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

        # Show error details
        run_info = store.get_run_info("extended_demo_001")
        for task_name, task_info in run_info['tasks'].items():
            if task_info['status'] == 'error':
                print(f"\n🔍 Task '{task_name}' failed:")
                print(f"   Error: {task_info.get('error', 'Unknown error')}")

    print(f"\n📋 Complete workflow data saved to: {store.data_dir}/runs/")
    print("💡 Try exploring the generated files in the ./data directory!")


if __name__ == "__main__":
    asyncio.run(main())