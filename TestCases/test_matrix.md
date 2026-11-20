# CSET302 — Testing and Verification Matrix
**Course:** CSET302 – Automata Theory and Computability  
**Project:** DFA Simulator (Topic 7: DFA String Processing Visualizer)  
**Team Members:** Mansimer Singh · Mayank Raj · Siddhi Sanap  

---

## 1. Test Verification Matrix (Prescribed Academic Template)

| Test ID | Feature / Machine Description | Input String | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T01** | DFA simulation: accepted string (*Ends with '01'*) | `01` | Accept (halting in $q_2 \in F$) | Accepted: halted in $q_2$ | **Pass** |
| **T02** | DFA simulation: rejected string (*Ends with '01'*) | `10` | Reject (halting in $q_0 \notin F$) | Rejected: halted in $q_0$ | **Pass** |
| **T03** | Unknown symbol in input alphabet | `10201` ($\Sigma = \{0, 1\}$) | Validation error / Reject invalid symbol | `REJECTED_INVALID_SYMBOL` ('2' at pos 2) | **Pass** |
| **T04** | Empty string $\varepsilon$ (Start state not accepting) | `""` (*Ends with '01'*, $q_0 \notin F$) | Reject (start state not final) | Rejected: $q_0 \notin F$ | **Pass** |
| **T05** | Empty string $\varepsilon$ (Start state is accepting) | `""` (*Even number of 0s*, $q_{even} \in F$) | Accept (start state is final) | Accepted: $q_{even} \in F$ | **Pass** |
| **T06** | Missing transition in partial DFA | Missing $\delta(q_1, 1)$ | Handled according to rules (reject) | `REJECTED_MISSING_TRANSITION` | **Pass** |
| **T07** | Non-deterministic duplicate transition definition | Duplicate $(q_0, 0) \to q_1$ and $(q_0, 0) \to q_2$ | `DFAValidationError` raised | Validation error caught & reported | **Pass** |
| **T08** | Invalid start state ($q_0 \notin Q$) | $q_0 = \text{"q99"}$ with $Q=\{q_0, q_1\}$ | `DFAValidationError` raised | Validation error: start state not in Q | **Pass** |
| **T09** | Invalid accepting state ($F \not\subseteq Q$) | $F = \{q_2\}$ with $Q=\{q_0, q_1\}$ | `DFAValidationError` raised | Validation error: accepting state not subset | **Pass** |
| **T10** | Empty state set $Q = \emptyset$ or $\Sigma = \emptyset$ | $Q = []$ | `DFAValidationError` raised | Validation error: Q must be non-empty | **Pass** |
| **T11** | Substring recognition (*Contains '101'*) | `01010` | Accept ($s_3 \in F$) | Accepted: halted in $s_3$ | **Pass** |
| **T12** | Substring non-occurrence (*Contains '101'*) | `111000` | Reject ($s_0 \notin F$) | Rejected: halted in $s_0$ | **Pass** |
| **T13** | Modulo arithmetic parity (*Even number of 0s*) | `0110` | Accept ($q_{even} \in F$) | Accepted: halted in $q_{even}$ | **Pass** |
| **T14** | Modulo arithmetic parity (*Even number of 0s*) | `010` (odd count: 2 zeros) | Reject ($q_{odd} \notin F$) | Rejected: halted in $q_{odd}$ | **Pass** |
| **T15** | Divisibility by 3 (*Binary divisible by 3*) | `110` (value 6, $6 \equiv 0 \pmod 3$) | Accept ($r_0 \in F$) | Accepted: halted in $r_0$ | **Pass** |
| **T16** | Cross-engine parity (Python engine vs JS engine) | All 6 demonstration presets | Identical verdict & step path | Exact parity verified via Node.js | **Pass** |
| **T17** | AI natural language DFA synthesis (*Odd number of 1s*) | Prompts Groq Qwen 27B model | Valid 5-tuple with $Q=\{q_0, q_1\}$ | Synthesized, verified by DFA engine | **Pass** |

---

## 2. Automated Test Execution Commands

To execute all unit, integration, and cross-verification tests:
```bash
python -m pytest tests/ -v
```

All 17 tests consistently execute in under 5 seconds with 100% pass rate.
