(function () {
  var d = document.documentElement;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var each = function (sel, fn) { Array.prototype.forEach.call(document.querySelectorAll(sel), fn); };

  // mobile menu
  var burger = document.querySelector('.burger');
  function setMenu(open) {
    d.classList.toggle('menu-open', open);
    if (burger) burger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (burger) {
    burger.addEventListener('click', function () { setMenu(!d.classList.contains('menu-open')); });
    each('.sheet a', function (a) { a.addEventListener('click', function () { setMenu(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 820) setMenu(false); });
  }

  // scroll progress line + hero mark drift
  var bar = document.querySelector('.progress');
  var mark = document.querySelector('.hero-mark');
  var queued = false;
  function onScroll() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      var y = window.scrollY, h = d.scrollHeight - window.innerHeight;
      if (bar) bar.style.transform = 'scaleX(' + (h > 0 ? Math.min(1, y / h) : 0) + ')';
      if (mark && !still && y < window.innerHeight * 1.5) mark.style.setProperty('--sy', y);
      queued = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // the mark leans away from the pointer on devices that have one
  var hero = document.querySelector('.hero');
  if (hero && mark && !still && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect();
      mark.style.setProperty('--mx', ((e.clientX - r.left) / r.width - 0.5).toFixed(3));
      mark.style.setProperty('--my', ((e.clientY - r.top) / r.height - 0.5).toFixed(3));
    });
    hero.addEventListener('pointerleave', function () {
      mark.style.setProperty('--mx', 0);
      mark.style.setProperty('--my', 0);
    });
  }

  if (!('IntersectionObserver' in window)) { each('.steps li', function (li) { li.classList.add('on'); }); return; }

  // the three steps fill in as they reach the middle of the screen
  var steps = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('on'); steps.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -30% 0px', threshold: 0.4 });
  each('.steps li', function (li) { steps.observe(li); });

  if (still) return;

  // count the stat numbers up when they scroll into view
  var counter = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      counter.unobserve(e.target);
      var el = e.target, end = +el.getAttribute('data-count'), t0 = null;
      requestAnimationFrame(function step(t) {
        if (!t0) t0 = t;
        var p = Math.min(1, (t - t0) / 900);
        el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step); else el.textContent = end;
      });
    });
  }, { threshold: 0.6 });
  each('[data-count]', function (el) { counter.observe(el); });

  // reveal on scroll: only for what starts below the first screen, so the page is complete on load
  d.classList.add('js');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('in');
      io.unobserve(e.target);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  var sel = '.section-head, .sell-card, .steps li, .stat, .quote, .stock-card, .empty, .sold li, .next article, .road li, .term, .faq details, .cta > *, .prose > *, .panel';
  each(sel, function (el) {
    if (el.getBoundingClientRect().top < window.innerHeight) return;
    var i = Array.prototype.indexOf.call(el.parentNode.children, el);
    el.classList.add('reveal');
    el.style.transitionDelay = Math.min(i, 5) * 70 + 'ms';
    el.addEventListener('transitionend', function done(ev) {
      if (ev.propertyName !== 'transform') return;
      el.removeEventListener('transitionend', done);
      el.style.transitionDelay = '';
      el.classList.remove('reveal', 'in');
    });
    io.observe(el);
  });
})();
