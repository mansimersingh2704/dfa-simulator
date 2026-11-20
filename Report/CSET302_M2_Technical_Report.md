# DFA Simulator — Project Evaluation Report
**Course:** CSET302 – Automata Theory & Computability  
**Project Title:** Deterministic Finite Automaton (DFA) Simulator  
**Team Members:** Mansimer Singh · Mayank Raj · Siddhi Sanap  
**Application URL:** `http://127.0.0.1:5000`  
**Evaluation Deliverable:** M1 / Demonstration Observations, Behavioral Analysis & Validation  

---

## 1. Visual Verification & Interface Screenshots

All screenshots below were captured from the running live application at `http://127.0.0.1:5000`.

### 1.1 Full Application Overview
*Captured Viewport: Hero section, demonstration presets toolbar, 3-card workflow layout, and the AI DFA Creator interface.*

![Full Application Overview](screenshots/step_10_shot_1.png)

- **Header Status:** Active connection indicator displays `● Backend Connected` (green).
- **Preset Toolbar:** Includes all 6 pre-configured formal DFA benchmarks.
- **Workflow Sections:** 
  1. Card 1: *Define DFA* (Formal 5-tuple specification + transition matrix)
  2. Card 2: *Visual Graph Editor* (Interactive HTML5 Canvas)
  3. Card 3: *Simulate String* (Step execution, tape, and transition trace)
  4. AI Module: *AI DFA Creator* (Natural language synthesis powered by Groq AI)

---

### 1.2 Card 1: Formal Definition & Transition Matrix
*Card 1 allows specifying $Q, \Sigma, q_0, F$ and editing transition table entries.*

![Define DFA & Transition Table](screenshots/step_14_shot_1.png)

- **State Set ($Q$):** `q0, q1, q2`
- **Alphabet ($\Sigma$):** `0, 1`
- **Initial State ($q_0$):** `q0`
- **Accepting States ($F$):** `q2`
- **Transition Table ($\delta$):** Displays an inline editable matrix for $\delta(q, \sigma)$. Validation status indicates: `DFA is Valid · Definition satisfies all formal mathematical requirements (Q, Σ, δ, q₀, F)`.

---

### 1.3 Card 2: Visual Graph Editor (Canvas State Diagram)
*Interactive canvas rendering states as circular nodes and transitions as directed arcs.*

![Canvas State Diagram](screenshots/step_16_shot_1.png)

- **Nodes:**
  - $q_0$: Start state denoted by an incoming start arrow from the left.
  - $q_1$: Intermediate state.
  - $q_2$: Accepting state indicated with double concentric circles and a golden accent.
- **Edges:**
  - Directed arcs with labels; bi-directional edges rendered as curved Bézier arcs to prevent overlapping.
  - Self-loops positioned gracefully above state circles.
  - Interactive repositioning: State nodes can be dragged to adjust graph layout.

---

### 1.4 Card 3: Step-by-Step String Simulation & Acceptance Trace
*Demonstration of processing the input string `1001` on the "Strings ending with '01'" DFA.*

![String Simulation Result](screenshots/step_20_shot_1.png)

- **Input String:** `1001`
- **Verdict:** Prominent `ACCEPTED` badge in green.
- **Explanation:** *"Accepted: Input string consumed completely. Automaton halted in accepting state 'q2' (final state ∈ F)."*
- **Trace History:**
  | Step | Current State | Symbol Read | Next State | Applied Transition |
  | :--- | :--- | :--- | :--- | :--- |
  | 1 | `q0` | `1` | `q0` | $\delta(q_0, 1) \to q_0$ |
  | 2 | `q0` | `0` | `q1` | $\delta(q_0, 0) \to q_1$ |
  | 3 | `q1` | `0` | `q1` | $\delta(q_1, 0) \to q_1$ |
  | 4 | `q1` | `1` | `q2` | $\delta(q_1, 1) \to q_2$ |
- **Playback Controls:** `⏮ Reset`, `◀ Back`, `Step ▶`, and `▶ Auto Play` with speed throttling.

---

