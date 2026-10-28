// meteors_eclipses: the showers and eclipses coming up, drawn as a printed
// timeline or as one event in large type with its radiant as a burst.
//
// Everything is computed in server.py; this file only lays it out. Nothing
// is fetched here and nothing animates. The timeline's collision handling
// (which caption goes in which lane) is done with pixel estimates from the
// cell's size, so the same payload lays out differently at sm and lg.

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function daysWords(n) {
  if (n < 0) return n === -1 ? "last night" : `${-n} days ago`;
  if (n === 0) return "tonight";
  if (n === 1) return "tomorrow night";
  return `in ${n} days`;
}

// ---------------------------------------------------------------- glyphs

// A comet: a disc with three streaks trailing to the upper right, as the
// printed symbol on a star-party flyer. Scaled by the CSS on .me-glyph.
function cometSvg(cls) {
  return `<svg class="me-glyph me-comet ${cls}" viewBox="0 0 64 64" aria-hidden="true">
    <circle cx="20" cy="44" r="9.5"/>
    <path class="st" d="M30 36 L58 8" stroke-width="4"/>
    <path class="st" d="M26 30 L44 6" stroke-width="2.6"/>
    <path class="st" d="M34 42 L62 22" stroke-width="2.6"/>
    <path class="st" d="M40 52 L56 46" stroke-width="2"/>
  </svg>`;
}

// The Moon's phase: a pale disc with the lit part drawn by its terminator.
// From the southern hemisphere the lit limb is on the other side.
function moonSvg(frac, waxing, south, cls) {
  const k = clamp(Number(frac) || 0, 0, 1);
  const r = 26;
  const litRight = Boolean(waxing) !== Boolean(south);
  const rx = Math.max(0.5, r * Math.abs(2 * k - 1));
  const outer = litRight ? 1 : 0;
  const inner = (k > 0.5) === litRight ? 1 : 0;
  const lit = k < 0.01 ? "" : k > 0.99
    ? `<circle class="lit" cx="32" cy="32" r="${r}"/>`
    : `<path class="lit" d="M32 ${32 - r} A${r} ${r} 0 0 ${outer} 32 ${32 + r} A${rx} ${r} 0 0 ${inner} 32 ${32 - r} Z"/>`;
  return `<svg class="me-glyph me-moon ${cls}" viewBox="0 0 64 64" aria-hidden="true">
    <circle class="disc" cx="32" cy="32" r="${r}"/>${lit}
  </svg>`;
}

let uid = 0;

// A lunar eclipse: the Moon with the Earth's shadow across it, offset by
// how deep the eclipse goes. A solar eclipse: the dark disc with its rim.
function eclipseSvg(ev, cls) {
  uid += 1;
  const id = `mecl${uid}`;
  if (ev.body === "lunar") {
    const depth = ev.type === "total" ? 6 : ev.type === "partial" ? 24 : 40;
    return `<svg class="me-glyph me-ecl lunar ${cls}" viewBox="0 0 64 64" aria-hidden="true">
      <defs><clipPath id="${id}"><circle cx="32" cy="32" r="25"/></clipPath></defs>
      <circle class="disc" cx="32" cy="32" r="25"/>
      <circle class="shadow" clip-path="url(#${id})" cx="${32 - depth}" cy="${30 + depth / 3}" r="31"/>
      <circle class="rim" cx="32" cy="32" r="25"/>
    </svg>`;
  }
  if (ev.type === "partial") {
    return `<svg class="me-glyph me-ecl solar ${cls}" viewBox="0 0 64 64" aria-hidden="true">
      <circle class="sun" cx="32" cy="32" r="22"/>
      <circle class="disc" cx="22" cy="28" r="22"/>
    </svg>`;
  }
  const ring = ev.type === "annular" ? 6 : 3.5;
  const rays = [0, 45, 90, 135, 180, 225, 270, 315]
    .map((a) => {
      const t = (a * Math.PI) / 180;
      const x1 = 32 + Math.cos(t) * 27;
      const y1 = 32 + Math.sin(t) * 27;
      const x2 = 32 + Math.cos(t) * 31;
      const y2 = 32 + Math.sin(t) * 31;
      return `<path class="ray" d="M${x1.toFixed(1)} ${y1.toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)}"/>`;
    })
    .join("");
  return `<svg class="me-glyph me-ecl solar ${cls}" viewBox="0 0 64 64" aria-hidden="true">
    ${rays}
    <circle class="rim" cx="32" cy="32" r="22" stroke-width="${ring}"/>
    <circle class="disc" cx="32" cy="32" r="${22 - ring / 2}"/>
  </svg>`;
}

