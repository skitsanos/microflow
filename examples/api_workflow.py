"""
Example demonstrating HTTP API workflows similar to n8n
"""

import asyncio
from microflow import (
    Workflow, task, JSONStateStore,
    http_get, http_post, http_put,
    webhook_call, rest_api_call,
    BearerAuth, APIKeyAuth,
    if_node, conditional_task
)


# Mock HTTP tasks for demonstration (since we don't have real APIs)
@task(name="mock_fetch_github_user", max_retries=2)
async def mock_fetch_github_user(ctx):
    """Mock fetching GitHub user data"""
    username = ctx.get("github_username", "octocat")
    print(f"🐙 Fetching GitHub user: {username}")

    await asyncio.sleep(0.5)  # Simulate API delay

    return {
        "github_user": {
            "login": username,
            "id": 12345,
            "name": "The Octocat",
            "public_repos": 8,
            "followers": 4000,
            "following": 9,
            "created_at": "2011-01-25T18:44:36Z"
        },
        "github_api_success": True
    }


@task(name="mock_fetch_user_repos", max_retries=2)
async def mock_fetch_user_repos(ctx):
    """Mock fetching user repositories"""
    username = ctx["github_user"]["login"]
    print(f"📦 Fetching repositories for: {username}")

    await asyncio.sleep(0.3)

    return {
        "repositories": [
            {"name": "Hello-World", "stars": 1500, "language": "Python"},
            {"name": "awesome-project", "stars": 234, "language": "JavaScript"},
            {"name": "data-analysis", "stars": 67, "language": "Python"}
        ],
        "repo_count": 3
    }


@task(name="mock_send_slack_message")
async def mock_send_slack_message(ctx):
    """Mock sending Slack notification"""
    user = ctx["github_user"]
    message = f"New GitHub user analyzed: {user['name']} (@{user['login']}) - {user['public_repos']} repos, {user['followers']} followers"

    print(f"💬 Slack: {message}")
    await asyncio.sleep(0.2)

    return {
        "slack_sent": True,
        "slack_message": message
    }


@task(name="mock_create_notion_page")
async def mock_create_notion_page(ctx):
    """Mock creating a Notion page"""
    user = ctx["github_user"]
    print(f"📄 Creating Notion page for: {user['name']}")

    await asyncio.sleep(0.4)

    return {
        "notion_page_created": True,
        "notion_page_id": f"page_{user['id']}"
    }


@task(name="mock_send_email")
async def mock_send_email(ctx):
    """Mock sending email report"""
    user = ctx["github_user"]
    repos = ctx.get("repositories", [])

    print(f"📧 Sending email report about {user['name']}")
    print(f"   - Total repositories: {len(repos)}")
    print(f"   - Most popular: {max(repos, key=lambda r: r['stars'])['name'] if repos else 'None'}")

    await asyncio.sleep(0.3)

    return {
        "email_sent": True,
        "report_generated": True
    }


@task(name="analyze_repo_languages")
def analyze_repo_languages(ctx):
    """Analyze programming languages in repositories"""
    repos = ctx.get("repositories", [])

    language_stats = {}
    for repo in repos:
        lang = repo.get("language", "Unknown")
        language_stats[lang] = language_stats.get(lang, 0) + 1

    print(f"💻 Language analysis: {language_stats}")

    return {
        "language_stats": language_stats,
        "primary_language": max(language_stats.items(), key=lambda x: x[1])[0] if language_stats else "Unknown"
    }


# Conditional logic: Check if user is "influential" (many followers)
check_influence = if_node(
    condition="ctx['github_user']['followers'] >= 1000",
    name="check_user_influence",
    true_route="influential",
    false_route="regular"
)


@conditional_task(route="influential", condition_node="check_user_influence")
@task(name="handle_influential_user")
async def handle_influential_user(ctx):
    """Special handling for influential users"""
    user = ctx["github_user"]
    print(f"⭐ {user['name']} is influential with {user['followers']} followers!")

    return {
        "influence_level": "high",
        "special_treatment": True,
        "priority": "high"
    }


@conditional_task(route="regular", condition_node="check_user_influence")
@task(name="handle_regular_user")
async def handle_regular_user(ctx):
    """Standard handling for regular users"""
    user = ctx["github_user"]
    print(f"👤 {user['name']} is a regular user with {user['followers']} followers")

    return {
        "influence_level": "normal",
        "special_treatment": False,
        "priority": "normal"
    }


