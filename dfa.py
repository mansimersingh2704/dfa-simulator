"""
DFA (Deterministic Finite Automaton) Engine
============================================
Mathematical Formalism:
    M = (Q, Σ, δ, q0, F)
    - Q: Non-empty finite set of states
    - Σ: Non-empty finite set of input symbols (alphabet)
    - δ: Transition function Q × Σ → Q (can be partial or total)
    - q0: Start state (q0 ∈ Q)
    - F: Set of accepting / final states (F ⊆ Q)

This module implements the core mathematical representations, validation,
step-by-step trace simulation, and formal theory operations:
    1. DFA Definition Validation (formal constraints)
    2. Missing transition detection and partial DFA support
    3. Step-by-step simulation with trace triples and plain-language explanations
    4. Unreachable state detection and removal
    5. Partial DFA completion with canonical sink state
    6. Language complementation (F' = Q \\ F on complete DFA)
    7. DFA minimization via Myhill-Nerode Table-Filling algorithm
    8. DFA equivalence checking with minimal counterexample generation
    9. JSON serialization and deserialization

Author: CSET302 Automata Theory & Computability Project Team
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


class DFAValidationError(ValueError):
    """Raised when a DFA definition violates formal mathematical requirements."""

    pass


@dataclass(frozen=True)
class TransitionStep:
    """Represents a single step in the DFA simulation trace."""

    step: int
    from_state: str
    symbol: str
    to_state: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "from_state": self.from_state,
            "symbol": self.symbol,
            "to_state": self.to_state,
            "triple": (self.from_state, self.symbol, self.to_state),
        }


@dataclass
class SimulationResult:
    """Contains the complete result and explanation of simulating a string on a DFA."""

    accepted: bool
    input_string: str
    start_state: str
    final_state: Optional[str]
    path: List[str]
    trace: List[Dict[str, Any]]
    status: str
    explanation: str
    consumed_count: int
    total_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DFA:
    """Deterministic Finite Automaton M = (Q, Σ, δ, q0, F).

    Attributes:
        states (Set[str]): Finite set of states Q.
        alphabet (Set[str]): Finite set of input symbols Σ.
        transitions (Dict[str, Dict[str, str]]): δ mapping state -> (symbol -> next_state).
        start_state (str): Initial state q0 ∈ Q.
        accepting_states (Set[str]): Subset of final states F ⊆ Q.
    """

    def __init__(
        self,
        states: Set[str] | List[str],
        alphabet: Set[str] | List[str],
        transitions: Dict[str, Dict[str, str]] | List[Dict[str, str]] | List[Tuple[str, str, str]],
        start_state: str,
        accepting_states: Set[str] | List[str],
        validate: bool = True,
    ) -> None:
        # Convert to standardized types
        self.states: Set[str] = {str(s).strip() for s in states}
        self.alphabet: Set[str] = {str(a) for a in alphabet}
        self.start_state: str = str(start_state).strip() if start_state is not None else ""
        self.accepting_states: Set[str] = {str(s).strip() for s in accepting_states}

        # Normalize transition function: δ[state][symbol] = next_state
        self.transitions: Dict[str, Dict[str, str]] = {q: {} for q in self.states}

        if isinstance(transitions, dict):
            for state, symbol_map in transitions.items():
                s = str(state).strip()
                if s not in self.transitions:
                    self.transitions[s] = {}
                if isinstance(symbol_map, dict):
                    for sym, next_s in symbol_map.items():
                        self.transitions[s][str(sym)] = str(next_s).strip()
        elif isinstance(transitions, list):
            # List of transition objects or tuples: check for non-determinism/duplicates
            seen_pairs: Set[Tuple[str, str]] = set()
            for entry in transitions:
                if isinstance(entry, dict):
                    q_from = str(entry.get("from") or entry.get("source") or entry.get("from_state")).strip()
                    sym = str(entry.get("symbol") if entry.get("symbol") is not None else entry.get("label"))
                    q_to = str(entry.get("to") or entry.get("target") or entry.get("to_state")).strip()
                elif isinstance(entry, (tuple, list)) and len(entry) == 3:
                    q_from, sym, q_to = str(entry[0]).strip(), str(entry[1]), str(entry[2]).strip()
                else:
                    raise DFAValidationError(f"Invalid transition format: {entry}")

                pair = (q_from, sym)
                if pair in seen_pairs:
                    raise DFAValidationError(
                        f"Non-deterministic transition detected: duplicate transition for state '{q_from}' on symbol '{sym}'."
                    )
                seen_pairs.add(pair)

                if q_from not in self.transitions:
                    self.transitions[q_from] = {}
                self.transitions[q_from][sym] = q_to

        if validate:
            self.validate()

    # -------------------------------------------------------------------------
    # Formal Definition Validation
    # -------------------------------------------------------------------------
    def validate(self) -> None:
        """Validates formal mathematical 5-tuple constraints for M = (Q, Σ, δ, q0, F).

        Raises:
            DFAValidationError: If any formal condition is violated.
        """
        # 1. Non-empty state set Q
        if not self.states:
            raise DFAValidationError("State set Q must be non-empty.")

        # 2. Non-empty alphabet Σ
        if not self.alphabet:
            raise DFAValidationError("Alphabet Σ must be non-empty.")

        for sym in self.alphabet:
            if sym == "":
                raise DFAValidationError("Alphabet symbols cannot be empty strings.")

        # 3. Start state q0 must belong to Q
        if not self.start_state:
            raise DFAValidationError("Start state q0 must be specified.")
        if self.start_state not in self.states:
            raise DFAValidationError(
                f"Start state '{self.start_state}' is not in the set of states Q: {sorted(self.states)}."
            )

        # 4. Accepting states F must be a subset of Q
        invalid_final = self.accepting_states - self.states
        if invalid_final:
            raise DFAValidationError(
                f"Accepting states must be a subset of Q. Invalid states: {sorted(invalid_final)}."
            )

        # 5. Transition source states, symbols, and destination states must be valid
        for q_from, sym_map in self.transitions.items():
            if q_from not in self.states:
                raise DFAValidationError(
                    f"Transition source state '{q_from}' does not belong to state set Q."
                )
            for sym, q_to in sym_map.items():
                if sym not in self.alphabet:
                    raise DFAValidationError(
                        f"Transition on symbol '{sym}' from state '{q_from}' uses a symbol not in alphabet Σ: {sorted(self.alphabet)}."
                    )
                if q_to not in self.states:
                    raise DFAValidationError(
                        f"Transition destination state '{q_to}' on symbol '{sym}' from state '{q_from}' is not in Q."
                    )

    def is_total(self) -> bool:
        """Returns True if the transition function δ is total (defined for all Q × Σ)."""
        for state in self.states:
            state_trans = self.transitions.get(state, {})
            for sym in self.alphabet:
                if sym not in state_trans:
                    return False
        return True

    def get_missing_transitions(self) -> List[Tuple[str, str]]:
        """Returns a sorted list of (state, symbol) pairs where δ(state, symbol) is undefined."""
        missing: List[Tuple[str, str]] = []
        for state in sorted(self.states):
            state_trans = self.transitions.get(state, {})
            for sym in sorted(self.alphabet):
                if sym not in state_trans:
                    missing.append((state, sym))
        return missing

    # -------------------------------------------------------------------------
    # Simulation Engine
    # -------------------------------------------------------------------------
    def simulate(self, input_string: str) -> SimulationResult:
        """Simulates an input string step-by-step through the automaton.

        Args:
            input_string (str): The sequence of symbols to test.

        Returns:
            SimulationResult: Detailed execution result, complete trace triples,
                              final state, acceptance verdict, and explainable message.
        """
        # Ensure automaton definition is valid before simulation
        self.validate()

        current_state = self.start_state
        path: List[str] = [current_state]
        trace: List[Dict[str, Any]] = []

        # Edge Case 1: Empty String ε
        if input_string == "":
            is_accepted = current_state in self.accepting_states
            status = "ACCEPTED" if is_accepted else "REJECTED_NON_FINAL"
            if is_accepted:
                explanation = (
                    f"Accepted: Empty string (ε) processed. Automaton remains in start state "
                    f"'{current_state}', which is an accepting state (q0 ∈ F)."
                )
            else:
                explanation = (
                    f"Rejected: Empty string (ε) processed. Automaton remains in start state "
                    f"'{current_state}', which is NOT an accepting state (q0 ∉ F)."
                )
            return SimulationResult(
                accepted=is_accepted,
                input_string=input_string,
                start_state=self.start_state,
                final_state=current_state,
                path=path,
                trace=trace,
                status=status,
                explanation=explanation,
                consumed_count=0,
                total_count=0,
            )

        # Process string symbol by symbol
        for idx, symbol in enumerate(input_string):
            # Check if symbol is part of alphabet Σ
            if symbol not in self.alphabet:
                return SimulationResult(
                    accepted=False,
                    input_string=input_string,
                    start_state=self.start_state,
                    final_state=None,
                    path=path,
                    trace=trace,
                    status="REJECTED_INVALID_SYMBOL",
                    explanation=(
                        f"Rejected: Symbol '{symbol}' at position {idx} is invalid. "
                        f"It does not belong to the alphabet Σ = {{{', '.join(sorted(self.alphabet))}}}."
                    ),
                    consumed_count=idx,
                    total_count=len(input_string),
                )

            # Check if transition is defined for (current_state, symbol)
            state_trans = self.transitions.get(current_state, {})
            if symbol not in state_trans:
                return SimulationResult(
                    accepted=False,
                    input_string=input_string,
                    start_state=self.start_state,
                    final_state=current_state,
                    path=path,
                    trace=trace,
                    status="REJECTED_MISSING_TRANSITION",
                    explanation=(
                        f"Rejected: Missing transition δ('{current_state}', '{symbol}'). "
                        f"Automaton halted abruptly at position {idx} because no transition is defined "
                        f"for state '{current_state}' on symbol '{symbol}'."
                    ),
                    consumed_count=idx,
                    total_count=len(input_string),
                )

            next_state = state_trans[symbol]
            step_record = TransitionStep(
                step=idx + 1,
                from_state=current_state,
                symbol=symbol,
                to_state=next_state,
            )
            trace.append(step_record.to_dict())
            current_state = next_state
            path.append(current_state)

        # String fully consumed: Check whether final state is in F
        is_accepted = current_state in self.accepting_states
        if is_accepted:
            status = "ACCEPTED"
            explanation = (
                f"Accepted: Entire input of length {len(input_string)} was successfully consumed. "
                f"Automaton halted in state '{current_state}', which is an accepting state (final state ∈ F)."
            )
        else:
            status = "REJECTED_NON_FINAL"
            explanation = (
                f"Rejected: Entire input of length {len(input_string)} was consumed, but the automaton "
                f"halted in state '{current_state}', which is NOT an accepting state (final state ∉ F)."
            )

        return SimulationResult(
            accepted=is_accepted,
            input_string=input_string,
            start_state=self.start_state,
            final_state=current_state,
            path=path,
            trace=trace,
            status=status,
            explanation=explanation,
            consumed_count=len(input_string),
            total_count=len(input_string),
        )

    # -------------------------------------------------------------------------
    # Theory Operations
    # -------------------------------------------------------------------------
    def get_reachable_states(self) -> Set[str]:
        """Finds all states reachable from the start state q0 via breadth-first search."""
        if self.start_state not in self.states:
            return set()

        visited: Set[str] = {self.start_state}
        queue: deque[str] = deque([self.start_state])

        while queue:
            state = queue.popleft()
            for next_state in self.transitions.get(state, {}).values():
                if next_state in self.states and next_state not in visited:
                    visited.add(next_state)
                    queue.append(next_state)

        return visited

    def get_unreachable_states(self) -> Set[str]:
        """Returns the set of states Q that cannot be reached from the start state q0."""
        return self.states - self.get_reachable_states()

    def remove_unreachable_states(self) -> DFA:
        """Returns a new DFA with all unreachable states and their incident transitions removed."""
        reachable = self.get_reachable_states()
        new_states = reachable if reachable else {self.start_state}
        new_accepting = self.accepting_states & new_states

        new_transitions: Dict[str, Dict[str, str]] = {q: {} for q in new_states}
        for q in new_states:
            for sym, next_q in self.transitions.get(q, {}).items():
                if next_q in new_states:
                    new_transitions[q][sym] = next_q

        return DFA(
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_transitions,
            start_state=self.start_state,
            accepting_states=new_accepting,
            validate=True,
        )

    def complete(self, sink_name: str = "dead_sink") -> DFA:
        """Completes a partial DFA by adding a canonical dead/sink state for all missing transitions.

        If the DFA is already total, returns an identical copy.

        Args:
            sink_name (str): Desired name for the sink state. If already taken, an index is appended.

        Returns:
            DFA: A new total DFA with identical language recognition.
        """
        self.validate()
        missing = self.get_missing_transitions()
        if not missing:
            # Already total
            return self.clone()

        # Find unique name for sink state
        actual_sink = sink_name
        idx = 1
        while actual_sink in self.states:
            actual_sink = f"{sink_name}_{idx}"
            idx += 1

        new_states = set(self.states)
        new_states.add(actual_sink)

        # Clone transitions
        new_transitions: Dict[str, Dict[str, str]] = {
            q: dict(self.transitions.get(q, {})) for q in self.states
        }
        new_transitions[actual_sink] = {}

        # Route all missing transitions to the sink state
        for q, sym in missing:
            new_transitions[q][sym] = actual_sink

        # Sink state self-loops on all alphabet symbols
        for sym in self.alphabet:
            new_transitions[actual_sink][sym] = actual_sink

        return DFA(
            states=new_states,
            alphabet=self.alphabet,
            transitions=new_transitions,
            start_state=self.start_state,
            accepting_states=self.accepting_states,
            validate=True,
        )

    def complement(self) -> DFA:
        """Computes the complement DFA M' such that L(M') = Σ* \\ L(M).

        Note: Automata theory strictly requires that complementation operates on a COMPLETE DFA.
        If this DFA is partial, it is automatically completed with a sink state before swapping states.

        Returns:
            DFA: The complemented automaton with accepting states F' = Q \\ F.
        """
        # Step 1: Ensure completeness
        completed_dfa = self.complete()

        # Step 2: Invert accepting states: F' = Q \ F
        new_accepting = completed_dfa.states - completed_dfa.accepting_states

        return DFA(
            states=completed_dfa.states,
            alphabet=completed_dfa.alphabet,
            transitions=completed_dfa.transitions,
            start_state=completed_dfa.start_state,
            accepting_states=new_accepting,
            validate=True,
        )

    def minimize(self) -> DFA:
        """Minimizes the DFA using the Myhill-Nerode Table-Filling Algorithm.

        Steps:
            1. Eliminate all unreachable states from q0.
            2. Complete the DFA so transitions are total across Q × Σ.
            3. Build distinguishable pair table:
               - Base case: All pairs (p, q) where (p ∈ F and q ∉ F) or vice-versa are distinguishable.
               - Induction: For unmarked (p, q), if there exists a ∈ Σ such that (δ(p, a), δ(q, a))
                 is distinguishable, mark (p, q) as distinguishable. Repeat until fixpoint.
            4. Unmarked pairs are equivalent (indistinguishable). Group into equivalence classes.
            5. Construct the quotient DFA from these equivalence classes.

        Returns:
            DFA: An equivalent minimal DFA with the smallest possible state count.
        """
        # Step 1: Eliminate unreachable states
        dfa_reachable = self.remove_unreachable_states()

        # Step 2: Complete the DFA to ensure total transition function for equivalence partitioning
        dfa_total = dfa_reachable.complete()

        states_list = sorted(dfa_total.states)
        n = len(states_list)
        if n <= 1:
            return dfa_total.clone()

        # Index mapping for states
        state_idx = {s: i for i, s in enumerate(states_list)}

        # Distinguishable table: table[i][j] for i < j
        # True = distinguishable, False = equivalent
        marked: List[List[bool]] = [[False] * n for _ in range(n)]

        # Base case: Partition F and Q \ F
        for i in range(n):
            p = states_list[i]
            for j in range(i + 1, n):
                q = states_list[j]
                if (p in dfa_total.accepting_states) != (q in dfa_total.accepting_states):
                    marked[i][j] = True

        # Iterative step: Propagate distinguishability
        changed = True
        while changed:
            changed = False
            for i in range(n):
                p = states_list[i]
                for j in range(i + 1, n):
                    if marked[i][j]:
                        continue
                    q = states_list[j]
                    for sym in dfa_total.alphabet:
                        p_next = dfa_total.transitions[p][sym]
                        q_next = dfa_total.transitions[q][sym]
                        if p_next != q_next:
                            u, v = state_idx[p_next], state_idx[q_next]
                            if u > v:
                                u, v = v, u
                            if marked[u][v]:
                                marked[i][j] = True
                                changed = True
                                break

        # Find equivalence classes via Union-Find or connected components
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for i in range(n):
            for j in range(i + 1, n):
                if not marked[i][j]:
                    union(i, j)

        # Group states by root
        groups: Dict[int, List[str]] = {}
        for i in range(n):
            r = find(i)
            groups.setdefault(r, []).append(states_list[i])

        # Assign clean, deterministic representative names to classes
        # e.g., if group contains start_state, prioritize naming or join states
        class_name_map: Dict[int, str] = {}
        for r, members in groups.items():
            sorted_m = sorted(members)
            # Create composite label if multiple states merged, e.g. "q0_q1"
            class_name = "_".join(sorted_m)
            class_name_map[r] = class_name

        # State mapping from old state to new representative state name
        state_to_new: Dict[str, str] = {}
        for r, members in groups.items():
            cname = class_name_map[r]
            for m in members:
                state_to_new[m] = cname

        new_states = set(class_name_map.values())
        new_start = state_to_new[dfa_total.start_state]

        new_accepting: Set[str] = set()
        for r, members in groups.items():
            if any(m in dfa_total.accepting_states for m in members):
                new_accepting.add(class_name_map[r])

        new_transitions: Dict[str, Dict[str, str]] = {s: {} for s in new_states}
        for r, members in groups.items():
            rep = members[0]
            new_s = class_name_map[r]
            for sym in sorted(dfa_total.alphabet):
                target_old = dfa_total.transitions[rep][sym]
                new_transitions[new_s][sym] = state_to_new[target_old]

        return DFA(
            states=new_states,
            alphabet=dfa_total.alphabet,
            transitions=new_transitions,
            start_state=new_start,
            accepting_states=new_accepting,
            validate=True,
        )

    def is_equivalent_to(self, other: DFA) -> Tuple[bool, Optional[str], str]:
        """Checks formal language equivalence L(M1) == L(M2) with another DFA.

        Uses the product automaton BFS method testing the symmetric difference:
            L(M1) ⊕ L(M2) = (L(M1) ∩ L(M2)') ∪ (L(M1)' ∩ L(M2))
        If an accepting state of the symmetric difference is reachable, the DFAs
        are NOT equivalent, and the BFS path directly yields the shortest counterexample string.

        Args:
            other (DFA): The other automaton to compare with.

        Returns:
            Tuple[bool, Optional[str], str]:
                - bool: True if L(M1) == L(M2), False otherwise.
                - Optional[str]: Shortest counterexample string distinguishing the two DFAs.
                - str: Detailed mathematical explanation.
        """
        # Alphabet unification
        unified_alphabet = sorted(self.alphabet | other.alphabet)

        # Complete both DFAs over the unified alphabet
        def expand_and_complete(d: DFA, alphabet: List[str]) -> DFA:
            base_transitions = {q: dict(d.transitions.get(q, {})) for q in d.states}
            sink = "dead_sink"
            while sink in d.states:
                sink = f"{sink}_eq"

            needs_sink = False
            for q in d.states:
                for sym in alphabet:
                    if sym not in base_transitions[q]:
                        needs_sink = True
                        break

            all_states = set(d.states)
            if needs_sink:
                all_states.add(sink)
                base_transitions[sink] = {sym: sink for sym in alphabet}

            for q in d.states:
                for sym in alphabet:
                    if sym not in base_transitions[q]:
                        base_transitions[q][sym] = sink

            return DFA(
                states=all_states,
                alphabet=alphabet,
                transitions=base_transitions,
                start_state=d.start_state,
                accepting_states=d.accepting_states,
                validate=True,
            )

        m1 = expand_and_complete(self, unified_alphabet)
        m2 = expand_and_complete(other, unified_alphabet)

        # BFS on product automaton: pair state (q1, q2)
        start_pair = (m1.start_state, m2.start_state)

        # Check if empty string distinguishes them
        m1_acc = m1.start_state in m1.accepting_states
        m2_acc = m2.start_state in m2.accepting_states
        if m1_acc != m2_acc:
            accepted_by = "first DFA" if m1_acc else "second DFA"
            rejected_by = "second DFA" if m1_acc else "first DFA"
            return (
                False,
                "",
                f"DFAs are NOT equivalent: the empty string (ε) is accepted by {accepted_by} "
                f"but rejected by {rejected_by}.",
            )

        visited: Set[Tuple[str, str]] = {start_pair}
        queue: deque[Tuple[Tuple[str, str], str]] = deque([(start_pair, "")])

        while queue:
            (q1, q2), path = queue.popleft()

            for sym in unified_alphabet:
                next_q1 = m1.transitions[q1][sym]
                next_q2 = m2.transitions[q2][sym]
                next_pair = (next_q1, next_q2)
                candidate_str = path + sym

                acc1 = next_q1 in m1.accepting_states
                acc2 = next_q2 in m2.accepting_states

                # Symmetric difference check
                if acc1 != acc2:
                    acc_dfa = "first DFA" if acc1 else "second DFA"
                    rej_dfa = "second DFA" if acc1 else "first DFA"
                    return (
                        False,
                        candidate_str,
                        f"DFAs are NOT equivalent. Counterexample string '{candidate_str}' "
                        f"is accepted by {acc_dfa} (reaches '{next_q1 if acc1 else next_q2}') "
                        f"and rejected by {rej_dfa} (reaches '{next_q2 if acc1 else next_q1}').",
                    )

                if next_pair not in visited:
                    visited.add(next_pair)
                    queue.append((next_pair, candidate_str))

        return (
            True,
            None,
            f"DFAs are EQUIVALENT: Both recognize the identical regular language L(M1) = L(M2) "
            f"over alphabet {{{', '.join(unified_alphabet)}}}.",
        )

    # -------------------------------------------------------------------------
    # Utility & Serialization
    # -------------------------------------------------------------------------
    def clone(self) -> DFA:
        """Creates a deep copy of this DFA."""
        return DFA(
            states=set(self.states),
            alphabet=set(self.alphabet),
            transitions={q: dict(t) for q, t in self.transitions.items()},
            start_state=self.start_state,
            accepting_states=set(self.accepting_states),
            validate=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the DFA to a standard JSON-compatible dictionary."""
        sorted_trans: Dict[str, Dict[str, str]] = {}
        for q in sorted(self.states):
            state_map = self.transitions.get(q, {})
            sorted_trans[q] = {sym: state_map[sym] for sym in sorted(state_map.keys())}

        return {
            "states": sorted(self.states),
            "alphabet": sorted(self.alphabet),
            "start_state": self.start_state,
            "accepting_states": sorted(self.accepting_states),
            "transitions": sorted_trans,
            "is_total": self.is_total(),
        }

    def to_transition_list(self) -> List[Dict[str, str]]:
        """Returns the transition function as a flat list of edge objects for frontend graph renderers."""
        edge_list: List[Dict[str, str]] = []
        for q in sorted(self.states):
            for sym in sorted(self.transitions.get(q, {}).keys()):
                target = self.transitions[q][sym]
                edge_list.append({"from": q, "symbol": sym, "to": target})
        return edge_list

    def to_json(self, indent: int = 2) -> str:
        """Converts DFA to a pretty-formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], validate: bool = True) -> DFA:
        """Creates a DFA instance from a dictionary."""
        states = data.get("states", [])
        alphabet = data.get("alphabet", [])
        start_state = data.get("start_state", "")
        accepting_states = data.get("accepting_states", [])
        transitions = data.get("transitions", {})

        return cls(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            start_state=start_state,
            accepting_states=accepting_states,
            validate=validate,
        )

    @classmethod
    def from_json(cls, json_str: str, validate: bool = True) -> DFA:
        """Parses a DFA instance from a JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as err:
            raise DFAValidationError(f"Invalid JSON format: {err}") from err
        return cls.from_dict(data, validate=validate)

    def __repr__(self) -> str:
        return (
            f"DFA(Q={sorted(self.states)}, Σ={sorted(self.alphabet)}, "
            f"q0='{self.start_state}', F={sorted(self.accepting_states)})"
        )
