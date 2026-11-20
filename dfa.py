"""
DFA (Deterministic Finite Automaton) Engine
============================================
Mathematical Formalism:
    M = (Q, Σ, δ, q0, F)
    - Q: Non-empty finite set of states
    - Σ: Non-empty finite set of input symbols (alphabet)
    - δ: Transition function Q × Σ → Q
    - q0: Start state (q0 ∈ Q)
    - F: Set of accepting / final states (F ⊆ Q)

This module implements the core formal DFA representations, validation,
and step-by-step simulation with trace records for college demonstration.

Author: CSET302 Automata Theory & Computability Project Team
"""

from __future__ import annotations

import json
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
    """Contains the result and trace of simulating a string on a DFA."""

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

        # 5. Transitions must use states in Q and symbols in Σ
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

    def simulate(self, input_string: str) -> SimulationResult:
        """Simulates an input string step-by-step through the formal DFA.

        Treatment of Edge Conditions:
        - Incomplete DFAs: Does NOT silently assume a trap state. If δ(current, symbol)
          is missing, simulation immediately halts with status 'REJECTED_MISSING_TRANSITION'.
        - Alphabet Validation: Every symbol in input_string must belong to Σ. An unrecognized
          symbol halts processing immediately with status 'REJECTED_INVALID_SYMBOL'.
        - Empty String (ε): Input string "" is tested by checking if start_state q₀ ∈ F.
          It returns ACCEPTED if q₀ ∈ F, and REJECTED_NON_FINAL otherwise.

        Args:
            input_string (str): The sequence of symbols to test (empty string represents ε).

        Returns:
            SimulationResult: Detailed execution result containing acceptance boolean,
                              complete trace triples (state, symbol, next_state), path,
                              final state, verdict status, and human-readable explanation.

        Raises:
            DFAValidationError: If the DFA definition is formally invalid before simulation.
        """
        self.validate()

        current_state = self.start_state
        path: List[str] = [current_state]
        trace: List[Dict[str, Any]] = []

        # Empty string case: check if start state is in F
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
            # Check symbol validity
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

            # Check if transition is defined
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
                        f"Automaton halted at position {idx} because no transition is defined."
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

        # Halt condition check
        is_accepted = current_state in self.accepting_states
        if is_accepted:
            status = "ACCEPTED"
            explanation = (
                f"Accepted: Input string consumed completely. "
                f"Automaton halted in accepting state '{current_state}' (final state ∈ F)."
            )
        else:
            status = "REJECTED_NON_FINAL"
            explanation = (
                f"Rejected: Input string consumed completely, but the automaton "
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
        }

    def to_transition_list(self) -> List[Dict[str, str]]:
        """Returns transitions as a flat list of edge objects for graph renderers."""
        edge_list: List[Dict[str, str]] = []
        for q in sorted(self.states):
            for sym in sorted(self.transitions.get(q, {}).keys()):
                target = self.transitions[q][sym]
                edge_list.append({"from": q, "symbol": sym, "to": target})
        return edge_list

    def to_json(self, indent: int = 2) -> str:
        """Converts DFA to a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], validate: bool = True) -> DFA:
        """Creates a DFA instance from a dictionary."""
        return cls(
            states=data.get("states", []),
            alphabet=data.get("alphabet", []),
            transitions=data.get("transitions", {}),
            start_state=data.get("start_state", ""),
            accepting_states=data.get("accepting_states", []),
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


def simulate_dfa(
    transitions: Dict[Tuple[str, str], str] | Dict[str, Dict[str, str]],
    start_state: str,
    final_states: Set[str] | List[str],
    input_string: str,
    alphabet: Optional[Set[str] | List[str]] = None,
) -> Tuple[bool, List[str]]:
    """Run a deterministic finite automaton on an input string.

    Treatment of Incomplete DFAs, Alphabet Validation and Epsilon (ε) Input:
    - Incomplete DFAs: If a transition (current_state, symbol) is missing from
      transitions, this function raises ValueError. It does not silently assume
      a trap/sink state unless one is explicitly included in the transition map.
    - Alphabet Validation: If an alphabet is provided, any symbol in input_string
      not present in the alphabet raises a ValueError.
    - Empty String (ε): An empty input string ("") skips the transition loop and
      evaluates whether start_state ∈ final_states directly.

    Args:
        transitions: dict mapping (state, symbol) -> next_state, or
                     nested dict state -> {symbol: next_state}.
        start_state: initial state identifier.
        final_states: set or list of accepting state identifiers.
        input_string: sequence of input symbols (empty string represents ε).
        alphabet: optional set or list of allowed alphabet symbols.

    Returns:
        (accepted, trace): tuple of boolean acceptance flag and list of visited state names.

    Raises:
        ValueError: if a required transition is missing or an invalid symbol is encountered.
    """
    final_set: Set[str] = {str(s).strip() for s in final_states}
    alpha_set: Optional[Set[str]] = {str(a) for a in alphabet} if alphabet is not None else None

    # Normalize transitions to (state, symbol) -> next_state
    trans_map: Dict[Tuple[str, str], str] = {}
    if isinstance(transitions, dict):
        for k, v in transitions.items():
            if isinstance(k, tuple) and len(k) == 2:
                trans_map[(str(k[0]).strip(), str(k[1]))] = str(v).strip()
            elif isinstance(v, dict):
                for sym, next_s in v.items():
                    trans_map[(str(k).strip(), str(sym))] = str(next_s).strip()

    current: str = str(start_state).strip()
    trace: List[str] = [current]

    for symbol in str(input_string):
        if alpha_set is not None and symbol not in alpha_set:
            raise ValueError(f"Invalid symbol '{symbol}': not in alphabet {sorted(alpha_set)}")
        key = (current, symbol)
        if key not in trans_map:
            raise ValueError(f"Missing transition: {current}, {symbol}")
        current = trans_map[key]
        trace.append(current)

    return (current in final_set), trace
