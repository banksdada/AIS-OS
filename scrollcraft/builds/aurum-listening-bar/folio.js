(function () {
  const numEl = document.getElementById('folioNum');
  const titleEl = document.getElementById('folioTitle');
  const barsWrap = document.getElementById('folioBars');
  const traceEl = document.getElementById('folioTrace');
  if (!numEl || !titleEl || !barsWrap || !traceEl) return;

  const bars = Array.from(barsWrap.querySelectorAll('span'));
  const chapters = Array.from(document.querySelectorAll('[data-chapter]'))
    .filter(el => /^\d+$/.test(el.dataset.chapter || ''));
  const seen = new Set();

  let lastY = window.scrollY;
  let lastT = performance.now();
  let velocity = 0;
  let raf = null;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function stamp(ch, progress) {
    if (seen.has(ch)) return;
    seen.add(ch);
    const mark = document.createElement('span');
    mark.className = 'groove';
    mark.style.top = Math.max(2, Math.min(98, progress * 100)) + '%';
    mark.title = 'Chapter ' + String(ch).padStart(2, '0');
    traceEl.appendChild(mark);
  }

  function updateChapter() {
    const mid = window.scrollY + window.innerHeight * 0.45;
    let current = chapters[0];
    for (const el of chapters) {
      const top = el.getBoundingClientRect().top + window.scrollY;
      if (top <= mid) current = el;
    }
    if (current) {
      const ch = current.dataset.chapter;
      const title = current.dataset.title || '';
      numEl.textContent = String(ch).padStart(2, '0');
      titleEl.textContent = title;
      const doc = document.documentElement;
      const max = Math.max(1, doc.scrollHeight - window.innerHeight);
      stamp(ch, (elTop(current) / max));
    }
  }
  function elTop(el){ return el.getBoundingClientRect().top + window.scrollY; }

  function renderBars() {
    raf = null;
    const v = Math.min(1, Math.abs(velocity) / 18);
    const t = performance.now() / 1000;
    bars.forEach((b, i) => {
      if (reduce) { b.style.height = '22%'; return; }
      const phase = t * (1.2 + i * 0.35) + i * 0.9;
      const base = 0.16 + 0.12 * (0.5 + 0.5 * Math.sin(phase));
      const react = v * (0.35 + 0.55 * Math.abs(Math.sin(phase * 1.7 + i)));
      const h = Math.max(12, Math.min(100, (base + react) * 100));
      b.style.height = h.toFixed(1) + '%';
    });
    velocity *= 0.85;
    if (!reduce && (Math.abs(velocity) > 0.02 || Math.random() < 0.3)) {
      raf = requestAnimationFrame(renderBars);
    } else if (!reduce) {
      raf = requestAnimationFrame(renderBars); // keep gentle idle motion
    }
  }

  function onScroll() {
    const y = window.scrollY;
    const t = performance.now();
    const dt = Math.max(16, t - lastT);
    velocity = velocity * 0.6 + ((y - lastY) / dt) * 12 * 0.4;
    lastY = y; lastT = t;
    updateChapter();
    if (!raf) raf = requestAnimationFrame(renderBars);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', updateChapter);
  updateChapter();
  if (!reduce) raf = requestAnimationFrame(renderBars); else bars.forEach(b => b.style.height = '22%');

  window.AurumFolio = { mount: function(){} };
})();
