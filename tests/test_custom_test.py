"""Regression tests for examiner-defined, non-hardcoded custom test cases."""
from mcp_canarytrap.harness import DemoHarness
from mcp_canarytrap.storage import Store


def test_custom_case_flags_a_configured_decoy_target(tmp_path):
    harness = DemoHarness(Store(tmp_path / "custom-flagged.sqlite3"))
    result = harness.run_custom(
        case_name="Examiner payroll case",
        description="A normal search touches a fabricated payroll resource.",
        decoy_targets=["secret://payroll/custom-decoy"],
        interactions=[
            {"operation": "tools/call", "target": "search_employee", "target_kind": "tool"},
            {"operation": "resources/read", "target": "secret://payroll/custom-decoy", "target_kind": "resource"},
        ],
    )
    assert result["verdict"]["status"] == "FLAGGED"
    assert len(result["verdict"]["evidence_event_ids"]) == 1
    assert [event["is_decoy"] for event in result["events"]] == [False, True]
    assert result["session"]["scenario"] == "custom: Examiner payroll case"


def test_custom_case_with_no_decoy_access_is_clean(tmp_path):
    harness = DemoHarness(Store(tmp_path / "custom-clean.sqlite3"))
    result = harness.run_custom(
        case_name="Different legitimate task",
        decoy_targets=["admin.fake_action"],
        interactions=[
            {"operation": "tools/call", "target": "search_employee", "target_kind": "tool"},
            {"operation": "resources/read", "target": "employee://profile/2048", "target_kind": "resource"},
        ],
    )
    assert result["verdict"]["status"] == "CLEAN"
    assert result["verdict"]["evidence_event_ids"] == []


def test_custom_decoy_match_is_case_insensitive_and_exact(tmp_path):
    harness = DemoHarness(Store(tmp_path / "custom-match.sqlite3"))
    result = harness.run_custom(
        case_name="Matching rule test",
        decoy_targets=["secret://PAYROLL/Decoy"],
        interactions=[
            {"operation": "resources/read", "target": "secret://payroll/decoy", "target_kind": "resource"},
            {"operation": "resources/read", "target": "secret://payroll/decoy-copy", "target_kind": "resource"},
        ],
    )
    assert result["verdict"]["status"] == "FLAGGED"
    assert [event["is_decoy"] for event in result["events"]] == [True, False]


def test_custom_test_requires_interactions_before_persisting(tmp_path):
    store = Store(tmp_path / "custom-invalid.sqlite3")
    harness = DemoHarness(store)
    try:
        harness.run_custom("Invalid case", ["decoy"], [{"operation": "tools/call", "target": " "}])
    except ValueError as exc:
        assert "operation and target" in str(exc)
    else:
        raise AssertionError("invalid interaction should be rejected")
    assert store.list_sessions() == []
