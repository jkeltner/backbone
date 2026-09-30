/* Backbone template kit.
   Data comes from window.BB (injected by tools/render_art.py from episodes/{topic}/assets/images/art.json).
   Opened directly in a browser, templates fall back to the Episode 1 sample below. */
(function () {
  const SAMPLE = {
    number: 1,
    topic: "Refrigeration",
    subtitle: "You Don't Make Cold, You Move Heat",
    accent: "ice",
    hosts: "Jeff Keltner & Cyrus Mistry",
    url: "backbone.fm",
    teaser: "Two hundred years from pond ice shipped to the tropics to a treaty every country on earth signed.",
    curve: {
      label: "U.S. households with a mechanical refrigerator",
      range: [1920, 1960],
      points: [[1930, 8], [1940, 44], [1950, 80]]
    },
    quote: {
      text: "You don't make cold. There's no such thing. You move heat.",
      speaker: "Jeff Keltner",
      context: "on why the coils on the back of your fridge are warm"
    },
    stat: {
      value: "8% → 80%",
      label: "of U.S. homes had a mechanical refrigerator, 1930 to 1950",
      context: "The steepest stretch of the curve ran straight through the Great Depression."
    },
    compare: {
      title: "Faster than the phone. Slower than TV.",
      label: "Share of U.S. households",
      range: [1900, 1960],
      series: [
        { name: "Electricity", points: [[1907, 8], [1920, 35], [1929, 68]] },
        { name: "Telephone", points: [[1920, 34], [1934, 31], [1946, 50]] },
        { name: "Refrigerator", points: [[1930, 8], [1940, 44], [1950, 80]], highlight: true },
        { name: "Television", points: [[1949, 2], [1950, 8], [1954, 59]] }
      ],
      context: "The fridge went from 8% to 80% of homes in twenty years, most of it during the Depression."
    }
  };

  const D = Object.assign({}, SAMPLE, window.BB || {});
  const ACCENTS = { ice: "--bb-ice", copper: "--bb-copper", sodium: "--bb-sodium",
    phosphor: "--bb-phosphor", rust: "--bb-rust", lilac: "--bb-lilac", signal: "--bb-signal" };
  const root = document.documentElement;
  if (D.accent) root.style.setProperty("--bb-accent",
    ACCENTS[D.accent] ? `var(${ACCENTS[D.accent]})` : D.accent);

  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, parent) => { const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]); if (parent) parent.appendChild(n); return n; };
  const css = (v) => getComputedStyle(root).getPropertyValue(v).trim();

  /* ---------- text binding ---------- */
  const pad = (n) => String(n).padStart(2, "0");
  const fields = {
    number: `No. ${pad(D.number)}`, topic: D.topic, subtitle: D.subtitle, hosts: D.hosts,
    url: D.url, teaser: D.teaser, "curve-label": D.curve && D.curve.label,
    "curve-span": D.curve && `${D.curve.points[0][0]} – ${D.curve.points[D.curve.points.length - 1][0]}`,
    "quote-text": D.quote && D.quote.text, "quote-speaker": D.quote && D.quote.speaker,
    "quote-context": D.quote && D.quote.context, "stat-value": D.stat && D.stat.value,
    "stat-label": D.stat && D.stat.label, "stat-context": D.stat && D.stat.context,
    "episode-line": `Episode ${D.number} · ${D.topic}`,
    "compare-title": D.compare && D.compare.title, "compare-label": D.compare && D.compare.label,
    "compare-context": D.compare && D.compare.context
  };
  if (!D.curve) root.classList.add("no-curve");
  document.querySelectorAll("[data-bb]").forEach((n) => {
    const v = fields[n.dataset.bb]; if (v != null) n.textContent = v; });

  /* ---------- signature mark ---------- */
  // viewBox 0 0 100 40: flat line, S-rise, flat line; ring node at the inflection (the tipping point).
  function drawMark(svg) {
    const w = parseFloat(svg.dataset.stroke || 1.4);
    svg.setAttribute("viewBox", "-6 0 112 40");
    const line = css("--bb-bone"), acc = css("--bb-accent");
    el("path", { d: "M-6 33 H26 C38 33 44 26 50 20 C56 14 62 7 74 7 H106",
      fill: "none", stroke: line, "stroke-width": w, "stroke-linecap": "round", opacity: svg.dataset.lineOpacity || .75 }, svg);
    el("circle", { cx: 50, cy: 20, r: 4.4, fill: css("--bb-night"), stroke: line, "stroke-width": w }, svg);
    el("circle", { cx: 50, cy: 20, r: 2, fill: acc }, svg);
  }
  document.querySelectorAll("svg.bb-mark").forEach(drawMark);

  /* ---------- adoption plate ---------- */
  // Monotone cubic (Fritsch–Carlson) so the curve never overshoots the data.
  function monotone(pts) {
    const n = pts.length, dx = [], m = [], t = [];
    for (let i = 0; i < n - 1; i++) { dx[i] = pts[i + 1][0] - pts[i][0]; m[i] = (pts[i + 1][1] - pts[i][1]) / dx[i]; }
    t[0] = m[0]; t[n - 1] = m[n - 2];
    for (let i = 1; i < n - 1; i++) t[i] = m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2;
    for (let i = 0; i < n - 1; i++) { if (m[i] === 0) { t[i] = t[i + 1] = 0; continue; }
      const a = t[i] / m[i], b = t[i + 1] / m[i], h = a * a + b * b;
      if (h > 9) { const k = 3 / Math.sqrt(h); t[i] = k * a * m[i]; t[i + 1] = k * b * m[i]; } }
    return (x) => { let i = 0; while (i < n - 2 && x > pts[i + 1][0]) i++;
      const h = dx[i], s = (x - pts[i][0]) / h, s2 = s * s, s3 = s2 * s;
      return (2*s3 - 3*s2 + 1) * pts[i][1] + (s3 - 2*s2 + s) * h * t[i] + (-2*s3 + 3*s2) * pts[i + 1][1] + (s3 - s2) * h * t[i + 1]; };
  }

  function drawPlate(box) {
    const c = D.curve; if (!c) return;
    const r = box.getBoundingClientRect(), W = r.width, H = r.height;
    const S = Math.min(innerWidth, innerHeight) / 100;           // 1 --s in px
    const opt = box.dataset;
    const fs = parseFloat(opt.fs || 1.6) * S;                     // tick label size
    const pts = c.points;
    // data-trim=N tightens the x-range to N years either side of the sourced points (steeper curve for small plates)
    const [x0, x1] = opt.trim ? [pts[0][0] - +opt.trim, pts[pts.length - 1][0] + +opt.trim] : c.range;
    const first = pts[0], last = pts[pts.length - 1], prev = pts[pts.length - 2] || first;
    // Dashed tails show the shape beyond the sourced points; they are not data.
    const lead = [x0, Math.max(0.5, first[1] * 0.12)];
    const tail = [x1, Math.min(97, last[1] + (100 - last[1]) * 0.6)];
    const all = [lead, ...pts, tail];
    const f = monotone(all);
    const padL = 0, padR = 0, padT = fs * 2.2, padB = fs * 2.8;
    const X = (x) => padL + (x - x0) / (x1 - x0) * (W - padL - padR);
    const Y = (y) => padT + (1 - y / 100) * (H - padT - padB);
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }); box.appendChild(svg);
    const bone = css("--bb-bone"), ash = css("--bb-ash"), rule = css("--bb-rule"), acc = css("--bb-accent"), night = css("--bb-night");
    const sw = parseFloat(opt.stroke || 0.28) * S;

    // axis + guides
    el("line", { x1: 0, x2: W, y1: Y(0), y2: Y(0), stroke: bone, "stroke-opacity": .35, "stroke-width": sw * .5 }, svg);
    if (opt.guides !== "off") [50, 100].forEach((g) => {
      el("line", { x1: 0, x2: W, y1: Y(g), y2: Y(g), stroke: rule, "stroke-width": sw * .4, "stroke-dasharray": `${sw} ${sw * 3}` }, svg);
      const t = el("text", { x: W, y: Y(g) - fs * .5, fill: ash, "font-family": "JetBrains Mono", "font-size": fs * .85,
        "text-anchor": "end", "letter-spacing": fs * .15 }, svg); t.textContent = g + "%"; });
    const step = (x1 - x0) > 60 ? 20 : 10;
    for (let yr = Math.ceil(x0 / step) * step; yr <= x1; yr += step) {
      el("line", { x1: X(yr), x2: X(yr), y1: Y(0), y2: Y(0) + fs * .6, stroke: bone, "stroke-opacity": .35, "stroke-width": sw * .5 }, svg);
      if (opt.years !== "off") { const t = el("text", { x: X(yr), y: Y(0) + fs * 1.9, fill: ash, "font-family": "JetBrains Mono",
        "font-size": fs, "text-anchor": yr === x0 ? "start" : yr === x1 ? "end" : "middle", "letter-spacing": fs * .12 }, svg); t.textContent = yr; } }

    // curve: dashed lead, solid data span, dashed tail
    const path = (a, b) => { let d = ""; const N = 90; for (let i = 0; i <= N; i++) {
      const x = a + (b - a) * i / N; d += (i ? "L" : "M") + X(x).toFixed(1) + " " + Y(f(x)).toFixed(1); } return d; };
    const dash = `${sw * 1.4} ${sw * 2.2}`;
    el("path", { d: path(x0, first[0]), fill: "none", stroke: bone, "stroke-opacity": .5, "stroke-width": sw, "stroke-dasharray": dash, "stroke-linecap": "round" }, svg);
    el("path", { d: path(last[0], x1), fill: "none", stroke: bone, "stroke-opacity": .5, "stroke-width": sw, "stroke-dasharray": dash, "stroke-linecap": "round" }, svg);
    if (opt.fill !== "off") el("path", { d: path(first[0], last[0]) + `L${X(last[0])} ${Y(0)} L${X(first[0])} ${Y(0)} Z`,
      fill: acc, "fill-opacity": .07 }, svg);
    el("path", { d: path(first[0], last[0]), fill: "none", stroke: bone, "stroke-width": sw * 1.35, "stroke-linecap": "round" }, svg);

    // tipping-point node where the curve crosses 50% (unlabelled: it is the logo's node, not a data claim)
    let cross = null; for (let x = x0; x <= x1; x += (x1 - x0) / 800) if (f(x) >= 50) { cross = x; break; }
    // sourced points
    pts.forEach(([x, y]) => {
      el("circle", { cx: X(x), cy: Y(y), r: sw * 1.6, fill: acc }, svg);
      if (opt.values !== "off") { const t = el("text", { x: X(x) - fs * .7, y: Y(y) - fs * .8, fill: bone, "font-family": "JetBrains Mono",
        "font-weight": 500, "font-size": fs * 1.05, "text-anchor": "end", "letter-spacing": fs * .08 }, svg); t.textContent = y + "%"; } });
    if (cross != null && opt.node !== "off") {
      const cx = X(cross), cy = Y(50), R = sw * 4.2;
      el("circle", { cx, cy, r: R, fill: night, "fill-opacity": .0, stroke: acc, "stroke-width": sw * .9 }, svg);
    }
  }
  /* ---------- comparison plate: several technologies on one axis ---------- */
  // Each series is sourced points only (solid, no dashed tails). The episode's own series is bone + accent dots;
  // the others are ash, labelled at their last point.
  function drawCompare(box) {
    const c = D.compare; if (!c) return;
    const r = box.getBoundingClientRect(), W = r.width, H = r.height;
    const S = Math.min(innerWidth, innerHeight) / 100, opt = box.dataset;
    const fs = parseFloat(opt.fs || 1.8) * S, sw = parseFloat(opt.stroke || 0.35) * S;
    const [x0, x1] = c.range, padT = fs * 1.5, padB = fs * 2.8, padR = fs * 7.5;
    const X = (x) => (x - x0) / (x1 - x0) * (W - padR), Y = (y) => padT + (1 - y / 100) * (H - padT - padB);
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }); box.appendChild(svg);
    const bone = css("--bb-bone"), ash = css("--bb-ash"), rule = css("--bb-rule"), acc = css("--bb-accent");
    el("line", { x1: 0, x2: W - padR, y1: Y(0), y2: Y(0), stroke: bone, "stroke-opacity": .35, "stroke-width": sw * .5 }, svg);
    [50, 100].forEach((g) => { el("line", { x1: 0, x2: W - padR, y1: Y(g), y2: Y(g), stroke: rule, "stroke-width": sw * .4, "stroke-dasharray": `${sw} ${sw * 3}` }, svg);
      const t = el("text", { x: 0, y: Y(g) - fs * .5, fill: ash, "font-family": "JetBrains Mono", "font-size": fs * .85, "letter-spacing": fs * .15 }, svg); t.textContent = g + "%"; });
    const step = (x1 - x0) > 50 ? 20 : 10;
    for (let yr = Math.ceil(x0 / step) * step; yr <= x1; yr += step) {
      el("line", { x1: X(yr), x2: X(yr), y1: Y(0), y2: Y(0) + fs * .6, stroke: bone, "stroke-opacity": .35, "stroke-width": sw * .5 }, svg);
      const t = el("text", { x: X(yr), y: Y(0) + fs * 1.9, fill: ash, "font-family": "JetBrains Mono", "font-size": fs,
        "text-anchor": yr === x0 ? "start" : "middle", "letter-spacing": fs * .12 }, svg); t.textContent = yr; }
    const order = [...c.series].sort((a, b) => (a.highlight ? 1 : 0) - (b.highlight ? 1 : 0));   // highlight drawn last, on top
    const labels = [];
    order.forEach((sr) => {
      const pts = sr.points, f = monotone(pts), a = pts[0][0], b = pts[pts.length - 1][0];
      let d = ""; for (let i = 0; i <= 80; i++) { const x = a + (b - a) * i / 80; d += (i ? "L" : "M") + X(x).toFixed(1) + " " + Y(f(x)).toFixed(1); }
      const hi = !!sr.highlight;
      el("path", { d, fill: "none", stroke: hi ? bone : ash, "stroke-width": hi ? sw * 1.5 : sw * .9, "stroke-linecap": "round", opacity: hi ? 1 : .9 }, svg);
      pts.forEach(([x, y]) => el("circle", { cx: X(x), cy: Y(y), r: hi ? sw * 1.7 : sw * 1.1, fill: hi ? acc : ash }, svg));
      labels.push({ name: sr.name, x: X(b) + fs * .8, y: Y(pts[pts.length - 1][1]), hi });
    });
    // keep end labels from colliding
    labels.sort((p, q) => p.y - q.y);
    for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < fs * 1.3) labels[i].y = labels[i - 1].y + fs * 1.3;
    labels.forEach((l) => { const t = el("text", { x: l.x, y: l.y + fs * .35, fill: l.hi ? bone : ash, "font-family": "JetBrains Mono",
      "font-weight": l.hi ? 500 : 400, "font-size": fs * (l.hi ? 1.05 : .95), "letter-spacing": fs * .1 }, svg); t.textContent = l.name.toUpperCase(); });
  }

  /* ---------- fit: shrink text marked .fit until it fits its box width (and data-lines lines) ---------- */
  function fit(n) {
    const S = Math.min(innerWidth, innerHeight) / 100;
    let size = parseFloat(n.dataset.max || 14) * S; const min = parseFloat(n.dataset.min || 3) * S;
    const lines = parseFloat(n.dataset.lines || 1);
    n.style.fontSize = size + "px";
    const lh = () => parseFloat(getComputedStyle(n).lineHeight) || size;
    while (size > min && (n.scrollWidth > n.clientWidth + 1 || n.scrollHeight > n.clientHeight + 1 || n.getBoundingClientRect().height > lh() * lines + 2)) {
      size *= 0.97; n.style.fontSize = size + "px"; }
  }

  document.fonts.ready.then(() => {
    document.querySelectorAll(".fit").forEach(fit);
    document.querySelectorAll(".plate").forEach(drawPlate);
    document.querySelectorAll(".plate-compare").forEach(drawCompare);
    window.__bbReady = true;
  });
})();
