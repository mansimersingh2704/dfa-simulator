"""
Test Suite for Core DFA Engine (CSET302)
========================================
Tests formal definition validation and single-string simulation:
- Non-empty Q and Σ validation
- Start state and accepting state validation
- Rejection of duplicate transitions (non-determinism)
- Accepted, rejected, and empty string handling
- Invalid input symbols and missing transition handling
- JSON serialization and deserialization
"""

import pytest
from dfa import DFA, DFAValidationError


@pytest.fixture
def ends_with_01_dfa():
    """DFA that accepts strings ending with '01' over {0, 1}."""
    return DFA(
        states=["q0", "q1", "q2"],
        alphabet=["0", "1"],
        start_state="q0",
        accepting_states=["q2"],
        transitions={
            "q0": {"0": "q1", "1": "q0"},
            "q1": {"0": "q1", "1": "q2"},
            "q2": {"0": "q1", "1": "q0"},
        },
    )


# -----------------------------------------------------------------------------
# 1. Accepted & Rejected Strings Simulation
# -----------------------------------------------------------------------------
def test_simulation_accepted_and_rejected_strings(ends_with_01_dfa):
    """Test that accepted strings reach accepting state and rejected strings do not."""
    # Accepted string
    res1 = ends_with_01_dfa.simulate("01")
    assert res1.accepted is True
    assert res1.final_state == "q2"
    assert res1.status == "ACCEPTED"
    assert len(res1.trace) == 2
    assert res1.trace[0]["from_state"] == "q0" and res1.trace[0]["symbol"] == "0" and res1.trace[0]["to_state"] == "q1"
    assert res1.trace[1]["from_state"] == "q1" and res1.trace[1]["symbol"] == "1" and res1.trace[1]["to_state"] == "q2"

    res2 = ends_with_01_dfa.simulate("100101")
    assert res2.accepted is True
    assert res2.final_state == "q2"

    # Rejected strings
    res3 = ends_with_01_dfa.simulate("10")
    assert res3.accepted is False
    assert res3.final_state == "q1"
    assert res3.status == "REJECTED_NON_FINAL"
    assert "NOT an accepting state" in res3.explanation

    res4 = ends_with_01_dfa.simulate("111")
    assert res4.accepted is False
    assert res4.final_state == "q0"


# -----------------------------------------------------------------------------
# 2. Empty String (ε) Handling
# -----------------------------------------------------------------------------
def test_simulation_empty_string_start_non_accepting(ends_with_01_dfa):
    """Test empty string on DFA where start state is non-accepting."""
    res = ends_with_01_dfa.simulate("")
    assert res.accepted is False
    assert res.final_state == "q0"
    assert len(res.trace) == 0
    assert "Empty string (ε)" in res.explanation
    assert res.status == "REJECTED_NON_FINAL"


def test_simulation_empty_string_start_accepting():
    """Test empty string on DFA where start state IS an accepting state."""
    dfa = DFA(
        states=["q_even", "q_odd"],
        alphabet=["0", "1"],
        start_state="q_even",
        accepting_states=["q_even"],
        transitions={
            "q_even": {"0": "q_odd", "1": "q_even"},
            "q_odd": {"0": "q_even", "1": "q_odd"},
        },
    )
    res = dfa.simulate("")
    assert res.accepted is True
    assert res.final_state == "q_even"
    assert len(res.trace) == 0
    assert "Empty string (ε)" in res.explanation
    assert res.status == "ACCEPTED"


# -----------------------------------------------------------------------------
# 3. Invalid Input Symbols
# -----------------------------------------------------------------------------
def test_simulation_invalid_symbol(ends_with_01_dfa):
    """Test that input symbols outside Σ immediately halt and reject."""
    res = ends_with_01_dfa.simulate("01201")
    assert res.accepted is False
    assert res.status == "REJECTED_INVALID_SYMBOL"
    assert "Symbol '2' at position 2 is invalid" in res.explanation
    assert res.consumed_count == 2
    assert res.total_count == 5


