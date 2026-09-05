/* Turning a skyline into a sound, and back again.
 *
 * The screen is two panels stacked.
 *
 *   ABOVE, the wheel. The city's towers stand on the rim of a drum, in their
 *   true compass order from the height-weighted centre of the city, at their
 *   true heights in metres - and at equalised spacing, so the ring is full.
 *   The far side is drawn cooler: it is behind you. Turning moves you, not
 *   the city.
 *
 *   BELOW, the meter. The same ring reduced to 96 bars across the field of
 *   view, animated, with peak markers that fall back the way a real meter's
 *   do. The meter is what sounds.
 *
 * THE SOUND is invented - every part of it is a choice, and the sidebar and
 * skyline.html say so. Position across the view picks a note of the city's
 * chord; a tower's height as a share of the city's tallest, to the power
 * 1.6, sets how loud that note is; the seven loudest sound at once over a
 * drone an octave below the root. The notes come from the city's key, an
 * editorial choice with a source (keys.py), voiced per mode (VOICING below)
 * so that no two sounding notes are closer than a minor third and each mode
 * keeps the tone that makes it itself.
 *
 * There is no empty horizon on a wheel. Turning changes which notes are
 * loud; it never produces silence. A previous rendering - a true panorama
 * with occlusion and empty sky - was retired before the page shipped, and
 * its data was still being carried and described as this instrument's
 * measured behaviour until 2026-09-04.
 *
 * Audio is one oscillator per partial through one gain each, built once and
 * left running with the gains moved. Rebuilding an oscillator bank per frame
 * is how a Web Audio page ends up clicking.
 */