def create_api_workflow():
    """Create a workflow that mimics common API automation patterns"""

    # Build the workflow DAG
    mock_fetch_github_user >> mock_fetch_user_repos
    mock_fetch_github_user >> check_influence

    # Parallel processing based on influence
    check_influence >> handle_influential_user
    check_influence >> handle_regular_user

    # Data analysis
    mock_fetch_user_repos >> analyze_repo_languages

    # Notifications and documentation (parallel)
    handle_influential_user >> mock_send_slack_message
    handle_regular_user >> mock_send_slack_message
    analyze_repo_languages >> mock_create_notion_page
    analyze_repo_languages >> mock_send_email

    all_tasks = [
        mock_fetch_github_user,
        mock_fetch_user_repos,
        check_influence,
        handle_influential_user,
        handle_regular_user,
        analyze_repo_languages,
        mock_send_slack_message,
        mock_create_notion_page,
        mock_send_email
    ]

    return Workflow(all_tasks, name="github_user_analysis")


# Real HTTP examples (commented out, can be used with real APIs)
"""
# Real GitHub API example
fetch_github_user = http_get(
    url=lambda ctx: f"https://api.github.com/users/{ctx['github_username']}",
    headers={"Accept": "application/vnd.github.v3+json"},
    auth=BearerAuth("your_github_token"),
    name="fetch_github_user",
    max_retries=2
)

# Real Slack webhook example
send_slack_notification = webhook_call(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    payload_keys=["github_user", "repositories", "language_stats"],
    name="slack_notification"
)

# Real Notion API example
create_notion_page = http_post(
    url="https://api.notion.com/v1/pages",
    headers={
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    },
    auth=BearerAuth("your_notion_token"),
    json_data={
        "parent": {"database_id": "your_database_id"},
        "properties": {
            "Name": {
                "title": [{"text": {"content": "ctx.github_user.name"}}]
            }
        }
    },
    name="create_notion_page"
)
"""


async def main():
    """Run the API workflow example"""
    print("=== API Workflow Example ===\n")

    # Test different user types
    test_users = [
        {"github_username": "octocat"},      # Influential user (4000 followers)
        {"github_username": "newbie_dev"}    # Regular user
    ]

    store = JSONStateStore("./data")

    for i, user_ctx in enumerate(test_users):
        print(f"\n🔄 Processing user {i+1}: {user_ctx['github_username']}")
        print("=" * 50)

        workflow = create_api_workflow()
        run_id = f"api_workflow_{i+1:03d}"

        # Modify mock data for different scenarios
        if user_ctx['github_username'] == 'newbie_dev':
            # Override for regular user scenario
            original_fetch = mock_fetch_github_user.spec.fn

            async def newbie_fetch(ctx):
                result = await original_fetch(ctx)
                result['github_user'].update({
                    'name': 'New Developer',
                    'login': 'newbie_dev',
                    'followers': 15,  # Low followers
                    'public_repos': 3
                })
                return result

            mock_fetch_github_user.spec.fn = newbie_fetch

        try:
            final_ctx = await workflow.run(
                run_id=run_id,
                store=store,
                initial_ctx=user_ctx
            )

            print(f"\n✅ Workflow completed for {user_ctx['github_username']}!")
            print(f"Influence level: {final_ctx.get('influence_level')}")
            print(f"Primary language: {final_ctx.get('primary_language')}")
            print(f"Notifications sent: {final_ctx.get('slack_sent', False)}")
            print(f"Documentation created: {final_ctx.get('notion_page_created', False)}")
            print(f"Report emailed: {final_ctx.get('email_sent', False)}")

        except Exception as e:
            print(f"❌ Workflow failed for {user_ctx['github_username']}: {e}")

    print(f"\n📋 View detailed logs at: {store.data_dir}/runs/")
    print("\n💡 Tips for real usage:")
    print("   - Replace mock tasks with real HTTP requests")
    print("   - Add proper API tokens and authentication")
    print("   - Use environment variables for sensitive data")
    print("   - Configure webhooks for external triggers")


if __name__ == "__main__":
    asyncio.run(main())