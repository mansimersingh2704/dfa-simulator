/**
 * DFA Simulator — Client Application Logic (CSET302)
 * ===================================================
 * Core Features:
 * - 3 Simple Demonstration Presets
 * - Interactive Canvas Graph Editor (drag states, self-loops, curved edges)
 * - Formal 5-tuple input and transition table editing
 * - Step-by-step simulation with tape display and trace table
 * - Transparent offline JS fallback
 */

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // 1. 3 Simple Demonstration Presets
  // ---------------------------------------------------------------------------
  const PRESETS = {
    ends_with_01: {
      id: 'ends_with_01',
      name: "Strings ending with '01'",
      description: "Accepts any binary string over {0, 1} that ends with '01'.",
      alphabet: ['0', '1'],
      states: ['q0', 'q1', 'q2'],
      start_state: 'q0',
      accepting_states: ['q2'],
      transitions: {
        q0: { '0': 'q1', '1': 'q0' },
        q1: { '0': 'q1', '1': 'q2' },
        q2: { '0': 'q1', '1': 'q0' }
      },
      sample_inputs: ['01', '101', '1001', '00', '10', '111', '']
    },
    contains_101: {
      id: 'contains_101',
      name: "Strings containing '101'",
      description: "Accepts any binary string over {0, 1} containing '101' as a substring.",
      alphabet: ['0', '1'],
      states: ['s0', 's1', 's2', 's3'],
      start_state: 's0',
      accepting_states: ['s3'],
      transitions: {
        s0: { '0': 's0', '1': 's1' },
        s1: { '0': 's2', '1': 's1' },
        s2: { '0': 's0', '1': 's3' },
        s3: { '0': 's3', '1': 's3' }
      },
      sample_inputs: ['101', '01010', '1101', '1001', '111', '000', '']
    },
    even_zeros: {
      id: 'even_zeros',
      name: 'Even number of 0s',
      description: "Accepts any binary string over {0, 1} with an even count of '0's (including zero '0's).",
      alphabet: ['0', '1'],
      states: ['q_even', 'q_odd'],
      start_state: 'q_even',
      accepting_states: ['q_even'],
      transitions: {
        q_even: { '0': 'q_odd', '1': 'q_even' },
        q_odd: { '0': 'q_even', '1': 'q_odd' }
      },
      sample_inputs: ['', '00', '11', '010', '1', '0', '0110']
    },
    ends_with_1: {
      id: 'ends_with_1',
      name: "Strings ending with '1'",
      description: "Accepts any binary string over {0, 1} whose last symbol is '1'. Minimal 2-state DFA.",
      alphabet: ['0', '1'],
      states: ['q0', 'q1'],
      start_state: 'q0',
      accepting_states: ['q1'],
      transitions: {
        q0: { '0': 'q0', '1': 'q1' },
        q1: { '0': 'q0', '1': 'q1' }
      },
      sample_inputs: ['1', '101', '111', '0', '10', '100', '']
    },
    divisible_by_3: {
      id: 'divisible_by_3',
      name: 'Binary number divisible by 3',
      description: 'Accepts binary strings representing non-negative integers divisible by 3 (e.g. 0, 11, 110).',
      alphabet: ['0', '1'],
      states: ['r0', 'r1', 'r2'],
      start_state: 'r0',
      accepting_states: ['r0'],
      transitions: {
        r0: { '0': 'r0', '1': 'r1' },
        r1: { '0': 'r2', '1': 'r0' },
        r2: { '0': 'r1', '1': 'r2' }
      },
      sample_inputs: ['0', '11', '110', '1001', '1', '10', '100']
    },
    starts_and_ends_1: {
      id: 'starts_and_ends_1',
      name: "Starts and ends with '1'",
      description: "Accepts binary strings that both start and end with '1' (minimum length 1).",
      alphabet: ['0', '1'],
      states: ['q0', 'q1', 'q2', 'qdead'],
      start_state: 'q0',
      accepting_states: ['q2'],
      transitions: {
        q0:    { '0': 'qdead', '1': 'q2' },
        q2:    { '0': 'q1',    '1': 'q2' },
        q1:    { '0': 'q1',    '1': 'q2' },
        qdead: { '0': 'qdead', '1': 'qdead' }
      },
      sample_inputs: ['1', '11', '101', '1001', '0', '10', '01']
    }
  };

  // ---------------------------------------------------------------------------
  // 2. Application State Model
  // ---------------------------------------------------------------------------
  const appState = {
    // Current DFA 5-Tuple: M = (Q, Σ, δ, q0, F)
    dfa: {
      states: ['q0', 'q1', 'q2'],
      alphabet: ['0', '1'],
      start_state: 'q0',
      accepting_states: ['q2'],
      transitions: {
        q0: { '0': 'q1', '1': 'q0' },
        q1: { '0': 'q1', '1': 'q2' },
        q2: { '0': 'q1', '1': 'q0' }
      }
    },

    // Canvas Layout Model
    graph: {
      nodes: {}, // stateName -> { x, y, radius }
      selectedNode: null,
      draggedNode: null,
      isDragging: false,
      dragOffset: { x: 0, y: 0 },
      activeState: null,
      activeEdge: null // { from, to, symbol }
    },

    // Step Simulation State
    simulation: {
      inputString: '01',
      fullResult: null,
      currentStep: 0,
      isPlaying: false,
      playTimer: null,
      speedMs: 650
    },

    isBackendConnected: true
  };

  // ---------------------------------------------------------------------------
  // 3. Pure-JavaScript Fallback Engine (Offline Mirror)
  // ---------------------------------------------------------------------------
  class JSAutomataEngine {
    static validate(dfa) {
      if (!dfa.states || dfa.states.length === 0) {
        throw new Error('State set Q must be non-empty.');
      }
      if (!dfa.alphabet || dfa.alphabet.length === 0) {
        throw new Error('Alphabet Σ must be non-empty.');
      }
      if (!dfa.start_state) {
        throw new Error('Start state q₀ must be specified.');
      }
      if (!dfa.states.includes(dfa.start_state)) {
        throw new Error(`Start state '${dfa.start_state}' is not in state set Q.`);
      }
      const invalidFinal = dfa.accepting_states.filter(s => !dfa.states.includes(s));
      if (invalidFinal.length > 0) {
        throw new Error(`Accepting states must be a subset of Q. Invalid: ${invalidFinal.join(', ')}`);
      }
      for (const [q, trans] of Object.entries(dfa.transitions || {})) {
        if (!dfa.states.includes(q)) {
          throw new Error(`Transition source state '${q}' not in Q.`);
        }
        for (const [sym, target] of Object.entries(trans)) {
          if (!dfa.alphabet.includes(sym)) {
            throw new Error(`Transition symbol '${sym}' from state '${q}' not in alphabet Σ.`);
          }
          if (!dfa.states.includes(target)) {
            throw new Error(`Transition target '${target}' from '${q}' on '${sym}' not in Q.`);
          }
        }
      }
      return true;
    }

    static simulate(dfa, inputStr) {
      this.validate(dfa);
      let currentState = dfa.start_state;
      const path = [currentState];
      const trace = [];

      // Empty string case
      if (inputStr === '') {
        const accepted = dfa.accepting_states.includes(currentState);
        return {
          accepted,
          input_string: '',
          start_state: dfa.start_state,
          final_state: currentState,
          path,
          trace,
          status: accepted ? 'ACCEPTED' : 'REJECTED_NON_FINAL',
          explanation: accepted
            ? `Accepted: Empty string (ε) processed. Automaton remains in start state '${currentState}' ∈ F.`
            : `Rejected: Empty string (ε) processed. Automaton remains in start state '${currentState}' ∉ F.`,
          consumed_count: 0,
          total_count: 0
        };
      }

      // Symbol by symbol
      for (let i = 0; i < inputStr.length; i++) {
        const symbol = inputStr[i];
        if (!dfa.alphabet.includes(symbol)) {
          return {
            accepted: false,
            input_string: inputStr,
            start_state: dfa.start_state,
            final_state: null,
            path,
            trace,
            status: 'REJECTED_INVALID_SYMBOL',
            explanation: `Rejected: Symbol '${symbol}' at position ${i} is not part of alphabet Σ = {${dfa.alphabet.join(', ')}}.`,
            consumed_count: i,
            total_count: inputStr.length
          };
        }

        const trans = (dfa.transitions && dfa.transitions[currentState]) || {};
        if (!(symbol in trans)) {
          return {
            accepted: false,
            input_string: inputStr,
            start_state: dfa.start_state,
            final_state: currentState,
            path,
            trace,
            status: 'REJECTED_MISSING_TRANSITION',
            explanation: `Rejected: Missing transition δ('${currentState}', '${symbol}'). Automaton halted at step ${i + 1}.`,
            consumed_count: i,
            total_count: inputStr.length
          };
        }

        const nextState = trans[symbol];
        trace.push({
          step: i + 1,
          from_state: currentState,
          symbol,
          to_state: nextState,
          triple: [currentState, symbol, nextState]
        });
        currentState = nextState;
        path.push(currentState);
      }

      const accepted = dfa.accepting_states.includes(currentState);
      return {
        accepted,
        input_string: inputStr,
        start_state: dfa.start_state,
        final_state: currentState,
        path,
        trace,
        status: accepted ? 'ACCEPTED' : 'REJECTED_NON_FINAL',
        explanation: accepted
          ? `Accepted: Input string consumed completely. Automaton halted in accepting state '${currentState}' ∈ F.`
          : `Rejected: Input string consumed completely. Automaton halted in non-accepting state '${currentState}' ∉ F.`,
        consumed_count: inputStr.length,
        total_count: inputStr.length
      };
    }
  }

  // ---------------------------------------------------------------------------
  // 4. API Client Wrapper (Transparent Online / Offline Switching)
  // ---------------------------------------------------------------------------
  async function apiPost(endpoint, payload) {
    if (appState.isBackendConnected) {
      try {
        const resp = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (resp.ok) {
          const data = await resp.json();
          updateEngineStatus(true);
          return data;
        } else {
          const errData = await resp.json().catch(() => ({}));
          updateEngineStatus(true);
          return errData;
        }
      } catch (networkErr) {
        console.warn('Backend offline, using local JS engine:', networkErr);
        updateEngineStatus(false);
      }
    }

    // Fallback execution
    try {
      if (endpoint === '/api/validate') {
        JSAutomataEngine.validate(payload);
        return { success: true, dfa: payload };
      } else if (endpoint === '/api/simulate') {
        const res = JSAutomataEngine.simulate(payload.dfa, payload.input_string);
        return { success: true, result: res };
      }
      return { success: false, error: 'Endpoint not supported offline' };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }

  function updateEngineStatus(isOnline) {
    appState.isBackendConnected = isOnline;
    const pill = document.getElementById('engine-status');
    const text = document.getElementById('engine-status-text');
    if (!pill || !text) return;
    if (isOnline) {
      pill.className = 'status-pill online';
      text.textContent = 'Backend Connected';
    } else {
      pill.className = 'status-pill offline';
      text.textContent = 'JS Fallback (Offline)';
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Canvas Visual Graph Visualizer
  // ---------------------------------------------------------------------------
  let canvas = null;
  let ctx = null;
  const STATE_RADIUS = 28;

  function initCanvasRefs() {
    if (typeof document !== 'undefined') {
      canvas = document.getElementById('dfa-canvas');
      if (canvas) {
        ctx = canvas.getContext('2d');
      }
    }
  }
  initCanvasRefs();

  function resizeCanvas() {
    if (!canvas || !ctx) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = 380 * dpr;
    ctx.resetTransform();
    ctx.scale(dpr, dpr);
    renderGraph();
  }

  function autoLayoutNodes() {
    if (!canvas) return;
    const states = appState.dfa.states;
    const n = states.length;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width || 800;
    const height = 380;

    const centerX = width / 2;
    const centerY = height / 2;
    const radiusX = Math.min(width * 0.38, 260);
    const radiusY = Math.min(height * 0.35, 120);

    states.forEach((state, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI;
      const x = Math.round(centerX + radiusX * Math.cos(angle));
      const y = Math.round(centerY + radiusY * Math.sin(angle));
      appState.graph.nodes[state] = { x, y, radius: STATE_RADIUS };
    });
    renderGraph();
  }

  function renderGraph() {
    if (!canvas || !ctx) return;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = 380;

    ctx.clearRect(0, 0, width, height);

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // Group transitions to merge labels and detect two-way edges
    const edgeMap = new Map();
    for (const [from, transMap] of Object.entries(appState.dfa.transitions || {})) {
      for (const [sym, to] of Object.entries(transMap)) {
        const key = `${from}->${to}`;
        if (!edgeMap.has(key)) {
          edgeMap.set(key, { from, to, symbols: [] });
        }
        edgeMap.get(key).symbols.push(sym);
      }
    }

    // Draw Edges
    edgeMap.forEach(edge => {
      drawTransitionEdge(edge, edgeMap, isDark);
    });

    // Draw States
    appState.dfa.states.forEach(state => {
      drawStateNode(state, isDark);
    });
  }

  function drawTransitionEdge(edge, allEdges, isDark) {
    const fromNode = appState.graph.nodes[edge.from];
    const toNode = appState.graph.nodes[edge.to];
    if (!fromNode || !toNode) return;

    const label = edge.symbols.sort().join(', ');
    const isSelfLoop = (edge.from === edge.to);
    const hasReverse = allEdges.has(`${edge.to}->${edge.from}`);

    // Active transition glow
    const isActive = appState.graph.activeEdge &&
      appState.graph.activeEdge.from === edge.from &&
      appState.graph.activeEdge.to === edge.to &&
      edge.symbols.includes(appState.graph.activeEdge.symbol);

    ctx.save();
    ctx.strokeStyle = isActive ? '#f59e0b' : (isDark ? '#94a3b8' : '#475569');
    ctx.fillStyle = isActive ? '#f59e0b' : (isDark ? '#fbbf24' : '#1e1b4b');
    ctx.lineWidth = isActive ? 3 : 2;

    if (isActive) {
      ctx.shadowColor = '#f59e0b';
      ctx.shadowBlur = 10;
    }

    if (isSelfLoop) {
      // Self loop on top of node
      const loopRadius = 22;
      const loopCenterX = fromNode.x;
      const loopCenterY = fromNode.y - fromNode.radius - loopRadius + 6;

      ctx.beginPath();
      ctx.arc(loopCenterX, loopCenterY, loopRadius, 0.25 * Math.PI, 0.75 * Math.PI, true);
      ctx.stroke();

      const arrowX = fromNode.x + fromNode.radius * Math.sin(0.3);
      const arrowY = fromNode.y - fromNode.radius * Math.cos(0.3);
      drawArrowhead(arrowX - 2, arrowY - 10, arrowX, arrowY, 10);

      ctx.font = '600 12px "Fira Code", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(label, loopCenterX, loopCenterY - loopRadius - 3);
    } else {
      const dx = toNode.x - fromNode.x;
      const dy = toNode.y - fromNode.y;
      const dist = Math.hypot(dx, dy);
      if (dist === 0) { ctx.restore(); return; }

      const ux = dx / dist;
      const uy = dy / dist;

      if (hasReverse) {
        // Curve two-way transitions
        const curvature = 26;
        const midX = (fromNode.x + toNode.x) / 2 - uy * curvature;
        const midY = (fromNode.y + toNode.y) / 2 + ux * curvature;

        const startX = fromNode.x + ux * fromNode.radius;
        const startY = fromNode.y + uy * fromNode.radius;
        const endX = toNode.x - ux * toNode.radius;
        const endY = toNode.y - uy * toNode.radius;

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.quadraticCurveTo(midX, midY, endX, endY);
        ctx.stroke();

        drawArrowhead(midX, midY, endX, endY, 10);

        const labelX = 0.25 * startX + 0.5 * midX + 0.25 * endX - uy * 10;
        const labelY = 0.25 * startY + 0.5 * midY + 0.25 * endY + ux * 10;

        ctx.font = '600 12px "Fira Code", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        drawLabelWithBackground(label, labelX, labelY, isDark);
      } else {
        // Straight line
        const startX = fromNode.x + ux * fromNode.radius;
        const startY = fromNode.y + uy * fromNode.radius;
        const endX = toNode.x - ux * toNode.radius;
        const endY = toNode.y - uy * toNode.radius;

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.stroke();

        drawArrowhead(startX, startY, endX, endY, 10);

        const labelX = (startX + endX) / 2 - uy * 12;
        const labelY = (startY + endY) / 2 + ux * 12;
        ctx.font = '600 12px "Fira Code", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        drawLabelWithBackground(label, labelX, labelY, isDark);
      }
    }
    ctx.restore();
  }

  function drawLabelWithBackground(text, x, y, isDark) {
    const pad = 3;
    const metrics = ctx.measureText(text);
    const w = metrics.width + pad * 2;
    const h = 14 + pad * 2;

    ctx.save();
    ctx.fillStyle = isDark ? '#15172e' : '#ffffff';
    ctx.fillRect(x - w / 2, y - h / 2, w, h);
    ctx.fillStyle = isDark ? '#fbbf24' : '#1e1b4b';
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  function drawArrowhead(fromX, fromY, toX, toY, size) {
    const angle = Math.atan2(toY - fromY, toX - fromX);
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - size * Math.cos(angle - Math.PI / 6), toY - size * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(toX - size * Math.cos(angle + Math.PI / 6), toY - size * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();
  }

  function drawStateNode(state, isDark) {
    const node = appState.graph.nodes[state];
    if (!node) return;

    const isStart = (state === appState.dfa.start_state);
    const isAccepting = appState.dfa.accepting_states.includes(state);
    const isSelected = (state === appState.graph.selectedNode);
    const isActive = (state === appState.graph.activeState);

    ctx.save();

    // Active state glow
    if (isActive) {
      ctx.shadowColor = '#f59e0b';
      ctx.shadowBlur = 18;
    }

    // Outer Circle Fill
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
    if (isActive) {
      ctx.fillStyle = isDark ? '#3d2c10' : '#fef3c7';
    } else if (isSelected) {
      ctx.fillStyle = isDark ? '#26294d' : '#f1f5f9';
    } else {
      ctx.fillStyle = isDark ? '#1a1b35' : '#ffffff';
    }
    ctx.fill();

    // Stroke
    ctx.lineWidth = isSelected ? 3 : 2;
    if (isActive) {
      ctx.strokeStyle = '#f59e0b';
    } else if (isSelected) {
      ctx.strokeStyle = '#6366f1';
    } else {
      ctx.strokeStyle = isDark ? '#fbbf24' : '#1a1b35';
    }
    ctx.stroke();

    // Accepting State: Concentric Inner Circle
    if (isAccepting) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius - 5, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // Start State Arrow (→)
    if (isStart) {
      const arrowLen = 30;
      const startX = node.x - node.radius - arrowLen;
      const startY = node.y;
      const endX = node.x - node.radius;
      const endY = node.y;

      ctx.save();
      ctx.strokeStyle = '#d97706';
      ctx.fillStyle = '#d97706';
      ctx.lineWidth = 3;

      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();
      drawArrowhead(startX, startY, endX, endY, 10);

      ctx.font = '700 11px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText('Start', startX - 4, startY + 4);
      ctx.restore();
    }

    // State Label
    ctx.font = '600 13px "Fira Code", monospace';
    ctx.fillStyle = isActive ? '#d97706' : (isDark ? '#f8fafc' : '#0f172a');
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(state, node.x, node.y);

    ctx.restore();
  }

  function getNodeAtCoords(x, y) {
    for (const [state, node] of Object.entries(appState.graph.nodes)) {
      if (Math.hypot(node.x - x, node.y - y) <= node.radius + 4) {
        return state;
      }
    }
    return null;
  }

  function initCanvasMouseListeners() {
    if (!canvas) return;

    canvas.addEventListener('mousedown', e => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const hitState = getNodeAtCoords(x, y);
      if (hitState) {
        appState.graph.selectedNode = hitState;
        appState.graph.draggedNode = hitState;
        appState.graph.isDragging = true;
        const node = appState.graph.nodes[hitState];
        appState.graph.dragOffset = { x: x - node.x, y: y - node.y };
        showSelectionPanel(hitState);
      } else {
        appState.graph.selectedNode = null;
        hideSelectionPanel();
      }
      renderGraph();
    });

    if (typeof window !== 'undefined') {
      window.addEventListener('mousemove', e => {
        if (!appState.graph.isDragging || !appState.graph.draggedNode) return;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const node = appState.graph.nodes[appState.graph.draggedNode];
        if (node) {
          node.x = Math.max(STATE_RADIUS + 10, Math.min(rect.width - STATE_RADIUS - 10, x - appState.graph.dragOffset.x));
          node.y = Math.max(STATE_RADIUS + 10, Math.min(380 - STATE_RADIUS - 10, y - appState.graph.dragOffset.y));
          renderGraph();
        }
      });

      window.addEventListener('mouseup', () => {
        appState.graph.isDragging = false;
        appState.graph.draggedNode = null;
      });
    }
  }

  function showSelectionPanel(state) {
    const panel = document.getElementById('selection-panel');
    const label = document.getElementById('selected-state-label');
    if (!panel || !label) return;
    panel.classList.remove('hidden');
    label.innerHTML = `Selected: <strong>${state}</strong>`;
  }

  function hideSelectionPanel() {
    const panel = document.getElementById('selection-panel');
    if (panel) panel.classList.add('hidden');
  }

  // ---------------------------------------------------------------------------
  // 6. UI Synchronization & Form Management
  // ---------------------------------------------------------------------------
  function syncDfaToUI() {
    document.getElementById('input-states').value = appState.dfa.states.join(', ');
    document.getElementById('input-alphabet').value = appState.dfa.alphabet.join(', ');
    document.getElementById('input-start-state').value = appState.dfa.start_state;
    document.getElementById('input-accepting-states').value = appState.dfa.accepting_states.join(', ');

    populateToolbarSelects();
    renderTransitionMatrix();
    ensureGraphNodes();
    renderGraph();
  }

  function ensureGraphNodes() {
    const states = appState.dfa.states;
    Object.keys(appState.graph.nodes).forEach(st => {
      if (!states.includes(st)) delete appState.graph.nodes[st];
    });

    const missingNodes = states.filter(s => !appState.graph.nodes[s]);
    if (missingNodes.length > 0) {
      autoLayoutNodes();
    }
  }

  function populateToolbarSelects() {
    const srcSel = document.getElementById('trans-source-select');
    const tgtSel = document.getElementById('trans-target-select');
    if (!srcSel || !tgtSel) return;

    srcSel.innerHTML = '';
    tgtSel.innerHTML = '';
    appState.dfa.states.forEach(s => {
      srcSel.add(new Option(s, s));
      tgtSel.add(new Option(s, s));
    });
  }

  function renderTransitionMatrix() {
    const table = document.getElementById('transition-matrix-table');
    if (!table) return;

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    const states = appState.dfa.states;
    const alphabet = appState.dfa.alphabet;

    // Header row
    let headHtml = '<tr><th>State <code>q</code></th>';
    alphabet.forEach(a => {
      headHtml += `<th>Input <code>${a}</code></th>`;
    });
    headHtml += '</tr>';
    thead.innerHTML = headHtml;

    // Body rows
    let bodyHtml = '';
    states.forEach(q => {
      const isStart = q === appState.dfa.start_state;
      const isAccept = appState.dfa.accepting_states.includes(q);
      const prefix = `${isStart ? '→ ' : ''}${isAccept ? '*' : ''}`;

      bodyHtml += `<tr><td><strong>${prefix}${q}</strong></td>`;
      alphabet.forEach(a => {
        const currentTarget = (appState.dfa.transitions[q] && appState.dfa.transitions[q][a]) || '';
        bodyHtml += `
          <td>
            <input type="text" class="matrix-input"
                   data-from="${q}" data-sym="${a}"
                   value="${currentTarget}" placeholder="target" />
          </td>
        `;
      });
      bodyHtml += '</tr>';
    });
    tbody.innerHTML = bodyHtml;

    tbody.querySelectorAll('.matrix-input').forEach(input => {
      input.addEventListener('change', e => {
        const from = e.target.getAttribute('data-from');
        const sym = e.target.getAttribute('data-sym');
        const target = e.target.value.trim();

        if (!appState.dfa.transitions[from]) appState.dfa.transitions[from] = {};
        if (target) {
          appState.dfa.transitions[from][sym] = target;
        } else {
          delete appState.dfa.transitions[from][sym];
        }
        renderGraph();
      });
    });
  }

  function readDfaFromInputs() {
    const states = document.getElementById('input-states').value.split(',').map(s => s.trim()).filter(Boolean);
    const alphabet = document.getElementById('input-alphabet').value.split(',').map(a => a.trim()).filter(Boolean);
    const start_state = document.getElementById('input-start-state').value.trim();
    const accepting_states = document.getElementById('input-accepting-states').value.split(',').map(f => f.trim()).filter(Boolean);

    appState.dfa.states = states;
    appState.dfa.alphabet = alphabet;
    appState.dfa.start_state = start_state;
    appState.dfa.accepting_states = accepting_states;

    const newTrans = {};
    states.forEach(s => {
      newTrans[s] = {};
      const old = appState.dfa.transitions[s] || {};
      alphabet.forEach(a => {
        if (old[a] && states.includes(old[a])) {
          newTrans[s][a] = old[a];
        }
      });
    });
    appState.dfa.transitions = newTrans;
    syncDfaToUI();
  }

  // ---------------------------------------------------------------------------
  // 7. Formal Definition Validation
  // ---------------------------------------------------------------------------
  async function validateCurrentDfa() {
    const alertBox = document.getElementById('validation-alert');
    const alertTitle = document.getElementById('validation-title');
    const alertMsg = document.getElementById('validation-message');

    const res = await apiPost('/api/validate', appState.dfa);
    alertBox.classList.remove('hidden', 'valid', 'invalid');

    if (res.success) {
      alertBox.classList.add('valid');
      alertTitle.textContent = 'DFA is Valid';
      alertMsg.textContent = 'Definition satisfies all formal mathematical requirements (Q, Σ, δ, q₀, F).';
    } else {
      alertBox.classList.add('invalid');
      alertTitle.textContent = 'Definition Error';
      alertMsg.textContent = res.error;
    }
  }

  // ---------------------------------------------------------------------------
  // 8. Step-by-Step Simulation Engine & AutoPlay
  // ---------------------------------------------------------------------------
  async function runFullSimulation() {
    stopAutoPlay();
    const inputStr = document.getElementById('sim-input-string').value;
    appState.simulation.inputString = inputStr;

    const res = await apiPost('/api/simulate', {
      dfa: appState.dfa,
      input_string: inputStr
    });

    if (res.success) {
      appState.simulation.fullResult = res.result;
      appState.simulation.currentStep = res.result.trace.length;
      updateSimulationUI();
    } else {
      showSimulationError(res.error);
    }
  }

  function resetSimulation() {
    stopAutoPlay();
    appState.simulation.currentStep = 0;
    appState.graph.activeState = appState.dfa.start_state;
    appState.graph.activeEdge = null;
    updateSimulationUI();
  }

  async function stepSimulationForward() {
    const inputStr = document.getElementById('sim-input-string').value;
    if (!appState.simulation.fullResult || appState.simulation.inputString !== inputStr) {
      appState.simulation.inputString = inputStr;
      const res = await apiPost('/api/simulate', {
        dfa: appState.dfa,
        input_string: inputStr
      });
      if (!res.success) {
        showSimulationError(res.error);
        stopAutoPlay();
        return;
      }
      appState.simulation.fullResult = res.result;
      appState.simulation.currentStep = 0;
    }

    const sim = appState.simulation;
    if (sim.currentStep < sim.fullResult.trace.length) {
      sim.currentStep++;
      updateSimulationUI();
    } else {
      stopAutoPlay();
    }
  }

  function stepSimulationBackward() {
    stopAutoPlay();
    if (appState.simulation.currentStep > 0) {
      appState.simulation.currentStep--;
      updateSimulationUI();
    }
  }

  function toggleAutoPlay() {
    if (appState.simulation.isPlaying) {
      stopAutoPlay();
    } else {
      startAutoPlay();
    }
  }

  async function startAutoPlay() {
    const btn = document.getElementById('btn-sim-autoplay');
    const inputStr = document.getElementById('sim-input-string').value;

    // Fetch simulation result if not already loaded or changed
    if (!appState.simulation.fullResult || appState.simulation.inputString !== inputStr) {
      appState.simulation.inputString = inputStr;
      const res = await apiPost('/api/simulate', {
        dfa: appState.dfa,
        input_string: inputStr
      });
      if (!res.success) {
        showSimulationError(res.error);
        return;
      }
      appState.simulation.fullResult = res.result;
      appState.simulation.currentStep = 0;
    }

    // If already at the end of the string, restart from step 0
    if (appState.simulation.currentStep >= appState.simulation.fullResult.trace.length) {
      appState.simulation.currentStep = 0;
      updateSimulationUI();
    }

    appState.simulation.isPlaying = true;
    if (btn) {
      btn.textContent = '⏸ Pause';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
    }

    const stepLoop = async () => {
      if (!appState.simulation.isPlaying) return;
      const sim = appState.simulation;
      if (sim.fullResult && sim.currentStep >= sim.fullResult.trace.length) {
        stopAutoPlay();
        return;
      }
      await stepSimulationForward();
      if (appState.simulation.isPlaying) {
        appState.simulation.playTimer = setTimeout(stepLoop, appState.simulation.speedMs);
      }
    };

    appState.simulation.playTimer = setTimeout(stepLoop, appState.simulation.speedMs);
  }

  function stopAutoPlay() {
    appState.simulation.isPlaying = false;
    clearTimeout(appState.simulation.playTimer);
    const btn = document.getElementById('btn-sim-autoplay');
    if (btn) {
      btn.textContent = '▶ Auto Play';
      btn.classList.remove('btn-secondary');
      btn.classList.add('btn-primary');
    }
  }

  function updateSimulationUI() {
    const sim = appState.simulation;
    const res = sim.fullResult;
    const step = sim.currentStep;

    const inputStr = document.getElementById('sim-input-string').value;
    renderTape(inputStr, step);

    if (!res) {
      appState.graph.activeState = appState.dfa.start_state;
      appState.graph.activeEdge = null;
      renderGraph();
      return;
    }

    let currentState = res.start_state;
    let activeEdge = null;

    if (step > 0 && res.trace[step - 1]) {
      const lastTrace = res.trace[step - 1];
      currentState = lastTrace.to_state;
      activeEdge = {
        from: lastTrace.from_state,
        to: lastTrace.to_state,
        symbol: lastTrace.symbol
      };
    }

    appState.graph.activeState = currentState;
    appState.graph.activeEdge = activeEdge;
    renderGraph();

    const banner = document.getElementById('verdict-banner');
    const badgeText = document.getElementById('verdict-badge-text');
    const currStateLabel = document.getElementById('verdict-current-state');
    const counter = document.getElementById('verdict-step-counter');

    currStateLabel.textContent = currentState || 'None';
    counter.textContent = `${step} / ${res.total_count}`;

    banner.className = 'verdict-banner';
    const isAtEnd = (step === res.trace.length);

    if (isAtEnd) {
      if (res.accepted) {
        banner.classList.add('accepted');
        badgeText.textContent = 'ACCEPTED';
      } else {
        banner.classList.add('rejected');
        badgeText.textContent = 'REJECTED';
      }
    } else {
      banner.classList.add('ready');
      badgeText.textContent = 'SIMULATING';
    }

    const whyText = document.getElementById('why-explanation-text');
    if (isAtEnd) {
      whyText.textContent = res.explanation;
    } else if (step === 0) {
      whyText.textContent = `At start state '${res.start_state}'. Ready to consume input string symbols.`;
    } else {
      const currTrace = res.trace[step - 1];
      whyText.textContent = `Step ${step}: Read symbol '${currTrace.symbol}' from state '${currTrace.from_state}', transitioned to state '${currTrace.to_state}'.`;
    }

    renderTraceTable(res.trace, step);
  }

  function renderTape(inputStr, currentStep) {
    const tapeContainer = document.getElementById('tape-cells');
    if (!tapeContainer) return;

    if (inputStr === '') {
      tapeContainer.innerHTML = '<div class="tape-cell epsilon active"><span class="cell-idx">ε</span>ε</div>';
      return;
    }

    let html = '';
    for (let i = 0; i < inputStr.length; i++) {
      const sym = inputStr[i];
      let cls = 'tape-cell';
      if (i < currentStep) {
        cls += ' consumed';
      } else if (i === currentStep) {
        cls += ' active';
      }
      html += `
        <div class="${cls}">
          <span class="cell-idx">${i}</span>
          ${sym}
        </div>
      `;
    }
    tapeContainer.innerHTML = html;
  }

  function renderTraceTable(trace, activeStep) {
    const tbody = document.getElementById('trace-table-body');
    if (!tbody) return;

    if (!trace || trace.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No state transitions executed.</td></tr>';
      return;
    }

    let html = '';
    trace.forEach((rec, i) => {
      const isCurrent = (i + 1 === activeStep);
      const rowStyle = isCurrent ? 'style="background-color: rgba(245, 158, 11, 0.15); font-weight: 600;"' : '';
      html += `
        <tr ${rowStyle}>
          <td>${rec.step}</td>
          <td>${rec.from_state}</td>
          <td><code>${rec.symbol}</code></td>
          <td>${rec.to_state}</td>
          <td><code>δ(${rec.from_state}, ${rec.symbol}) → ${rec.to_state}</code></td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  }

  function showSimulationError(msg) {
    const whyText = document.getElementById('why-explanation-text');
    const badgeText = document.getElementById('verdict-badge-text');
    const banner = document.getElementById('verdict-banner');

    banner.className = 'verdict-banner rejected';
    badgeText.textContent = 'ERROR';
    whyText.textContent = `Simulation Error: ${msg}`;
  }

  // ---------------------------------------------------------------------------
  // 9. Presets & Sample Inputs Loading
  // ---------------------------------------------------------------------------
  function loadPreset(presetKey) {
    stopAutoPlay();
    const preset = PRESETS[presetKey];
    if (!preset) return;

    appState.dfa = JSON.parse(JSON.stringify(preset));

    const banner = document.getElementById('preset-info-banner');
    const nameEl = document.getElementById('preset-name');
    const descEl = document.getElementById('preset-desc');
    const chipsEl = document.getElementById('preset-sample-chips');

    if (banner) banner.style.display = 'block';
    if (nameEl) nameEl.textContent = preset.name;
    if (descEl) descEl.textContent = preset.description;

    if (chipsEl) {
      chipsEl.innerHTML = '';
      (preset.sample_inputs || []).forEach(sample => {
        const chip = document.createElement('span');
        chip.className = 'sample-chip';
        chip.textContent = sample === '' ? 'ε' : sample;
        chip.title = `Click to test '${sample}'`;
        chip.addEventListener('click', () => {
          document.getElementById('sim-input-string').value = sample;
          runFullSimulation();
        });
        chipsEl.appendChild(chip);
      });
    }

    const firstSample = (preset.sample_inputs && preset.sample_inputs[0]) !== undefined ? preset.sample_inputs[0] : '';
    document.getElementById('sim-input-string').value = firstSample;

    syncDfaToUI();
    validateCurrentDfa();
    runFullSimulation();
  }

  // ---------------------------------------------------------------------------
  // 10. Event Listeners & Initialization
  // ---------------------------------------------------------------------------
  function setupEventListeners() {
    initCanvasMouseListeners();

    // Theme toggle
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const curr = document.documentElement.getAttribute('data-theme');
        const next = curr === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('dfa_theme', next);
        renderGraph();
      });
    }

    // Preset selector
    const btnLoadPreset = document.getElementById('btn-load-preset');
    if (btnLoadPreset) {
      btnLoadPreset.addEventListener('click', () => {
        const val = document.getElementById('preset-select').value;
        if (val) loadPreset(val);
      });
    }

    // Clear Canvas
    document.getElementById('btn-clear-all')?.addEventListener('click', () => {
      if (confirm('Clear entire automaton?')) {
        appState.dfa = {
          states: ['q0'],
          alphabet: ['0', '1'],
          start_state: 'q0',
          accepting_states: [],
          transitions: { q0: {} }
        };
        syncDfaToUI();
      }
    });

    // Form inputs sync
    document.getElementById('btn-sync-definition')?.addEventListener('click', readDfaFromInputs);
    document.getElementById('btn-validate')?.addEventListener('click', validateCurrentDfa);

    // Canvas toolbar buttons
    document.getElementById('btn-auto-layout')?.addEventListener('click', autoLayoutNodes);

    // Add State
    document.getElementById('btn-add-state')?.addEventListener('click', () => {
      const nameInput = document.getElementById('new-state-name');
      const name = nameInput.value.trim();
      if (!name) return;
      if (appState.dfa.states.includes(name)) {
        alert(`State '${name}' already exists.`);
        return;
      }
      appState.dfa.states.push(name);
      appState.dfa.transitions[name] = {};
      nameInput.value = '';
      autoLayoutNodes();
      syncDfaToUI();
    });

    // Add Transition
    document.getElementById('btn-add-transition')?.addEventListener('click', () => {
      const src = document.getElementById('trans-source-select').value;
      const tgt = document.getElementById('trans-target-select').value;
      const sym = document.getElementById('trans-symbol-input').value.trim();
      if (!src || !tgt || !sym) return;

      if (!appState.dfa.alphabet.includes(sym)) {
        appState.dfa.alphabet.push(sym);
      }
      if (!appState.dfa.transitions[src]) appState.dfa.transitions[src] = {};
      appState.dfa.transitions[src][sym] = tgt;

      document.getElementById('trans-symbol-input').value = '';
      syncDfaToUI();
    });

    // Selected state actions
    document.getElementById('btn-toggle-start')?.addEventListener('click', () => {
      if (appState.graph.selectedNode) {
        appState.dfa.start_state = appState.graph.selectedNode;
        syncDfaToUI();
      }
    });

    document.getElementById('btn-toggle-accept')?.addEventListener('click', () => {
      const st = appState.graph.selectedNode;
      if (!st) return;
      const idx = appState.dfa.accepting_states.indexOf(st);
      if (idx >= 0) {
        appState.dfa.accepting_states.splice(idx, 1);
      } else {
        appState.dfa.accepting_states.push(st);
      }
      syncDfaToUI();
    });

    document.getElementById('btn-delete-state')?.addEventListener('click', () => {
      const st = appState.graph.selectedNode;
      if (!st) return;
      if (appState.dfa.states.length <= 1) {
        alert('DFA must contain at least one state.');
        return;
      }
      appState.dfa.states = appState.dfa.states.filter(s => s !== st);
      appState.dfa.accepting_states = appState.dfa.accepting_states.filter(s => s !== st);
      delete appState.dfa.transitions[st];
      Object.keys(appState.dfa.transitions).forEach(q => {
        Object.keys(appState.dfa.transitions[q]).forEach(sym => {
          if (appState.dfa.transitions[q][sym] === st) {
            delete appState.dfa.transitions[q][sym];
          }
        });
      });
      if (appState.dfa.start_state === st) {
        appState.dfa.start_state = appState.dfa.states[0];
      }
      appState.graph.selectedNode = null;
      hideSelectionPanel();
      autoLayoutNodes();
      syncDfaToUI();
    });

    // Simulation controls
    document.getElementById('btn-sim-run')?.addEventListener('click', runFullSimulation);
    document.getElementById('btn-sim-step')?.addEventListener('click', stepSimulationForward);
    document.getElementById('btn-sim-back')?.addEventListener('click', stepSimulationBackward);
    document.getElementById('btn-sim-reset')?.addEventListener('click', resetSimulation);
    document.getElementById('btn-sim-autoplay')?.addEventListener('click', toggleAutoPlay);

    document.getElementById('sim-speed')?.addEventListener('input', e => {
      appState.simulation.speedMs = parseInt(e.target.value, 10);
    });

    window.addEventListener('resize', resizeCanvas);
  }

  function init() {
    const savedTheme = localStorage.getItem('dfa_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    setupEventListeners();
    resizeCanvas();
    loadPreset('ends_with_01');
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  // Export for Node.js test environment if available
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { JSAutomataEngine, PRESETS };
  }
})();

// =============================================================================
// AI DFA CREATOR — Grok xAI Integration
// =============================================================================
(function () {
  'use strict';

  // State: holds the last AI-generated DFA so we can load it
  let _aiDfa = null;

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const textarea      = () => document.getElementById('ai-description-input');
  const btnGenerate   = () => document.getElementById('btn-ai-create');
  const btnText       = () => document.getElementById('ai-btn-text');
  const spinner       = () => document.getElementById('ai-spinner');
  const resultPanel   = () => document.getElementById('ai-result-panel');
  const errorPanel    = () => document.getElementById('ai-error-panel');
  const errorText     = () => document.getElementById('ai-error-text');
  const btnLoad       = () => document.getElementById('btn-ai-load');
  const explText      = () => document.getElementById('ai-explanation-text');
  const previewStates = () => document.getElementById('ai-preview-states');
  const previewAlpha  = () => document.getElementById('ai-preview-alphabet');
  const previewStart  = () => document.getElementById('ai-preview-start');
  const previewAccept = () => document.getElementById('ai-preview-accepting');
  const sampleChips   = () => document.getElementById('ai-sample-chips');

  function setLoading(on) {
    const btn = btnGenerate();
    const sp  = spinner();
    const bt  = btnText();
    if (!btn) return;
    btn.disabled = on;
    if (sp) sp.classList.toggle('hidden', !on);
    if (bt) bt.textContent = on ? 'Generating…' : '✦ Generate DFA';
  }

  function showError(msg) {
    const ep = errorPanel();
    const et = errorText();
    const rp = resultPanel();
    if (ep) ep.classList.remove('hidden');
    if (rp) rp.classList.add('hidden');
    if (et) et.textContent = msg;
  }

  function showResult(data) {
    const ep = errorPanel();
    const rp = resultPanel();
    if (ep) ep.classList.add('hidden');
    if (!rp) return;
    rp.classList.remove('hidden');

    _aiDfa = data.dfa;

    if (explText()) explText().textContent = data.explanation || 'AI-generated DFA.';
    if (previewStates()) previewStates().textContent = (data.dfa.states || []).join(', ');
    if (previewAlpha())  previewAlpha().textContent  = (data.dfa.alphabet || []).join(', ');
    if (previewStart())  previewStart().textContent  = data.dfa.start_state || '—';
    if (previewAccept()) previewAccept().textContent = (data.dfa.accepting_states || []).join(', ');

    // Sample input chips
    const sc = sampleChips();
    if (sc) {
      sc.innerHTML = '';
      const samples = data.sample_inputs || [];
      samples.forEach(s => {
        const chip = document.createElement('button');
        chip.className = 'sample-chip';
        chip.textContent = s === '' ? 'ε (empty)' : s;
        chip.title = 'Load this string into simulator';
        chip.addEventListener('click', () => {
          // Fill simulator input and trigger the preset load path
          const simInput = document.getElementById('sim-input-string');
          if (simInput) {
            simInput.value = s;
            simInput.dispatchEvent(new Event('input'));
          }
        });
        sc.appendChild(chip);
      });
    }
  }

  async function generateDFA() {
    const desc = (textarea() ? textarea().value : '').trim();
    if (!desc) {
      showError('Please describe the language before generating.');
      return;
    }

    setLoading(true);
    if (errorPanel()) errorPanel().classList.add('hidden');
    if (resultPanel()) resultPanel().classList.add('hidden');

    try {
      const resp = await fetch('/api/ai-create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: desc }),
      });

      const json = await resp.json();

      if (!json.success) {
        showError(json.error || 'Unknown error from AI service.');
      } else {
        showResult(json);
      }
    } catch (err) {
      showError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  function loadAiDfaIntoSimulator() {
    if (!_aiDfa) return;

    // Build a synthetic preset object matching the app's preset structure
    const pseudo = {
      states:           _aiDfa.states,
      alphabet:         _aiDfa.alphabet,
      start_state:      _aiDfa.start_state,
      accepting_states: _aiDfa.accepting_states,
      transitions:      _aiDfa.transitions,
      sample_inputs:    [],
      name:             'AI-Generated DFA',
      description:      document.getElementById('ai-explanation-text')
                          ? document.getElementById('ai-explanation-text').textContent
                          : 'Generated by Grok AI',
    };

    // Write directly into the form fields (same approach as loadPreset)
    const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
    setVal('input-states',           pseudo.states.join(', '));
    setVal('input-alphabet',         pseudo.alphabet.join(', '));
    setVal('input-start-state',      pseudo.start_state);
    setVal('input-accepting-states', pseudo.accepting_states.join(', '));

    // Trigger the "Apply Changes" button to sync the state machine + redraw canvas
    const applyBtn = document.getElementById('btn-sync-definition');
    if (applyBtn) applyBtn.click();

    // Populate transitions in the matrix after a short tick
    setTimeout(() => {
      // Fill each cell in the transition matrix
      Object.entries(pseudo.transitions || {}).forEach(([fromState, symMap]) => {
        Object.entries(symMap).forEach(([sym, toState]) => {
          // Find the input cell with data attributes matching this transition
          const cell = document.querySelector(
            `input[data-from="${fromState}"][data-sym="${sym}"]`
          );
          if (cell) {
            cell.value = toState;
            cell.dispatchEvent(new Event('change'));
          }
        });
      });

      // Trigger Apply again to pick up the transitions
      if (applyBtn) applyBtn.click();

      // Update preset banner
      const bannerName = document.getElementById('preset-name');
      const bannerDesc = document.getElementById('preset-desc');
      if (bannerName) bannerName.textContent = pseudo.name;
      if (bannerDesc) bannerDesc.textContent  = pseudo.description;

      // Scroll to the DFA editor card
      const card = document.getElementById('card-define');
      if (card) card.scrollIntoView({ behavior: 'smooth' });
    }, 80);
  }

  function init() {
    const gen  = btnGenerate();
    const load = btnLoad();

    if (gen) gen.addEventListener('click', generateDFA);
    if (load) load.addEventListener('click', loadAiDfaIntoSimulator);

    // Allow Enter (without shift) in textarea to generate
    const ta = textarea();
    if (ta) {
      ta.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          generateDFA();
        }
      });
    }

    // Quick example chips
    document.querySelectorAll('.ai-example-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const ta = textarea();
        if (ta) {
          ta.value = chip.dataset.prompt;
          ta.focus();
        }
      });
    });
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})();