function glyphFor(ev, cls) {
  return ev.kind === "shower" ? cometSvg(cls) : eclipseSvg(ev, cls);
}

// The radiant: thin lines from one point, a few of them in the accent.
// Lengths follow a fixed sequence so a render is the same every time.
function burstSvg() {
  const n = 72;
  const lines = [];
  for (let i = 0; i < n; i += 1) {
    const a = (i / n) * Math.PI * 2 + 0.07;
    const seed = Math.abs(Math.sin(i * 12.9898 + 4.1414) * 43758.5453) % 1;
    const len = 120 + seed * 160;
    const x = 200 + Math.cos(a) * len;
    const y = 160 + Math.sin(a) * len * 0.72;
    const accent = i % 9 === 4 ? " acc" : "";
    lines.push(`<path class="ray${accent}" d="M200 160 L${x.toFixed(1)} ${y.toFixed(1)}"/>`);
  }
  return `<svg class="me-burst" viewBox="0 0 400 320" preserveAspectRatio="xMidYMid meet" aria-hidden="true">${lines.join("")}</svg>`;
}

// ---------------------------------------------------------------- captions

function showerLine2(ev) {
  if (!ev.visible) return `${ev.when} · radiant never rises`;
  return `peaks ${ev.when} · ZHR ${ev.zhr}${ev.variable ? "+" : ""}`;
}

function eclipseLine2(ev) {
  if (ev.body === "lunar") {
    return ev.visible ? `${ev.when} · Moon up at ${ev.time}` : `${ev.when} · not visible here`;
  }
  return ev.visible ? `${ev.when} · partial from here` : `${ev.when} · not visible here`;
}

function captionLines(ev) {
  return [ev.name, ev.kind === "shower" ? showerLine2(ev) : eclipseLine2(ev)];
}

function nextBoxLines(ev, compact) {
  const head = `Next: ${ev.name}`;
  if (ev.kind === "shower") {
    const r = ev.radiant || {};
    const m = ev.moon || {};
    if (compact) return [head, `${ev.night} · ${m.note || ""}`];
    const where = r.rises ? `Radiant ${r.words}, best ${r.best}` : "Radiant never rises here";
    return [head, `Peak night ${ev.night} · ZHR ${ev.zhr} · ${daysWords(ev.days_to)}`, m.note || "", where];
  }
  if (compact) return [head, `${ev.when} · ${ev.visible ? "visible" : "not visible here"}`];
  const where = ev.body === "solar" ? `Central over ${ev.path || ev.region}` : `Seen from ${ev.region}`;
  return [head, `${ev.when} at ${ev.time} local · ${daysWords(ev.days_to)}`, ev.note || "", where];
}

// ---------------------------------------------------------------- lanes

// Lane assignment along one axis: an item takes the first lane where it
// overlaps nothing already placed. The next event goes first so it always
// lands in lane 0, then the bigger showers and the eclipses, so when a
// small cell runs out of lanes it is the minor showers that lose their
// caption (they keep their tick on the rule).
function assignLanes(items, maxLanes, gap) {
  const lanes = [];
  for (const it of items) {
    it.lane = -1;
    for (let k = 0; k < maxLanes; k += 1) {
      lanes[k] = lanes[k] || [];
      if (lanes[k].every((o) => o.hi + gap <= it.lo || it.hi + gap <= o.lo)) {
        it.lane = k;
        lanes[k].push(it);
        break;
      }
    }
  }
}

function laneOrder(items) {
  const rank = (it) => (it.isNext ? 0 : it.ev.kind === "eclipse" || it.ev.zhr >= 20 ? 1 : 2);
  return items.slice().sort((a, b) => rank(a) - rank(b) || a.lo - b.lo);
}

// ---------------------------------------------------------------- timeline