# -----------------------------------------------------------------------------
# 4. Missing Transitions (Partial DFA)
# -----------------------------------------------------------------------------
def test_simulation_missing_transition():
    """Test that missing transition in partial DFA halts and rejects cleanly."""
    partial_dfa = DFA(
        states=["A", "B"],
        alphabet=["a", "b"],
        start_state="A",
        accepting_states=["B"],
        transitions={
            "A": {"a": "B"},
            # A has no transition on 'b'
            "B": {"a": "B", "b": "A"},
        },
    )
    res = partial_dfa.simulate("ba")
    assert res.accepted is False
    assert res.status == "REJECTED_MISSING_TRANSITION"
    assert "Missing transition δ('A', 'b')" in res.explanation
    assert res.consumed_count == 0


# -----------------------------------------------------------------------------
# 5. Invalid Start State Validation
# -----------------------------------------------------------------------------
def test_validation_invalid_start_state():
    """Test that start state not in Q raises DFAValidationError."""
    with pytest.raises(DFAValidationError, match="Start state 'q99' is not in the set of states Q"):
        DFA(
            states=["q0", "q1"],
            alphabet=["0", "1"],
            start_state="q99",
            accepting_states=["q1"],
            transitions={"q0": {"0": "q1", "1": "q0"}, "q1": {"0": "q1", "1": "q0"}},
        )


# -----------------------------------------------------------------------------
# 6. Invalid Accepting States Validation
# -----------------------------------------------------------------------------
def test_validation_invalid_accepting_states():
    """Test that accepting states not subset of Q raises DFAValidationError."""
    with pytest.raises(DFAValidationError, match="Accepting states must be a subset of Q"):
        DFA(
            states=["q0", "q1"],
            alphabet=["0", "1"],
            start_state="q0",
            accepting_states=["q1", "qGhost"],
            transitions={"q0": {"0": "q1", "1": "q0"}, "q1": {"0": "q1", "1": "q0"}},
        )


# -----------------------------------------------------------------------------
# 7. Non-empty Q and Σ Validation
# -----------------------------------------------------------------------------
def test_validation_empty_states_or_alphabet():
    """Test that empty state set or empty alphabet raises DFAValidationError."""
    with pytest.raises(DFAValidationError, match="State set Q must be non-empty"):
        DFA(
            states=[],
            alphabet=["0", "1"],
            start_state="q0",
            accepting_states=[],
            transitions={},
        )

    with pytest.raises(DFAValidationError, match="Alphabet Σ must be non-empty"):
        DFA(
            states=["q0"],
            alphabet=[],
            start_state="q0",
            accepting_states=[],
            transitions={},
        )


# -----------------------------------------------------------------------------
# 8. Duplicate Transitions (Determinism Validation)
# -----------------------------------------------------------------------------
def test_validation_duplicate_transitions_rejected():
    """Test that duplicate transition for same state and symbol raises DFAValidationError."""
    transition_list = [
        {"from": "q0", "symbol": "0", "to": "q1"},
        {"from": "q0", "symbol": "0", "to": "q2"},
    ]
    with pytest.raises(DFAValidationError, match="Non-deterministic transition detected"):
        DFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            start_state="q0",
            accepting_states=["q1"],
            transitions=transition_list,
        )


# -----------------------------------------------------------------------------
# 9. JSON Serialization and Deserialization Roundtrip
# -----------------------------------------------------------------------------
def test_json_serialization_roundtrip(ends_with_01_dfa):
    """Test to_dict, to_json, from_dict, and from_json roundtripping."""
    json_str = ends_with_01_dfa.to_json()
    reconstructed = DFA.from_json(json_str)

    assert reconstructed.states == ends_with_01_dfa.states
    assert reconstructed.alphabet == ends_with_01_dfa.alphabet
    assert reconstructed.start_state == ends_with_01_dfa.start_state
    assert reconstructed.accepting_states == ends_with_01_dfa.accepting_states
    assert reconstructed.transitions == ends_with_01_dfa.transitions

    # Simulation results must match
    assert reconstructed.simulate("01").accepted is True
    assert reconstructed.simulate("00").accepted is False
