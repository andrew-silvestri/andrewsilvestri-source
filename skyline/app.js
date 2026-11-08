/* Turning a skyline into a sound, and back again.
 *
 * The screen is two panels stacked.
 *
 *   ABOVE, the stage. The city's towers stand around you as seen from the
 *   height-weighted centre of the city, unrolled across the screen: in
 *   their true compass order, at their true heights in metres, each in its
 *   true outline as seen along the line from the centre (build_massing.py)
 *   - and at equalised spacing, so the ring is full. A small map in the
 *   corner shows the same towers at their true bearings and distances, with
 *   the view as a wedge. Turning moves you, not the city. (Until 2026-11-07
 *   this panel was a drum seen from outside, each tower a bar.)
 *
 *   BELOW, the meter. The same ring reduced to 96 bars across the field of
 *   view, animated, with peak markers that fall back the way a real meter's
 *   do. The meter is what sounds.
 *
 * THE SOUND is invented - every part of it is a choice, and the sidebar and
 * skyline.html say so. Position across the view picks a note of the city's
 * chord; a tower's height as a share of the city's tallest, to the power
 * 1.6, sets how loud that note is; the seven loudest sound at once over a
 * root an octave down as the lowest note. The notes come from the city's key, an
 * editorial choice with a source (keys.py), voiced per mode (VOICING below)
 * so that no two sounding notes are closer than a minor third and each mode
 * keeps the tone that makes it itself.
 *
 * There is no empty horizon on a wheel. Turning changes which notes are
 * loud; it never produces silence. The stage keeps the wheel's equalised
 * slots for exactly that reason. A previous rendering - a true panorama at
 * true angular spacing, with occlusion and empty sky - was retired before
 * the page shipped, and
 * its data was still being carried and described as this instrument's
 * measured behavior until 2026-09-04.
 *
 * Audio is one oscillator per partial through one gain each, built once and
 * left running with the gains moved. Rebuilding an oscillator bank per frame
 * is how a Web Audio page ends up clicking.
 */
