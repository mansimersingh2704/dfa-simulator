# DFA Simulator (Topic 7) — CSET302

**Course:** CSET302 – Automata Theory and Computability  
**Project Topic 7:** DFA String Processing Visualizer  
**Group Members:**
- Mansimer Singh
- Mayank Raj
- Siddhi Sanap  
**Institution:** Bennett University | School of Computer Science Engineering & Technology (SCSET)  
**Milestone:** Milestone-II Final Demonstration & Source Code Submission  

---

## Overview: What does the simulator do?

The **DFA Simulator** is a complete, interactive, web-based automata laboratory designed for educational demonstration and theoretical validation in formal language theory. 

The application implements the formal 5-tuple specification of a Deterministic Finite Automaton:
$$M = (Q, \Sigma, \delta, q_0, F)$$

It allows students and instructors to:
1. **Define and configure** arbitrary custom DFAs or choose from 6 mathematical presets.
2. **Interact visually** with an HTML5 canvas graph editor that renders states, self-loops, and curved transition edges.
3. **Simulate string processing step-by-step** with a dynamic input tape, animated active states, real-time transition highlighting, and an automated trace history table.
4. **Synthesize DFAs using AI (Groq AI)** from natural language descriptions, complete with automatic mathematical verification by the core Python engine.
5. **Operate offline** with a built-in client-side JavaScript engine that runs symmetrically if the backend is detached.

---

## Supported features: list implemented operations

- **Formal 5-Tuple DFA Creation & Validation:**
  - Dynamic definition of state set $Q$, input alphabet $\Sigma$, start state $q_0 \in Q$, and final states $F \subseteq Q$.
  - Strict validation preventing duplicate transitions (guaranteeing determinism).
  - Explicit error handling for unknown symbols, unreachable states, and malformed definitions.
- **Interactive Visual Canvas Graph Editor:**
  - Drag-and-drop state node positioning with persistent layout calculations.
  - Distinct visual representations: incoming start arrow ($\to q_0$), double-ring concentric circles for accepting states ($q \in F$), and active amber highlight for execution state.
  - Curved Bézier arcs for two-way edges and self-loop arcs for recursive transitions.
  - Automatic circular graph layout button.
- **Step-by-Step String Processing Simulation:**
  - Turing-style horizontal tape visualizer showing consumed, active, and remaining characters.
  - Playback controls: `Run String` (immediate verdict), `Step ▶` (single symbol transition), `◀ Back` (step rewind), `⏮ Reset`, and `▶ Auto Play` with speed adjustment.
  - Comprehensive execution trace table recording $(q_{\text{current}}, \sigma, q_{\text{next}})$ triples.
  - Clear, prominent `ACCEPTED` (green) or `REJECTED` (red) status badges with theoretical explanations.
  - Handles the empty string ($\varepsilon$), invalid alphabet symbols, and missing transitions without silent failure.
- **AI-Powered Natural Language DFA Creator:**
  - Natural language translation of formal language descriptions into valid DFAs via Groq's high-speed inference engine (`qwen/qwen3.8-27b`).
  - Pre-load verification by the Python engine before displaying to ensure mathematical correctness.
  - One-click `Load into Simulator →` button to test and visually step through AI-synthesized machines.
- **6 Demonstration Presets:**
  - Strings ending with `'01'`
  - Strings containing `'101'`
  - Even number of `'0'`s (parity language)
  - Strings ending with `'1'`
  - Binary number divisible by 3 (modulo-3 arithmetic)
  - Strings starting and ending with `'1'`

---

## Technology stack and dependencies: versions

- **Backend Language & Framework:** Python 3.10+ (tested on Python 3.14.3), Flask $\ge$ 3.0.0
- **Frontend Architecture:** Vanilla JavaScript (ES6+), HTML5 Canvas API, CSS3 (Modern Deep-Indigo & Warm-Amber theme with Light/Dark mode)
- **AI Integration:** Groq API (`qwen/qwen3.8-27b` fast reasoning model via `requests`)
- **Automated Testing Suite:** `pytest` $\ge$ 8.0.0
- **Documentation & Presentation:** `python-pptx` $\ge$ 1.0.0

---

## Installation: numbered setup commands

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mansimersingh2704/dfa-simulator.git
   cd dfa-simulator
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Configure AI Creator API Key:**
   To use your own Groq API key, copy `.env.example` to `.env` or set the environment variable:
   ```bash
   set GROQ_API_KEY=your_groq_api_key_here
   ```
   *(A working default key is already pre-configured in `app.py` for immediate demonstration).*

---

## How to run: exact command and entry point

1. **Start the Flask server:**
   ```bash
   python app.py
   ```
2. **Access the application:**
   Open any modern browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## Example: sample automaton definition, input and output

### Sample DFA: Strings ending with '01'
- **States ($Q$):** `q0, q1, q2`
- **Alphabet ($\Sigma$):** `0, 1`
- **Start State ($q_0$):** `q0`
- **Accepting States ($F$):** `q2`
- **Transition Table ($\delta$):**
  - $\delta(q_0, 0) = q_1, \quad \delta(q_0, 1) = q_0$
  - $\delta(q_1, 0) = q_1, \quad \delta(q_1, 1) = q_2$
  - $\delta(q_2, 0) = q_1, \quad \delta(q_2, 1) = q_0$

