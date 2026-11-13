/* scales.js - grows the mass / power-per-kilogram chart on scales.html as the reader scrolls (2026-11-13).
 *
 * Markup (written by scales/update_page.py):
 *   <figure class="ladder wide">
 *     <div class="ladder-fig"> two SVGs (.plot-wide, .plot-phone) whose layers
 *       carry data-o, the step they belong to (0 life .. 5 stars) </div>
 *     <div class="ladder-steps"> <div class="step" data-step="k"> ... </div> ... </div>
 *   </figure>
 *
 * The page is complete without this file: every layer shows. With motion on
 * (assets/motion.js), the figure sticks and the step whose card crosses the
 * middle of the screen decides how many layers show. Layers of a later step
 * get .off; the current step's layers get .now. With motion off, or on
 * "motionchange" to off, it tears down. The pattern is chain.js's (oxygen.html).
 */
(function () {
  'use strict';
  var root = document.documentElement;
  if (!('IntersectionObserver' in window)) return;
  function motionOn() { return root.dataset.motion !== 'off'; }

  function Ladder(sec) {
    var self = this;
    this.sec = sec;
    this.els = [].slice.call(sec.querySelectorAll('.plot [data-o]'));
    this.steps = [].slice.call(sec.querySelectorAll('.step[data-step]'));
    this.cur = 0;
    this.live = false;
    this.io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) self.set(+e.target.getAttribute('data-step'));
      });
    }, { rootMargin: '-50% 0px -49% 0px' });
  }
  Ladder.prototype.set = function (k) {
    this.cur = k;
    if (!this.live) return;
    this.els.forEach(function (el) {
      var o = +el.getAttribute('data-o');
      el.classList.toggle('off', o > k);
      el.classList.toggle('now', o === k);
    });
  };
  Ladder.prototype.start = function () {
    if (this.live) return;
    this.live = true;
    this.sec.classList.add('is-live');
    var io = this.io;
    this.steps.forEach(function (s) { io.observe(s); });
    // before any card reaches the middle, show what is above the reader
    var mid = window.innerHeight / 2, k = 0;
    this.steps.forEach(function (s) { if (s.getBoundingClientRect().top < mid) k = +s.getAttribute('data-step'); });
    this.set(k);
  };
  Ladder.prototype.stop = function () {
    if (!this.live) return;
    this.live = false;
    this.io.disconnect();
    this.sec.classList.remove('is-live');
    this.els.forEach(function (el) { el.classList.remove('off', 'now'); });
  };

  var all = [].slice.call(document.querySelectorAll('figure.ladder')).map(function (s) { return new Ladder(s); });
  function sync() { all.forEach(function (c) { if (motionOn()) c.start(); else c.stop(); }); }
  document.addEventListener('motionchange', sync);
  sync();
  window.__ladder = all;   // test hook
}());
