"""Regression tests for the original MCP foundation and decoy design."""
import pytest
from mcp_canarytrap.phase1_design import DecoyCategory, build_phase1_decoys, create_placement_plan

def test_taxonomy_contains_three_required_categories():
    """The initial taxonomy must contain all categories in the project plan."""
    assert {item.category for item in build_phase1_decoys()} == set(DecoyCategory)

def test_placement_reproducible_for_same_session():
    """Same session IDs produce the same order; different IDs may differ."""
    first = create_placement_plan("session-a")
    second = create_placement_plan("session-a")
    assert [d.name for d in first.decoys] == [d.name for d in second.decoys]

def test_empty_session_id_is_rejected():
    """A session identifier is required to derive reproducible placement."""
    with pytest.raises(ValueError):
        create_placement_plan(" ")