### Execution Example 1 (Accepted String):
- **Input:** `1001`
- **Trace:**
  - Step 1: $q_0 \xrightarrow{1} q_0$
  - Step 2: $q_0 \xrightarrow{0} q_1$
  - Step 3: $q_1 \xrightarrow{0} q_1$
  - Step 4: $q_1 \xrightarrow{1} q_2$
- **Output:** **ACCEPTED** (Halts in state $q_2 \in F$).

### Execution Example 2 (Rejected String):
- **Input:** `1000`
- **Trace:** $q_0 \xrightarrow{1} q_0 \xrightarrow{0} q_1 \xrightarrow{0} q_1 \xrightarrow{0} q_1$
- **Output:** **REJECTED** (Halts in state $q_1 \notin F$).

---

## Project structure: modules and responsibilities

```text
dfa-simulator/
├── app.py                          # Flask backend web server & REST API endpoints
├── dfa.py                          # Core formal DFA mathematical engine (M = (Q, Σ, δ, q0, F))
├── requirements.txt                # Pinned project dependencies
├── README.md                       # Comprehensive project documentation
├── .gitignore                      # Git exclusion rules
├── .env.example                    # Sample environment variables for Groq AI
├── templates/
│   └── index.html                  # Responsive single-page application interface
├── static/
│   ├── style.css                   # Custom theme styling & dark mode support
│   └── app.js                      # Canvas visual editor, step playback & offline JS engine
├── tests/
│   ├── test_dfa.py                 # Core engine unit tests (validation & simulation)
│   ├── test_api.py                 # Flask REST API endpoint verification tests
│   └── test_cross_verification.py  # Python vs JS cross-engine parity verification
├── TestCases/
│   ├── test_matrix.md              # Formal evaluation test matrix (T01 - T17)
│   └── sample_dfas.json            # Machine definitions & sample inputs
├── Report/
│   ├── CSET302_M2_Technical_Report.md # Formal Milestone-II technical report
│   └── DFA_Simulator_M1.pptx       # Milestone-I design presentation slides
└── Screenshots/                    # Captured live application feature screenshots
    ├── step_10_shot_1.png          # Full application overview
    ├── step_14_shot_1.png          # Formal definition & transition matrix
    ├── step_16_shot_1.png          # Visual graph canvas diagram
    ├── step_20_shot_1.png          # Step execution trace & acceptance verdict
    ├── step_24_shot_1.png          # AI DFA Creator interface
    ├── step_28_shot_1.png          # Divisible by 3 preset demonstration
    └── step_32_shot_1.png          # AI synthesized DFA result
```

---

## Testing: command, test data and expected behavior

### Running the Test Suite
Execute pytest from the project root:
```bash
python -m pytest tests/ -v
```

### Test Coverage Highlights
- **Engine Logic (`test_dfa.py`):**
  - Validation of non-empty $Q$ and $\Sigma$.
  - Start state membership $q_0 \in Q$ and subset check $F \subseteq Q$.
  - Detection and rejection of non-deterministic transitions.
  - Acceptance and rejection across binary strings.
  - Empty string ($\varepsilon$) handling for both accepting and non-accepting start states.
  - Rejection of invalid alphabet symbols.
  - Explicit handling and reporting of missing transitions in partial DFAs.
- **REST API Contracts (`test_api.py`):**
  - `GET /` serves HTML frontend.
  - `GET /api/presets` returns the 6 benchmark configurations.
  - `POST /api/validate` validates formal specifications.
  - `POST /api/simulate` processes string and returns step triples.
- **Cross-Engine Parity (`test_cross_verification.py`):**
  - Uses Node.js to simulate the same test cases on `static/app.js` and asserts 100% trace and verdict equality with `dfa.py`.

---

## Known limitations and troubleshooting

- **Canvas Visual Density:** On complex automata ($> 7$ states) with numerous transitions, edge labels may cluster. Users can drag nodes to arrange them cleanly or click **Auto Layout**.
- **Alphabet Character Size:** Input alphabet symbols must be single characters (e.g., `'0'`, `'1'`, `'a'`). Multi-character tokens are not supported.
- **Incomplete DFAs:** Missing transitions are not silently completed into a sink state; the simulator explicitly halts with `REJECTED_MISSING_TRANSITION` to emphasize mathematical precision.
- **Port In Use (5000):** If port 5000 is occupied, run with a custom port:
  ```bash
  set PORT=5050
  python app.py
  ```

---

## Team contributions and acknowledgements

### Group Members & Roles
- **Mansimer Singh:** Core DFA mathematical engine (`dfa.py`), transition function validation, step trace algorithm, and Groq AI synthesis module.
- **Mayank Raj:** Flask web server (`app.py`), REST API endpoint architecture, backend error handling, and test suite implementation (`tests/`).
- **Siddhi Sanap:** Frontend interface (`templates/index.html`), interactive HTML5 Canvas visual graph editor (`static/app.js`), responsive CSS styling, and documentation.

### Acknowledgements
- Developed for **CSET302: Automata Theory and Computability**, Bennett University.
- Prescribed curriculum aligned with Hopcroft, Motwani, and Ullman's *Introduction to Automata Theory, Languages, and Computation*.
