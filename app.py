"""
DFA Simulator — Flask Web Application Backend
==============================================
Provides RESTful JSON API endpoints for:
- DFA 5-tuple validation
- String simulation and trace generation
- Batch simulation with pass/fail metrics
- Formal theory operations: Completion, Complement, Minimization,
  Equivalence checking with counterexamples, and Unreachable state pruning
- Mathematical presets loading
- Serving the single-page application frontend

Author: CSET302 Automata Theory & Computability Project Team
"""

from __future__ import annotations

import os
from typing import Any, Dict
from flask import Flask, jsonify, render_template, request

from dfa import DFA, DFAValidationError

app = Flask(__name__, template_folder="templates", static_folder="static")

# -----------------------------------------------------------------------------
# Curated Mathematical DFA Presets (CSET302)
# -----------------------------------------------------------------------------
PRESETS: Dict[str, Dict[str, Any]] = {
    "ends_with_01": {
        "id": "ends_with_01",
        "name": "Strings ending with '01'",
        "description": "Accepts any binary string over {0, 1} whose suffix is '01'.",
        "alphabet": ["0", "1"],
        "states": ["q0", "q1", "q2"],
        "start_state": "q0",
        "accepting_states": ["q2"],
        "transitions": {
            "q0": {"0": "q1", "1": "q0"},
            "q1": {"0": "q1", "1": "q2"},
            "q2": {"0": "q1", "1": "q0"},
        },
        "sample_inputs": ["01", "101", "1001", "00", "10", "111", ""],
    },
    "contains_101": {
        "id": "contains_101",
        "name": "Strings containing '101'",
        "description": "Accepts any binary string that contains '101' as a substring.",
        "alphabet": ["0", "1"],
        "states": ["s0", "s1", "s2", "s3"],
        "start_state": "s0",
        "accepting_states": ["s3"],
        "transitions": {
            "s0": {"0": "s0", "1": "s1"},
            "s1": {"0": "s2", "1": "s1"},
            "s2": {"0": "s0", "1": "s3"},
            "s3": {"0": "s3", "1": "s3"},
        },
        "sample_inputs": ["101", "01010", "1101", "1001", "111", "000", ""],
    },
    "even_zeros_and_ones": {
        "id": "even_zeros_and_ones",
        "name": "Even number of 0s and 1s",
        "description": "Accepts binary strings containing both an even count of '0's and an even count of '1's.",
        "alphabet": ["0", "1"],
        "states": ["q_ee", "q_oe", "q_eo", "q_oo"],
        "start_state": "q_ee",
        "accepting_states": ["q_ee"],
        "transitions": {
            "q_ee": {"0": "q_oe", "1": "q_eo"},
            "q_oe": {"0": "q_ee", "1": "q_oo"},
            "q_eo": {"0": "q_oo", "1": "q_ee"},
            "q_oo": {"0": "q_eo", "1": "q_oe"},
        },
        "sample_inputs": ["", "00", "11", "0101", "0011", "0", "1", "001"],
    },
    "binary_divisible_by_3": {
        "id": "binary_divisible_by_3",
        "name": "Binary numbers divisible by 3",
        "description": "Evaluates a binary number from MSB to LSB and accepts if the integer value is a multiple of 3 (remainder 0).",
        "alphabet": ["0", "1"],
        "states": ["rem0", "rem1", "rem2"],
        "start_state": "rem0",
        "accepting_states": ["rem0"],
        "transitions": {
            "rem0": {"0": "rem0", "1": "rem1"},
            "rem1": {"0": "rem2", "1": "rem0"},
            "rem2": {"0": "rem1", "1": "rem2"},
        },
        "sample_inputs": ["0", "11", "110", "1001", "1100", "1", "10", "100"],
    },
    "starts_with_ab": {
        "id": "starts_with_ab",
        "name": "Strings starting with 'ab'",
        "description": "Accepts strings over {a, b} that have the prefix 'ab'.",
        "alphabet": ["a", "b"],
        "states": ["p0", "p1", "p2", "trap"],
        "start_state": "p0",
        "accepting_states": ["p2"],
        "transitions": {
            "p0": {"a": "p1", "b": "trap"},
            "p1": {"a": "trap", "b": "p2"},
            "p2": {"a": "p2", "b": "p2"},
            "trap": {"a": "trap", "b": "trap"},
        },
        "sample_inputs": ["ab", "aba", "abbb", "a", "b", "ba", ""],
    },
    "length_divisible_by_3": {
        "id": "length_divisible_by_3",
        "name": "Length divisible by 3 (|w| mod 3 == 0)",
        "description": "Accepts any string whose length is an exact multiple of 3 (including length 0).",
        "alphabet": ["0", "1"],
        "states": ["len0", "len1", "len2"],
        "start_state": "len0",
        "accepting_states": ["len0"],
        "transitions": {
            "len0": {"0": "len1", "1": "len1"},
            "len1": {"0": "len2", "1": "len2"},
            "len2": {"0": "len0", "1": "len0"},
        },
        "sample_inputs": ["", "011", "101", "000111", "1", "01", "1111"],
    },
    "no_consecutive_1s": {
        "id": "no_consecutive_1s",
        "name": "No two consecutive 1s",
        "description": "Accepts binary strings where '11' never appears as a substring.",
        "alphabet": ["0", "1"],
        "states": ["s_ok", "s_one", "s_dead"],
        "start_state": "s_ok",
        "accepting_states": ["s_ok", "s_one"],
        "transitions": {
            "s_ok": {"0": "s_ok", "1": "s_one"},
            "s_one": {"0": "s_ok", "1": "s_dead"},
            "s_dead": {"0": "s_dead", "1": "s_dead"},
        },
        "sample_inputs": ["", "0", "1", "0101", "10101", "11", "0110", "10011"],
    },
    "keyword_cat": {
        "id": "keyword_cat",
        "name": "Keyword matcher for 'cat'",
        "description": "Recognizes words containing the token sequence 'cat' over alphabet {a, c, t, x}.",
        "alphabet": ["a", "c", "t", "x"],
        "states": ["w0", "w1", "w2", "w3"],
        "start_state": "w0",
        "accepting_states": ["w3"],
        "transitions": {
            "w0": {"c": "w1", "a": "w0", "t": "w0", "x": "w0"},
            "w1": {"c": "w1", "a": "w2", "t": "w0", "x": "w0"},
            "w2": {"c": "w1", "a": "w0", "t": "w3", "x": "w0"},
            "w3": {"c": "w3", "a": "w3", "t": "w3", "x": "w3"},
        },
        "sample_inputs": ["cat", "xcatx", "ccat", "ca", "dog", "at", ""],
    },
}