function timelineHtml(d, ctx, dims) {
  const { w, h, G, F } = dims;
  const portrait = h > w * 1.15;
  const size = ctx.cell.size;
  const compactBox = size === "sm";
  const charW = F * 0.57;
  const events = (d.events || []).filter((e) => e.in_span);
  const nextIdx = d.next;
  const next = nextIdx != null ? d.events[nextIdx] : null;
  const nextCode = next && next.in_span ? next.code + next.date : null;

  const items = events.map((ev) => {
    const isNext = nextCode === ev.code + ev.date;
    const lines = isNext ? nextBoxLines(ev, compactBox) : captionLines(ev);
    const chars = Math.max(...lines.slice(1).map((l) => l.length), lines[0].length * (isNext ? 1.25 : 1.05));
    const capW = chars * charW + (isNext ? F * 2.4 + G * 0.9 : F * 0.6);
    const capH = lines.length * F * 1.32 + (isNext ? F * 1.4 : F * 0.3);
    return { ev, isNext, lines, capW, capH };
  });

  const padX = clamp(w * 0.03, 10, 36);
  const monthsH = F * 2.2;
  const stemGap = F * 0.5;

  if (!portrait) {
    const trackW = w - padX * 2;
    const left = padX;
    for (const it of items) {
      it.x = left + it.ev.pos * trackW;
      const width = Math.min(it.capW, trackW);
      it.bx = it.isNext ? clamp(it.x - G * 0.6, left, left + trackW - width) : clamp(it.x - width / 2, left, left + trackW - width);
      it.lo = it.bx;
      it.hi = it.bx + width;
      it.width = width;
    }
    let maxLanes = size === "sm" ? 2 : size === "md" ? 3 : 4;
    let laneH = [];
    const ordered = laneOrder(items);
    for (;;) {
      assignLanes(ordered, maxLanes, F * 0.6);
      laneH = [];
      for (const it of items) {
        if (it.lane < 0) continue;
        laneH[it.lane] = Math.max(laneH[it.lane] || 0, G + it.capH + stemGap);
      }
      const used = laneH.reduce((a, v) => a + (v || 0), 0) + monthsH + F * 0.4;
      if (used <= dims.trackH || maxLanes <= 1) break;
      maxLanes -= 1;
    }
    const laneTop = [];
    let y = 0;
    for (let k = laneH.length - 1; k >= 0; k -= 1) {
      laneTop[k] = y;
      y += laneH[k] || 0;
    }
    const ruleY = y + (items.length ? F * 0.4 : G);
    const totalH = ruleY + monthsH;
    const stems = [];
    const parts = [];
    for (const it of items) {
      parts.push(`<div class="me-tick ev" style="left:${it.x.toFixed(1)}px;top:${ruleY.toFixed(1)}px"></div>`);
      if (it.lane < 0) continue;
      const top = laneTop[it.lane] + (laneH[it.lane] - (G + it.capH + stemGap));
      stems.push(`<div class="me-stem" style="left:${it.x.toFixed(1)}px;top:${(top + G * 0.7).toFixed(1)}px;height:${(ruleY - top - G * 0.7).toFixed(1)}px"></div>`);
      parts.push(`<div class="${evClass(it)}" style="left:${(it.x - G / 2).toFixed(1)}px;top:${top.toFixed(1)}px;width:${G}px;height:${G}px">${glyphFor(it.ev, "")}</div>`);
      parts.push(captionHtml(it, d, it.bx, top + G + stemGap * 0.4, it.width));
    }
    parts.unshift(...stems);
    const months = d.span.months.map((m) => {
      const x0 = left + (m.offset / d.span.days) * trackW;
      const mw = (m.days / d.span.days) * trackW;
      const name = mw < m.name.length * F * 0.98 ? m.short : m.name;
      return `<div class="me-tick month" style="left:${x0.toFixed(1)}px;top:${ruleY.toFixed(1)}px"></div>
        <div class="me-month" style="left:${x0.toFixed(1)}px;width:${mw.toFixed(1)}px;top:${(ruleY + F * 0.6).toFixed(1)}px">${esc(name)}</div>`;
    }).join("");
    const todayX = left + todayPos(d) * trackW;
    return `<div class="me-track" style="height:${totalH.toFixed(1)}px">
      ${parts.join("")}
      <div class="me-rule" style="left:${left}px;width:${trackW}px;top:${ruleY.toFixed(1)}px"></div>
      <div class="me-tick month" style="left:${(left + trackW).toFixed(1)}px;top:${ruleY.toFixed(1)}px"></div>
      ${months}
      <div class="me-today" style="left:${todayX.toFixed(1)}px;top:${ruleY.toFixed(1)}px" title="today"></div>
    </div>`;
  }

  // Portrait: the rule runs down the left, months beside it, events to the
  // right in one column. Captions that would collide are nudged apart
  // along the rule and joined to their true date by an elbow.
  const monthsW = F * 3.2;
  const ruleX = padX + monthsW;
  const padY = F * 0.5;
  const trackH = Math.max(F * 8, dims.trackH - padY * 2);
  const gx = ruleX + F * 1.6;
  const capLeft = gx + G + stemGap;
  const capMax = w - capLeft - padX;
  for (const it of items) {
    it.y = padY + it.ev.pos * trackH;
    if (it.isNext && it.capW > capMax) {
      it.noMoon = true;
      it.capW -= G * 0.9 + F * 0.6;
    }
    it.h = Math.max(it.capH, G) + F * 0.3;
    it.width = Math.min(it.capW, capMax);
  }
  // Drop the captions that cannot fit, minor showers first.
  const ranked = laneOrder(items);
  let need = items.reduce((a, it) => a + it.h, 0) + (items.length - 1) * F * 0.3;
  for (let i = ranked.length - 1; i >= 0 && need > trackH; i -= 1) {
    ranked[i].lane = -1;
    need -= ranked[i].h + F * 0.3;
  }
  const shown = items.filter((it) => it.lane !== -1).sort((a, b) => a.y - b.y);
  for (const it of shown) it.by = it.y - it.h / 2;
  const gap = F * 0.3;
  for (let i = 1; i < shown.length; i += 1) {
    shown[i].by = Math.max(shown[i].by, shown[i - 1].by + shown[i - 1].h + gap);
  }
  if (shown.length) {
    const last = shown[shown.length - 1];
    last.by = Math.min(last.by, padY + trackH - last.h);
    for (let i = shown.length - 2; i >= 0; i -= 1) {
      shown[i].by = Math.min(shown[i].by, shown[i + 1].by - shown[i].h - gap);
    }
    for (const it of shown) it.by = Math.max(it.by, padY);
  }
  const stems = [];
  const parts = [];
  for (const it of items) {
    parts.push(`<div class="me-tick ev v" style="left:${ruleX}px;top:${it.y.toFixed(1)}px"></div>`);
  }
  for (const it of shown) {
    const gy = it.isNext ? it.by + G / 2 + F * 0.5 : it.by + it.h / 2;
    const x1 = ruleX + F * 0.7;
    const x2 = gx - F * 0.35;
    stems.push(`<polyline points="${ruleX},${it.y.toFixed(1)} ${x1.toFixed(1)},${it.y.toFixed(1)} ${x2.toFixed(1)},${gy.toFixed(1)} ${(gx + G * 0.3).toFixed(1)},${gy.toFixed(1)}"/>`);
    parts.push(`<div class="${evClass(it)}" style="left:${gx.toFixed(1)}px;top:${(gy - G / 2).toFixed(1)}px;width:${G}px;height:${G}px">${glyphFor(it.ev, "")}</div>`);
    parts.push(captionHtml(it, d, capLeft, it.isNext ? it.by : gy - it.capH / 2, it.width));
  }
  const months = d.span.months.map((m) => {
    const y0 = padY + (m.offset / d.span.days) * trackH;
    const mh = (m.days / d.span.days) * trackH;
    return `<div class="me-tick month v" style="left:${ruleX}px;top:${y0.toFixed(1)}px"></div>
      <div class="me-month v" style="left:${padX}px;width:${(monthsW - F * 0.6).toFixed(1)}px;top:${y0.toFixed(1)}px;height:${mh.toFixed(1)}px">${esc(m.short)}</div>`;
  }).join("");
  const todayY = padY + todayPos(d) * trackH;
  const totalH = trackH + padY * 2;
  return `<div class="me-track v" style="height:${totalH.toFixed(1)}px">
    <svg class="me-stems" width="${w}" height="${totalH.toFixed(1)}" viewBox="0 0 ${w} ${totalH.toFixed(1)}" aria-hidden="true">${stems.join("")}</svg>
    ${parts.join("")}
    <div class="me-rule v" style="left:${ruleX}px;top:${padY}px;height:${trackH.toFixed(1)}px"></div>
    <div class="me-tick month v" style="left:${ruleX}px;top:${(padY + trackH).toFixed(1)}px"></div>
    ${months}
    <div class="me-today v" style="left:${ruleX}px;top:${todayY.toFixed(1)}px"></div>
  </div>`;
}