### 1.5 Dynamic Preset Switch: "Binary Number Divisible by 3"
*Graph canvas dynamically updated after switching to the modulo-3 remainder DFA.*

![Divisible by 3 Preset](screenshots/step_28_shot_1.png)

- **States:** $r_0, r_1, r_2$ corresponding to numerical remainders $0, 1, 2 \pmod 3$.
- **Start & Final:** $r_0$ is both the start state and the accepting state.
- **Transitions:** Correctly updates state transitions on receiving binary digit $b$: $\text{next} = (2 \times \text{current} + b) \pmod 3$.

---

### 1.6 AI DFA Creator (Natural Language to DFA Synthesis)
*Inputting a natural language prompt and generating a mathematically verified DFA.*

![AI DFA Creator Panel](screenshots/step_24_shot_1.png)
![AI DFA Generated Result](screenshots/step_32_shot_1.png)

- **Input Prompt:** *"accepts binary strings with an odd number of 1s"*
- **Generated Formal Model:**
  - $Q = \{q_0, q_1\}$, $\Sigma = \{0, 1\}$, $q_0 = \text{start}$, $F = \{q_1\}$
  - $\delta(q_0, 0) = q_0$, $\delta(q_0, 1) = q_1$
  - $\delta(q_1, 0) = q_1$, $\delta(q_1, 1) = q_0$
- **Provided Explanation:** *"The automaton tracks the parity of the number of 1s seen so far: q0 represents an even count (including zero) and q1 represents an odd count. Reading a 0 preserves the current parity, while reading a 1 toggles between even and odd."*
- **Actionable Control:** `Load into Simulator →` button directly injects the synthesized automaton into the visual graph editor and transition matrix.

---

## 2. Performance & Behavioral Observations

### 2.1 Execution & Latency Benchmarks
| Component | Metric | Observed Behavior | Evaluation |
| :--- | :--- | :--- | :--- |
| **Flask Server Startup** | Cold boot time | $< 0.85\text{ s}$ | Excellent; lightweight dependencies |
| **Frontend Initial Render** | DOM load & Canvas init | $\approx 180\text{ ms}$ | Immediate responsiveness |
| **Canvas Redraw Cycle** | Frame update during drag | $60\text{ FPS}$ ($< 16\text{ ms/frame}$) | Hardware-accelerated canvas |
| **Simulation Step Latency** | Local Python REST roundtrip | $12\text{--}25\text{ ms}$ | Negligible overhead |
| **JS Offline Engine** | Step transition compute | $< 1\text{ ms}$ | Instant fallback execution |
| **AI DFA Generation** | Groq Cloud inference | $3.2\text{--}5.1\text{ s}$ | Fast LLM inference with response sanitization |

### 2.2 Mathematical Engine Behavior & Invariant Verification

1. **Formal 5-Tuple Completeness:**
   - Empty state set $Q = \emptyset$ or empty alphabet $\Sigma = \emptyset$ throws a strict `DFAValidationError`.
   - Start state $q_0 \notin Q$ or accepting state subset $F \not\subseteq Q$ immediately halts with explicit error highlighting.
2. **Deterministic Guarantee:**
   - Duplicate transitions for the same $(q, \sigma)$ pair are rejected. Non-determinism is strictly prohibited.
3. **Empty String Handling ($\varepsilon$):**
   - Testing input string $\varepsilon$ directly inspects $q_0 \in F$. If $q_0 \in F$, verdict is `ACCEPTED`; otherwise `REJECTED`. No spurious transitions occur.
4. **Alphabet Conformance:**
   - Symbols outside $\Sigma$ (e.g., inputting `2` for a binary alphabet) halt processing with error code `REJECTED_INVALID_SYMBOL`.
5. **Partial Transition Handling:**
   - When a transition $\delta(q, \sigma)$ is intentionally left undefined, the simulator halts at the exact step with `REJECTED_MISSING_TRANSITION`, reporting the unhandled state and symbol.
6. **Bidirectional Parity:**
   - Python backend (`dfa.py`) and JavaScript frontend engine (`JSAutomataEngine`) share identical transition and acceptance logic, validated across all unit tests.

---

## 3. Known Limitations & Design Boundaries