# -----------------------------------------------------------------------------
# Frontend Route
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Serves the single-page application frontend."""
    return render_template("index.html")


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Returns the list of mathematically verified preset DFAs."""
    return jsonify({"success": True, "presets": PRESETS})


@app.route("/api/validate", methods=["POST"])
def validate_dfa():
    """Validates a formal DFA definition 5-tuple."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body: expected JSON."}), 400

    try:
        dfa_instance = DFA.from_dict(data, validate=True)
        missing = dfa_instance.get_missing_transitions()
        return jsonify({
            "success": True,
            "message": "DFA definition is mathematically valid.",
            "dfa": dfa_instance.to_dict(),
            "edge_list": dfa_instance.to_transition_list(),
            "is_total": dfa_instance.is_total(),
            "missing_transitions": missing,
            "unreachable_states": sorted(dfa_instance.get_unreachable_states()),
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal validation error: {str(e)}"}), 400


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Simulates an input string step-by-step through the DFA."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body: expected JSON."}), 400

    dfa_data = data.get("dfa")
    input_str = data.get("input_string", "")
    if dfa_data is None:
        return jsonify({"success": False, "error": "Missing 'dfa' configuration in request body."}), 400

    try:
        dfa_instance = DFA.from_dict(dfa_data, validate=True)
        result = dfa_instance.simulate(str(input_str))
        return jsonify({"success": True, "result": result.to_dict()})
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Simulation failure: {str(e)}"}), 400


@app.route("/api/batch", methods=["POST"])
def batch_simulate():
    """Simulates a batch of input strings against the DFA with optional expected values."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body: expected JSON."}), 400

    dfa_data = data.get("dfa")
    inputs = data.get("inputs", [])
    if dfa_data is None:
        return jsonify({"success": False, "error": "Missing 'dfa' configuration."}), 400

    try:
        dfa_instance = DFA.from_dict(dfa_data, validate=True)
        results = []
        pass_count = 0
        total_count = len(inputs)

        for item in inputs:
            if isinstance(item, dict):
                test_str = str(item.get("input", ""))
                expected = item.get("expected")
            else:
                test_str = str(item)
                expected = None

            sim_res = dfa_instance.simulate(test_str)
            actual = sim_res.accepted

            passed = None
            if expected is not None:
                passed = (bool(expected) == actual)
                if passed:
                    pass_count += 1

            results.append({
                "input": test_str,
                "actual": actual,
                "expected": expected,
                "passed": passed,
                "final_state": sim_res.final_state,
                "status": sim_res.status,
                "explanation": sim_res.explanation,
                "trace_length": len(sim_res.trace),
            })

        return jsonify({
            "success": True,
            "results": results,
            "total": total_count,
            "passed": pass_count,
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Batch simulation error: {str(e)}"}), 400


@app.route("/api/operations/complete", methods=["POST"])
def complete_dfa_op():
    """Completes a partial DFA with a canonical sink state."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing request JSON."}), 400

    try:
        dfa_instance = DFA.from_dict(data.get("dfa", data), validate=True)
        was_total = dfa_instance.is_total()
        completed = dfa_instance.complete()
        return jsonify({
            "success": True,
            "was_total": was_total,
            "message": "DFA already total." if was_total else "Added sink state to complete all transitions.",
            "dfa": completed.to_dict(),
            "edge_list": completed.to_transition_list(),
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/operations/complement", methods=["POST"])
def complement_dfa_op():
    """Computes language complement: F' = Q \\ F (operating on complete DFA)."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing request JSON."}), 400

    try:
        dfa_instance = DFA.from_dict(data.get("dfa", data), validate=True)
        complemented = dfa_instance.complement()
        return jsonify({
            "success": True,
            "message": "Successfully complemented automaton (accepting states swapped).",
            "dfa": complemented.to_dict(),
            "edge_list": complemented.to_transition_list(),
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/operations/minimize", methods=["POST"])
def minimize_dfa_op():
    """Minimizes DFA using the Myhill-Nerode Table-Filling algorithm."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing request JSON."}), 400

    try:
        dfa_instance = DFA.from_dict(data.get("dfa", data), validate=True)
        original_count = len(dfa_instance.states)
        minimized = dfa_instance.minimize()
        min_count = len(minimized.states)

        return jsonify({
            "success": True,
            "message": f"DFA minimized from {original_count} states down to {min_count} states.",
            "original_states_count": original_count,
            "minimized_states_count": min_count,
            "dfa": minimized.to_dict(),
            "edge_list": minimized.to_transition_list(),
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/operations/unreachable", methods=["POST"])
def unreachable_states_op():
    """Detects and prunes unreachable states."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Missing request JSON."}), 400

    try:
        dfa_instance = DFA.from_dict(data.get("dfa", data), validate=True)
        unreachable = sorted(dfa_instance.get_unreachable_states())
        pruned = dfa_instance.remove_unreachable_states()

        return jsonify({
            "success": True,
            "unreachable_states": unreachable,
            "pruned_dfa": pruned.to_dict(),
            "edge_list": pruned.to_transition_list(),
            "message": f"Found {len(unreachable)} unreachable state(s)." if unreachable else "No unreachable states detected.",
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/operations/equivalence", methods=["POST"])
def equivalence_dfa_op():
    """Checks whether two DFAs recognize the identical language, with counterexample."""
    data = request.get_json(force=True, silent=True)
    if not data or "dfa1" not in data or "dfa2" not in data:
        return jsonify({"success": False, "error": "Expected 'dfa1' and 'dfa2' in request body."}), 400

    try:
        dfa1 = DFA.from_dict(data["dfa1"], validate=True)
        dfa2 = DFA.from_dict(data["dfa2"], validate=True)

        is_equiv, counterexample, explanation = dfa1.is_equivalent_to(dfa2)

        return jsonify({
            "success": True,
            "equivalent": is_equiv,
            "counterexample": counterexample,
            "explanation": explanation,
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    # College project local development server
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting DFA Simulator on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