function evClass(it) {
  return `me-ev${it.isNext ? " next" : ""}${it.ev.past ? " past" : ""}${it.ev.visible ? "" : " faint"}`;
}

function todayPos(d) {
  const start = new Date(d.span.start + "T00:00:00");
  const today = new Date(d.today + "T00:00:00");
  const days = Math.round((today - start) / 86400000) + 0.5;
  return clamp(days / d.span.days, 0, 1);
}

function captionHtml(it, d, left, top, width) {
  const ev = it.ev;
  if (it.isNext) {
    const moon = ev.kind === "shower" && ev.moon
      ? moonSvg(ev.moon.frac, ev.moon.waxing, d.south, "box")
      : eclipseSvg(ev, "box");
    const [head, ...rest] = it.lines;
    return `<div class="me-next" style="left:${left.toFixed(1)}px;top:${top.toFixed(1)}px;width:${width.toFixed(1)}px">
      <div class="me-next-text">
        <div class="me-next-head">${esc(head)}</div>
        ${rest.filter(Boolean).map((l) => `<div class="me-next-line">${esc(l)}</div>`).join("")}
      </div>
      ${it.noMoon ? "" : `<div class="me-next-moon">${moon}</div>`}
    </div>`;
  }
  return `<div class="me-cap" style="left:${left.toFixed(1)}px;top:${top.toFixed(1)}px;width:${width.toFixed(1)}px">
    <div class="me-cap-1">${esc(it.lines[0])}</div>
    <div class="me-cap-2">${esc(it.lines[1])}</div>
  </div>`;
}

