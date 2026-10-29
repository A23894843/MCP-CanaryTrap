# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Tests for logging, persistence and deterministic verdict generation."""
# Explanation: Imports names from mcp_canarytrap.harness.
from mcp_canarytrap.harness import DemoHarness
# Explanation: Imports names from mcp_canarytrap.storage.
from mcp_canarytrap.storage import Store

# Explanation: Function test_benign_scenario_is_clean_and_has_no_decoy_events: A benign scripted task must not touch decoys in the simulation.
def test_benign_scenario_is_clean_and_has_no_decoy_events(tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """A benign scripted task must not touch decoys in the simulation."""
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(Store(tmp_path / "benign.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    result = harness.run("benign", "benign-test")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verdict"]["status"] == "CLEAN"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert not any(event["is_decoy"] for event in result["events"])

# Explanation: Function test_overreaching_scenario_is_flagged_with_evidence: A decoy touch must create a FLAGGED verdict and evidence references.
def test_overreaching_scenario_is_flagged_with_evidence(tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """A decoy touch must create a FLAGGED verdict and evidence references."""
    # Explanation: Assigns or updates a value used later by this function or module.
    harness = DemoHarness(Store(tmp_path / "overreach.sqlite3"))
    # Explanation: Assigns or updates a value used later by this function or module.
    result = harness.run("overreaching", "overreach-test")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert result["verdict"]["status"] == "FLAGGED"
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len(result["verdict"]["evidence_event_ids"]) == 3
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert len([event for event in result["events"] if event["is_decoy"]]) == 3

# Explanation: Function test_session_is_persisted: The report can be retrieved after the harness returns.
def test_session_is_persisted(tmp_path):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """The report can be retrieved after the harness returns."""
    # Explanation: Assigns or updates a value used later by this function or module.
    store = Store(tmp_path / "sessions.sqlite3")
    # Explanation: Assigns or updates a value used later by this function or module.
    result = DemoHarness(store).run("benign", "persist-test")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert store.get_session("persist-test")["status"] == result["verdict"]["status"]
