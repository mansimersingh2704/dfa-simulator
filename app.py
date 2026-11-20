"""
DFA Simulator — Flask Web Application Backend
==============================================
Provides RESTful JSON API endpoints for:
- Serving the single-page application frontend
- Fetching demonstration presets (6 presets)
- Validating formal DFA 5-tuples
- Simulating input strings step-by-step
- AI DFA Creator powered by xAI Grok API

Author: CSET302 Automata Theory & Computability Project Team
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests
from flask import Flask, jsonify, render_template, request

from dfa import DFA, DFAValidationError

app = Flask(__name__, template_folder="templates", static_folder="static")

# -----------------------------------------------------------------------------
# Environment & Groq API Configuration
# -----------------------------------------------------------------------------
def _load_env_file() -> None:
    """Loads key-value pairs from .env if present (without requiring external dotenv)."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip().strip("\"'")
                    if key and key not in os.environ:
                        os.environ[key] = val

_load_env_file()

GROK_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROK_API_URL = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROK_MODEL   = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")

# -----------------------------------------------------------------------------
# 6 Demonstration Presets
# -----------------------------------------------------------------------------
PRESETS: Dict[str, Dict[str, Any]] = {
    # ── Preset 1 ──────────────────────────────────────────────────────────────
    "ends_with_01": {
        "id": "ends_with_01",
        "name": "Strings ending with '01'",
        "description": "Accepts any binary string over {0, 1} that ends with '01'.",
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
    # ── Preset 2 ──────────────────────────────────────────────────────────────
    "contains_101": {
        "id": "contains_101",
        "name": "Strings containing '101'",
        "description": "Accepts any binary string over {0, 1} containing '101' as a substring.",
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
    # ── Preset 3 ──────────────────────────────────────────────────────────────
    "even_zeros": {
        "id": "even_zeros",
        "name": "Even number of 0s",
        "description": "Accepts binary strings with an even count of '0's (zero '0's also counts as even).",
        "alphabet": ["0", "1"],
        "states": ["q_even", "q_odd"],
        "start_state": "q_even",
        "accepting_states": ["q_even"],
        "transitions": {
            "q_even": {"0": "q_odd", "1": "q_even"},
            "q_odd":  {"0": "q_even", "1": "q_odd"},
        },
        "sample_inputs": ["", "00", "11", "010", "1", "0", "0110"],
    },
    # ── Preset 4 ──────────────────────────────────────────────────────────────
    "ends_with_1": {
        "id": "ends_with_1",
        "name": "Strings ending with '1'",
        "description": "Accepts any binary string over {0, 1} whose last symbol is '1'. Minimal 2-state DFA.",
        "alphabet": ["0", "1"],
        "states": ["q0", "q1"],
        "start_state": "q0",
        "accepting_states": ["q1"],
        "transitions": {
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q0", "1": "q1"},
        },
        "sample_inputs": ["1", "101", "111", "0", "10", "100", ""],
    },
    # ── Preset 5 ──────────────────────────────────────────────────────────────
    "divisible_by_3": {
        "id": "divisible_by_3",
        "name": "Binary number divisible by 3",
        "description": "Accepts binary strings representing non-negative integers divisible by 3 (e.g. 0, 11, 110).",
        "alphabet": ["0", "1"],
        "states": ["r0", "r1", "r2"],
        "start_state": "r0",
        "accepting_states": ["r0"],
        "transitions": {
            "r0": {"0": "r0", "1": "r1"},
            "r1": {"0": "r2", "1": "r0"},
            "r2": {"0": "r1", "1": "r2"},
        },
        "sample_inputs": ["0", "11", "110", "1001", "1", "10", "100"],
    },
    # ── Preset 6 ──────────────────────────────────────────────────────────────
    "starts_and_ends_1": {
        "id": "starts_and_ends_1",
        "name": "Starts and ends with '1'",
        "description": "Accepts binary strings that both start and end with '1' (minimum length 1).",
        "alphabet": ["0", "1"],
        "states": ["q0", "q1", "q2", "qdead"],
        "start_state": "q0",
        "accepting_states": ["q2"],
        "transitions": {
            "q0":    {"0": "qdead", "1": "q2"},
            "q2":    {"0": "q1",    "1": "q2"},
            "q1":    {"0": "q1",    "1": "q2"},
            "qdead": {"0": "qdead", "1": "qdead"},
        },
        "sample_inputs": ["1", "11", "101", "1001", "0", "10", "01"],
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
# Core API Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Returns the list of demonstration presets."""
    return jsonify({"success": True, "presets": PRESETS})


@app.route("/api/validate", methods=["POST"])
def validate_dfa():
    """Validates a formal DFA definition 5-tuple."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body: expected JSON."}), 400

    try:
        dfa_instance = DFA.from_dict(data, validate=True)
        return jsonify({
            "success": True,
            "message": "DFA definition is valid.",
            "dfa": dfa_instance.to_dict(),
            "edge_list": dfa_instance.to_transition_list(),
        })
    except DFAValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Validation error: {str(e)}"}), 400


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Simulates an input string step-by-step through the DFA."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request body: expected JSON."}), 400

    dfa_data   = data.get("dfa")
    input_str  = data.get("input_string", "")
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


# -----------------------------------------------------------------------------
# AI DFA Creator — xAI Grok API
# -----------------------------------------------------------------------------
@app.route("/api/ai-create", methods=["POST"])
def ai_create_dfa():
    """
    Uses xAI Grok to convert a natural-language description into a formal DFA.

    Request body:  { "description": "A DFA that accepts strings ending with 1" }
    Response:      { "success": true, "dfa": {...}, "explanation": "...", "edge_list": [...] }
    """
    data = request.get_json(force=True, silent=True)
    if not data or not data.get("description", "").strip():
        return jsonify({"success": False, "error": "Provide a 'description' field describing the DFA language."}), 400

    user_description = data["description"].strip()

    if not GROK_API_KEY:
        return jsonify({
            "success": False,
            "error": "Groq API key not configured. Please set GROQ_API_KEY environment variable or configure .env file."
        }), 500

    system_prompt = """You are an expert in formal automata theory.
Your task is to design a Deterministic Finite Automaton (DFA) for the language described by the user.

RULES:
1. Return ONLY valid JSON — no markdown, no code fences, no commentary outside the JSON.
2. The JSON must have EXACTLY these top-level keys:
   {
     "states": ["q0", "q1", ...],
     "alphabet": ["0", "1", ...],
     "start_state": "q0",
     "accepting_states": ["q1", ...],
     "transitions": {
       "q0": {"0": "q0", "1": "q1"},
       ...
     },
     "explanation": "Plain-English explanation of how the DFA works.",
     "sample_inputs": ["accepted_example1", "accepted_example2", "rejected_example1", "rejected_example2"]
   }
3. Transitions must be deterministic — at most one target per (state, symbol) pair.
4. All states in transitions, start_state, and accepting_states MUST be in the states list.
5. All symbols in transitions MUST be in the alphabet list.
6. Keep the DFA minimal and correct. Use simple state names like q0, q1, q2, ...
7. The explanation should be 1-2 sentences suitable for a college student.
8. sample_inputs should include 2 accepted and 2 rejected examples (use empty string "" for ε if relevant).
"""

    payload = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Design a DFA for the following language:\n{user_description}"},
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(GROK_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "AI request timed out. Please try again."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"AI service unreachable: {str(e)}"}), 502

    try:
        ai_response = resp.json()
        raw_content = ai_response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError):
        return jsonify({"success": False, "error": "Unexpected response format from AI service."}), 502

    # Strip <think>…</think> blocks that reasoning models emit
    import re as _re
    raw_content = _re.sub(r'<think>.*?</think>', '', raw_content, flags=_re.DOTALL).strip()

    # Strip markdown code fences if the model wrapped the JSON
    if raw_content.startswith("```"):
        lines = raw_content.splitlines()
        raw_content = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    try:
        dfa_data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        return jsonify({
            "success": False,
            "error": f"AI returned invalid JSON: {str(e)}",
            "raw": raw_content[:500],
        }), 502

    # Extract optional fields before passing to DFA engine
    explanation   = dfa_data.pop("explanation", "AI-generated DFA.")
    sample_inputs = dfa_data.pop("sample_inputs", [])

    # Validate with our engine
    try:
        dfa_instance = DFA.from_dict(dfa_data, validate=True)
    except DFAValidationError as e:
        return jsonify({
            "success": False,
            "error": f"AI generated an invalid DFA: {str(e)}",
            "raw_dfa": dfa_data,
        }), 422

    return jsonify({
        "success": True,
        "dfa": dfa_instance.to_dict(),
        "edge_list": dfa_instance.to_transition_list(),
        "explanation": explanation,
        "sample_inputs": sample_inputs,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting DFA Simulator on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