// ---------------------------------------------------------------- hero

function factRow(label, value) {
  return `<div class="me-fact"><span class="me-fact-l">${esc(label)}:</span> <span class="me-fact-v">${esc(value)}</span></div>`;
}

function heroHtml(d, ctx) {
  const compact = ctx.cell && ctx.cell.size === "sm";
  const ev = d.next != null ? d.events[d.next] : null;
  if (!ev) {
    return `<div class="me-hero"><div class="me-empty">Nothing coming up in the next year.</div></div>`;
  }
  const facts = [];
  let art;
  let moonBlock = "";
  if (ev.kind === "shower") {
    const r = ev.radiant || {};
    const m = ev.moon || {};
    art = burstSvg();
    facts.push(factRow("Peak night", ev.night));
    facts.push(factRow("Expected rate", `up to ${ev.zhr}${ev.variable ? " or more" : ""} an hour`));
    facts.push(factRow("Best viewing", r.rises ? (compact ? `${r.best}, ${r.words}` : `${r.best}, radiant ${r.words}`) : "radiant never rises here"));
    moonBlock = `<div class="me-hero-moon">
      ${moonSvg(m.frac, m.waxing, d.south, "hero")}
      <div class="me-hero-moon-t">${esc(m.note || "")}</div>
    </div>`;
  } else {
    art = `<div class="me-hero-ecl">${eclipseSvg(ev, "hero")}</div>`;
    facts.push(factRow("Date", `${ev.when}, ${ev.time} local`));
    if (ev.body === "lunar") {
      facts.push(factRow("From here", ev.visible ? `Moon ${ev.alt}° up at greatest eclipse` : "Moon below the horizon"));
      facts.push(factRow("Seen from", ev.region));
    } else {
      facts.push(factRow("From here", ev.visible ? `partial phases reach ${d.continent}` : "not visible"));
      facts.push(factRow(ev.path ? "Central line" : "Partial over", ev.path || ev.region));
    }
  }
  const up = (d.upcoming || []).map((u) => `<div class="me-up-row">${esc(u.name)} · ${esc(u.when)}${u.visible ? "" : " · not from here"}</div>`).join("");
  return `<div class="me-hero${ev.kind === "shower" ? " shower" : " eclipse"}">
    <div class="me-hero-eyebrow">Next · ${esc(daysWords(ev.days_to))}</div>
    <div class="me-hero-art">${art}<div class="me-hero-name"><span>${esc(ev.name)}</span></div></div>
    <div class="me-facts">${facts.join("")}</div>
    ${moonBlock}
    ${up ? `<div class="me-up"><div class="me-up-h">Upcoming events</div>${up}</div>` : ""}
  </div>`;
}

