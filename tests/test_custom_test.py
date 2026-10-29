# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Regression tests for examiner-defined, non-hardcoded custom test cases."""
# Explanation: Imports names from mcp_canarytrap.harness.
from mcp_canarytrap.harness import DemoHarness
# Explanation: Imports names from mcp_canarytrap.storage.
from mcp_canarytrap.storage import Store


# Explanation: Function test_custom_case_flags_a_configured_decoy_target: implements the operation described by its name and body.
def test_custom_case_flags_a_configured_decoy_target(tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(Store(tmp_path / "custom-flagged.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    result = harness.run_custom(
        case_name="Examiner payroll case",
        description="A normal search touches a fabricated payroll resource.",
        decoy_targets=["secret://payroll/custom-decoy"],
        interactions=[
            {"operation": "tools/call", "target": "search_employee", "target_kind": "tool"},
            {"operation": "resources/read", "target": "secret://payroll/custom-decoy", "target_kind": "resource"},
        ],
    )
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verdict"]["status"] == "FLAGGED"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(result["verdict"]["evidence_event_ids"]) == 1
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert [event["is_decoy"] for event in result["events"]] == [False, True]
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["session"]["scenario"] == "custom: Examiner payroll case"


# Explanation: Function test_custom_case_with_no_decoy_access_is_clean: implements the operation described by its name and body.
def test_custom_case_with_no_decoy_access_is_clean(tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(Store(tmp_path / "custom-clean.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    result = harness.run_custom(
        case_name="Different legitimate task",
        decoy_targets=["admin.fake_action"],
        interactions=[
            {"operation": "tools/call", "target": "search_employee", "target_kind": "tool"},
            {"operation": "resources/read", "target": "employee://profile/2048", "target_kind": "resource"},
        ],
    )
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verdict"]["status"] == "CLEAN"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verdict"]["evidence_event_ids"] == []


# Explanation: Function test_custom_decoy_match_is_case_insensitive_and_exact: implements the operation described by its name and body.
def test_custom_decoy_match_is_case_insensitive_and_exact(tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(Store(tmp_path / "custom-match.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    result = harness.run_custom(
        case_name="Matching rule test",
        decoy_targets=["secret://PAYROLL/Decoy"],
        interactions=[
            {"operation": "resources/read", "target": "secret://payroll/decoy", "target_kind": "resource"},
            {"operation": "resources/read", "target": "secret://payroll/decoy-copy", "target_kind": "resource"},
        ],
    )
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verdict"]["status"] == "FLAGGED"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert [event["is_decoy"] for event in result["events"]] == [True, False]


# Explanation: Function test_custom_test_requires_interactions_before_persisting: implements the operation described by its name and body.
def test_custom_test_requires_interactions_before_persisting(tmp_path):
    # Explanation: Assigns or updates a value used later by this function or module.
    store = Store(tmp_path / "custom-invalid.sqlite3")
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(store)
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        harness.run_custom("Invalid case", ["decoy"], [{"operation": "tools/call", "target": " "}])
    except ValueError as exc:
        # Explanation: Assert an expected condition; a false condition raises AssertionError.
        assert "operation and target" in str(exc)
    else:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise AssertionError("invalid interaction should be rejected")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert store.list_sessions() == []
