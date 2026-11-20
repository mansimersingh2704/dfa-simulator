"""
Cross-Verification Test Suite: Python DFA Engine vs JavaScript Fallback Engine
==============================================================================
Validates that the Python backend and JavaScript client fallback engine
produce identical simulation results and step traces for the same DFA and inputs.
"""

import json
import subprocess
import pytest
from dfa import DFA
from app import PRESETS


def run_js_simulation(dfa_dict: dict, input_string: str) -> dict:
    """Invokes JSAutomataEngine.simulate in Node.js and returns JSON result."""
    node_script = f"""
    const {{ JSAutomataEngine }} = require('./static/app.js');
    const dfa = {json.dumps(dfa_dict)};
    const res = JSAutomataEngine.simulate(dfa, {json.dumps(input_string)});
    console.log(JSON.stringify(res));
    """
    proc = subprocess.run(
        ["node", "-e", node_script],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout.strip())


def test_cross_engine_simulation_all_presets():
    """Verify that Python and JavaScript engines produce identical acceptance & traces."""
    test_cases = [
        ("ends_with_01", "01"),
        ("ends_with_01", "101"),
        ("ends_with_01", "1001"),
        ("ends_with_01", "00"),
        ("ends_with_01", "10"),
        ("ends_with_01", ""),
        ("contains_101", "101"),
        ("contains_101", "01010"),
        ("contains_101", "1001"),
        ("contains_101", ""),
        ("even_zeros", ""),
        ("even_zeros", "00"),
        ("even_zeros", "11"),
        ("even_zeros", "0"),
        ("even_zeros", "010"),
    ]

    for preset_key, test_str in test_cases:
        preset_data = PRESETS[preset_key]
        py_dfa = DFA.from_dict(preset_data)

        # 1. Run Python simulation
        py_res = py_dfa.simulate(test_str)

        # 2. Run JS simulation
        js_res = run_js_simulation(preset_data, test_str)

        # Assert identical verdicts
        assert py_res.accepted == js_res["accepted"], (
            f"Verdict mismatch on preset '{preset_key}' with input '{test_str}': "
            f"Py={py_res.accepted}, JS={js_res['accepted']}"
        )
        assert py_res.final_state == js_res["final_state"]
        assert len(py_res.trace) == len(js_res["trace"])

        # Assert identical step traces
        for i in range(len(py_res.trace)):
            py_step = py_res.trace[i]
            js_step = js_res["trace"][i]
            assert py_step["from_state"] == js_step["from_state"]
            assert py_step["symbol"] == js_step["symbol"]
            assert py_step["to_state"] == js_step["to_state"]