function tinyHtml(d) {
  const ev = d.next != null ? d.events[d.next] : null;
  if (!ev) return `<div class="me-tiny"><div class="me-tiny-n">Quiet sky</div></div>`;
  return `<div class="me-tiny">
    <div class="me-tiny-g">${glyphFor(ev, "")}</div>
    <div class="me-tiny-n">${esc(ev.name)}</div>
    <div class="me-tiny-d">${esc(daysWords(ev.days_to))}</div>
  </div>`;
}

// ---------------------------------------------------------------- render

export default async function render(shadow, ctx) {
  const d = ctx.data || {};
  const size = (ctx.cell && ctx.cell.size) || "md";
  const w = (ctx.cell && ctx.cell.w) || 640;
  const h = (ctx.cell && ctx.cell.h) || 400;
  const fragment = (ctx.cell && ctx.cell.fragment) || "";
  const head = `<link rel="stylesheet" href="/static/style/spectra-widgets.css">
    <link rel="stylesheet" href="/plugins/meteors_eclipses/client.css">`;

  if (d.error || !d.span) {
    shadow.innerHTML = `${head}<div class="me size-${size} err"><div class="me-err">
      <i class="ph-bold ph-warning-circle" aria-hidden="true"></i>
      <div>${esc(d.error || "No data yet.")}</div></div></div>`;
    return;
  }

  const base = Math.min(w, h);
  const G = Math.round(clamp(base * 0.09, 26, 60));
  const F = Math.round(clamp(base * 0.033, 11, 19) * 10) / 10;
  const layout = fragment === "next" ? "next" : fragment === "timeline" ? "timeline" : d.layout || "timeline";
  const title = d.title || "";
  const monthsLabel = d.span.months.length
    ? `${d.span.months[0].short} ${d.span.start.slice(0, 4)} to ${d.span.months[d.span.months.length - 1].short} ${new Date(d.span.end + "T00:00:00").getFullYear() - (d.span.end.endsWith("-01-01") ? 1 : 0)}`
    : "";
  const meta = [d.label, layout === "timeline" ? monthsLabel : ""].filter(Boolean).join(" · ");

  let body;
  let mode = layout;
  if (size === "xs") {
    mode = "tiny";
    body = tinyHtml(d);
  } else if (layout === "next") {
    body = heroHtml(d, ctx);
  } else {
    const portrait = h > w * 1.15;
    const headH = title ? F * (portrait ? 5 : 3.6) : F * 1.2;
    const footH = size === "lg" && h >= 600 ? F * 1.9 : 0;
    const trackH = h - headH - footH - F * 1.2;
    const events = d.events.filter((e) => e.in_span);
    body = events.length
      ? timelineHtml(d, ctx, { w, h, G, F, trackH })
      : `<div class="me-empty">Nothing ${d.only_visible ? "visible from here " : ""}in the next ${d.months} months.</div>`;
    if (footH) {
      const place = d.label ? ` from ${d.label}` : "";
      body += `<div class="me-foot">Radiant heights at 2 am and the Moon on each peak night${esc(place)}. Times are local.${d.show_eclipses ? " Solar eclipse visibility is by continent, roughly." : ""}</div>`;
    }
  }

  shadow.innerHTML = `${head}
    <div class="me size-${size} mode-${mode}${h > w * 1.15 ? " portrait" : ""}" style="--G:${G}px;--F:${F}px">
      ${mode === "tiny" ? "" : `<div class="me-head">
        ${title ? `<div class="me-title">${esc(title)}</div>` : ""}
        ${meta ? `<div class="me-meta">${esc(meta)}</div>` : ""}
      </div>`}
      ${body}
    </div>`;
}