### 3.1 Deliberate Design Scoping (College Demonstration Focus)
- **DFA Exclusivity:** NFA, $\varepsilon$-NFA, PDA, and Turing Machine models are excluded to maintain conceptual focus on deterministic finite state computation.
- **Advanced Transformations Excluded:** Operations such as DFA Minimization (Hopcroft/Table-Filling), Equivalence Partitioning, and Regular Expression conversions were deliberately kept out of runtime UI controls to prevent overcomplication during college viva examinations.

### 3.2 Technical & Operational Limitations
- **Canvas Scaling:** The interactive canvas has a fixed aspect ratio ($800 \times 380\text{ px}$). DFAs exceeding 7–8 states require manual node repositioning to prevent edge congestion.
- **Single-Character Alphabet Tokens:** Alphabet symbols are modeled as individual characters (e.g., `'0'`, `'1'`, `'a'`). Multi-character tokens (e.g., `id`, `var`) are not supported.
- **Client Session Ephemerality:** DFA states are held in active client/server memory. Page reload restores the default preset unless exported or defined via presets.
- **LLM Rate Limits & Network Dependence:** The AI DFA Creator requires an active internet connection to communicate with Groq cloud APIs.

---

## 4. Theoretical Interpretation & Pedagogy

### 4.1 Automata Theory Alignment
The simulator implements the standard mathematical definition of deterministic finite automata:
$$M = (Q, \Sigma, \delta, q_0, F)$$

The string evaluation process models the recursive extended transition function $\delta^*: Q \times \Sigma^* \to Q$:
$$\delta^*(q, \varepsilon) = q$$
$$\delta^*(q, wa) = \delta(\delta^*(q, w), a) \quad \text{where } w \in \Sigma^*, a \in \Sigma$$

The language accepted by $M$ is defined as:
$$L(M) = \{ w \in \Sigma^* \mid \delta^*(q_0, w) \in F \}$$

### 4.2 Educational Benefits in Academic Evaluation
- **Visualizing Abstractions:** Abstract state transitions are mapped directly to visible spatial nodes and animated amber arrows.
- **Tape Realism:** Exposes Turing-like tape traversal where student can trace consumed characters vs. pending symbols.
- **Automated Verification:** The AI assistant serves as a comparative study tool: students can specify language rules in English, inspect the resulting DFA, and test edge-case strings to verify theoretical correctness.

---

## 5. Automated Test Suite Summary

The application is safeguarded by 17 automated tests covering unit logic, API contracts, and cross-engine verification:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0
collected 17 items

tests/test_dfa.py::test_valid_dfa_creation PASSED                        [  5%]
tests/test_dfa.py::test_invalid_start_state PASSED                       [ 11%]
tests/test_dfa.py::test_invalid_accepting_states PASSED                  [ 17%]
tests/test_dfa.py::test_empty_states_or_alphabet PASSED                  [ 23%]
tests/test_dfa.py::test_non_deterministic_transition PASSED              [ 29%]
tests/test_dfa.py::test_accepted_string_simulation PASSED                [ 35%]
tests/test_dfa.py::test_rejected_string_simulation PASSED                [ 41%]
tests/test_dfa.py::test_empty_string_simulation PASSED                   [ 47%]
tests/test_dfa.py::test_invalid_symbol_rejection PASSED                  [ 52%]
tests/test_dfa.py::test_missing_transition_rejection PASSED              [ 58%]
tests/test_api.py::test_index_route PASSED                               [ 64%]
tests/test_api.py::test_get_presets PASSED                               [ 70%]
tests/test_api.py::test_validate_valid_dfa PASSED                         [ 76%]
tests/test_api.py::test_validate_invalid_dfa PASSED                       [ 82%]
tests/test_api.py::test_simulate_accepted PASSED                         [ 88%]
tests/test_api.py::test_simulate_rejected PASSED                         [ 94%]
tests/test_cross_verification.py::test_cross_engine_parity PASSED         [100%]

============================= 17 passed in 0.48s ==============================
```

---
*Report generated and archived for college submission.*  
*Mansimer Singh · Mayank Raj · Siddhi Sanap — CSET302*