(function () {
  'use strict';

  var BARS = 96;
  var C = D.cities;

  var canvas = document.getElementById('c');
  var ctx = canvas.getContext('2d');
  var tip = document.getElementById('tip');

  /* There used to be a second rendering, "realistic", which sounded the
     whole mode over four octaves at the buildings' true angular spacing. It
     was the less pleasant of the two and nobody chose it, so the instrument
     is now only the musical one and the branches are gone rather than
     stranded behind a control that no longer exists. */
  var S = { i: 0, az: 0, fov: 100, vol: 0.55, playing: false, spin: 0 };

  // display state that eases towards the data, so the meter moves like a meter
  var lvl = new Float32Array(BARS);
  var pk = new Float32Array(BARS);
  var pkv = new Float32Array(BARS);

  function css(n) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(n).trim();
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch];
    });
  }
  function wrap(d) { return ((d % 360) + 360) % 360; }
  function delta(a, b) { return ((a - b + 540) % 360) - 180; }

  /* ------------------------------------------------------------ geometry -- */
  function bars() {
    var c = C[S.i], p = c.rprof;
    var n = p.length;
    var out = new Float32Array(BARS);
    var step = S.fov / BARS;
    for (var k = 0; k < BARS; k++) {
      var a0 = S.az - S.fov / 2 + k * step;
      var lo = Math.floor(a0), hi = Math.ceil(a0 + step);
      var m = 0;
      for (var i = lo; i <= hi; i++) {
        var v = p[((i % n) + n) % n];
        if (v > m) m = v;
      }
      out[k] = m;
    }
    return out;
  }

  var peakCache = {};
  function peak() {
    var ck = S.i;
    if (peakCache[ck] === undefined) {
      var p = C[S.i].rprof, m = 0;
      for (var i = 0; i < p.length; i++) if (p[i] > m) m = p[i];
      peakCache[ck] = m || 1;
    }
    return peakCache[ck];
  }

  /* --------------------------------------------------------------- audio -- */
  var actx = null, master = null, parts = [], rootHz = 110;
  var tilt = null, lpf = null;

  function rootFreq(pc) {
    /* A4 is 440 Hz and MIDI note 69. The root is placed in the octave below
       middle C, which is low enough to sound like a ground and high enough to
       leave four octaves of ladder above it. */
    var midi = 48 + pc;                 // C3 = 48
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  function buildAudio() {
    /* A closed context is not a usable one, and this used to read "if (actx)
       return true", which meant that once anything closed the context the
       button went on working and the instrument went on being silent for the
       rest of the page's life. A page put into the back-forward cache and
       then restored does exactly that. So a dead context is thrown away and
       built again rather than trusted because the variable is not null. */
    if (actx && actx.state === 'closed') {
      actx = null; master = null; parts = []; tilt = null; lpf = null;
    }
    if (actx) return true;
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) { noaudio('This browser did not offer Web Audio, so the ' +
                       'skyline is drawn but not played.');
               return false; }
    actx = new AC();
    master = actx.createGain();
    master.gain.value = 0;

    /* Four stages between the oscillators and your ears, and none of them are
       decoration. A bank of sines whose amplitudes are driven by a data set
       can, at some bearing in some city, line up: twenty partials at full
       tilt in the two-to-four kilohertz band where hearing is most sensitive
       and least forgiving. That is the sound of a smoke alarm, and no amount
       of tuning the mapping prevents it, because the mapping does not know
       what the ear finds painful.

       So it is made structurally impossible rather than avoided by taste. */

    // 1. a shelf that pulls down the band the ear is sharpest in
    tilt = actx.createBiquadFilter();
    tilt.type = 'highshelf'; tilt.frequency.value = 1800;
    tilt.gain.value = -9;

    // 2. a lowpass above which nothing useful lives here
    lpf = actx.createBiquadFilter();
    lpf.type = 'lowpass'; lpf.frequency.value = 3200; lpf.Q.value = 0.5;

    // 3. a limiter. Fast enough to catch a spin, slow enough not to pump.
    var comp = actx.createDynamicsCompressor();
    comp.threshold.value = -24; comp.knee.value = 12;
    comp.ratio.value = 20; comp.attack.value = 0.004;
    comp.release.value = 0.25;

    // 4. a fixed ceiling after it, so even a limiter overshoot cannot clip
    var ceiling = actx.createGain();
    ceiling.gain.value = 0.62;

    master.connect(tilt).connect(lpf).connect(comp).connect(ceiling)
          .connect(actx.destination);
    // enough oscillators for the widest scale in the set, seven notes over
    // four octaves; the unused ones sit silent rather than being rebuilt
    for (var k = 0; k < 28; k++) {
      var o = actx.createOscillator();
      o.type = k % 4 === 0 ? 'triangle' : 'sine';
      var g = actx.createGain();
      g.gain.value = 0;
      o.connect(g).connect(master);
      o.start();
      parts.push({ o: o, g: g, f: 0 });
    }
    return true;
  }

  /* Ninety-six bars is the right number to look at and the wrong number to
     play: four octaves of a five-note scale is twenty notes, so five or six
     adjacent bars land on the same pitch and would be five oscillators
     detuned by nothing, beating against each other. The bars are therefore
     mapped onto the distinct pitches of the scale, and a pitch takes the
     loudest bar that feeds it. Twenty-odd real partials, ninety-six bars,
     and no unison mud. */
  var pitch = [];      // frequency per partial
  var barTo = new Int16Array(BARS);

  /* Which notes of the mode sound. Until 2026-09-04 this was degrees 1, 3,
     5 and 6 of whatever the mode was, then a filter that dropped anything
     closer than a minor third to its neighbour. That filter took the
     flattened second out of hijaz and insen, the sixth out of major, and
     left eight modes sounding as five: Dubai in D hijaz was Vienna in
     D major, note for note.

     So the voicing is now chosen per mode, in semitones from the root, and
     chosen so the minor-third rule never fires: `ground` sounds in the
     lowest octave, `upper` in the two above it. The tone that makes a mode
     itself - hijaz's flattened second, insen's, the blues' flattened fifth -
     sits an octave up, where it colours the chord instead of clashing with
     the root beside it. A root an octave down is always added as a drone.
     `says` is what the sidebar tells the reader. All of this is invented. */
  var VOICING = {
    major:      { ground: [0, 4, 7],     upper: [0, 4, 7],
                  says: 'root, major third and fifth' },
    minor:      { ground: [0, 3, 7],     upper: [0, 3, 7],
                  says: 'root, minor third and fifth' },
    hijaz:      { ground: [0, 4, 7],     upper: [1, 4, 7],
                  says: 'root, major third and fifth; the flattened second ' +
                        'that makes it hijaz sits an octave up' },
    pent_major: { ground: [0, 4, 9],     upper: [0, 4, 9],
                  says: 'root, major third and sixth, with no fifth' },
    yo:         { ground: [0, 5, 9],     upper: [0, 5, 9],
                  says: 'root, fourth and sixth, with no third' },
    pent_minor: { ground: [0, 3, 7, 10], upper: [3, 7, 10],
                  says: 'root, minor third, fifth and flattened seventh' },
    blues:      { ground: [0, 3, 7, 10], upper: [3, 6, 10],
                  says: 'root, minor third, fifth and flattened seventh; ' +
                        'the blue flattened fifth sits an octave up' },
    insen:      { ground: [0, 5, 10],    upper: [1, 5, 10],
                  says: 'root, fourth and flattened seventh; the flattened ' +
                        'second that darkens it sits an octave up' }
  };
  var voicingClash = 0;   // how many notes the safety net removed; must stay 0

  function freqOf(k) {           // the pitch a given bar contributes to
    return pitch.length ? pitch[barTo[k]] : rootHz;
  }

  function setKey() {
    rootHz = rootFreq(C[S.i].key.pc);
    var st = C[S.i].key.steps;
    pitch = [];

    var vo = VOICING[C[S.i].key.mode] || VOICING.major;
    pitch.push(rootHz / 2);                      // the drone
    var gi, oc;
    for (gi = 0; gi < vo.ground.length; gi++) {
      pitch.push(rootHz * Math.pow(2, vo.ground[gi] / 12));
    }
    for (oc = 1; oc < 3; oc++) {
      for (gi = 0; gi < vo.upper.length; gi++) {
        var f = rootHz * Math.pow(2, oc + vo.upper[gi] / 12);
        if (f < 1500) pitch.push(f);             // nothing shrill, ever
      }
    }

    pitch.sort(function (a, b) { return a - b; });
    /* Nothing closer than a minor third. The voicings above are built so
       this never removes anything; it stays as the guarantee rather than
       the mechanism, and counts what it took out so the test can check. */
    var minSemi = 2.9;
    var clean = [];
    for (var q = 0; q < pitch.length; q++) {
      if (!clean.length ||
          12 * Math.log(pitch[q] / clean[clean.length - 1]) / Math.LN2
            >= minSemi) {
        clean.push(pitch[q]);
      } else {
        voicingClash++;
      }
    }
    pitch = clean;

    for (var k = 0; k < BARS; k++) {
      barTo[k] = Math.min(pitch.length - 1,
                          Math.floor(k / BARS * pitch.length));
    }
    if (lpf) {
      var tc = actx.currentTime;
      lpf.frequency.setTargetAtTime(2400, tc, .1);
      tilt.gain.setTargetAtTime(-12, tc, 0.1);
    }
    if (!actx) return;
    var t = actx.currentTime;
    for (var j = 0; j < parts.length; j++) {
      var f = pitch[j % pitch.length];
      parts[j].f = f;
      parts[j].o.frequency.setTargetAtTime(f, t, 0.03);
      if (j >= pitch.length) parts[j].g.gain.setTargetAtTime(0, t, 0.05);
    }
  }

  /* Which partials are sounding, from the meter's current levels. The
     audio and the text line under the meter both read this, so what a
     reader who cannot hear is told is exactly what is sent to the output. */
  var VOICES = 7;
  function sounding() {
    var mx = peak(), k;
    var acc = new Float32Array(Math.max(parts.length, pitch.length));
    for (k = 0; k < BARS; k++) {
      var j = barTo[k];
      var a = Math.pow(Math.min(1, lvl[k] / mx), 1.6);
      if (a > acc[j]) acc[j] = a;      // loudest bar wins the pitch
    }
    /* Voice limit. A bearing that lights every partial at once is a chord
       nobody wrote; keeping only the loudest few turns it back into a chord
       somebody might have. This is also the single most effective thing here
       against harshness, because harshness is mostly density. */
    var idx = [];
    for (var j3 = 0; j3 < pitch.length; j3++) idx.push(j3);
    idx.sort(function (p, q) { return acc[q] - acc[p]; });
    var keep = {};
    for (var v = 0; v < Math.min(VOICES, idx.length); v++) {
      if (acc[idx[v]] > 1e-4) keep[idx[v]] = 1;
    }
    return { acc: acc, keep: keep };
  }

  var NOTES_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A',
                     'A#', 'B'];
  var NOTES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A',
                    'Bb', 'B'];
  function noteName(f) {
    var midi = Math.round(69 + 12 * Math.log(f / 440) / Math.LN2);
    var key = C[S.i].key;
    var flats = /b/.test(key.root) || (!/#/.test(key.root) &&
      /^(minor|hijaz|insen|pent_minor|blues)$/.test(key.mode));
    var names = flats ? NOTES_FLAT : NOTES_SHARP;
    return names[((midi % 12) + 12) % 12] + (Math.floor(midi / 12) - 1);
  }
  var notesEl = document.getElementById('notes');
  var notesLast = '';
  /* The text form of the sound: the notes sounding now, lowest first. This
     is the path through the app for a reader who cannot hear - the meter is
     the same information as bars, this is it as names. Updated whenever the
     set changes, not every frame, so it does not flicker. */
  function notesLine() {
    var snd = sounding();
    var on = [];
    for (var j = 0; j < pitch.length; j++) if (snd.keep[j]) on.push(j);
    var names = on.map(function (j) { return noteName(pitch[j]); }).join(' ');
    var txt = !on.length ? (S.playing ? 'sounding nothing' : 'stopped')
      : (S.playing ? 'sounding ' : 'stopped \u00b7 would sound ') + names;
    if (txt !== notesLast) { notesLast = txt; notesEl.textContent = txt; }
  }

  function pushAudio() {
    if (!actx) return;
    var t = actx.currentTime;
    var snd = sounding(), acc = snd.acc, keep = snd.keep;

    /* Constant power, computed on the gains that are actually sent. The first
       version normalised the raw levels and then applied the one-over-root-j
       spectral tilt afterwards, which un-did the normalisation: a bearing
       lighting only low partials came out several times louder than one
       lighting only high ones, and turning became a volume ride of fourteen
       to one. Tilt first, normalise second. */
    var want = new Float32Array(parts.length);
    var sum = 0;
    for (var j4 = 0; j4 < pitch.length; j4++) {
      if (!keep[j4]) continue;
      // the ear expects an instrument to lose energy with height; a flat
      // spectrum is the definition of a buzz
      want[j4] = acc[j4] / Math.sqrt(j4 * 0.5 + 1);
      sum += want[j4] * want[j4];
    }
    var norm = sum > 0 ? 0.46 / Math.sqrt(sum) : 0;

    var slew = 0.22;                 // a pad, not a plucked thing
    for (var j2 = 0; j2 < parts.length; j2++) {
      parts[j2].g.gain.setTargetAtTime(want[j2] * norm, t, slew);
    }
    master.gain.setTargetAtTime(S.playing ? S.vol * 0.8 : 0, t, 0.12);
  }

  /* --------------------------------------------------------------- draw -- */
  var dpr = 1, W = 1, H = 1;
  function resize() {
    var r = canvas.getBoundingClientRect();
    dpr = Math.min(2, window.devicePixelRatio || 1);
    W = canvas.width = Math.max(1, Math.round(r.width * dpr));
    H = canvas.height = Math.max(1, Math.round(r.height * dpr));
  }

  function xOf(az) {
    // where a bearing lands across the panel, given the current view window
    return PAD + (0.5 + delta(az, S.az) / S.fov) * (W - PAD * 2);
  }

  var PAD = 0;
  function draw() {
    PAD = 26 * dpr;
    var c = C[S.i];
    var acc = css('--acc'), cool = css('--cool'), dim = css('--dim');
    var rule = css('--rule'), ink = css('--ink');

    ctx.clearRect(0, 0, W, H);

    var splitY = Math.round(H * 0.56);          // horizon of the city panel
    var eqTop = splitY + 46 * dpr;
    var eqBase = H - 30 * dpr;
    var mx = peak();

    /* ---- the wheel ---------------------------------------------------- */
    /* A cylinder seen from slightly above and outside, the way a reverb room
       or a rotary control is drawn. Each building is a stave standing on the
       rim. Screen position comes from the sine of its angle, depth from the
       cosine: front-centre is nearest the viewer and lowest on screen, and
       the far side rides higher and dimmer, which is what makes a flat ring
       read as a solid. Drawn back to front so near towers occlude far ones
       for free. */
    var i;
    var cx = W / 2;
    var Rx = (W - PAD * 2) * 0.40;
    var Ry = Math.min(Rx * 0.17, 74 * dpr);
    /* The near rim has to clear the divider. Placing the ellipse centre a
       fixed distance above it let the front of the wheel - which is half an
       ellipse lower than the centre - hang down over the meter. Anchor the
       bottom of the ellipse instead, and the whole drum stays in its own
       panel however wide the window gets. */
    var cyc = splitY - Ry - 16 * dpr;
    /* The wheel is scaled by real height in metres, not by apparent angle.
       Angle was the bug that made this panel look empty: from the middle of a
       downtown the nearest tower is a hundred metres away and subtends nearly
       eighty degrees, so it set the scale and squashed every other building
       in the city to a hairline. Metres are what "the hundred tallest" means
       anyway, and distance still shows, through perspective. */
    var hmax = 1;
    for (i = 0; i < c.ring.length; i++)
      if (c.ring[i][3] > hmax) hmax = c.ring[i][3];
    var vscale = (splitY - 78 * dpr) / hmax;

    var ring = c.ring;
    var order = [];
    for (i = 0; i < ring.length; i++) {
      // the equalised slot, not the true bearing
      var ang = ring[i][0];
      var ph = (ang - S.az) * Math.PI / 180;
      order.push({ b: ring[i], s: Math.sin(ph), z: Math.cos(ph) });
    }
    order.sort(function (p, q) { return p.z - q.z; });   // far side first

    // the rim, so the ring reads as a ring even where towers are short
    ctx.strokeStyle = rule; ctx.lineWidth = 1 * dpr;
    ctx.beginPath();
    for (i = 0; i <= 96; i++) {
      var a2 = i / 96 * Math.PI * 2;
      var rx = cx + Rx * Math.sin(a2), ry = cyc + Ry * Math.cos(a2);
      if (i) ctx.lineTo(rx, ry); else ctx.moveTo(rx, ry);
    }
    ctx.stroke();

    for (i = 0; i < order.length; i++) {
      var o = order[i], bb = o.b;
      var front = (o.z + 1) / 2;                 // 0 at the back, 1 at the front
      var px = cx + Rx * o.s;
      var py = cyc + Ry * o.z;
      var persp = 0.70 + 0.30 * front;           // near towers stand taller
      var bh = bb[3] * vscale * persp;
      if (bh < 1) bh = 1;
      var wpx = Math.max(1.6 * dpr, (Rx * 2 * Math.PI / ring.length) * 0.42 *
                         Math.abs(Math.cos(o.s * 0.6)) * persp);

      // the back half is a darker, cooler colour: it is behind you
      ctx.globalAlpha = 0.22 + 0.72 * front;
      ctx.fillStyle = o.z >= 0 ? acc : cool;
      ctx.fillRect(px - wpx / 2, py - bh, wpx, bh);
      ctx.globalAlpha = 0.30 + 0.70 * front;
      ctx.fillStyle = o.z >= 0 ? ink : dim;
      ctx.fillRect(px - wpx / 2, py - bh, wpx, 1.3 * dpr);
    }
    ctx.globalAlpha = 1;

    /* No separate near-rim overlay. An earlier build stroked the front of
       the drum in the accent colour here, with sin and cos swapped, which
       drew a bright arc up the right-hand side of the wheel instead of along
       its front edge. The single quiet rim above already closes the ring,
       and it looks the same from every side, which is the point of a drum. */

    // a compass ring under it, so turning still reads as turning
    ctx.fillStyle = dim;
    ctx.font = (12 * dpr) + 'px ui-sans-serif, system-ui, sans-serif';
    ctx.textAlign = 'center';
    for (var d2 = 0; d2 < 360; d2 += 45) {
      var ph2 = (d2 - S.az) * Math.PI / 180;
      if (Math.cos(ph2) < -0.15) continue;         // behind the drum
      // never below 0.8: at 0.35 the side points were 1.8:1 against the stage
      ctx.globalAlpha = 0.8 + 0.2 * (Math.cos(ph2) + 1) / 2;
      ctx.fillText(compass(d2), cx + Rx * 1.10 * Math.sin(ph2),
                   cyc + Ry * 1.10 * Math.cos(ph2) + 20 * dpr);
    }
    ctx.globalAlpha = 1;

    /* ---- the analyser ------------------------------------------------ */
    var bw = (W - PAD * 2) / BARS;
    var eqH = eqBase - eqTop;
    var grad = ctx.createLinearGradient(0, eqBase, 0, eqTop);
    grad.addColorStop(0, cool);
    grad.addColorStop(1, acc);

    for (var k = 0; k < BARS; k++) {
      var v = Math.min(1, lvl[k] / mx);
      var x = PAD + k * bw;
      var bh = v * eqH;
      if (bh > 0.6) {
        ctx.fillStyle = grad;
        ctx.globalAlpha = 0.35 + 0.65 * v;
        ctx.fillRect(x + bw * 0.14, eqBase - bh, bw * 0.72, bh);
      }
      // peak marker, falling back under its own weight
      var ph = Math.min(1, pk[k] / mx) * eqH;
      if (ph > 1.5) {
        ctx.globalAlpha = 0.75;
        ctx.fillStyle = acc;
        ctx.fillRect(x + bw * 0.14, eqBase - ph - 2 * dpr, bw * 0.72,
                     1.6 * dpr);
      }
    }
    ctx.globalAlpha = 1;
    ctx.strokeStyle = rule;
    ctx.beginPath();
    ctx.moveTo(PAD, eqBase + 0.5); ctx.lineTo(W - PAD, eqBase + 0.5);
    ctx.stroke();

    // the towers worth naming, labelled in place, biggest first and dropped
    // rather than stacked when they collide
    /* Names ran into each other before, because the test for a collision
       used the width of the label being placed against the *centres* of the
       ones already down, and the clamp that keeps a name on the canvas ran
       after the test rather than before it. Two long names near an edge both
       got clamped inward and printed on top of one another. Widths are now
       measured rather than guessed from the character count, the clamp runs
       first, and two labels clash when their boxes overlap. */
    ctx.textAlign = 'center';
    var fpx = 12 * dpr;                     // the site's floor, on a phone too
    ctx.font = fpx + 'px ui-sans-serif, system-ui, sans-serif';
    var maxLabels = W < 560 * dpr ? 3 : (W < 900 * dpr ? 4 : 6);
    var gap = 14 * dpr;
    var placed = [];
    // the tallest towers on the near face of the wheel, biggest first
    var seen = ring.slice().filter(function (r) {
      return r[4] && Math.cos((r[0] - S.az) * Math.PI / 180) > 0.25;
    }).sort(function (p, q) { return q[3] - p[3]; }).slice(0, 12);
    for (i = 0; i < seen.length && placed.length < maxLabels; i++) {
      var nm = seen[i][4];
      var half = ctx.measureText(nm).width / 2;
      if (half * 2 > W - 8 * dpr) continue;         // no room for it at all
      var tx = cx + Rx * Math.sin((seen[i][0] - S.az) * Math.PI / 180);
      tx = Math.min(W - half - 4 * dpr, Math.max(half + 4 * dpr, tx));
      var clash = false;
      for (var j = 0; j < placed.length; j++) {
        if (Math.abs(tx - placed[j].x) < half + placed[j].half + gap) {
          clash = true; break;
        }
      }
      if (clash) continue;
      placed.push({ x: tx, half: half });
      ctx.fillStyle = dim;
      ctx.fillText(nm, tx, splitY + 18 * dpr);
    }
  }

  function compass(d) {
    var n = { 0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 180: 'S', 225: 'SW',
              270: 'W', 315: 'NW' };
    return n[d] || (d + '°');
  }

  /* ---------------------------------------------------------------- loop -- */
  /* The meter is animated, so unlike the other scenes on this site this one
     genuinely does have something to draw every frame - but only while it is
     still settling or the observer is moving. Once the bars have caught up and
     the peaks have fallen, it stops. */
  var last = 0;
  function frame(ts) {
    requestAnimationFrame(frame);
    var dt = Math.min(0.05, (ts - last) / 1000 || 0.016);
    last = ts;

    if (S.spin) { S.az += S.spin * dt * 22; panelSoon(); }

    var b = bars(), moved = false, k;
    for (k = 0; k < BARS; k++) {
      var target = b[k];
      if (motionOff) {
        /* Reduced motion: the meter is a reading, not an animation. Bars
           take their value at once and the peak markers sit on the bars
           rather than falling. Turning still redraws - that is the reader's
           own hand - and the sound is untouched, because a preference for
           less motion is not a preference for less sound. */
        if (Math.abs(target - lvl[k]) > 1e-4) moved = true;
        lvl[k] = target; pk[k] = target; pkv[k] = 0;
        continue;
      }
      // fast attack, slow release: the shape of every meter ever built
      var rate = target > lvl[k] ? 16 : 5;
      var nv = lvl[k] + (target - lvl[k]) * Math.min(1, rate * dt);
      if (Math.abs(nv - lvl[k]) > 1e-4) moved = true;
      lvl[k] = nv;

      if (lvl[k] >= pk[k]) { pk[k] = lvl[k]; pkv[k] = 0; }
      else { pkv[k] += 9 * dt; pk[k] -= pkv[k] * dt; moved = true; }
      if (pk[k] < 0) pk[k] = 0;
    }
    if (!moved && !S.spin && !dirty) return;
    dirty = false;
    draw();
    pushAudio();
    notesLine();
  }
  var dirty = true;
  function touch() { dirty = true; }

  /* The motion contract. <html data-motion> is set before first paint by the
     snippet in the head, from prefers-reduced-motion alone, and flips with a
     "motionchange" event if the preference changes while the page is open.
     Off means: no easing, no falling peaks, and no Spin - Spin is the one
     thing here that moves without a hand on it. Drag, wheel and arrows keep
     working. Audio is not gated by this; Play and Stop are the audio gate. */
  var motionOff = false;
  function readMotion() {
    motionOff = document.documentElement.dataset.motion === 'off';
    if (motionOff && S.spin) { S.spin = 0; spinBtn.classList.remove('on'); }
    spinBtn.hidden = motionOff;
    touch();
  }
  document.addEventListener('motionchange', readMotion);

  /* ------------------------------------------------------------- panel -- */
  var panelPending = false;
  function panelSoon() {
    if (panelPending) return;
    panelPending = true;
    setTimeout(function () { panelPending = false; panel(); }, 90);
  }

  function panel() {
    var c = C[S.i];
    document.getElementById('stats').innerHTML =
      '<dt>Key</dt><dd>' + esc(c.key.label) + '</dd>' +
      '<dt>Towers</dt><dd>' + c.n + ' at or above ' +
        D.minHeight.toFixed(0) + ' m</dd>' +
      '<dt>Tallest</dt><dd>' + c.tallest.toFixed(0) + ' m' +
        (c.tallestName ? ' &middot; ' + esc(c.tallestName) : '') + '</dd>' +
      '<dt>Median</dt><dd>' + c.median.toFixed(0) + ' m</dd>' +
      '<dt>On the wheel</dt><dd>' + c.ring.length + ' at or above ' +
        D.ringFloor.toFixed(0) + ' m</dd>' +
      '<dt>Standing</dt><dd>at the height-weighted centre of them</dd>' +
      '<dt>Heights</dt><dd>' + (c.hand
        ? c.hand + ' of ' + c.ring.length + ' from the city&rsquo;s published ' +
          'tallest-buildings list (Wikipedia); above ' + c.listFloor +
          ' m the list overrules Wikidata' + (c.ring.length > c.hand
            ? ', the other ' + (c.ring.length - c.hand) + ' from Wikidata'
            : '')
        : 'Wikidata, each tower linked below') + '</dd>';

    document.getElementById('why').innerHTML =
      '<b>' + esc(c.key.label) + '</b>, from ' + esc(c.key.why) + '. ' +
      '<span class="tier">' + c.key.tier.toLowerCase() + '</span>';
    var vo = VOICING[c.key.mode] || VOICING.major;
    document.getElementById('voice').textContent =
      'Voiced as ' + vo.says + ', over a drone an octave below the root. ' +
      'A choice, like the key.';

    /* The list is the wheel, in the order it is drawn, with whatever is
       currently on the near face marked. It used to be the twenty tallest in
       true-bearing order, which no longer matched anything on screen. */
    var named = c.ring.filter(function (r) { return r[4]; })
                 .sort(function (p, q) { return q[3] - p[3]; }).slice(0, 40);
    document.getElementById('towers').innerHTML = named.map(function (r) {
      var front = Math.cos((r[0] - S.az) * Math.PI / 180) > 0;
      /* A building links to the record it came from where there is one.
         The hand-entered supplements have no entity, so they are plain text
         rather than a link that goes nowhere. */
      var label = r[7]
        ? '<a href="https://www.wikidata.org/wiki/' + esc(r[7]) +
          '" target="_blank" rel="noopener">' + esc(r[4]) + '</a>'
        : esc(r[4]);
      return '<li' + (front ? ' class="in"' : '') + '><b>' + label +
             '</b> <span>' + r[3].toFixed(0) + ' m' +
             (r[5] ? ' &middot; ' + r[5] : '') + ' &middot; ' +
             compass(Math.round(r[6] / 45) * 45 % 360) + ' of centre' +
             (front ? '' : ' &middot; behind you') + '</span></li>';
    }).join('') || '<li>no named towers in this city</li>';

    document.getElementById('az').textContent =
      'bearing ' + Math.round(wrap(S.az)) + '°  ·  ' + S.fov +
      '° wide';
  }

  /* ------------------------------------------------------------ events -- */
  var drag = null;
  canvas.addEventListener('pointerdown', function (e) {
    drag = { x: e.clientX, az: S.az };
    S.spin = 0; spinBtn.classList.remove('on');
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', function (e) {
    if (drag) {
      var r = canvas.getBoundingClientRect();
      S.az = drag.az - (e.clientX - drag.x) / r.width * S.fov;
      touch(); panelSoon();
      return;
    }
    hover(e);
  });
  canvas.addEventListener('pointerup', function () { drag = null; });
  canvas.addEventListener('pointerleave', function () {
    drag = null; tip.style.display = 'none';
  });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    S.az += Math.sign(e.deltaY) * 4;
    touch(); panelSoon();
  }, { passive: false });

  function hover(e) {
    var r = canvas.getBoundingClientRect();
    var f = (e.clientX - r.left) / r.width;
    var az = S.az - S.fov / 2 + f * S.fov;
    var c = C[S.i], near = null, best = 6.0;
    c.ring.forEach(function (b) {
      var off = Math.abs(delta(b[0], az));
      if (off < best && b[4]) { best = off; near = b; }
    });
    if (!near) { tip.style.display = 'none'; return; }
    tip.innerHTML = '<b>' + esc(near[4]) + '</b><br>' + near[3].toFixed(0) +
                    ' m &middot; ' + (near[2] <= 0.4 ? 'under 0.4' :
                                      near[2].toFixed(1)) +
                    ' km from the centre' +
                    (near[5] ? ' &middot; ' + near[5] : '');
    tip.style.display = 'block';
    tip.style.left = Math.min(r.width - tip.offsetWidth - 8,
                              Math.max(4, e.clientX - r.left + 14)) + 'px';
    tip.style.top = Math.max(4, e.clientY - r.top - 46) + 'px';
  }

  window.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (tag === 'SELECT' || tag === 'INPUT' || tag === 'BUTTON') return;
    var step = e.shiftKey ? 15 : 3;
    if (e.key === 'ArrowLeft') S.az -= step;
    else if (e.key === 'ArrowRight') S.az += step;
    else if (e.key === ' ') { if (!motionOff) spinBtn.click(); }
    else return;
    e.preventDefault();
    touch(); panelSoon();
  });

  document.getElementById('city').addEventListener('change', function () {
    S.i = +this.value;
    S.az = C[S.i].look;
    lvl.fill(0); pk.fill(0); pkv.fill(0);
    setKey(); touch(); panel();
  });
  document.getElementById('fov').addEventListener('input', function () {
    S.fov = +this.value; touch(); panelSoon();
  });
  document.getElementById('vol').addEventListener('input', function () {
    S.vol = +this.value / 100; pushAudio();
  });

  var playBtn = document.getElementById('play');

  /* One place that stops the sound, so leaving the page, hiding the tab and
     pressing Stop all take the same route. The gain is set straight to zero
     rather than eased, because an eased stop that is still running when the
     page goes into the background carries on in a tab nobody is looking at. */
  var noaudioEl = document.getElementById('noaudio');
  function noaudio(msg) {
    noaudioEl.textContent = msg || '';
    noaudioEl.style.display = msg ? 'block' : 'none';
  }

  function silence() {
    S.playing = false;
    noaudio('');
    notesLine();
    playBtn.textContent = 'Play';
    playBtn.classList.remove('on');
    if (master) {
      try { master.gain.cancelScheduledValues(actx.currentTime); } catch (e) {}
      master.gain.value = 0;
    }
    if (actx && actx.state === 'running' && actx.suspend) {
      try { actx.suspend(); } catch (e) {}
    }
  }

  playBtn.addEventListener('click', function () {
    if (!S.playing) {
      if (!buildAudio()) return;
      setKey();
      if (actx.state === 'suspended') actx.resume();
      S.playing = true;
      playBtn.textContent = 'Stop';
      playBtn.classList.add('on');
      pushAudio();
      notesLine();
      /* A context that will not run - a phone on mute, a machine with no
         output - used to leave the button saying Stop over a dancing meter
         and nothing else. The API cannot see a mute switch, so this only
         catches what it can see; the line under the meter carries the rest. */
      setTimeout(function () {
        if (S.playing && actx && actx.state !== 'running') {
          noaudio('Play is on, but the browser reports no running audio ' +
                  'output. Check the mute switch or the output device; the ' +
                  'notes sounding are named under the meter.');
        }
      }, 800);
    } else {
      silence();
    }
  });

  /* A browser tab keeps running when it is not on screen, and a tab quietly
     playing a chord behind whatever the reader moved on to is the worst kind
     of bug to track down. Hiding the tab stops it; coming back leaves it
     stopped, because restarting an instrument nobody asked to restart is its
     own annoyance. pagehide covers the back button and the phone browsers
     that never fire unload. */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden && S.playing) silence();
  });
  window.addEventListener('pagehide', function (e) {
    silence();
    /* Closing the context frees the audio thread, but only when the page is
       actually going away. e.persisted means it is going into the
       back-forward cache and may come back, and a context closed on the way
       out is still closed on the way in. */
    if (!e.persisted && actx && actx.close) {
      try { actx.close(); } catch (err) {}
    }
  });

  var spinBtn = document.getElementById('spin');
  spinBtn.addEventListener('click', function () {
    S.spin = S.spin ? 0 : 1;
    spinBtn.classList.toggle('on', !!S.spin);
    touch();
  });

  var ro = window.ResizeObserver ? new ResizeObserver(function () {
    resize(); touch();
  }) : null;
  if (ro) ro.observe(document.getElementById('stage'));
  window.addEventListener('resize', function () { resize(); touch(); });

  /* --------------------------------------------------------------- boot -- */
  document.getElementById('city').innerHTML = C.map(function (c, i) {
    return '<option value="' + i + '">' + esc(c.city) + ' &middot; ' +
           esc(c.key.label) + '</option>';
  }).join('');
  S.az = C[0].look;
  setKey();
  resize();
  readMotion();
  panel();
  requestAnimationFrame(frame);

  window.__sky = {
    S: S, cities: C, bars: bars, peak: peak, freqOf: freqOf, setKey: setKey,
    // for the test harness: whether anything is actually reaching the output,
    // rather than whether the button thinks it is
    audio: function () {
      return { state: actx ? actx.state : 'none',
               gain: master ? master.gain.value : 0 };
    },
    root: function () { return rootHz; }, draw: draw, panel: panel,
    pitches: function () { return pitch; },
    voicing: VOICING, clashes: function () { return voicingClash; },
    motionOff: function () { return motionOff; },
    notes: function () { return notesLast; },
    barOf: function (k) { return barTo[k]; },
    levels: function () { return lvl; }, BARS: BARS,
    step: function (dt) {                      // for the test harness
      var b = bars();
      for (var k = 0; k < BARS; k++) {
        if (motionOff) { lvl[k] = pk[k] = b[k]; continue; }
        var rate = b[k] > lvl[k] ? 16 : 5;
        lvl[k] += (b[k] - lvl[k]) * Math.min(1, rate * dt);
        if (lvl[k] >= pk[k]) { pk[k] = lvl[k]; pkv[k] = 0; }
        else { pkv[k] += 9 * dt; pk[k] = Math.max(0, pk[k] - pkv[k] * dt); }
      }
    }
  };
})();
