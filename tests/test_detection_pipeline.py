"""Tests for logging, persistence and deterministic verdict generation."""
from mcp_canarytrap.harness import DemoHarness
from mcp_canarytrap.storage import Store

def test_benign_scenario_is_clean_and_has_no_decoy_events(tmp_path):
    """A benign scripted task must not touch decoys in the simulation."""
    harness = DemoHarness(Store(tmp_path / "benign.sqlite3"))
    result = harness.run("benign", "benign-test")
    assert result["verdict"]["status"] == "CLEAN"
    assert not any(event["is_decoy"] for event in result["events"])

def test_overreaching_scenario_is_flagged_with_evidence(tmp_path):
    """A decoy touch must create a FLAGGED verdict and evidence references."""
    harness = DemoHarness(Store(tmp_path / "overreach.sqlite3"))
    result = harness.run("overreaching", "overreach-test")
    assert result["verdict"]["status"] == "FLAGGED"
    assert len(result["verdict"]["evidence_event_ids"]) == 3
    assert len([event for event in result["events"] if event["is_decoy"]]) == 3

def test_session_is_persisted(tmp_path):
    """The report can be retrieved after the harness returns."""
    store = Store(tmp_path / "sessions.sqlite3")
    result = DemoHarness(store).run("benign", "persist-test")
    assert store.get_session("persist-test")["status"] == result["verdict"]["status"]
