# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Regression tests for the original MCP foundation and decoy design."""
# Explanation: Imports modules that this file uses.
import pytest
# Explanation: Imports names from mcp_canarytrap.phase1_design.
from mcp_canarytrap.phase1_design import DecoyCategory, build_phase1_decoys, create_placement_plan

# Explanation: Function test_taxonomy_contains_three_required_categories: The initial taxonomy must contain all categories in the project plan.
def test_taxonomy_contains_three_required_categories():
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """The initial taxonomy must contain all categories in the project plan."""
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert {item.category for item in build_phase1_decoys()} == set(DecoyCategory)

# Explanation: Function test_placement_reproducible_for_same_session: Same session IDs produce the same order; different IDs may differ.
def test_placement_reproducible_for_same_session():
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Same session IDs produce the same order; different IDs may differ."""
    # Explanation: Assigns or updates a value used later by this function or module.
    first = create_placement_plan("session-a")
    # Explanation: Assigns or updates a value used later by this function or module.
    second = create_placement_plan("session-a")
    # Explanation: Assert an expected condition; a false condition raises AssertionError.
    assert [d.name for d in first.decoys] == [d.name for d in second.decoys]

# Explanation: Function test_empty_session_id_is_rejected: A session identifier is required to derive reproducible placement.
def test_empty_session_id_is_rejected():
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """A session identifier is required to derive reproducible placement."""
    # Explanation: Acquire/manage the context resource and release it reliably on exit.
    with pytest.raises(ValueError):
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        create_placement_plan(" ")

