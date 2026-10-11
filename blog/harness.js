(() => {
  'use strict';

  const byId = (id) => document.getElementById(id);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const chartWidth = (element) => Math.max(280, Math.round(element.getBoundingClientRect().width));
  const text = (x, y, value, className = 'chart-tick', anchor = 'middle') =>
    `<text x="${x}" y="${y}" class="${className}" text-anchor="${anchor}">${value}</text>`;
  const rule = (x1, y1, x2, y2) =>
    `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="chart-rule"/>`;
  const svg = (width, height, label, contents) =>
    `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${label}">${contents}</svg>`;
  const dataTable = (caption, headings, rows) =>
    `<table class="visually-hidden"><caption>${caption}</caption><thead><tr>${headings.map((heading) => `<th scope="col">${heading}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr><th scope="row">${row[0]}</th>${row.slice(1).map((value) => `<td>${value}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

  const scaling = [
    [10, 6.1, 0, 0], [20, 10.6, 5.9, 0], [30, 14.6, 12.3, 7],
    [40, 18.2, 18.1, 15], [50, 21.5, 23.3, 22.2], [60, 24.5, 28.1, 28.8],
    [80, 29.9, 36.6, 40.3], [100, 34.7, 43.8, 49.8], [140, 43, 55.2, 64.1],
    [180, 51.5, 63.7, 73.9], [225, 56.5, 70.7, 81.3], [260, 61, 73.5, 84],
    [300, 62, 76, 86.5], [400, 62.8, 79, 89.5], [510, 63.5, 80, 90.8],
    [750, 67.5, 81.5, 91.6], [1000, 69.5, 83, 92],
  ];

  function renderScaling() {
    const root = byId('scaling-figure');
    const width = chartWidth(root);
    const compact = width < 440;
    const height = compact ? 220 : 260;
    const left = 42;
    const right = 42;
    const top = 16;
    const bottom = 30;
    const x = (steps) => left + (steps - 10) / 990 * (width - left - right);
    const y = (value) => height - bottom - value / 100 * (height - top - bottom);
    let content = '';
    for (const value of [0, 50, 100]) {
      content += rule(left, y(value), width - right, y(value));
      content += text(left - 8, y(value) + 4, `${value}%`, 'chart-tick', 'end');
    }
    for (const value of compact ? [10, 510, 1000] : [10, 260, 510, 760, 1000]) {
      content += text(x(value), height - 8, value);
    }
    const series = [
      { column: 1, label: 'N=1', className: 'series-one' },
      { column: 2, label: 'N=10', className: 'series-ten' },
      { column: 3, label: 'N=20', className: 'series-twenty' },
    ];
    for (const item of series) {
      const path = scaling.map((row, index) => `${index ? 'L' : 'M'} ${x(row[0]).toFixed(2)} ${y(row[item.column]).toFixed(2)}`).join(' ');
      content += `<path d="${path}" class="plot-line ${item.className}"/>`;
      content += text(width - right + 5, y(scaling.at(-1)[item.column]) + 4, item.label, `plot-label ${item.className}`, 'start');
    }
    root.innerHTML = `<div class="figure-kicker">Task completion (%)</div>` +
      svg(width, height, 'DiscoveryWorld task completion by experimental steps for N=1, N=10, and N=20', content) +
      '<div class="axis-caption">Experimental steps per task</div>' +
      dataTable('DiscoveryWorld scaling', ['Experimental steps per task', 'N=1', 'N=10', 'N=20'],
        scaling.map((row) => [row[0], ...row.slice(1).map((value) => `${value}%`)]));
  }

  const communication = [
    { name: 'Single agent', efficiency: 58.44, tokens: '1.0x', gain: '0%', className: 'single-agent' },
    { name: 'Independent sampling', efficiency: 75.86, tokens: '13.7x', gain: '+29.8%', className: 'sampling' },
    { name: 'Swarm + communication', efficiency: 57.10, tokens: '27.4x', gain: '-2.3%', className: 'communication-only' },
    { name: 'Our harness', efficiency: 84.10, tokens: '25.5x', gain: '+43.9%', className: 'our-harness' },
  ];

  function renderCommunication() {
    byId('communication-figure').innerHTML = `
      ${communication.map((row) => `
        <div class="comparison-row ${row.className}">
          <div class="comparison-name">${row.name}</div>
          <div class="comparison-track" aria-label="${row.name}: ${row.efficiency.toFixed(2)}% experimental efficiency">
            <div class="comparison-bar" style="width:${row.efficiency}%"><span>${row.efficiency.toFixed(2)}%</span></div>
          </div>
          <div class="comparison-tokens">${row.tokens} tokens</div>
          <div class="comparison-gain">${row.gain} vs single</div>
        </div>`).join('')}
      <div class="comparison-axis"><span>0%</span><span>50%</span><span>100%</span></div>` +
      dataTable('DiscoveryWorld experimental efficiency by approach',
        ['Approach', 'Experimental efficiency', 'Token multiple', 'Gain versus single agent'],
        communication.map((row) => [row.name, `${row.efficiency.toFixed(2)}%`, row.tokens, row.gain]));
  }

  const made = [
    [0, 0, 0, 0, 0], [5, 3.3, 2.1, 3.8, 1.9], [10, 5.5, 4, 7.3, 3.2],
    [15, 6.7, 6.4, 9.7, 5.2], [20, 8.3, 8.6, 11.6, 7], [25, 10.1, 10.8, 13.8, 9.5],
    [30, 11.5, 13, 15.1, 12.1], [35, 13.2, 15.4, 16.6, 13.5],
    [40, 14.7, 17.4, 19.4, 15.8], [45, 15.6, 19.5, 21.1, 17.9],
    [50, 16.4, 21.5, 24.2, 20.3], [55, 18.1, 24.1, 25.8, 22.4],
    [60, 19.4, 26, 27.7, 24.2],
  ];

  function madeChart(width, title, singleIndex, swarmIndex, maximum) {
    const compact = width < 440;
    const height = compact ? 202 : 222;
    const left = 34;
    const right = 45;
    const top = 10;
    const bottom = 29;
    const x = (value) => left + value / 60 * (width - left - right);
    const y = (value) => height - bottom - value / maximum * (height - top - bottom);
    let content = '';
    for (const value of [0, 10, 20, 30]) {
      content += rule(left, y(value), width - right, y(value));
      content += text(left - 8, y(value) + 4, value, 'chart-tick', 'end');
    }
    for (const value of [0, 15, 30, 45, 60]) content += text(x(value), height - 8, value);
    for (const item of [
      { index: singleIndex, label: 'N=1', className: 'series-one', offset: -10 },
      { index: swarmIndex, label: 'N=20', className: 'series-twenty', offset: 10 },
    ]) {
      const path = made.map((row, index) => `${index ? 'L' : 'M'} ${x(row[0]).toFixed(2)} ${y(row[item.index]).toFixed(2)}`).join(' ');
      content += `<path d="${path}" class="plot-line ${item.className}"/>`;
      content += text(width - right + 5, y(made.at(-1)[item.index]) + item.offset + 4, item.label, `plot-label ${item.className}`, 'start');
    }
    return `<div class="made-chart"><div class="figure-kicker">${title}</div>${svg(width, height,
      `MADE ${title.toLowerCase()} over experiments for N=1 and N=20`, content)}</div>`;
  }

  function renderMade() {
    const root = byId('made-figure');
    const width = chartWidth(root);
    root.innerHTML = madeChart(width, 'Regions explored', 1, 3, 35) +
      madeChart(width, 'Stable structures', 2, 4, 30) +
      '<div class="axis-caption">Experiments</div>' +
      dataTable('MADE discovery and exploration',
        ['Experiments', 'N=1 regions', 'N=1 stable structures', 'N=20 regions', 'N=20 stable structures'], made);
  }

  const lith = [
    ['Bookkeeping', 11.73, 7.20],
    ['Evidence sharing', 26.31, 38.86],
    ['Experiment proposal', 35.61, 34.17],
    ['Critique/falsification', 8.71, 5.28],
    ['Recombination', 0.00, 0.04],
    ['Resource coordination', 17.64, 13.91],
    ['Other', 0.00, 0.54],
  ];

  function renderLith() {
    byId('lith-figure').innerHTML = `<div class="figure-kicker">Share of messages</div>` +
      lith.map(([name, without, withLith]) => `
        <div class="lith-group">
          <div class="lith-category">${name}</div>
          <div class="lith-measure"><span>No Lith</span><div class="lith-track"><i style="width:${without / 40 * 100}%"></i></div><span class="lith-value">${without.toFixed(2)}%</span></div>
          <div class="lith-measure with-lith"><span>With Lith</span><div class="lith-track"><i style="width:${withLith / 40 * 100}%"></i></div><span class="lith-value">${withLith.toFixed(2)}%</span></div>
        </div>`).join('') +
      `<div class="lith-axis"><span>0%</span><span>20%</span><span>40%</span></div>` +
      dataTable('Share of messages with and without Lith', ['Category', 'No Lith', 'With Lith'],
        lith.map(([name, without, withLith]) => [name, `${without.toFixed(2)}%`, `${withLith.toFixed(2)}%`]));
  }

  const candidates = [
    { label: 'rigid polycycle', agent: 32 },
    { label: 'fused quinone', agent: 8 },
    { label: 'N-limited aromatic', agent: 12 },
    { label: 'fused ester', agent: 19 },
    { label: 'cyclic imine', agent: 20 },
    { label: 'lipophilic quinone', agent: 25 },
    { label: 'low-donor fused core', agent: 32 },
    { label: 'low-donor redox core', agent: 32, pass: true },
  ];
  const parents = [[0, 3], [1, 3], [1, 4], [3, 5], [2, 5], [4, 6], [5, 6], [6, 7]];

  function lineagePositions(width) {
    if (width < 580) {
      const left = Math.max(70, width * 0.28);
      const right = width - left;
      return {
        height: 492,
        points: [[left, 34], [right, 94], [left, 154], [right, 214],
          [left, 274], [right, 334], [left, 394], [right, 454]],
      };
    }
    return {
      height: 305,
      points: [[64, 50], [64, 152], [64, 270], [width * 0.32, 95],
        [width * 0.32, 210], [width * 0.55, 255], [width * 0.76, 185], [width - 76, 98]],
    };
  }

  function renderLineage() {
    const root = byId('lineage-figure');
    const width = Math.max(240, Math.round(root.getBoundingClientRect().width));
    const narrow = width < 580;
    root.classList.toggle('lineage-mobile', narrow);
    const { height, points } = lineagePositions(width);
    let content = `<title>SMDD hypothesis lineage</title><desc>Four failed branches combine over several rounds into a passing low-donor redox core.</desc>`;
    for (const [from, to] of parents) {
      const [x1, y1] = points[from];
      const [x2, y2] = points[to];
      const bend = (x2 - x1) * 0.5;
      content += `<path class="lineage-edge" d="M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}"/>`;
    }
    candidates.forEach((candidate, index) => {
      const [x, y] = points[index];
      const labelX = x;
      const anchor = 'middle';
      const labelY = narrow ? y - 15 : y - (candidate.pass ? 22 : 17);
      content += `<g class="lineage-node${candidate.pass ? ' passing' : ''}">` +
        `<title>${candidate.label}, agent ${candidate.agent}${candidate.pass ? ', pass' : ''}</title>` +
        `<circle cx="${x}" cy="${y}" r="5"/>` +
        (candidate.pass ? text(labelX, labelY - (narrow ? 17 : 25), 'PASS', 'lineage-pass', anchor) : '') +
        text(labelX, labelY, candidate.label, 'lineage-label', anchor) +
        text(labelX, narrow ? y + 17 : y + 18, `agent ${candidate.agent}`, 'lineage-agent', anchor) +
        '</g>';
    });
    root.innerHTML = svg(width, height, 'SMDD hypothesis lineage from four failed branches to a passing candidate', content);
  }

  const messages = [
    ['agent 5', 'all agents', 'A submission check has been queued for the shared verifier.'],
    ['agent 2', 'all agents', 'I tightened my MACCS rule; all 10 actives still match. Submitting.'],
    ['agent 17', 'agent 2', "Stop submitting. You replaced agent 5's check before it resolved."],
    ['agent 1', 'agent 2', "STOP queuing MACCS variants. Let agent 5's pending check resolve."],
    ['agent 12', 'agent 2', 'Hold further submissions. Replacing queued checks prevents attribution.'],
    ['agent 15', 'all agents', 'Queued a submission check for a single N-H-carbamate candidate.'],
    ['agent 2', 'all agents', 'My MACCS variant is going in. Hold other checks until it returns.'],
    ['agent 18', 'agent 2', 'Stop queuing. Repeated MACCS checks add no new information.'],
    ['agent 16', 'agent 2', "STOP. Let agent 15's carbamate check complete, then freeze."],
    ['agent 5', 'agent 2', 'Stop duplicate Morgan/MACCS checks; report what is still queued.'],
  ];
  let boardActive = false;
  let boardTimer;
  let latestMessage = 2;

  function messageElement(message, slot) {
    const entry = document.createElement('div');
    entry.className = 'board-entry';
    entry.style.setProperty('--slot', slot);
    const from = document.createElement('div');
    from.className = 'board-from';
    const sender = document.createElement('span');
    sender.className = 'board-sender';
    sender.textContent = message[0];
    from.append(sender, document.createTextNode(` to ${message[1]}`));
    const body = document.createElement('p');
    body.textContent = message[2];
    entry.append(from, body);
    return entry;
  }

  function renderBoard() {
    const root = byId('resource-figure');
    if (reducedMotion.matches) {
      root.innerHTML = '<div class="board-all"></div>';
      const all = root.firstElementChild;
      [1, 2, 3, 6].forEach((index) => all.append(messageElement(messages[index], 0)));
      return;
    }
    root.innerHTML = '<div class="board-window"><div class="board-stack"></div></div>';
    const stack = root.querySelector('.board-stack');
    for (let i = 0; i < 3; i++) stack.append(messageElement(messages[i], i));
  }

  function stopBoard() {
    boardActive = false;
    clearTimeout(boardTimer);
    boardTimer = undefined;
  }

  function advanceBoard() {
    if (!boardActive || reducedMotion.matches) return;
    boardTimer = setTimeout(() => {
      const root = byId('resource-figure');
      const stack = root.querySelector('.board-stack');
      if (!stack) return;
      if (latestMessage === messages.length - 1) {
        stack.classList.add('board-reset');
        boardTimer = setTimeout(() => {
          latestMessage = 2;
          renderBoard();
          advanceBoard();
        }, 350);
        return;
      }
      const next = messageElement(messages[latestMessage + 1], 3);
      next.classList.add('entering');
      stack.append(next);
      requestAnimationFrame(() => {
        [...stack.children].forEach((entry, index) => {
          entry.style.setProperty('--slot', index - 1);
          if (index === 0) entry.classList.add('leaving');
          if (index === 3) entry.classList.remove('entering');
        });
      });
      boardTimer = setTimeout(() => {
        stack.firstElementChild?.remove();
        latestMessage++;
        advanceBoard();
      }, 450);
    }, 1980);
  }

  function watch(element, onChange) {
    if (!('IntersectionObserver' in window)) {
      onChange(true);
      return;
    }
    new IntersectionObserver(([entry]) => onChange(entry.isIntersecting), { threshold: 0.2 }).observe(element);
  }

  function resizeFigures() {
    renderScaling();
    renderMade();
    renderLineage();
  }

  renderCommunication();
  renderLith();
  renderBoard();
  resizeFigures();
  watch(byId('resource-figure'), (visible) => {
    if (visible && !boardActive && !reducedMotion.matches) {
      boardActive = true;
      advanceBoard();
    } else if (!visible && boardActive) stopBoard();
  });
  reducedMotion.addEventListener('change', () => {
    clearTimeout(boardTimer);
    boardTimer = undefined;
    if (reducedMotion.matches) {
      renderBoard();
    } else {
      renderBoard();
      if (boardActive) advanceBoard();
    }
  });
  const resizeObserver = new ResizeObserver(() => {
    const width = Math.round(byId('scaling-figure').getBoundingClientRect().width);
    if (width !== resizeObserver.lastWidth) {
      resizeObserver.lastWidth = width;
      resizeFigures();
    }
  });
  resizeObserver.lastWidth = Math.round(byId('scaling-figure').getBoundingClientRect().width);
  resizeObserver.observe(byId('scaling-figure'));
})();
