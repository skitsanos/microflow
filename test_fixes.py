"""Test script to verify the critical fixes"""

import asyncio
from microflow import Workflow, task, JSONStateStore
from microflow.nodes.data_transform import select_fields, rename_fields

@task(name="setup_test_data")
def setup_test_data(ctx):
    """Setup test data for the fixes"""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@test.com", "department": "Engineering"},
            {"id": 2, "name": "Bob", "email": "bob@test.com", "department": "Sales"}
        ]
    }

# Test the fixed select_fields function
select_user_fields = select_fields(
    data_key="users",
    fields=["id", "name"],
    output_key="selected_users"
)

# Test the fixed rename_fields function
rename_user_fields = rename_fields(
    data_key="selected_users",
    field_mapping={"id": "user_id", "name": "full_name"},
    output_key="renamed_users"
)

@task(name="verify_results")
def verify_results(ctx):
    """Verify that the transformations worked"""
    selected = ctx.get("selected_users", [])
    renamed = ctx.get("renamed_users", [])

    print("Original users:", ctx.get("users"))
    print("Selected fields:", selected)
    print("Renamed fields:", renamed)
    print("Full context keys:", list(ctx.keys()))
    print("Transform error:", ctx.get("transform_error"))

    # Verify select_fields worked
    if selected and len(selected) == 2 and "email" not in selected[0]:
        print("✅ select_fields fix verified")
    else:
        print("❌ select_fields still broken")

    # Verify rename_fields worked
    if renamed and "user_id" in renamed[0] and "full_name" in renamed[0]:
        print("✅ rename_fields fix verified")
    else:
        print("❌ rename_fields still broken")

    return {"verification_complete": True}

async def main():
    """Test the critical fixes"""
    print("Testing critical fixes...")

    # Build workflow
    setup_test_data >> select_user_fields >> rename_user_fields >> verify_results

    workflow = Workflow([setup_test_data, select_user_fields, rename_user_fields, verify_results],
                       name="fix_test")

    store = JSONStateStore("./data")

    try:
        result = await workflow.run("fix_test_001", store, {})
        print("✅ All fixes working correctly!")

    except Exception as e:
        print(f"❌ Fix test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())