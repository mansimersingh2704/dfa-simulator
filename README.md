# DFA Simulator — CSET302 Automata Theory & Computability

A comprehensive, mathematically rigorous Deterministic Finite Automaton (DFA) Simulator built for college demonstration and coursework evaluation in **CSET302 – Automata Theory and Computability**.

---

## 🌟 Key Features

1. **Formal Automaton Mathematical Engine (`dfa.py`)**:
   - Formal 5-tuple: $M = (Q, \Sigma, \delta, q_0, F)$
   - Non-empty state and alphabet validation ($Q \neq \emptyset$, $\Sigma \neq \emptyset$)
   - Determinism validation: duplicate transition detection rejecting non-deterministic definitions
   - Support for both partial and total transition functions
   - Step-by-step trace simulation returning `(state, symbol, next_state)` triples
   - Plain-language explanation for every acceptance and rejection verdict

2. **Automata Theory Operations**:
   - **Minimization**: Myhill-Nerode Table-Filling algorithm (Hopcroft/Moore equivalence partitioning)
   - **Complement**: $F' = Q \setminus F$ operating strictly on completed DFAs
   - **Completion**: Adds a canonical sink/trap state with self-loops to guarantee totality
   - **Equivalence Checking**: Product automaton BFS over symmetric difference with minimal counterexample string generation
   - **Unreachable State Pruning**: Disconnected state detection and automatic removal

3. **Interactive Visual DFA Editor & Studio**:
   - HTML5 Canvas interactive graph with drag-and-drop state positioning
   - Start state indicator arrow ($\to q_0$) and accepting double-ring circles
   - Self-loops, curved bidirectional edges (preventing overlap), and merged symbol labels
   - Real-time synchronization between the visual canvas, formal 5-tuple inputs, and the transition table matrix
   - Deep-indigo and warm-amber theme with one-click Dark Mode toggle

4. **Step-by-Step Simulation & Tape**:
   - Interactive tape display highlighting consumed, active, and remaining symbols
   - Step, Back, Reset, and Auto-Play with customizable playback speed
   - Glowing active-state and active-transition edge highlights
   - "Why?" explainability panel breaking down every step

5. **Batch Testing & CSV Export**:
   - Multi-string batch simulation with expected pass/fail evaluation
   - One-click CSV export of batch test results

6. **Dual-Mode Execution (Integration & Fallback)**:
   - Modern `fetch` connection to Flask HTTP REST API
   - Pure-JavaScript client fallback engine guaranteeing identical results even when offline

7. **8 Curated Mathematical Presets**:
   - Strings ending with `01`
   - Strings containing `101`
   - Even number of 0s and 1s
   - Binary numbers divisible by 3
   - Strings starting with `ab`
   - Length divisible by 3
   - No two consecutive 1s
   - Keyword matcher for `cat`

---

## 📂 Project Structure

```text
dfa-simulator/
├── app.py                         # Flask web API backend and routes
├── dfa.py                         # Core formal DFA mathematical engine
├── requirements.txt               # Project dependencies
├── README.md                      # Documentation and run instructions
├── templates/
│   └── index.html                 # Single-page application frontend
├── static/
│   ├── style.css                  # Deep-indigo & warm-amber CSS (with Dark Mode)
│   └── app.js                     # Canvas visualizer & client-side fallback simulator
└── tests/
    ├── test_dfa.py                # Core mathematical & simulation unit tests (18 tests)
    ├── test_api.py                # Flask REST API endpoint tests (11 tests)
    └── test_cross_verification.py # Python vs JS cross-engine verification tests (3 tests)
```

---

## 🚀 Setup and Run Instructions

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Modern web browser (Chrome, Edge, Firefox, Safari)
- Optional: Node.js (for running cross-verification tests)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Web Application
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

### 4. Run Pytest Test Suite
To run all 32 unit, integration, and cross-verification tests:
```bash
python -m pytest tests/ -v
```

---

## 🔬 Live Demonstration Guide for College Viva

1. **Preset Exploration**: Select "Binary numbers divisible by 3" or "Strings ending with '01'". Click "Load Preset" and test sample inputs using the quick-fill chips.
2. **Visual Editor**: Add custom states, drag them on the canvas, add transitions, and observe real-time updates in the formal 5-tuple and transition matrix.
3. **Step Simulation**: Type an input string like `1001` or `01`. Click "Step" repeatedly to observe the input tape pointer, glowing state transitions on the canvas, and the "Why?" panel explanation.
4. **Theory Operations**:
   - Click "Minimize DFA" under the Theory Operations tab to witness state reduction via the Myhill-Nerode table-filling algorithm.
   - Click "Equivalence Checker" to compare against another preset; observe the generated minimal counterexample string when they differ.
5. **Batch Testing**: Run batch simulations on multiple strings simultaneously and export the evaluated results to CSV.