(function () {
  'use strict';

  var BARS = 96;
  var C = D.cities;
  /* Each tower's shape, aligned with its city's ring (build_massing.py,
     folded in by build_app.py): [source, facade, floors, u-min, u-max,
     needle, parts]. Source 0 = OSM 3D parts, 1 = OSM outline extruded,
     2 = drawn by hand from photographs, 3 = nothing to draw from,
     4 = a complex's outline as podium under a plain slab. */
  var SHAPES = D.shapes;

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
  /* How many degrees of the wheel are in view: the slider's value. A small
     wheel opens wider by default - Hong Kong's 18 towers sit 20 degrees
     apart, so at 100 degrees the stage showed five towers in a lot of sky -
     unless the reader has set the slider themselves. The slider always
     shows the value in use. */
  var MIN_IN_VIEW = 9;
  function view() { return S.fov; }
  function defaultFov(i) {
    var w = 360 * MIN_IN_VIEW / C[i].ring.length;
    return Math.min(160, Math.max(100, Math.ceil(w / 5) * 5));
  }

  function bars() {
    var c = C[S.i], p = c.rprof;
    var n = p.length;
    var out = new Float32Array(BARS);
    var step = view() / BARS;
    for (var k = 0; k < BARS; k++) {
      var a0 = S.az - view() / 2 + k * step;
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
  var tilt = null, lpf = null, levelNode = null;

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
      levelNode = null;
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
    tilt.gain.value = -12;

    // 2. a lowpass above which nothing useful lives here
    lpf = actx.createBiquadFilter();
    /* 2.4 kHz and -12 dB above are the values that sound. Until 2026-10-24
       this built 3.2 kHz and -9 dB, which skyline.html described, and then
       setKey() retargeted both to 2.4 kHz and -12 dB on every Play, so the
       described values never played (QA, D-31). One value, set once. */
    lpf.type = 'lowpass'; lpf.frequency.value = 2400; lpf.Q.value = 0.5;

    // 3. a limiter. Fast enough to catch a spin, slow enough not to pump.
    var comp = actx.createDynamicsCompressor();
    comp.threshold.value = -24; comp.knee.value = 12;
    comp.ratio.value = 20; comp.attack.value = 0.004;
    comp.release.value = 0.25;

    // 4. a fixed ceiling after it, so even a limiter overshoot cannot clip
    var ceiling = actx.createGain();
    ceiling.gain.value = 0.62;

    // 5. how tall the towers in view are, as a level (pushAudio); after the
    // limiter, so it cannot be squashed, and never above 1
    levelNode = actx.createGain();
    levelNode.gain.value = 0;

    master.connect(tilt).connect(lpf).connect(comp).connect(levelNode)
          .connect(ceiling)
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
     the root beside it. A root an octave down is always added as the lowest
     note (it sounds when the left of the view is among the seven loudest;
     it is not a held drone).
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
    pitch.push(rootHz / 2);                      // the root, an octave down
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

    /* ...and the level follows height, AFTER the limiter. Until 2026-10-24
       every bearing came out at the same power (0.46 rms at all 180
       bearings in all 27 cities, QA sk_audio.py) and the meter held
       elevation angle, not height, so turning towards the tallest towers
       never got louder. The first repair scaled the gains above by the
       loudest note, ahead of the limiter, and the limiter (-24 dB, 20:1)
       flattened it: halving the height share moved the output 2.7 dB
       instead of 9.6 (claims check, 2026-10-24). So the partials reach the
       limiter at constant power, as before, and the height-driven level is
       a gain after it: a bearing whose tallest tower is the city's tallest
       plays at full level, one whose tallest is half as tall at 0.5^1.6. */
    var top = 0;
    for (var j5 = 0; j5 < pitch.length; j5++)
      if (keep[j5] && acc[j5] > top) top = acc[j5];
    levelNode.gain.setTargetAtTime(top, t, 0.22);

    var slew = 0.22;                 // a pad, not a plucked thing
    for (var j2 = 0; j2 < parts.length; j2++) {
      parts[j2].g.gain.setTargetAtTime(want[j2] * norm, t, slew);
    }
    master.gain.setTargetAtTime(S.playing ? S.vol * 0.8 : 0, t, 0.12);
  }

  /* --------------------------------------------------------------- draw -- */
  /* THE STAGE. Until 2026-11-07 the city was a drum seen from outside, each
     tower a bar. It is now what the data always described: the view from the
     height-weighted centre, looking out, unrolled across the screen. Each
     tower keeps its slot on the wheel (true compass order, equalised
     spacing, so there is still no empty horizon), and stands at its true
     height in metres with its true outline, seen along the line from the
     centre to it (build_massing.py). The small circle at the top right is
     the same city from above at its true bearings and distances, with the
     view as a wedge: the stage rearranges the city; the circle does not.

     The depth is staged, not optical. Height falls off with distance only as
     d^-0.3, so the nearest tower cannot swallow the frame (the bug that made
     the first panorama look empty), and towers stand in four depth bands,
     the far ones a little higher and lost in haze, the way a matte painting
     is layered. Everything on the surface - light, windows, sky, haze, the
     searchlights, the blimp - is invented, and the sidebar says so. */
  var dpr = 1, W = 1, H = 1;
  function resize() {
    var r = canvas.getBoundingClientRect();
    dpr = Math.min(2, window.devicePixelRatio || 1);
    W = canvas.width = Math.max(1, Math.round(r.width * dpr));
    H = canvas.height = Math.max(1, Math.round(r.height * dpr));
    SC = null;
  }

  function xOf(az) {
    // where a slot lands across the panel, given the current view window
    return PAD + (0.5 + delta(az, S.az) / view()) * (W - PAD * 2);
  }

  var PAD = 0;

  /* The palettes. Each is painted from near-black up: the ink the towers
     are cut from, the light that falls on their left faces, the window
     glow, and a sky in three stops with a haze the far towers sink into.
     Which city gets which sky is a choice, like its key. */
  var SKY = {
    dusk:  { top: '#2a0d11', mid: '#86282a', low: '#cf6a48', glow: '#f0bd86',
             moon: '#f2e3c2', ink: '#0b0709', lit: '#d9a47c', fog: '#4f1e1e',
             win: '#f4d79c', stars: 0 },
    night: { top: '#05061a', mid: '#20205a', low: '#4c3f8c', glow: '#9c84d0',
             moon: '#ebe6f7', ink: '#06060c', lit: '#a594d6', fog: '#231f45',
             win: '#f1dca6', stars: 1 },
    teal:  { top: '#031214', mid: '#0f3b44', low: '#2b7486', glow: '#93c8c6',
             moon: '#e6efe9', ink: '#040909', lit: '#8fbfbc', fog: '#14343c',
             win: '#f2dfa8', stars: 1 },
    amber: { top: '#1a1007', mid: '#5f3c15', low: '#c07c33', glow: '#f3c983',
             moon: '#fbe8c3', ink: '#0a0705', lit: '#d8a96c', fog: '#442d15',
             win: '#f7dc9e', stars: 0 },
    rose:  { top: '#16081a', mid: '#55204c', low: '#b25a77', glow: '#eab0ac',
             moon: '#f7e3dd', ink: '#0a050a', lit: '#d49ea8', fog: '#3f1d31',
             win: '#f5dba6', stars: 1 },
    slate: { top: '#080b10', mid: '#25313d', low: '#5c6e7f', glow: '#b3c1cc',
             moon: '#eef1f4', ink: '#050709', lit: '#a9b7c2', fog: '#222b34',
             win: '#f2dca8', stars: 1 }
  };
  var CITY_SKY = {
    'New York': 'dusk', 'Dubai': 'amber', 'Shenzhen': 'teal',
    'Tokyo': 'night', 'Chicago': 'slate', 'Toronto': 'night',
    'Paris': 'rose', 'Moscow': 'dusk', 'Taipei': 'teal',
    'Hong Kong': 'night', 'Tel Aviv': 'amber', 'Seoul': 'rose',
    'Austin': 'amber', 'London': 'slate', 'Frankfurt': 'teal',
    'Warsaw': 'dusk', 'Osaka': 'rose', 'Los Angeles': 'amber',
    'Auckland': 'teal', 'Nashville': 'dusk', 'Calgary': 'slate',
    'Madrid': 'amber', 'Vienna': 'night', 'Brussels': 'slate'
  };
  var COOL_WIN = [205, 226, 246];
  var BAND_BG = '#0c0b0d';    // the meter's ground; the foot's CSS assumes it

  function hx(c) {
    var n = parseInt(c.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function mix(a, b, t) {
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t];
  }
  function rgba(c, a) {
    return 'rgba(' + Math.round(c[0]) + ',' + Math.round(c[1]) + ',' +
           Math.round(c[2]) + ',' + (a == null ? 1 : a) + ')';
  }
  /* Twilight and day are the same for every city; night is the city's own.
     The sun's height blends them (sky()), so a city at 3 pm is in daylight
     and the dark painting is what its night looks like. */
  var TWILIGHT = { top: '#1c1430', mid: '#5e2f4f', low: '#d5845a',
                   glow: '#f4bd86', moon: '#f6e9cf', ink: '#130c13',
                   lit: '#f0a774', fog: '#73404f', win: '#f6d59a' };
  var DAY = { top: '#5486ad', mid: '#97b8cb', low: '#e9dfc9', glow: '#fff1d2',
              moon: '#ffffff', ink: '#2c3442', lit: '#f6e4bd', fog: '#a3b1bb',
              win: '#f5e2b2' };
  var OVERCAST = [128, 132, 138];
  function pal(L) {
    var night = SKY[CITY_SKY[C[S.i].city]] || SKY.night, o = {};
    var wN = L ? L.wN : 1, wD = L ? L.wD : 0, wT = 1 - wN - wD;
    var cl = L ? L.cloud : 0;
    for (var k in night) {
      if (typeof night[k] !== 'string') { o[k] = night[k]; continue; }
      var a = hx(night[k]), t = hx(TWILIGHT[k]), d = hx(DAY[k]);
      var c = [a[0] * wN + t[0] * wT + d[0] * wD, a[1] * wN + t[1] * wT + d[1] * wD,
               a[2] * wN + t[2] * wT + d[2] * wD];
      // cloud greys the sky and the haze, and flattens the light
      if (cl && /top|mid|low|fog|glow/.test(k)) {
        var g = mix(OVERCAST, [12, 12, 14], wN * 0.85);
        c = mix(c, g, cl * (k === 'glow' ? 0.4 : 0.55));
      }
      o[k] = c;
    }
    // fog is lit by the city: a pale haze, not a darker one
    if (L && L.fog) o.fog = mix(o.fog, o.glow, Math.min(0.6, L.fog * 1.4));
    o.stars = night.stars;
    return o;
  }

  // a stable hash to [0, 1): the same window is the same window every visit
  function hh(a, b, c, d) {
    var x = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263) +
             Math.imul(c | 0, 1274126177) + Math.imul(d | 0, 1597334677)) | 0;
    x = Math.imul(x ^ (x >>> 13), 1274126177);
    return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
  }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  /* Slots and bearings. The ring is sorted by true bearing, so slot and
     bearing rise together; between two towers, each is interpolated from
     the other. The compass labels on the street and the wedge on the map
     use these, so "N" is printed where north actually falls between the
     towers either side of it, not at slot 0. */
  function slotOfBearing(b) {
    var r = C[S.i].ring, n = r.length;
    for (var i = 0; i < n; i++) {
      var a0 = r[i], a1 = r[(i + 1) % n];
      // two towers on one bearing span nothing; a lone tower spans the lot
      var span = n === 1 ? 360 : wrap(a1[6] - a0[6]);
      var off = wrap(b - a0[6]);
      if (off <= span && (span > 0 || off === 0)) {
        var s1 = i + 1 === n ? a1[0] + 360 : a1[0];
        return wrap(a0[0] + (s1 - a0[0]) * off / span);
      }
    }
    return 0;
  }
  function bearingOfSlot(sl) {
    var r = C[S.i].ring, n = r.length;
    for (var i = 0; i < n; i++) {
      var a0 = r[i], a1 = r[(i + 1) % n];
      var s1 = i + 1 === n ? a1[0] + 360 : a1[0];
      var off = wrap(sl - a0[0]);
      if (off <= s1 - a0[0]) {
        var span = n === 1 ? 360 : wrap(a1[6] - a0[6]);
        return wrap(a0[6] + span * off / (s1 - a0[0] || 1));
      }
    }
    return 0;
  }

  /* ------------------------------------------- the sky's real state -- */
  /* Where the sun and the moon are, for the city's own coordinates and the
     instant shown (now, or wherever the time slider is), and the moon's
     phase. These are the standard low-precision formulas (after Meeus, as
     in V. Agafonkin's SunCalc): good to a fraction of a degree, which is
     far finer than anything drawn here. Measured, not invented. */
  var RAD = Math.PI / 180, J1970 = 2440588, J2000 = 2451545, OBL = RAD * 23.4397;
  function days(t) { return t / 86400000 - 0.5 + J1970 - J2000; }
  function sidereal(d, lw) { return RAD * (280.16 + 360.9856235 * d) - lw; }
  function altAz(H, phi, dec) {
    var alt = Math.asin(Math.sin(phi) * Math.sin(dec) +
                        Math.cos(phi) * Math.cos(dec) * Math.cos(H));
    var az = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) -
                        Math.tan(dec) * Math.cos(phi));
    return { el: alt, az: wrap(az / RAD + 180) };   // az: compass bearing
  }
  function sunCoords(d) {
    var M = RAD * (357.5291 + 0.98560028 * d);
    var C2 = RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) +
                    0.0003 * Math.sin(3 * M));
    var L = M + C2 + RAD * 102.9372 + Math.PI;
    return { dec: Math.asin(Math.sin(OBL) * Math.sin(L)),
             ra: Math.atan2(Math.sin(L) * Math.cos(OBL), Math.cos(L)) };
  }
  function moonCoords(d) {
    var L = RAD * (218.316 + 13.176396 * d), M = RAD * (134.963 + 13.064993 * d),
        F = RAD * (93.272 + 13.229350 * d);
    var l = L + RAD * 6.289 * Math.sin(M), b = RAD * 5.128 * Math.sin(F);
    return { ra: Math.atan2(Math.sin(l) * Math.cos(OBL) - Math.tan(b) * Math.sin(OBL),
                            Math.cos(l)),
             dec: Math.asin(Math.sin(b) * Math.cos(OBL) +
                            Math.cos(b) * Math.sin(OBL) * Math.sin(l)),
             dist: 385001 - 20905 * Math.cos(M) };
  }
  function sky(t, lat, lon) {
    var d = days(t), lw = RAD * -lon, phi = RAD * lat, th = sidereal(d, lw);
    var sc = sunCoords(d), mc = moonCoords(d);
    var sun = altAz(th - sc.ra, phi, sc.dec), moon = altAz(th - mc.ra, phi, mc.dec);
    var sd = 149598000;
    var ph = Math.acos(Math.sin(sc.dec) * Math.sin(mc.dec) +
                       Math.cos(sc.dec) * Math.cos(mc.dec) * Math.cos(sc.ra - mc.ra));
    var inc = Math.atan2(sd * Math.sin(ph), mc.dist - sd * Math.cos(ph));
    var ang = Math.atan2(Math.cos(sc.dec) * Math.sin(sc.ra - mc.ra),
                         Math.sin(sc.dec) * Math.cos(mc.dec) -
                         Math.cos(sc.dec) * Math.sin(mc.dec) * Math.cos(sc.ra - mc.ra));
    moon.frac = (1 + Math.cos(inc)) / 2;                 // lit fraction
    moon.phase = 0.5 + 0.5 * inc * (ang < 0 ? -1 : 1) / Math.PI;  // 0 new, .5 full
    return { sun: sun, moon: moon };
  }

  /* The city's clock. The time slider sets an offset from now, in whole
     minutes of the city's local day; Now clears it. */
  var TZ = {
    'New York': 'America/New_York', 'Dubai': 'Asia/Dubai',
    'Shenzhen': 'Asia/Shanghai', 'Tokyo': 'Asia/Tokyo',
    'Chicago': 'America/Chicago', 'Toronto': 'America/Toronto',
    'Paris': 'Europe/Paris', 'Moscow': 'Europe/Moscow', 'Taipei': 'Asia/Taipei',
    'Hong Kong': 'Asia/Hong_Kong', 'Tel Aviv': 'Asia/Jerusalem',
    'Seoul': 'Asia/Seoul', 'Austin': 'America/Chicago',
    'London': 'Europe/London', 'Frankfurt': 'Europe/Berlin',
    'Warsaw': 'Europe/Warsaw', 'Osaka': 'Asia/Tokyo',
    'Los Angeles': 'America/Los_Angeles', 'Auckland': 'Pacific/Auckland',
    'Nashville': 'America/Chicago', 'Calgary': 'America/Edmonton',
    'Madrid': 'Europe/Madrid', 'Vienna': 'Europe/Vienna',
    'Brussels': 'Europe/Brussels'
  };
  S.shift = 0;                       // ms added to the real clock
  function instant() { return Date.now() + S.shift; }
  function localParts(t) {
    try {
      var f = new Intl.DateTimeFormat('en-GB', { timeZone: TZ[C[S.i].city],
        hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
      var p = f.formatToParts(new Date(t)), h = 0, m = 0;
      p.forEach(function (x) { if (x.type === 'hour') h = +x.value;
                               if (x.type === 'minute') m = +x.value; });
      return { h: h, m: m, mins: h * 60 + m };
    } catch (e) {
      var dd = new Date(t);
      return { h: dd.getUTCHours(), m: dd.getUTCMinutes(),
               mins: dd.getUTCHours() * 60 + dd.getUTCMinutes() };
    }
  }

  /* --------------------------------------------------------- weather -- */
  /* Current conditions from Open-Meteo (open-meteo.com, CC BY 4.0), one
     request when a city is chosen, kept ten minutes. Nothing about the
     reader is sent: the request carries the city's coordinates only. If it
     fails - offline, the downloaded copy, a blocked request - the sky is
     drawn clear and the panel says the weather is unavailable. */
  var WX = {};                       // by city: {t, ok, code, cloud, ...}
  function wx() { return WX[C[S.i].city] || { ok: false, cloud: 0 }; }
  function fetchWeather() {
    var c = C[S.i], name = c.city, have = WX[name];
    if (have && Date.now() - have.t < 600000) return;
    WX[name] = { t: Date.now(), ok: false, cloud: 0, pending: true };
    if (!window.fetch) { WX[name].pending = false; return; }
    var u = 'https://api.open-meteo.com/v1/forecast?latitude=' +
            c.centre[0].toFixed(3) + '&longitude=' + c.centre[1].toFixed(3) +
            '&current=temperature_2m,weather_code,cloud_cover,precipitation,' +
            'wind_speed_10m,wind_direction_10m,visibility';
    var done = false;
    var to = setTimeout(function () { if (!done) { WX[name].pending = false; panelSoon(); } }, 8000);
    fetch(u).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        done = true; clearTimeout(to);
        var cur = j && j.current;
        if (!cur) { WX[name] = { t: Date.now(), ok: false, cloud: 0 }; panelSoon(); return; }
        WX[name] = { t: Date.now(), ok: true, code: cur.weather_code,
                     temp: cur.temperature_2m, cloud: (cur.cloud_cover || 0) / 100,
                     precip: cur.precipitation || 0, wind: cur.wind_speed_10m || 0,
                     wdir: cur.wind_direction_10m || 0,
                     vis: cur.visibility == null ? 20000 : cur.visibility };
        startFade(900); SC = null; touch(); panelSoon();
      })
      .catch(function () {
        done = true; clearTimeout(to);
        WX[name] = { t: Date.now(), ok: false, cloud: 0 }; panelSoon();
      });
  }
  // WMO weather codes, as Open-Meteo reports them
  function wxKind(w) {
    var k = w.code;
    if (!w.ok || k == null) return 'clear';
    if (k >= 95) return 'storm';
    if ((k >= 71 && k <= 77) || k === 85 || k === 86) return 'snow';
    if ((k >= 51 && k <= 67) || (k >= 80 && k <= 82)) return 'rain';
    if (k === 45 || k === 48) return 'fog';
    if (k >= 2) return 'cloud';
    return 'clear';
  }
  var WX_WORD = { clear: 'clear', cloud: 'cloudy', fog: 'fog', rain: 'rain',
                  snow: 'snow', storm: 'thunderstorm' };

  /* The light the scene is painted in, from the sun and moon now: which
     source, from where, how strong, and how far toward night, twilight or
     day the palette is. key changes only when the light has moved enough
     to see, so the sprites are rebuilt every few minutes of sky, not every
     frame. */
  var SC_wN = 1;
  function light() {
    var c = C[S.i], t = instant();
    var sk = sky(t, c.centre[0], c.centre[1]);
    var se = sk.sun.el / RAD, me = sk.moon.el / RAD;
    var w = wx(), kind = wxKind(w);
    var cloud = w.ok ? w.cloud : 0;
    var wN = clamp((-se - 2) / 8, 0, 1), wD = clamp((se - 2) / 10, 0, 1);
    var src, I;
    if (se > -4) {
      src = sk.sun; I = clamp((se + 4) / 12, 0, 1);
    } else {
      src = sk.moon; I = 0.32 * sk.moon.frac * clamp(me / 10, 0, 1);
    }
    I *= 1 - 0.75 * cloud;              // overcast: light without direction
    var fog = kind === 'fog' ? 0.32 : (w.ok ? 0.25 * clamp((10000 - w.vis) / 9000, 0, 1) : 0);
    var amb = 0.05 * wD + 0.12 * cloud * wD;
    var q = function (v, k) { return Math.round(v / k); };
    return { sun: sk.sun, moon: sk.moon, az: src.az, el: Math.max(0, src.el),
             I: I, wN: wN, wD: wD, cloud: cloud, fog: fog, amb: amb, kind: kind,
             key: [q(src.az, 3), q(src.el / RAD, 1.5), q(I, 0.05), q(wN, 0.05),
                   q(wD, 0.05), q(cloud, 0.1), q(fog, 0.05)].join(',') };
  }

  /* ------------------------------------------------------ the scene -- */
  /* Built once per city and size: where the ground is, each tower's scale,
     depth band and haze, and its sprite - the tower drawn once, faces,
     roofs, unlit windows and all - plus the list of its windows, which are
     lit per frame. */
  var SC = null;
  var GAMMA = 0.12;     // height falls as distance^-GAMMA: staged, not optical
  var BANDS = 4;

  function layout() {
    // on a phone the notes line wraps to three lines over the canvas foot
    var phone = W < 560 * dpr;
    var groundY = Math.round(H * (phone ? 0.55 : 0.60));
    var splitY = groundY + Math.round(48 * dpr);
    return { groundY: groundY, splitY: splitY,
             eqTop: splitY + Math.round(14 * dpr),
             /* 66, not 30: the foot (the notes line and the hint, two lines
                of 12px with padding) sits over the bottom of this canvas.
                The test's label check reads this value. */
             eqBase: H - (phone ? 104 : 66) * dpr };
  }

  function topOf(sh) {
    var t = 0, ps = sh[6];
    for (var i = 0; i < ps.length; i++) t = Math.max(t, ps[i][1] + ps[i][2]);
    if (sh[5]) t = Math.max(t, sh[5][2]);
    return t;
  }

  function scene() {
    var LT = light();
    var key = S.i + ':' + W + 'x' + H;
    if (SC && SC.key === key) {
      /* Same city and size, new light: repaint the towers over the next few
         frames rather than all at once. A full repaint of New York is about
         150 ms, which is a stall when the time slider is dragged; this way
         the sky moves at once and the towers follow within a few frames. */
      if (SC.lkey !== LT.key) {
        startFade(420);           // the old light dissolves into the new
        SC.LT = LT; SC.P = pal(LT); SC.lkey = LT.key; SC_wN = LT.wN;
        for (var q = 0; q < SC.T.length; q++) SC.T[q].stale = true;
        SC.stale = SC.T.length;
      }
      return SC;
    }
    var c = C[S.i], ring = c.ring, shapes = SHAPES[S.i];
    var L = layout(), P = pal(LT);
    var dmin = 1e9, dmax = 0, i;
    for (i = 0; i < ring.length; i++) {
      dmin = Math.min(dmin, ring[i][2]); dmax = Math.max(dmax, ring[i][2]);
    }
    var lspan = Math.log(dmax / dmin) || 1;
    var lift = 0.08 * L.groundY, topPad = 0.07 * L.groundY;
    var T = [], s0 = 1e9;
    for (i = 0; i < ring.length; i++) {
      var r = ring[i], sh = shapes[i];
      var t = Math.log(r[2] / dmin) / lspan;
      var f = Math.pow(r[2] / dmin, -GAMMA);
      var o = { i: i, r: r, sh: sh, t: t, f: f, top: topOf(sh),
                lift: t * lift, band: Math.min(BANDS - 1, Math.floor(t * BANDS)),
                hz: 0.02 + 0.42 * Math.pow(t, 1.4), lit: 0.1, x: 0 };
      s0 = Math.min(s0, (L.groundY - topPad - o.lift) / (o.top * f));
      T.push(o);
    }
    SC_wN = LT.wN;
    /* The one liberty taken with the towers' shapes. Heights are true;
       widths are stretched or narrowed, the same for every tower in a
       city, so the typical tower fills about three-quarters of the space
       its slot gets at the city's default field of view: Dubai's towers,
       4 to 14 km out, would otherwise be needles in an empty sky, and
       Nashville's, all within a kilometre, a solid wall. Never more than
       x1.6 or less than x0.65; the sidebar says so. */
    var slotPx = (W - 2 * 26 * dpr) / defaultFov(S.i) * 360 / ring.length;
    var ws = [];
    for (i = 0; i < T.length; i++) ws.push((T[i].sh[4] - T[i].sh[3]) * s0 * T[i].f);
    ws.sort(function (a, b) { return a - b; });
    var wmed = ws[ws.length >> 1] || 1;
    var wf = clamp(0.75 * slotPx / wmed, 0.65, 1.6);
    for (i = 0; i < T.length; i++) {
      T[i].s = s0 * T[i].f;
      T[i].hs = T[i].s * wf;
      T[i].base = L.groundY - T[i].lift;
      sprite(T[i], P, LT);
    }
    // far first, so near towers are drawn over them
    var order = T.slice().sort(function (a, b) {
      return b.r[2] - a.r[2] || a.i - b.i;
    });
    if (SC) startFade(520);     // a new city, size or weather: dissolve
    SC = { key: key, lkey: LT.key, stale: 0, T: T, order: order, P: P, L: L,
           s0: s0, LT: LT, wf: wf, back: backdrop(T, s0, L),
           stars: stars(P), grain: grain() };
    return SC;
  }

  /* The low city behind the towers. INVENTED, and the sidebar says so: the
     data holds only the towers of 55 m and more, and a skyline of towers
     alone stands on nothing, so a hazy band of low blocks is drawn behind
     them in two depths, all the way round. It is decoration in the way the
     sky is: it is not on the map, it does not sound, it does not light up
     with the chord, and it never reaches higher than a third of the
     city's median tower. */
  function backdrop(T, s0, L) {
    var hs = [], i;
    for (i = 0; i < T.length; i++) hs.push(T[i].r[3]);
    hs.sort(function (a, b) { return a - b; });
    var med = hs[hs.length >> 1] || 100;
    var fFar = 1e9, fMid = 0;
    for (i = 0; i < T.length; i++) { fFar = Math.min(fFar, T[i].f); fMid += T[i].f; }
    fMid /= T.length;
    function layer(n, f, hmax, seed) {
      var out = [];
      var a = 0;
      for (var k = 0; k < n; k++) {
        a += (360 / n) * (0.5 + hh(k, seed, S.i, 1));
        var hm = 12 + (hmax - 12) * Math.pow(hh(k, seed, S.i, 2), 1.6);
        var wm = 18 + 45 * hh(k, seed, S.i, 3);
        out.push([wrap(a), wm * s0 * f, hm * s0 * f, k * 7 + seed]);
      }
      return out;
    }
    return { far: layer(300, fFar, med * 0.34, 31),
             mid: layer(150, (fFar + fMid) / 2, med * 0.22, 57) };
  }

  function drawBackdrop(list, baseY, col, winCol, P, LT, wf) {
    ctx.fillStyle = col;
    var half = view() / 2 + 6;
    for (var k = 0; k < list.length; k++) {
      var b = list[k];
      if (Math.abs(delta(b[0], S.az)) > half) continue;
      var x = xOf(b[0]), w = b[1] * wf, h = b[2];
      ctx.fillRect(x - w / 2, baseY - h, w, h + 1);
    }
    // a few lit windows, steady: the far city at night
    if (LT.wN < 0.1) return;
    ctx.fillStyle = winCol;
    var sz = Math.max(1, 1.3 * dpr);
    for (k = 0; k < list.length; k++) {
      b = list[k];
      if (Math.abs(delta(b[0], S.az)) > half) continue;
      x = xOf(b[0]); w = b[1] * wf; h = b[2];
      var n = Math.min(10, Math.floor(w * h / (60 * dpr * dpr) * 0.12 * LT.wN));
      for (var j = 0; j < n; j++) {
        ctx.fillRect(x - w / 2 + 2 * dpr + (w - 4 * dpr) * hh(b[3], j, 5, 5),
                     baseY - h + 2 * dpr + (h - 4 * dpr) * hh(b[3], j, 6, 6), sz, sz);
      }
    }
  }

  function offscreen(w, h) {
    var cv = document.createElement('canvas');
    cv.width = Math.max(1, w); cv.height = Math.max(1, h);
    var g = cv.getContext && cv.getContext('2d');
    return g ? { cv: cv, g: g } : null;
  }

  /* One tower, drawn once. Faces come from build_massing.py as
     [u0, u1, shade, true length] across the line of sight; shade is the
     cosine to the one light, from the viewer's upper left, that falls on
     every tower on every wheel. */
  function sprite(o, P, LT) {
    var sh = o.sh, s = o.s, hs = o.hs, parts = sh[6];
    var pad = Math.ceil(3 * dpr);
    var w = Math.ceil((sh[4] - sh[3]) * hs) + pad * 2;
    // padded at the top and sides only: the base sits on the ground
    var h = Math.ceil(o.top * s) + pad;
    o.ox = -sh[3] * hs + pad;      // where u = 0 falls in the sprite
    o.oy = h;                     // where z = 0 falls
    o.w = w; o.h = h;
    o.wins = new Float32Array(0); o.nw = 0;
    var os = offscreen(w, h);
    o.cv = os ? os.cv : null;
    if (!os) return;
    var g = os.g;
    var ink = P.ink, fog = P.fog;
    var hz = Math.min(0.9, o.hz * (1 - 0.3 * LT.wD) + LT.fog);
    /* A face's brightness is the real light on it: the sun (or, at night,
       the moon, weighted by its phase) on a surface whose outward normal
       points to compass bearing nb, tilted up by tilt degrees (0 a wall,
       90 a flat roof). The ambient floor is the sky's. */
    function lum(nb, tilt) {
      var t = (tilt || 0) * Math.PI / 180;
      var d = LT.I * (Math.cos(LT.el) * Math.cos((nb - LT.az) * Math.PI / 180) *
                      Math.cos(t) + Math.sin(LT.el) * Math.sin(t));
      return Math.max(0, d);
    }
    function tone(nb, tilt) {
      return mix(mix(ink, P.lit, 0.04 + LT.amb + 0.72 * lum(nb, tilt)), fog, hz);
    }
    var vb = o.r[6] + 180;          // the bearing that faces the viewer
    var storey = clamp(o.r[3] / Math.max(1, sh[2]), 2.8, 5.2);
    var stPx = storey * s;
    var wins = [], cover = [];
    for (var pi = 0; pi < parts.length; pi++) {
      var p = parts[pi], fs = p[6];
      var yTop = o.oy - p[1] * s, yBot = o.oy - p[0] * s;
      if (yBot - yTop < 0.5) continue;
      var leftF = null, rightF = null;
      for (var fi = 0; fi < fs.length; fi++) {
        var F = fs[fi];
        var x0 = o.ox + F[0] * hs, x1 = o.ox + F[1] * hs;
        var col = tone(F[2]);
        g.fillStyle = rgba(col);
        // a hair of overlap, so neighbouring faces do not show a seam
        g.fillRect(x0 - 0.3, yTop, x1 - x0 + 0.6, yBot - yTop);
        cover.push([x0, x1, yTop, yBot, pi]);
        if (!leftF || F[0] < leftF[0]) leftF = F;
        if (!rightF || F[1] > rightF[1]) rightF = F;
        faceWindows(g, wins, o, pi, fi, x0, x1, yTop, yBot, F, sh[1], stPx,
                    col, P);
      }
      // the light catches the left edge and the parapet
      var px0 = o.ox + p[4] * hs, px1 = o.ox + p[5] * hs;
      // the edge of a part on the side the light comes from catches it
      if (leftF && lum(leftF[2]) > 0.15) {
        g.fillStyle = rgba(mix(tone(leftF[2]), P.lit, 0.3));
        g.fillRect(o.ox + leftF[0] * hs, yTop, Math.max(0.8, 0.9 * dpr),
                   yBot - yTop);
      }
      if (rightF && lum(rightF[2]) > 0.15) {
        g.fillStyle = rgba(mix(tone(rightF[2]), P.lit, 0.3));
        g.fillRect(o.ox + rightF[1] * hs - Math.max(0.8, 0.9 * dpr), yTop,
                   Math.max(0.8, 0.9 * dpr), yBot - yTop);
      }
      if (!p[3]) {
        g.fillStyle = rgba(mix(tone(vb, 90), P.lit, 0.12));
        g.fillRect(px0, yTop, px1 - px0, Math.max(0.8, 0.9 * dpr));
      }
      roof(g, p, o, tone, vb);
    }
    if (sh[5]) {                         // a needle: spire or mast
      var nx = o.ox + sh[5][0] * hs;
      var nb = o.oy - sh[5][1] * s, nt = o.oy - sh[5][2] * s;
      var hw = Math.max(0.7 * dpr, 1.6 * s);
      g.fillStyle = rgba(tone(vb - 60));
      g.beginPath(); g.moveTo(nx - hw, nb); g.lineTo(nx, nt);
      g.lineTo(nx, nb); g.closePath(); g.fill();
      g.fillStyle = rgba(tone(vb + 60));
      g.beginPath(); g.moveTo(nx, nb); g.lineTo(nx, nt);
      g.lineTo(nx + hw, nb); g.closePath(); g.fill();
    }
    /* A window painted on a part that a nearer part then covers is hidden
       in the sprite, but the lit overlay is drawn on top of the sprite and
       would show it through the wall (Ping An's 53 parts lit up like a
       lantern). So a window survives only if no later part's face covers
       its middle. */
    wins = wins.filter(function (w) {
      var cx = w[0] + w[2] / 2, cy = w[1] + w[3] / 2;
      for (var k = 0; k < cover.length; k++) {
        var c = cover[k];
        if (c[4] > w[6] && cx > c[0] && cx < c[1] && cy > c[2] && cy < c[3])
          return false;
      }
      return true;
    });
    // windows sorted by rank: the lit ones each frame are a prefix
    wins.sort(function (a, b) { return a[4] - b[4]; });
    var fa = new Float32Array(wins.length * 6);
    for (var k = 0; k < wins.length; k++)
      for (var j = 0; j < 6; j++) fa[k * 6 + j] = wins[k][j];
    o.wins = fa; o.nw = wins.length;
    o.cv = os.cv;
  }

  /* Windows: the rhythm is the floor count; the pattern is the facade type
     (punched openings for masonry, ribbons for the post-war slabs, a glass
     grid after), and the bay is measured along the face's true length, so
     an oblique face shows its bays closer together, as it should. Where
     the cells would come out under two pixels, floors and bays are grouped
     rather than drawn as noise. Each window gets a rank; a frame lights
     the windows whose rank is under the tower's level. Ranks are clumped
     by floor, because offices light by the floor. */
  function faceWindows(g, wins, o, pi, fi, x0, x1, yTop, yBot, F, fac,
                       stPx, col, P) {
    var wpx = x1 - x0, hpx = yBot - yTop;
    if (wpx < 1.6 * dpr || hpx < 3 * dpr) return;
    var bayM = fac === 0 ? 2.8 : (fac === 1 ? 6.0 : 3.2);
    var nb = Math.max(1, Math.round((F[3] || wpx / o.s) / bayM));
    var nf = Math.max(1, Math.round(hpx / stPx));
    var gx = Math.max(1, Math.ceil(2.2 * dpr / (wpx / nb)));
    var gy = Math.max(1, Math.ceil(2.6 * dpr / (hpx / nf)));
    nb = Math.max(1, Math.floor(nb / gx)); nf = Math.max(1, Math.floor(nf / gy));
    if (nb * nf > 2400) return;
    var cw = wpx / nb, chh = hpx / nf;
    var ww, wh;
    if (fac === 0) { ww = Math.max(0.8, cw * 0.42); wh = Math.max(0.8, chh * 0.56); }
    else if (fac === 1) { ww = Math.max(0.8, cw * 0.9); wh = Math.max(0.8, chh * 0.46); }
    else { ww = Math.max(0.8, cw - Math.max(0.6, cw * 0.16));
           wh = Math.max(0.8, chh - Math.max(0.7, chh * 0.2)); }
    // unlit glass: darker than the wall on the lit side, a touch of sky
    // reflection on the grid
    // by day the glass barely reads against the wall; at night it is dark
    var glass = fac === 2 ? mix(col, P.mid, 0.08 + 0.04 * SC_wN)
                          : mix(col, [0, 0, 0], 0.12 + 0.33 * SC_wN);
    g.fillStyle = rgba(glass);
    for (var a = 0; a < nf; a++) {
      var y = yTop + a * chh + (chh - wh) / 2;
      for (var b = 0; b < nb; b++) {
        var x = x0 + b * cw + (cw - ww) / 2;
        g.fillRect(x, y, ww, wh);
        // an office is a few bays of one or two floors, lit together
        var clump = hh(o.i, pi * 31 + fi, Math.floor(a / 2), Math.floor(b / 4));
        var rank = 0.75 * clump + 0.25 * hh(o.i, pi * 31 + fi, a, b);
        var cool = hh(b, a, o.i, 99) < 0.13 ? 1 : 0;
        wins.push([x, y, ww, wh, rank, cool, pi]);
      }
    }
  }

  function roof(g, p, o, tone, vb) {
    var code = p[3], rh = p[2], s = o.s, hs = o.hs;
    if (!code || rh <= 0) return;
    var x0 = o.ox + p[4] * hs, x1 = o.ox + p[5] * hs, xm = (x0 + x1) / 2;
    var yb = o.oy - p[1] * s, yt = o.oy - (p[1] + rh) * s;
    var prof = p[8];
    if (prof && prof.length > 1 && (code === 4 || code === 1)) {
      /* The roof's real outline from the line of sight (build_massing
         roof_profile): a skillion is lit as the plane it is; a pyramid's
         two visible flanks split at its apex. */
      var fill = p[9] ? rgba(tone(p[9][0], p[9][1])) : rgba(tone(vb - 45, 40));
      g.fillStyle = fill;
      g.beginPath();
      g.moveTo(o.ox + prof[0][0] * hs, yb);
      for (var q = 0; q < prof.length; q++)
        g.lineTo(o.ox + prof[q][0] * hs, yb - prof[q][1] * s);
      g.lineTo(o.ox + prof[prof.length - 1][0] * hs, yb);
      g.closePath(); g.fill();
      if (code === 1 && prof.length === 3) {
        g.fillStyle = rgba(tone(vb + 45, 40));
        g.beginPath();
        g.moveTo(o.ox + prof[1][0] * hs, yb - prof[1][1] * s);
        g.lineTo(o.ox + prof[2][0] * hs, yb);
        g.lineTo(o.ox + prof[1][0] * hs, yb);
        g.closePath(); g.fill();
      }
      return;
    }
    // the slopes facing the viewer's left and right
    var lit = rgba(tone(vb - 45, 40)), dark = rgba(tone(vb + 45, 40));
    function poly(pts, fill) {
      g.fillStyle = fill; g.beginPath(); g.moveTo(pts[0], pts[1]);
      for (var k = 2; k < pts.length; k += 2) g.lineTo(pts[k], pts[k + 1]);
      g.closePath(); g.fill();
    }
    if (code === 1) {                                   // pyramid, cone, spire
      poly([x0, yb, xm, yt, xm, yb], lit);
      poly([xm, yb, xm, yt, x1, yb], dark);
    } else if (code === 2 || code === 5) {              // dome, onion
      var rx = (x1 - x0) / 2, ry = yb - yt;
      g.fillStyle = dark; g.beginPath();
      if (code === 5) {
        g.moveTo(x0, yb);
        g.bezierCurveTo(x0 - rx * 0.25, yb - ry * 0.55, xm - rx * 0.1,
                        yb - ry * 0.8, xm, yt);
        g.bezierCurveTo(xm + rx * 0.1, yb - ry * 0.8, x1 + rx * 0.25,
                        yb - ry * 0.55, x1, yb);
      } else {
        g.ellipse(xm, yb, rx, ry, 0, Math.PI, 2 * Math.PI);
      }
      g.closePath(); g.fill();
      g.save(); g.clip();
      g.fillStyle = lit; g.fillRect(x0 - rx, yt - 1, rx * 1.15 + 0.5, ry + 2);
      g.restore();
    } else if (code === 3 || code === 6) {              // gabled, hipped, mansard
      var k = code === 3 ? 0.18 : 0.34;
      var a0 = xm - (x1 - x0) * k, a1 = xm + (x1 - x0) * k;
      poly([x0, yb, a0, yt, xm, yt, xm, yb], lit);
      poly([xm, yb, xm, yt, a1, yt, x1, yb], dark);
    } else if (code === 4) {                            // skillion
      /* A sloped roof. Its fall across the line of sight (build_massing)
         says which side is high; one falling toward or away from the
         viewer shows as its full face. One World Trade Center is mapped
         as four of these over a 55 m base: its chamfered taper. */
      var fall = p[7] || 0;
      if (fall > 0.35) poly([x0, yb, x0, yt, x1, yb], lit);
      else if (fall < -0.35) poly([x0, yb, x1, yt, x1, yb], dark);
      else poly([x0, yb, x0, yt, x1, yt, x1, yb], rgba(tone(vb, 30)));
    }
  }

  var STAR_N = 140;
  function stars(P) {
    var out = [];
    if (!P.stars) return out;
    for (var k = 0; k < STAR_N; k++) {
      out.push([hh(k, 1, S.i, 3) * 360, hh(k, 2, S.i, 3),
                0.5 + hh(k, 3, S.i, 3) * 1.1, 0.25 + 0.6 * hh(k, 4, S.i, 3)]);
    }
    return out;
  }

  // film grain: a tile of noise laid over the painting, still
  var grainTile = null;
  function grain() {
    if (grainTile) return grainTile;
    var os = offscreen(160, 160);
    if (!os || !os.g.createImageData) return null;
    var im = os.g.createImageData(160, 160), d = im.data;
    for (var k = 0; k < d.length; k += 4) {
      var v = hh(k, 5, 9, 2) * 255;
      d[k] = d[k + 1] = d[k + 2] = v; d[k + 3] = 255;
    }
    os.g.putImageData(im, 0, 0);
    grainTile = os.cv;
    return grainTile;
  }

  /* --------------------------------------------------------- the frame -- */
  var clock = 0;            // seconds of ambient time; frozen when motion is off
  function draw() {
    PAD = 26 * dpr;
    var c = C[S.i];
    var SCn = scene(), P = SCn.P, L = SCn.L;
    if (SCn.stale) repaint(SCn, 12);
    var groundY = L.groundY, splitY = L.splitY;
    var eqTop = L.eqTop, eqBase = L.eqBase;
    var mx = peak(), now = clock, i;
    var spanPx = W - PAD * 2;

    ctx.clearRect(0, 0, W, H);

    /* ---- the sky ------------------------------------------------------ */
    var sky = ctx.createLinearGradient(0, 0, 0, groundY);
    sky.addColorStop(0, rgba(P.top));
    sky.addColorStop(0.55, rgba(P.mid));
    sky.addColorStop(1, rgba(P.low));
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, groundY);

    var LT = SCn.LT, W8 = wx();
    var st = SCn.stars, starA = LT.wN * (1 - LT.cloud);
    for (i = 0; starA > 0.02 && i < st.length; i++) {
      var sx = xOf(st[i][0]);
      if (sx < -4 || sx > W + 4) continue;
      var tw = motionOff ? 1 : 0.75 + 0.25 * Math.sin(now * 1.3 + i);
      ctx.globalAlpha = starA * st[i][3] * tw * (1 - st[i][1]);
      ctx.fillStyle = rgba(P.moon);
      var sz = st[i][2] * dpr;
      ctx.fillRect(sx, st[i][1] * groundY * 0.6, sz, sz);
    }
    ctx.globalAlpha = 1;

    /* The sun and the moon, at their real bearings and heights for this
       city and this instant (light(), sky()), placed among the towers by
       bearing the way the compass points are. Drawn several times larger
       than life, which is the one liberty taken with them; the moon shows
       its real phase. */
    function elY(el) {
      return groundY - clamp(el / RAD / 72, 0, 1) * groundY * 0.9;
    }
    var sunEl = LT.sun.el / RAD;
    if (sunEl > -1.5) {
      var sxs = xOf(slotOfBearing(LT.sun.az)), sys = elY(LT.sun.el);
      var sr = 0.045 * groundY, warm = clamp(1 - sunEl / 25, 0, 1);
      var sc2 = mix([255, 248, 228], [255, 170, 100], warm);
      var vis = 1 - 0.8 * LT.cloud;
      var sg = ctx.createRadialGradient ?
        ctx.createRadialGradient(sxs, sys, sr * 0.5, sxs, sys, sr * 7) : null;
      if (sg) {
        sg.addColorStop(0, rgba(sc2, 0.55 * vis)); sg.addColorStop(1, rgba(sc2, 0));
        ctx.fillStyle = sg;
        ctx.fillRect(sxs - sr * 7, sys - sr * 7, sr * 14, sr * 14);
      }
      ctx.fillStyle = rgba(sc2, vis);
      ctx.beginPath(); ctx.arc(sxs, sys, sr, 0, Math.PI * 2); ctx.fill();
    }
    if (LT.moon.el > -0.01) {
      var mxs = xOf(slotOfBearing(LT.moon.az)), mys = elY(LT.moon.el);
      var mr = 0.06 * groundY, mvis = (1 - 0.85 * LT.cloud) * (0.35 + 0.65 * LT.wN);
      if (mxs > -mr * 3 && mxs < W + mr * 3) {
        var mg = ctx.createRadialGradient ?
          ctx.createRadialGradient(mxs, mys, mr * 0.9, mxs, mys, mr * 3) : null;
        if (mg) {
          mg.addColorStop(0, rgba(P.glow, 0.22 * mvis * LT.moon.frac));
          mg.addColorStop(1, rgba(P.glow, 0));
          ctx.fillStyle = mg;
          ctx.fillRect(mxs - mr * 3, mys - mr * 3, mr * 6, mr * 6);
        }
        moonDisc(mxs, mys, mr, LT.moon.phase, c.centre[0] < 0, P, mvis);
      }
    }
    clouds(SCn, P, LT, W8, now);

    // the glow of the city on the air above it
    var dome = ctx.createLinearGradient(0, groundY * 0.45, 0, groundY);
    dome.addColorStop(0, rgba(P.glow, 0));
    dome.addColorStop(1, rgba(P.glow, 0.30));
    ctx.fillStyle = dome;
    ctx.fillRect(0, groundY * 0.45, W, groundY * 0.55);

    // searchlights, behind the skyline
    var beams = [[wrap(c.look + 63), 0.0], [wrap(c.look - 48), 2.1],
                 [wrap(c.look + 171), 4.0]];
    ctx.globalCompositeOperation = 'lighter';
    for (i = 0; LT.wN > 0.05 && i < beams.length; i++) {
      var bx = xOf(beams[i][0]);
      if (bx < -W * 0.3 || bx > W * 1.3) continue;
      var ang = (motionOff ? 0.18 : Math.sin(now * 0.23 + beams[i][1]) * 0.42);
      var len = groundY * 1.05, spread = 0.035;
      var bg = ctx.createLinearGradient(bx, groundY, bx + Math.sin(ang) * len,
                                        groundY - Math.cos(ang) * len);
      bg.addColorStop(0, rgba(P.glow, 0.20 * LT.wN));
      bg.addColorStop(1, rgba(P.glow, 0));
      ctx.fillStyle = bg;
      ctx.beginPath();
      ctx.moveTo(bx, groundY);
      ctx.lineTo(bx + Math.sin(ang - spread) * len, groundY - Math.cos(ang - spread) * len);
      ctx.lineTo(bx + Math.sin(ang + spread) * len, groundY - Math.cos(ang + spread) * len);
      ctx.closePath();
      ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';

    // the blimp, drifting a slot every second or so
    var blz = wrap(c.look - 30 + (motionOff ? 0 : now * (0.4 + 0.08 * windCross(W8))));
    var blx = xOf(blz), bly = groundY * (0.17 + (motionOff ? 0 : 0.012 * Math.sin(now * 0.4)));
    if (blx > -100 * dpr && blx < W + 100 * dpr) blimp(blx, bly, 34 * dpr, P, now);

    /* ---- the towers --------------------------------------------------- */
    /* The ground they stand on: the far rows stand higher, as if further
       up a slope, so the land between the rows is drawn as a band that
       darkens toward the viewer. Nothing is on it; it is ground, not an
       invented low-rise city. */
    var lifted = 0.08 * groundY;
    var gg = ctx.createLinearGradient(0, groundY - lifted, 0, groundY);
    gg.addColorStop(0, rgba(mix(P.fog, P.low, 0.25)));
    gg.addColorStop(1, rgba(mix(P.ink, P.fog, 0.3)));
    ctx.fillStyle = gg;
    ctx.fillRect(0, groundY - lifted - 1, W, lifted + 1);

    var T = SCn.T, order = SCn.order;
    var bw = spanPx / BARS;
    var bk = SCn.back;
    drawBackdrop(bk.far, groundY - lifted, rgba(mix(P.ink, P.fog, 0.62)),
                 rgba(mix(P.win, P.fog, 0.6), 0.55), P, LT, SCn.wf);
    var midDone = false;
    var half = view() / 2 + 8;
    var band = BANDS;
    for (i = 0; i < order.length; i++) {
      var o = order[i];
      if (o.band < band) {
        // haze between depth bands: the bases of the far rows sink into it
        fogBand(SCn, band, P);
        band = o.band;
        if (!midDone && band <= 1) {
          drawBackdrop(bk.mid, groundY - lifted * 0.45,
                       rgba(mix(P.ink, P.fog, 0.4)),
                       rgba(mix(P.win, P.fog, 0.4), 0.6), P, LT, SCn.wf);
          midDone = true;
        }
      }
      if (Math.abs(delta(o.r[0], S.az)) > half) { o.vis = false; continue; }
      o.vis = true;
      o.x = xOf(o.r[0]);
      var left = o.x - o.ox, topY = o.base - o.oy;
      o.left = o.x + o.sh[3] * o.hs; o.right = o.x + o.sh[4] * o.hs;
      o.topY = o.base - o.top * o.s;
      if (o.right < 0 || o.left > W) continue;
      if (o.cv) ctx.drawImage(o.cv, left, topY);
      else {           // no offscreen canvas (a test DOM): the outline alone
        ctx.fillStyle = rgba(mix(P.ink, P.fog, o.hz));
        ctx.fillRect(o.left, o.topY, o.right - o.left, o.base - o.topY);
      }

      // how lit: this tower's share of the chord, from the meter under it
      var k = clamp(Math.floor((o.x - PAD) / bw), 0, BARS - 1);
      var a = Math.pow(Math.min(1, lvl[k] / mx), 1.6);
      var want = 0.01 + 0.11 * LT.wN +
                 (S.playing ? 0.6 : 0.14) * a * (0.12 + 0.88 * LT.wN);
      o.lit = motionOff ? want : o.lit + (want - o.lit) * Math.min(1, 3 * dtLast);
      windowsLit(o, left, topY, P, now);
      beacon(o, P, now);
    }
    fogBand(SCn, band, P);
    if (!midDone) drawBackdrop(bk.mid, groundY - lifted * 0.45,
                               rgba(mix(P.ink, P.fog, 0.4)),
                               rgba(mix(P.win, P.fog, 0.4), 0.6), P, LT, SCn.wf);
    weather(SCn, P, LT, W8, now);

    /* ---- the street --------------------------------------------------- */
    ctx.fillStyle = rgba(P.ink);
    ctx.fillRect(0, groundY, W, splitY - groundY);
    ctx.fillStyle = rgba(P.glow, 0.35);
    ctx.fillRect(0, groundY, W, Math.max(1, dpr));

    var gt = SCn.grain;
    if (gt && ctx.createPattern) {
      var pat = ctx.createPattern(gt, 'repeat');
      if (pat) {
        ctx.globalAlpha = 0.07;
        ctx.globalCompositeOperation = 'overlay';
        ctx.fillStyle = pat;
        ctx.fillRect(0, 0, W, splitY);
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = 1;
      }
    }

    // compass points, where each true bearing falls between its towers
    ctx.font = (12 * dpr) + 'px ui-sans-serif, system-ui, sans-serif';
    ctx.textAlign = 'center';
    /* every piece of text drawn on the canvas goes in here as a box, so a
       label placed later can be tested against all of them, compass points
       included - "One World Trade Center" printed straight through "NW"
       until they were (2026-09-04) */
    var placed = [];
    var lineH = 12 * dpr;
    var cy = groundY + 16 * dpr;
    /* Equalised spacing squeezes a wide stretch of empty horizon into one
       gap between two towers, so several compass points can fall on one
       spot (New York's south-west to north-west all lie between Lower
       Manhattan and Midtown). Points closer than a label's width are
       printed as one run, "SW–NW", which is what that gap holds. */
    var pts = [];
    for (var d2 = 0; d2 < 360; d2 += 45) {
      var sl2 = slotOfBearing(d2);
      if (Math.abs(delta(sl2, S.az)) > view() / 2) continue;
      pts.push({ x: xOf(sl2), d: d2 });
    }
    pts.sort(function (p, q) { return p.x - q.x; });
    var runs = [];
    for (i = 0; i < pts.length; i++) {
      var last = runs[runs.length - 1];
      if (last && pts[i].x - last.x1 < 34 * dpr) { last.b = pts[i].d; last.x1 = pts[i].x; }
      else runs.push({ a: pts[i].d, b: pts[i].d, x0: pts[i].x, x1: pts[i].x });
    }
    for (i = 0; i < runs.length; i++) {
      var lab = runs[i].a === runs[i].b ? compass(runs[i].a)
              : compass(runs[i].a) + '\u2013' + compass(runs[i].b);
      var cx2 = (runs[i].x0 + runs[i].x1) / 2;
      ctx.fillStyle = rgba(P.glow, 0.9);
      ctx.fillText(lab, cx2, cy);
      placed.push({ x: cx2, half: ctx.measureText(lab).width / 2, y: cy });
    }

    /* ---- the analyser ------------------------------------------------ */
    ctx.fillStyle = BAND_BG;
    ctx.fillRect(0, splitY, W, H - splitY);
    var bwm = (W - PAD * 2) / BARS;
    var eqH = eqBase - eqTop;
    var grad = ctx.createLinearGradient(0, eqBase, 0, eqTop);
    grad.addColorStop(0, rgba(P.fog));
    grad.addColorStop(1, rgba(P.lit));

    for (k = 0; k < BARS; k++) {
      var v = Math.min(1, lvl[k] / mx);
      var xk = PAD + k * bwm;
      var bh = v * eqH;
      if (bh > 0.6) {
        ctx.fillStyle = grad;
        ctx.globalAlpha = 0.45 + 0.55 * v;
        ctx.fillRect(xk + bwm * 0.14, eqBase - bh, bwm * 0.72, bh);
      }
      // peak marker, falling back under its own weight
      var ph = Math.min(1, pk[k] / mx) * eqH;
      if (ph > 1.5) {
        ctx.globalAlpha = 0.85;
        ctx.fillStyle = rgba(P.win);
        ctx.fillRect(xk + bwm * 0.14, eqBase - ph - 2 * dpr, bwm * 0.72,
                     1.6 * dpr);
      }
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = rgba(P.lit, 0.35);
    ctx.fillRect(PAD, eqBase, W - PAD * 2, Math.max(1, dpr));

    // the towers worth naming, labelled on the street under them, biggest
    // first and dropped rather than stacked when they collide
    /* Names ran into each other before, because the test for a collision
       used the width of the label being placed against the *centres* of the
       ones already down, and the clamp that keeps a name on the canvas ran
       after the test rather than before it. Widths are measured, the clamp
       runs first, and two labels clash when their boxes overlap. */
    var fpx = 12 * dpr;                     // the site's floor, on a phone too
    ctx.font = fpx + 'px ui-sans-serif, system-ui, sans-serif';
    var maxLabels = W < 560 * dpr ? 3 : (W < 900 * dpr ? 4 : 6);
    var gap = 14 * dpr;
    var named = 0;
    var ty = groundY + 34 * dpr;
    var ring = c.ring;
    var seen = ring.slice().filter(function (r) {
      return r[4] && Math.abs(delta(r[0], S.az)) < view() / 2 * 0.92;
    }).sort(function (p, q) { return q[3] - p[3]; }).slice(0, 12);
    for (i = 0; i < seen.length && named < maxLabels; i++) {
      var nm = seen[i][4];
      var hw = ctx.measureText(nm).width / 2;
      if (hw * 2 > W - 8 * dpr) continue;         // no room for it at all
      var tx = xOf(seen[i][0]);
      tx = Math.min(W - hw - 4 * dpr, Math.max(hw + 4 * dpr, tx));
      var clash = false;
      for (var j = 0; j < placed.length; j++) {
        if (Math.abs(ty - placed[j].y) < lineH + 2 * dpr &&
            Math.abs(tx - placed[j].x) < hw + placed[j].half + gap) {
          clash = true; break;
        }
      }
      if (clash) continue;
      placed.push({ x: tx, half: hw, y: ty });
      named++;
      ctx.fillStyle = rgba(P.lit, 0.95);
      ctx.fillText(nm, tx, ty);
    }

    minimap(SCn, P);
  }
  var dtLast = 0.016;

  /* Cross-dissolve. Whenever the picture would change at once - a new
     city, the weather arriving, the light moving on - the last frame is
     kept and laid over the new ones, fading out, so nothing snaps. */
  var fadeCv = null, fadeT0 = 0, fadeDur = 0, fading = false;
  function startFade(ms) {
    if (motionOff || !canvas.width) return;
    if (!fadeCv || fadeCv.cv.width !== W || fadeCv.cv.height !== H) {
      fadeCv = offscreen(W, H);
      if (!fadeCv) return;
    }
    fadeCv.g.clearRect(0, 0, W, H);
    fadeCv.g.drawImage(canvas, 0, 0);
    fadeT0 = performance.now(); fadeDur = ms; fading = true;
  }
  function fadeOver() {
    if (!fading || !fadeCv) return;
    var t = (performance.now() - fadeT0) / fadeDur;
    if (t >= 1) { fading = false; return; }
    var a = 1 - t * t * (3 - 2 * t);           // smoothstep out
    ctx.save(); ctx.globalAlpha = a;
    ctx.drawImage(fadeCv.cv, 0, 0);
    ctx.restore();
  }

  function aim(goal) {
    S.fling = 0;
    S.azGoal = goal;
    touch();
  }

  /* Motion blur, while the view swings: the last frame is laid over the
     new one at an opacity that grows with the turning speed, so a fast
     turn smears as a camera's pan would. Nothing when still or with
     reduced motion. Only the painting (above the street) is blurred; the
     meter and its labels stay sharp. */
  var ghost = null;
  function blur() {
    if (!SC) return;
    var splitY = SC.L.groundY;
    var v = Math.abs(S.vel || 0);
    if (!ghost || ghost.cv.width !== W || ghost.cv.height !== splitY) {
      ghost = offscreen(W, splitY);
      if (!ghost) return;
    }
    var a = motionOff ? 0 : clamp((v - 15) / 180, 0, 0.45);
    // on a slow frame the old image is too far back to read as blur: skip
    if (dtLast > 0.03) a = 0;
    if (a > 0.01) {
      // the old frame, shifted half a step back along the swing, then the
      // copy for next time is taken from the blended result
      var shift = -(S.vel || 0) * dtLast * (W - PAD * 2) / view() * 0.5;
      ctx.save();
      ctx.globalAlpha = a;
      ctx.drawImage(ghost.cv, -shift, 0);
      ctx.restore();
      minimap(SC, SC.P);         // the map stays crisp
    }
    ghost.g.clearRect(0, 0, W, splitY);
    ghost.g.drawImage(canvas, 0, 0, W, splitY, 0, 0, W, splitY);
  }

  // repaint stale towers, the ones in view first, within a time budget
  function repaint(SCn, ms) {
    var t0 = (window.performance || Date).now(), T = SCn.T, pass, i;
    for (pass = 0; pass < 2; pass++) {
      for (i = 0; i < T.length; i++) {
        var o = T[i];
        if (!o.stale) continue;
        var inView = Math.abs(delta(o.r[0], S.az)) <= view() / 2 + 8;
        if (pass === 0 && !inView) continue;
        sprite(o, SCn.P, SCn.LT);
        o.stale = false; SCn.stale--;
        if ((window.performance || Date).now() - t0 > ms) return;
      }
    }
  }

  function fogBand(SCn, band, P) {
    if (band >= BANDS || band <= 0) return;
    var L = SCn.L;
    var y1 = L.groundY - (band / BANDS) * 0.08 * L.groundY;
    var hgt = 0.16 * L.groundY;
    var fg = ctx.createLinearGradient(0, y1 - hgt, 0, L.groundY);
    fg.addColorStop(0, rgba(P.fog, 0));
    fg.addColorStop(0.6, rgba(P.fog, 0.16));
    fg.addColorStop(1, rgba(P.fog, 0.34));
    ctx.fillStyle = fg;
    ctx.fillRect(0, y1 - hgt, W, L.groundY - y1 + hgt);
  }

  // the wind's push across the view, + to the right, in km/h
  function windCross(w) {
    if (!w.ok) return 1;
    var to = w.wdir + 180;            // reported as where it blows from
    return w.wind * Math.sin((to - bearingOfSlot(S.az)) * RAD);
  }

  function moonDisc(x, y, R, phase, south, P, a) {
    ctx.fillStyle = rgba(mix(P.mid, P.moon, 0.12), 0.55 * a);  // earthshine
    ctx.beginPath(); ctx.arc(x, y, R, 0, Math.PI * 2); ctx.fill();
    var waxing = phase < 0.5;
    if (south) waxing = !waxing;      // seen upside down from the south
    var k = Math.cos(2 * Math.PI * phase);   // 1 new, -1 full
    ctx.fillStyle = rgba(P.moon, a);
    ctx.beginPath();
    if (waxing) ctx.arc(x, y, R, -Math.PI / 2, Math.PI / 2, false);
    else ctx.arc(x, y, R, Math.PI / 2, 3 * Math.PI / 2, false);
    if (ctx.ellipse) {
      if (waxing) ctx.ellipse(x, y, R * Math.abs(k), R, 0, Math.PI / 2, -Math.PI / 2, k > 0);
      else ctx.ellipse(x, y, R * Math.abs(k), R, 0, -Math.PI / 2, Math.PI / 2, k > 0);
    }
    ctx.closePath(); ctx.fill();
  }

  /* Cloud, as banks of soft ovals across the sky, as many as the reported
     cover, drifting with the wind. Lit from below by the city at night. */
  function clouds(SCn, P, LT, w, now) {
    // the count is for the whole ring; about a third is in view
    var n = Math.round(LT.cloud * 54);
    if (!n) return;
    var drift = motionOff ? 0 : now * 0.05 * windCross(w);
    var gy = SCn.L.groundY;
    var top = mix(P.low, [255, 255, 255], 0.35 * LT.wD);
    var under = mix(P.mid, P.glow, 0.25 + 0.2 * LT.wN);
    for (var k = 0; k < n; k++) {
      var a = wrap(hh(k, 11, S.i, 1) * 360 + drift);
      var x = xOf(a), y = gy * (0.1 + 0.42 * hh(k, 12, S.i, 1));
      var wd = gy * (0.22 + 0.4 * hh(k, 13, S.i, 1)),
          ht = wd * (LT.cloud > 0.7 ? 0.09 : 0.15);
      if (x < -wd || x > W + wd) continue;
      ctx.globalAlpha = 0.55 + 0.35 * LT.cloud;
      for (var j = 0; j < 6; j++) {
        var ox = (hh(k, j, 21, 2) - 0.5) * wd, oy = (hh(k, j, 22, 2) - 0.5) * ht;
        var rr = ht * (0.6 + 0.8 * hh(k, j, 23, 2));
        ctx.fillStyle = rgba(under);
        ctx.beginPath(); ctx.ellipse(x + ox, y + oy + rr * 0.25, rr * 2.2, rr, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = rgba(top);
        ctx.beginPath(); ctx.ellipse(x + ox, y + oy, rr * 2.0, rr * 0.8, 0, 0, Math.PI * 2); ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
  }

  /* Rain, snow and lightning, from the reported weather. Rain leans with
     the wind across the view. Lightning is rare and soft - a short lift of
     the sky and a bolt - and never shown with reduced motion. */
  var flash = { next: 4, at: -10, x: 0 };
  function weather(SCn, P, LT, w, now) {
    var kind = LT.kind, gy = SCn.L.groundY;
    if (kind !== 'rain' && kind !== 'storm' && kind !== 'snow') return;
    var snow = kind === 'snow';
    var amt = clamp((w.precip || 0.5) / 3, 0.25, 1);
    var n = Math.round((snow ? 160 : 140) + (snow ? 160 : 360) * amt);
    var lean = clamp(windCross(w) / 40, -0.6, 0.6);
    var t = motionOff ? 0 : now;
    var pan = S.az / view() * (W - PAD * 2) * 0.6;    // a little parallax
    ctx.strokeStyle = rgba(mix(P.lit, [255, 255, 255], 0.3), snow ? 0.8 : 0.32);
    ctx.fillStyle = rgba([240, 240, 245], 0.75);
    ctx.lineWidth = Math.max(1, 0.8 * dpr);
    ctx.beginPath();
    for (var k = 0; k < n; k++) {
      var sp = snow ? (30 + 30 * hh(k, 1, 2, 3)) * dpr : (700 + 400 * hh(k, 1, 2, 3)) * dpr;
      var y = (hh(k, 4, 5, 6) * gy + sp * t) % gy;
      var x = (((hh(k, 7, 8, 9) * W + lean * y - pan +
                 (snow ? Math.sin(t * 0.8 + k) * 6 * dpr : 0)) % W) + W) % W;
      if (snow) {
        var r = (0.8 + 1.2 * hh(k, 2, 2, 2)) * dpr;
        ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, Math.PI * 2);
      } else {
        var len = 14 * dpr;
        ctx.moveTo(x, y); ctx.lineTo(x - lean * len, y - len);
      }
    }
    if (snow) ctx.fill(); else ctx.stroke();

    if (kind === 'storm' && !motionOff) {
      if (now > flash.next) {
        flash.at = now; flash.next = now + 6 + 10 * Math.random();
        flash.x = (0.15 + 0.7 * Math.random()) * W;
      }
      var age = now - flash.at;
      if (age < 0.6) {
        ctx.fillStyle = rgba([235, 235, 255], 0.16 * Math.exp(-age * 8));
        ctx.fillRect(0, 0, W, gy);
        if (age < 0.18) {
          ctx.strokeStyle = 'rgba(240,240,255,0.85)';
          ctx.lineWidth = 1.5 * dpr;
          ctx.beginPath();
          var bx = flash.x, by = gy * 0.08;
          ctx.moveTo(bx, by);
          for (var q = 1; q < 9; q++) {
            bx += (hh(q, Math.floor(flash.at * 10), 3, 3) - 0.5) * 40 * dpr;
            by += gy * 0.06;
            ctx.lineTo(bx, by);
          }
          ctx.stroke();
        }
      }
    }
  }

  function windowsLit(o, left, topY, P, now) {
    if (!o.nw) return;
    var lit = o.lit, w = o.wins, n = o.nw;
    var fz = Math.min(0.85, o.hz * 0.6 + SC.LT.fog * 1.2);
    var warm = rgba(mix(P.win, P.fog, fz)),
        cool = rgba(mix(COOL_WIN, P.fog, fz));
    var drift = motionOff ? 0 : 0.035;
    var lim = lit + drift;
    for (var pass = 0; pass < 2; pass++) {
      ctx.fillStyle = pass ? cool : warm;
      ctx.beginPath();
      var any = false;
      for (var k = 0; k < n; k++) {
        var b = k * 6;
        if (w[b + 4] > lim) break;
        if (w[b + 5] !== pass) continue;
        // a few windows switch on and off on their own: the city is lived in
        var r = w[b + 4] + (drift ? drift * Math.sin(now * 0.37 + k * 1.7) : 0);
        if (r > lit) continue;
        ctx.rect(left + w[b], topY + w[b + 1], w[b + 2], w[b + 3]);
        any = true;
      }
      if (any) ctx.fill();
    }
  }

  /* Red obstruction lights on the towers tall enough to carry them; they
     flash about once every two seconds, out of step with each other. */
  function beacon(o, P, now) {
    if (o.r[3] < 150) return;
    var on = motionOff ? 1 : ((now * 0.5 + hh(o.i, 4, 4, 4)) % 1 < 0.45 ? 1 : 0.15);
    var bx = o.x + (o.sh[5] ? o.sh[5][0] : (o.sh[3] + o.sh[4]) / 2) * o.hs;
    var by = o.topY;
    var rr = 1.6 * dpr;
    on *= 0.5 + 0.5 * SC_wN;
    ctx.fillStyle = 'rgba(255,70,55,' + (0.25 * on * (1 - o.hz)) + ')';
    ctx.beginPath(); ctx.arc(bx, by, rr * 3.2, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(255,92,72,' + (0.95 * on * (1 - o.hz * 0.7)) + ')';
    ctx.beginPath(); ctx.arc(bx, by, rr, 0, Math.PI * 2); ctx.fill();
  }

  function blimp(x, y, len, P, now) {
    var body = rgba(mix(P.ink, P.mid, 0.35)), lit = rgba(mix(P.ink, P.lit, 0.35));
    ctx.fillStyle = body;
    ctx.beginPath();
    ctx.ellipse(x, y, len, len * 0.32, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = lit;
    ctx.beginPath();
    ctx.ellipse(x, y - len * 0.06, len * 0.92, len * 0.2, 0, Math.PI * 1.05, Math.PI * 1.95);
    ctx.fill();
    ctx.fillStyle = body;
    ctx.beginPath();          // fins
    ctx.moveTo(x - len * 0.8, y); ctx.lineTo(x - len * 1.18, y - len * 0.36);
    ctx.lineTo(x - len * 1.05, y); ctx.lineTo(x - len * 1.18, y + len * 0.36);
    ctx.closePath(); ctx.fill();
    ctx.fillRect(x - len * 0.18, y + len * 0.28, len * 0.36, len * 0.1);
    var on = motionOff ? 1 : (Math.sin(now * 3) > 0.3 ? 1 : 0.2);
    ctx.fillStyle = 'rgba(255,90,70,' + on + ')';
    ctx.fillRect(x - len * 0.02, y + len * 0.38, 1.5 * dpr, 1.5 * dpr);
  }

  /* The city from above: every ring tower at its true bearing and its
     square-rooted distance from the centre, north up. The wedge is the view,
     carried back from slots to true bearings, so a wide-open stretch of the
     stage shows here as the narrow wedge of real horizon it is. Drag or
     click it to turn. */
  var MM = { x: 0, y: 0, r: 0 };
  function minimap(SCn, P) {
    var R = (W < 560 * dpr ? 38 : 52) * dpr;
    var mx0 = W - PAD - R, my0 = PAD + R + 4 * dpr;
    MM.x = mx0; MM.y = my0; MM.r = R;
    var ring = C[S.i].ring, i, dmax = 0, hmax = 0;
    for (i = 0; i < ring.length; i++) {
      dmax = Math.max(dmax, ring[i][2]); hmax = Math.max(hmax, ring[i][3]);
    }
    ctx.fillStyle = rgba(P.ink, 0.78);
    ctx.beginPath(); ctx.arc(mx0, my0, R, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = rgba(P.lit, 0.45); ctx.lineWidth = dpr;
    ctx.beginPath(); ctx.arc(mx0, my0, R, 0, Math.PI * 2); ctx.stroke();

    var b0 = bearingOfSlot(wrap(S.az - view() / 2));
    var b1 = bearingOfSlot(wrap(S.az + view() / 2));
    var sweep = wrap(b1 - b0);
    if (view() >= 359) sweep = 360;
    ctx.fillStyle = rgba(P.glow, 0.16);
    ctx.beginPath();
    ctx.moveTo(mx0, my0);
    ctx.arc(mx0, my0, R * 0.97, (b0 - 90) * Math.PI / 180,
            (b0 + sweep - 90) * Math.PI / 180);
    ctx.closePath(); ctx.fill();

    var tile = Math.max(1.2 * dpr, R * 0.035);
    for (i = 0; i < ring.length; i++) {
      var r = ring[i];
      var rr = R * 0.9 * Math.sqrt(r[2] / dmax);
      var a = r[6] * Math.PI / 180;
      var x = mx0 + rr * Math.sin(a), y = my0 - rr * Math.cos(a);
      var inView = Math.abs(delta(r[0], S.az)) <= view() / 2;
      var sz = tile * (0.6 + 1.4 * r[3] / hmax);
      ctx.fillStyle = inView ? rgba(P.win, 0.95) : rgba(P.lit, 0.35);
      ctx.fillRect(x - sz / 2, y - sz / 2, sz, sz);
    }
    ctx.fillStyle = rgba(P.lit, 0.9);
    ctx.fillRect(mx0 - dpr, my0 - dpr, 2 * dpr, 2 * dpr);
    ctx.font = (12 * dpr) + 'px ui-sans-serif, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('N', mx0, my0 - R - 4 * dpr);
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
  var last = 0, lastAmbient = 0;
  function frame(ts) {
    requestAnimationFrame(frame);
    var dt = Math.min(0.05, (ts - last) / 1000 || 0.016);
    last = ts;

    dtLast = dt;
    var az0 = S.az;
    if (S.spin) { S.az += S.spin * dt * 22; panelSoon(); }
    /* Turning eases: the hand, the keys and the map set a goal and the view
       closes on it fast (about 60 ms), so a mouse that reports 60 times a
       second still turns the city smoothly on a 144 Hz screen. A release
       mid-swing coasts. */
    if (S.azGoal != null) {
      var dg = delta(S.azGoal, S.az);
      if (motionOff || Math.abs(dg) < 0.01) { S.az = S.azGoal; S.azGoal = null; }
      else S.az += dg * Math.min(1, dt * 10);
      panelSoon();
    } else if (S.fling) {
      S.az += S.fling * dt;
      S.fling *= Math.exp(-dt * 4.5);
      if (Math.abs(S.fling) < 0.15) S.fling = 0;
      panelSoon();
    }
    S.vel = dt > 0 ? delta(S.az, az0) / dt : 0;
    /* The field of view and the clock glide too: a slider dragged or a
       button pressed sets a goal, and the view and the sky close on it. */
    if (S.fovGoal != null) {
      var df = S.fovGoal - S.fov;
      if (motionOff || Math.abs(df) < 0.05) { S.fov = S.fovGoal; S.fovGoal = null; }
      else S.fov += df * Math.min(1, dt * 9);
      panelSoon();
    }
    if (S.shiftGoal != null) {
      var ds = S.shiftGoal - S.shift;
      if (motionOff || Math.abs(ds) < 20000) { S.shift = S.shiftGoal; S.shiftGoal = null; }
      else S.shift += ds * Math.min(1, dt * 6);
      panelSoon();
    }
    /* The painting has things that move on their own - beacons, the
       searchlights, the blimp, windows - so it redraws while motion is
       allowed, at up to 30 frames a second when nothing else is changing.
       With motion off it stands still until a hand moves it. */
    var ambient = false;
    if (!motionOff) {
      clock += dt;
      // every frame: at 30 the beacons and the blimp stuttered
      ambient = true; lastAmbient = ts;
    }

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
    if (!moved && !S.spin && !dirty && !ambient && !(SC && SC.stale) &&
        S.azGoal == null && !S.fling && S.fovGoal == null &&
        S.shiftGoal == null && !fading) return;
    dirty = false;
    draw();
    blur();
    fadeOver();
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
      '<dt>Heights</dt><dd>Wikidata, each tower linked below; every one ' +
        'also mapped as a standing building in OpenStreetMap</dd>' +
      /* A thin city is kept on the list by choice, not because it clears the
         bar the other wheels clear; the panel says so beside its numbers. */
      (c.thin ? '<dt>Thin data</dt><dd>The database confirms only ' +
        c.ring.length + ' towers here, fewer than the other wheels need. ' +
        'The wheel shows those towers, not the whole skyline.</dd>' : '');

    document.getElementById('why').innerHTML =
      '<b>' + esc(c.key.label) + '</b>, from ' + esc(c.key.why) + '. ' +
      '<span class="tier">' + c.key.tier.toLowerCase() + '</span>';
    var vo = VOICING[c.key.mode] || VOICING.major;
    document.getElementById('voice').textContent =
      'Voiced as ' + vo.says + ', with the root an octave down as the ' +
      'lowest note. ' +
      'A choice, like the key.';

    /* The list is the wheel, in the order it is drawn, with whatever is
       currently on the near face marked. It used to be the twenty tallest in
       true-bearing order, which no longer matched anything on screen. */
    /* The canvas's aria-label says "the towers ... are listed as text in the
       panel", and for New York that was 40 of 120. A text alternative that
       silently holds a third of the picture is a claim, not an alternative,
       so the list says what it is: the cap is reported beside it, from the
       same numbers the stats already carry. */
    var onWheel = c.ring.filter(function (r) { return r[4]; });
    var named = onWheel.slice()
                 .sort(function (p, q) { return q[3] - p[3]; }).slice(0, 40);
    var cap = document.getElementById('listcap');
    /* NAMED, not "on the wheel": the stat above counts every tower at or
       above 55 m and this counts the ones with a name to list, so New York
       reads 120 there and 119 here. Two numbers a line apart differing by one
       is worse than either, so each says which set it is. */
    if (cap) cap.textContent = named.length < onWheel.length
      ? 'The tallest ' + named.length + ' of ' + onWheel.length +
        ' named towers on the wheel. The rest are drawn but not listed.'
      : 'All ' + onWheel.length + ' named towers on the wheel.';
    document.getElementById('towers').innerHTML = named.map(function (r) {
      var front = Math.abs(delta(r[0], S.az)) <= view() / 2;
      /* A building links to the Wikidata record it came from. Every tower
         has one since the hand-entered supplements were retired
         (2026-10-24); a row without one stays plain text rather than a
         link that goes nowhere. */
      var label = r[7]
        ? '<a href="https://www.wikidata.org/wiki/' + esc(r[7]) +
          '" target="_blank" rel="noopener">' + esc(r[4]) + '</a>'
        : esc(r[4]);
      return '<li' + (front ? ' class="in"' : '') + '><b>' + label +
             '</b> <span>' + r[3].toFixed(0) + ' m' +
             (r[5] ? ' &middot; ' + r[5] : '') + ' &middot; ' +
             compass(Math.round(r[6] / 45) * 45 % 360) + ' of centre' +
             (front ? '' : ' &middot; out of view') + '</span></li>';
    }).join('') || '<li>no named towers in this city</li>';

    /* How this city's towers got their shapes, counted from the same
       records the tooltips read. */
    var looks = document.getElementById('looks');
    if (looks) {
      var n = [0, 0, 0, 0, 0], nd = 0;
      SHAPES[S.i].forEach(function (sh) { n[sh[0]]++; if (sh[5]) nd++; });
      var bits = [];
      if (n[0]) bits.push(n[0] + ' modelled in 3D by OpenStreetMap mappers, ' +
                          'every part at its own height');
      if (n[1]) bits.push(n[1] + ' from their OpenStreetMap outline, ' +
                          'raised to their height');
      if (n[2]) bits.push(n[2] + ' drawn by hand from published heights, ' +
                          'plans and photographs, where the mapped shape ' +
                          'was missing or wrong');
      if (n[3]) bits.push(n[3] + ' with no outline to draw from, shown ' +
                          'as plain slabs');
      if (n[4]) bits.push(n[4] + ' mapped only as part of a larger complex, ' +
                          'shown as a plain slab on its podium');
      looks.textContent = 'Of the ' + c.ring.length + ' towers here: ' +
        bits.join('; ') + '.' + (nd ? ' On ' + nd + ', the mapped shape ' +
        'stops short of the recorded height and the rest is drawn as a ' +
        'spire or mast.' : '');
    }

    when();

    document.getElementById('az').textContent =
      'bearing ' + Math.round(wrap(S.az)) + '°  ·  ' + Math.round(view()) +
      '° wide';
  }

  /* The clock line, and the slider kept on the city's time while it is
     live. */
  var timeEl = document.getElementById('time'), nowBtn = document.getElementById('now');
  function compassWord(b) {
    return ['north', 'north-east', 'east', 'south-east', 'south', 'south-west',
            'west', 'north-west'][Math.round(wrap(b) / 45) % 8];
  }
  function when() {
    var el = document.getElementById('when');
    if (!el) return;
    var c = C[S.i], t = instant(), lp = localParts(t);
    var sk = sky(t, c.centre[0], c.centre[1]);
    var se = sk.sun.el / RAD, me = sk.moon.el / RAD;
    var hm = (lp.h < 10 ? '0' : '') + lp.h + ':' + (lp.m < 10 ? '0' : '') + lp.m;
    var bits = [];
    if (se > 0) bits.push('The sun is ' + Math.round(se) + '\u00b0 up in the ' +
                          compassWord(sk.sun.az));
    else if (se > -6) bits.push('Twilight');
    else bits.push('Night');
    var ph = sk.moon.phase, pw = sk.moon.frac < 0.03 ? 'a new moon'
      : sk.moon.frac > 0.97 ? 'a full moon'
      : Math.round(sk.moon.frac * 100) + '% of a ' + (ph < 0.5 ? 'waxing' : 'waning') + ' moon';
    bits.push(me > 0 ? pw + ' ' + Math.round(me) + '\u00b0 up in the ' +
                       compassWord(sk.moon.az) : pw + ', below the horizon');
    var w = wx();
    var wt = w.ok ? (Math.round(w.temp) + '\u00b0C, ' + WX_WORD[wxKind(w)] +
                     ', ' + Math.round(w.cloud * 100) + '% cloud')
      : (w.pending ? 'weather loading' : 'weather unavailable, drawn clear');
    el.textContent = (S.shift ? 'Showing ' + hm + ' in ' + c.city + ' (now ' +
                      fmt(localParts(Date.now())) + '). ' : hm + ' in ' + c.city + '. ') +
                     bits.join('; ') + '. Weather now: ' + wt + '.';
    if (!S.shift && timeEl) timeEl.value = Math.round(lp.mins / 5) * 5;
    if (nowBtn) nowBtn.classList.toggle('on', !S.shift);
  }
  function fmt(lp) {
    return (lp.h < 10 ? '0' : '') + lp.h + ':' + (lp.m < 10 ? '0' : '') + lp.m;
  }
  if (timeEl) timeEl.addEventListener('input', function () {
    var cur = localParts(Date.now()).mins;
    S.shiftGoal = (+this.value - cur) * 60000;
    touch(); panelSoon();
  });
  if (nowBtn) nowBtn.addEventListener('click', function () {
    S.shiftGoal = 0; touch(); panel();
  });
  // the clock line moves with the clock
  setInterval(function () { if (!document.hidden) when(); }, 30000);

  /* ------------------------------------------------------------ events -- */
  var drag = null;
  canvas.addEventListener('pointerdown', function (e) {
    S.fling = 0;
    if (onMap(e)) {
      drag = { map: true };
      S.spin = 0; spinBtn.classList.remove('on');
      canvas.setPointerCapture(e.pointerId);
      return;
    }
    drag = { x: e.clientX, az: S.az };
    S.spin = 0; spinBtn.classList.remove('on');
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', function (e) {
    if (drag && drag.map) { onMap(e); return; }
    if (drag) {
      var r = canvas.getBoundingClientRect();
      var goal = drag.az - (e.clientX - drag.x) / r.width * view();
      // remember how fast the hand is moving, for the fling on release
      var nowT = performance.now();
      if (drag.lt) drag.v = 0.7 * (drag.v || 0) +
        0.3 * delta(goal, drag.lg) / Math.max(0.008, (nowT - drag.lt) / 1000);
      drag.lt = nowT; drag.lg = goal;
      aim(goal);
      touch(); panelSoon();
      return;
    }
    hover(e);
  });
  canvas.addEventListener('pointerup', function () {
    // let go mid-swing and the view coasts to a stop
    /* Hand the view's actual speed straight to the coast and drop what was
       left of the ease, so the motion carries on with no seam: no stop
       followed by a second push. A hand that had come to rest just settles. */
    if (drag && !drag.map && S.azGoal != null && !motionOff &&
        performance.now() - (drag.lt || 0) < 80 && Math.abs(S.vel || 0) > 3) {
      S.fling = clamp(S.vel, -400, 400);
      S.azGoal = null;
    }
    drag = null;
  });
  canvas.addEventListener('pointerleave', function () {
    drag = null; tip.style.display = 'none';
  });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    aim((S.azGoal == null ? S.az : S.azGoal) + Math.sign(e.deltaY) * 4);
    touch(); panelSoon();
  }, { passive: false });

  var SRC = ['modelled in 3D in OpenStreetMap',
             'its OpenStreetMap outline, raised to its height',
             'drawn by hand from published heights, plans and photographs',
             'no outline found: a plain slab',
             'its OpenStreetMap outline as the podium, which covers a whole ' +
             'complex; the tower above it is a plain slab'];
  function hover(e) {
    var r = canvas.getBoundingClientRect();
    var px = (e.clientX - r.left) * dpr, py = (e.clientY - r.top) * dpr;
    var near = null;
    if (SC) {
      // nearest first: the tower drawn last at this point is the one seen
      for (var k = SC.order.length - 1; k >= 0; k--) {
        var o = SC.order[k];
        if (o.vis && px >= o.left && px <= o.right && py >= o.topY &&
            py <= o.base) { near = o; break; }
      }
    }
    if (!near || !near.r[4]) { tip.style.display = 'none'; return; }
    var b = near.r, sh = near.sh;
    tip.innerHTML = '<b>' + esc(b[4]) + '</b><br>' + b[3].toFixed(0) +
                    ' m &middot; ' + (b[2] <= 0.4 ? 'under 0.4' :
                                      b[2].toFixed(1)) +
                    ' km from the centre' +
                    (b[5] ? ' &middot; ' + b[5] : '') +
                    '<br><span class="src">Shape: ' + SRC[sh[0]] +
                    (sh[0] === 0 ? ' (' + sh[6].length + ' parts)' : '') +
                    (sh[0] === 2 && sh[7] >= 0 ? ', ' +
                      ['high', 'medium', 'low'][sh[7]] + ' confidence' : '') +
                    (sh[8] ? ', checked against photographs' : '') +
                    (sh[5] ? '; spire or mast to the recorded height' : '') +
                    '</span>';
    tip.style.display = 'block';
    tip.style.left = Math.min(r.width - tip.offsetWidth - 8,
                              Math.max(4, e.clientX - r.left + 14)) + 'px';
    tip.style.top = Math.max(4, e.clientY - r.top - 66) + 'px';
  }

  /* The map turns the stage: a press or drag on it faces the bearing under
     the pointer. */
  function onMap(e) {
    var r = canvas.getBoundingClientRect();
    var px = (e.clientX - r.left) * dpr, py = (e.clientY - r.top) * dpr;
    var dx = px - MM.x, dy = py - MM.y;
    if (dx * dx + dy * dy > MM.r * MM.r * 1.1) return false;
    if (dx * dx + dy * dy < 4 * dpr * dpr) return true;
    var b = wrap(Math.atan2(dx, -dy) * 180 / Math.PI);
    aim(slotOfBearing(b));
    touch(); panelSoon();
    return true;
  }

  window.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (tag === 'SELECT' || tag === 'INPUT' || tag === 'BUTTON') return;
    var step = e.shiftKey ? 15 : 3;
    var base = S.azGoal == null ? S.az : S.azGoal;
    if (e.key === 'ArrowLeft') aim(base - step);
    else if (e.key === 'ArrowRight') aim(base + step);
    else if (e.key === ' ') { if (!motionOff) spinBtn.click(); }
    else return;
    e.preventDefault();
    touch(); panelSoon();
  });

  document.getElementById('city').addEventListener('change', function () {
    startFade(520);
    S.azGoal = null; S.fling = 0; S.fovGoal = null;
    S.i = +this.value;
    S.az = C[S.i].look;
    if (!S.fovSet) {
      S.fov = defaultFov(S.i);
      document.getElementById('fov').value = S.fov;
    }
    SC = null;
    fetchWeather();
    lvl.fill(0); pk.fill(0); pkv.fill(0);
    setKey(); touch(); panel();
  });
  document.getElementById('fov').addEventListener('input', function () {
    S.fovGoal = +this.value; S.fovSet = true; touch(); panelSoon();
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

  /* The phone sidebar's "more below" cue (template.html, .more): shown while
     the box has content below its fold, hidden at the end and when nothing
     scrolls. Defensive, because the harness's DOM has no layout. */
  (function () {
    var side = document.getElementById('side');
    if (!side || typeof side.addEventListener !== 'function') return;
    function cue() {
      var atEnd = side.scrollHeight - side.clientHeight - side.scrollTop < 4 ||
                  side.scrollHeight <= side.clientHeight;
      /* The cue is a sibling of #side now, not a child, so the class goes on
         the wrapper that holds both. The measurement still comes from #side:
         it is the box that scrolls. */
      var wrap = document.getElementById('sidewrap') || side;
      if (wrap.classList && wrap.classList.toggle) wrap.classList.toggle('end', atEnd);
    }
    side.addEventListener('scroll', cue);
    window.addEventListener('resize', cue);
    /* The city list, the stats and the tower list are all filled by script
       after this runs, so cue() at boot measured an empty panel, found it did
       not scroll, and set the end class. At 1440 the panel was already long
       enough for that to be wrong immediately; at 1920 the taller viewport
       hid it until the panel filled, and nothing fired afterwards - 2,109px
       sat below a cue that had hidden itself. Recompute when the content
       changes, not only when the reader does something. */
    if (window.MutationObserver)
      new MutationObserver(cue).observe(side, {childList: true, subtree: true,
                                               characterData: true});
    cue();
  })();

  /* --------------------------------------------------------------- boot -- */
  document.getElementById('city').innerHTML = C.map(function (c, i) {
    return '<option value="' + i + '">' + esc(c.city) + ' &middot; ' +
           esc(c.key.label) + (c.thin ? ' &middot; thin data' : '') +
           '</option>';
  }).join('');
  S.az = C[0].look;
  fetchWeather();
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
    scene: function () { return scene(); }, layout: function () { return layout(); },
    slotOfBearing: slotOfBearing, bearingOfSlot: bearingOfSlot,
    defaultFov: defaultFov,
    localMins: function () { return localParts(Date.now()).mins; },
    shapes: SHAPES, sky: function () { return CITY_SKY[C[S.i].city]; },
    pitches: function () { return pitch; },
    voicing: VOICING, clashes: function () { return voicingClash; },
    motionOff: function () { return motionOff; },
    notes: function () { return notesLast; },
    barOf: function (k) { return barTo[k]; },
    levels: function () { return lvl; }, BARS: BARS,
    // what each oscillator is sent, after pushAudio(): the loudness test
    push: pushAudio,
    sent: function () {
      return parts.map(function (p) { return p.g.gain.value; });
    },
    level: function () { return levelNode ? levelNode.gain.value : 0; },
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
