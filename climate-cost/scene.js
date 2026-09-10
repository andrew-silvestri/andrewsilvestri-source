/* The life cycle as a place you can walk around.
 *
 * A footprint printed as a number ends the conversation. A tree printed as an
 * indented list continues it, but badly: at four levels deep the indentation
 * has eaten the page and the eye cannot tell a large branch from a small one
 * without reading every figure. So the same graph is put in space.
 *
 * The composition is two objects and one idea:
 *
 *   The globe carries the geography. Producing region, consuming region, and
 *   the freight route drawn as the great circle it actually is, lifted off the
 *   surface. A flat map would place Spain and Texas at a distance that depends
 *   on the projection; a sphere places them at the distance the model used.
 *
 *   The spine carries the chronology. Cultivation to bin, left to right, one
 *   ball per life-cycle stage. It is a straight line because the thing itself
 *   happens in a straight line.
 *
 *   Everything else hangs off the spine as a cone of branches, and each branch
 *   is itself a cone. That recursion is the point of the model, and it is the
 *   one thing a list cannot show: a tomato needs fertiliser, the fertiliser
 *   needs ammonia, the ammonia needs gas, and getting the gas leaks methane.
 *   Four levels, four real emissions, all of them in one tomato.
 *
 * The freight branch is the exception. Instead of hanging in the fan with its
 * siblings it is placed at the apex of the great-circle arc, so the edge that
 * joins it to its stage visibly crosses from the chain to the world. Freight
 * is the one step whose size is set by geography rather than chemistry, and
 * that is worth being able to see rather than read.
 *
 * Progressive enhancement throughout: the list is not a fallback bolted on
 * afterwards, it is the same tree rendered a second way, and it is one button
 * away at all times. Without WebGL the page opens straight into it.
 */
(function () {
  'use strict';

  /* ------------------------------------------------------------ helpers -- */
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  };
  var fmt = function (v) {
    var a = Math.abs(v);
    return a >= 10 ? v.toFixed(1) : a >= 1 ? v.toFixed(2)
         : a >= 0.01 ? v.toFixed(3) : v.toFixed(4);
  };
  var css = function (n) {
    return getComputedStyle(document.documentElement)
             .getPropertyValue(n).trim();
  };

  /* Colour says what kind of emission this is, and it is derived from the
     process record rather than from a hand-kept list, so a process added to
     the data gets a colour without anyone remembering to come back here. */
  var COMBUSTION = /gas|diesel|heat|landfill|n2o|burn|coal|oil/i;
  function kindOf(n) {
    if (n.spine) return 'acc';
    if (D.transport[n.id] || String(n.id).indexOf('freight_') === 0)
      return 'moss';
    var pr = D.processes[n.id];
    if (pr && pr.grid_scaled) return 'cool';
    if (COMBUSTION.test(String(n.id))) return 'rose';
    return 'slate';
  }
  var PAL = {};
  /* The scene's five node colours come from the --scene-* tokens, not the
     page's --acc/--moss/...: the nodes sit on the dark sea, and the page's
     colours are chosen for paper (the brown --moss is 1.6:1 on the sea).
     The legend in the panel uses the same --scene-* names, so what the
     key shows is what the globe draws. (2026-09-04) */
  function palette() {
    PAL = { acc: css('--scene-acc'), moss: css('--scene-moss'), cool: css('--scene-cool'),
            rose: css('--scene-rose'), slate: css('--scene-slate'), dim: css('--dim'),
            ink: css('--ink'), rule: css('--rule') };
  }
  palette();
  var colourOf = function (n) { return PAL[kindOf(n)]; };

  /* ---------------------------------------------------------- geometry -- */
  var RAD = Math.PI / 180;
  var GLOBE_R = 1.55;
  var SPACING = 1.75;
  var GLOBE_GAP = 2.9;          // globe surface to the first stage

  function lonlat(lon, lat, r) {
    var la = lat * RAD, lo = lon * RAD, cl = Math.cos(la);
    return new THREE.Vector3(r * cl * Math.sin(lo), r * Math.sin(la),
                             r * cl * Math.cos(lo));
  }

  /* An arbitrary unit vector perpendicular to d. Picking the world axis that d
     is least aligned with avoids the degenerate cross product that would
     otherwise appear exactly when a branch points straight up. */
  function perp(d) {
    var a = Math.abs(d.x) < 0.9 ? new THREE.Vector3(1, 0, 0)
                                : new THREE.Vector3(0, 1, 0);
    return new THREE.Vector3().crossVectors(d, a).normalize();
  }

  /* Lay the whole result out in space.
     Returns a flat list of placed nodes, each keeping a reference to its
     parent and its source record, plus the edge list. */
  function layout(res) {
    var nodes = [], edges = [], maxAbs = 0;

    (function scan(n) {
      maxAbs = Math.max(maxAbs, Math.abs(n.total));
      (n.children || []).forEach(scan);
    })({ total: 0, children: res.spine });

    var n = res.spine.length;
    var x0 = -(n - 1) * SPACING / 2;

    function radius(t, spine) {
      var f = maxAbs > 0 ? Math.pow(Math.abs(t) / maxAbs, 1 / 3) : 0;
      return spine ? 0.13 + 0.30 * f : 0.045 + 0.235 * f;
    }

    function add(src, pos, depth, parent, spine) {
      var nd = {
        src: src, id: src.id, name: src.name, total: src.total,
        direct: src.direct, alloc: src.alloc, amount: src.amount,
        unit: src.unit, note: src.note, quality: src.quality,
        basis: src.basis || '',
        pos: pos, depth: depth, parent: parent, spine: !!spine,
        kids: [], r: radius(src.total, spine)
      };
      nd.colour = colourOf(nd);
      if (parent) { parent.kids.push(nd); edges.push([parent, nd]); }
      nodes.push(nd);
      return nd;
    }

    /* The recursive fan. Children are spread on a cone about the direction the
       parent was already travelling, so a branch keeps going the way it was
       going and opens as it goes - which is what makes the shape read as one
       structure rather than as a pile of stars. */
    function place(parent, dir, depth) {
      var kids = (parent.src.children || []).slice()
                   .sort(function (a, b) {
                     return Math.abs(b.total) - Math.abs(a.total);
                   })
                   .filter(function (c) { return !c.__placed; });
      var k = kids.length;
      if (!k || depth > 6) return;
      var len = 1.30 * Math.pow(0.71, depth - 1);
      var half = depth === 1 ? 0.80 : 0.52;
      var u = perp(dir), v = new THREE.Vector3().crossVectors(dir, u);
      for (var j = 0; j < k; j++) {
        var a = k === 1 ? 0.18 : half;
        var phi = k === 1 ? 0 : (j / k) * Math.PI * 2 + depth * 0.9;
        var cd = dir.clone().multiplyScalar(Math.cos(a))
                   .addScaledVector(u, Math.sin(a) * Math.cos(phi))
                   .addScaledVector(v, Math.sin(a) * Math.sin(phi))
                   .normalize();
        var cp = parent.pos.clone().addScaledVector(cd, len);
        var nd = add(kids[j], cp, depth, parent, false);
        place(nd, cd, depth + 1);
      }
    }

    var globeC = new THREE.Vector3(x0 - GLOBE_GAP - GLOBE_R, 0, 0);

    res.spine.forEach(function (st, i) {
      var p = new THREE.Vector3(x0 + i * SPACING, 0, 0);
      var nd = add(st, p, 0, null, true);
      nd.idx = i;

      /* The freight child is pinned to the route rather than fanned, so the
         edge from its stage crosses the gap to the globe. */
      var fr = (st.children || []).filter(function (c) {
        return String(c.id).indexOf('freight_') === 0;
      })[0];
      if (fr) {
        fr.__placed = true;
        var apex = res.__arcApex ? res.__arcApex.clone()
                                 : globeC.clone().add(
                                     new THREE.Vector3(0, GLOBE_R + 0.9, 0));
        var fn = add(fr, apex, 1, nd, false);
        fn.onRoute = true;
      }

      /* Each stage rolls its fan by the golden angle so that consecutive fans
         interleave instead of stacking in the same plane. */
      var roll = i * 2.39996;
      place(nd, new THREE.Vector3(0, -Math.cos(roll), Math.sin(roll))
                  .normalize(), 1);
    });

    relax(nodes);
    return { nodes: nodes, edges: edges, globeC: globeC, maxAbs: maxAbs };
  }

  /* Push overlapping balls apart. Layout by rule alone will occasionally sit
     two branches on top of each other; a few relaxation passes fix that
     without moving anything far enough to lie about the structure. Spine
     nodes are pinned, because their positions carry meaning. */
  function relax(nodes) {
    for (var pass = 0; pass < 10; pass++) {
      for (var i = 0; i < nodes.length; i++) {
        for (var j = i + 1; j < nodes.length; j++) {
          var a = nodes[i], b = nodes[j];
          if (a.parent === b || b.parent === a) continue;
          var d = a.pos.distanceTo(b.pos), want = a.r + b.r + 0.10;
          if (d >= want || d < 1e-6) continue;
          var push = (want - d) / 2;
          var dir = b.pos.clone().sub(a.pos).divideScalar(d);
          if (!a.spine && !a.onRoute) a.pos.addScaledVector(dir, -push);
          if (!b.spine && !b.onRoute) b.pos.addScaledVector(dir, push);
        }
      }
    }
  }

  /* ------------------------------------------------------------- three -- */
  var canvas = document.getElementById('gl');
  var labels = document.getElementById('labels');
  var hoverEl = document.getElementById('hover');
  var renderer, scene, camera, sceneOK = false, hasTHREE = false;
  var group = null, meshes = [], globeGrp, routeGrp;
  var picked = null, selected = null;
  var view = { az: 0.62, el: 0.30, dist: 15.5,
               target: new THREE.Vector3(),
               want: { az: 0.62, el: 0.30, dist: 15.5,
                       target: new THREE.Vector3() } };
  var HOME = null;

  function initGL() {
    if (!window.THREE) return false;
    hasTHREE = true;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(36, 1, 0.05, 400);
    scene.add(new THREE.AmbientLight(0xffffff, 0.72));
    var key = new THREE.DirectionalLight(0xffffff, 0.62);
    key.position.set(2, 3, 4);
    scene.add(key);
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvas, antialias: true, alpha: true,
        powerPreference: 'low-power'
      });
    } catch (e) { return false; }
    if (!renderer || !renderer.getContext()) return false;
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    sceneOK = true;
    return true;
  }

  /* The globe: a dark body, a fresnel rim so the limb reads against the
     background, coastlines, and a graticule every thirty degrees so that
     rotation looks like rotation rather than like drift. */
  function buildGlobe(centre) {
    var g = new THREE.Group();
    g.position.copy(centre);

    g.add(new THREE.Mesh(new THREE.SphereGeometry(GLOBE_R, 64, 48),
      new THREE.MeshBasicMaterial({ color: 0x0b1226 })));

    g.add(new THREE.Mesh(new THREE.SphereGeometry(GLOBE_R * 1.05, 64, 48),
      new THREE.ShaderMaterial({
        transparent: true, side: THREE.BackSide, depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: { c: { value: new THREE.Color(0x6f8ae0) } },
        vertexShader:
          'varying float i;void main(){vec3 n=normalize(normalMatrix*normal);' +
          'vec4 mv=modelViewMatrix*vec4(position,1.);' +
          'i=pow(1.0-abs(dot(n,normalize(-mv.xyz))),2.8);' +
          'gl_Position=projectionMatrix*mv;}',
        fragmentShader:
          'uniform vec3 c;varying float i;' +
          'void main(){gl_FragColor=vec4(c,i*0.75);}'
      })));

    var cp = [];
    (D.coast || []).forEach(function (ring) {
      for (var i = 0; i < ring.length - 1; i++) {
        var a = lonlat(ring[i][0], ring[i][1], GLOBE_R * 1.003);
        var b = lonlat(ring[i + 1][0], ring[i + 1][1], GLOBE_R * 1.003);
        if (a.distanceTo(b) > GLOBE_R * 0.5) continue;
        cp.push(a.x, a.y, a.z, b.x, b.y, b.z);
      }
    });
    var cg = new THREE.BufferGeometry();
    cg.setAttribute('position', new THREE.Float32BufferAttribute(cp, 3));
    g.add(new THREE.LineSegments(cg, new THREE.LineBasicMaterial({
      color: 0x6f8ab4, transparent: true, opacity: 0.46 })));

    var gp = [];
    for (var lo = -150; lo <= 180; lo += 30)
      for (var la = -80; la < 80; la += 5) {
        var a1 = lonlat(lo, la, GLOBE_R), b1 = lonlat(lo, la + 5, GLOBE_R);
        gp.push(a1.x, a1.y, a1.z, b1.x, b1.y, b1.z);
      }
    for (var la2 = -60; la2 <= 60; la2 += 30)
      for (var lo2 = -180; lo2 < 180; lo2 += 5) {
        var a2 = lonlat(lo2, la2, GLOBE_R), b2 = lonlat(lo2 + 5, la2, GLOBE_R);
        gp.push(a2.x, a2.y, a2.z, b2.x, b2.y, b2.z);
      }
    var gg = new THREE.BufferGeometry();
    gg.setAttribute('position', new THREE.Float32BufferAttribute(gp, 3));
    g.add(new THREE.LineSegments(gg, new THREE.LineBasicMaterial({
      color: 0x2a3352, transparent: true, opacity: 0.5 })));
    return g;
  }

  /* The great circle, lifted so it clears the surface at its midpoint by an
     amount proportional to how far it goes. A short hop stays near the ground;
     a Peru-to-China route arches. Spherical linear interpolation gives the
     true path, which is the same path route_km measured. */
  function arcPoints(o, d, lift) {
    var a = lonlat(D.regions[o].lon, D.regions[o].lat, 1).normalize();
    var b = lonlat(D.regions[d].lon, D.regions[d].lat, 1).normalize();
    var ang = Math.acos(Math.max(-1, Math.min(1, a.dot(b))));
    var pts = [], N = 96;
    for (var i = 0; i <= N; i++) {
      var t = i / N, p;
      if (ang < 1e-6) { p = a.clone(); }
      else {
        p = a.clone().multiplyScalar(Math.sin((1 - t) * ang) / Math.sin(ang))
             .addScaledVector(b, Math.sin(t * ang) / Math.sin(ang)).normalize();
      }
      var h = GLOBE_R * (1.012 + lift * Math.sin(Math.PI * t));
      pts.push(p.multiplyScalar(h));
    }
    return pts;
  }

  function marker(lon, lat, colour, r) {
    var m = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 14),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(colour) }));
    m.position.copy(lonlat(lon, lat, GLOBE_R * 1.015));
    return m;
  }

  /* ---------------------------------------------------------- the build -- */
  var placed = null, res = null;

  function build(result) {
    res = result;
    if (!hasTHREE) return;
    if (group) { scene.remove(group); disposeGroup(group); }
    group = new THREE.Group();
    meshes = [];

    var item = document.getElementById('item').value;
    var o = document.getElementById('origin').value;
    var d = document.getElementById('dest').value;

    var n = result.spine.length;
    var x0 = -(n - 1) * SPACING / 2;
    var globeC = new THREE.Vector3(x0 - GLOBE_GAP - GLOBE_R, 0, 0);

    /* the arc first, because the freight node is pinned to its apex */
    var lift = 0.10 + 0.42 * Math.min(1, result.km / 18000);
    var pts = arcPoints(o, d, lift);
    result.__arcApex = pts[Math.floor(pts.length / 2)].clone().add(globeC);

    placed = layout(result);

    globeGrp = buildGlobe(globeC);
    globeGrp.add(marker(D.regions[o].lon, D.regions[o].lat, PAL.acc, 0.062));
    globeGrp.add(marker(D.regions[d].lon, D.regions[d].lat, PAL.cool, 0.062));
    var ag = new THREE.BufferGeometry().setFromPoints(pts);
    globeGrp.add(new THREE.Line(ag, new THREE.LineBasicMaterial({
      color: new THREE.Color(PAL.moss), transparent: true, opacity: 0.95 })));
    group.add(globeGrp);

    /* What happens at the far end depends on what the thing is. The label
       used to read "eaten here" for everything, which was true of nine
       products and wrong for the cars, flights and clothing. */
    var grp = (D.products[item] || {}).group;
    var ends = grp === 'Food'      ? 'eaten here'
             : grp === 'Clothing'  ? 'worn here'
             : grp === 'Transport' ? 'journey ends here'
             : 'used here';
    var starts = grp === 'Food' ? 'grown here'
               : grp === 'Transport' ? 'journey starts here'
               : 'made here';
    globeGrp.userData.pins = [
      { lon: D.regions[o].lon, lat: D.regions[o].lat,
        text: D.regions[o].name + ' &middot; ' + starts },
      { lon: D.regions[d].lon, lat: D.regions[d].lat,
        text: D.regions[d].name + ' &middot; ' + ends }
    ];

    /* edges */
    var ep = [], ec = [];
    placed.edges.forEach(function (e) {
      var c = new THREE.Color(e[1].colour);
      ep.push(e[0].pos.x, e[0].pos.y, e[0].pos.z,
              e[1].pos.x, e[1].pos.y, e[1].pos.z);
      ec.push(c.r * 0.45, c.g * 0.45, c.b * 0.45, c.r, c.g, c.b);
    });
    // the spine itself, drawn brighter, because it is the thing being read
    for (var i = 0; i < placed.nodes.length; i++) {
      var a = placed.nodes[i];
      if (!a.spine || a.idx === 0) continue;
      var prev = placed.nodes.filter(function (x) {
        return x.spine && x.idx === a.idx - 1; })[0];
      var col = new THREE.Color(PAL.acc);
      ep.push(prev.pos.x, prev.pos.y, prev.pos.z, a.pos.x, a.pos.y, a.pos.z);
      ec.push(col.r, col.g, col.b, col.r, col.g, col.b);
    }
    var eg = new THREE.BufferGeometry();
    eg.setAttribute('position', new THREE.Float32BufferAttribute(ep, 3));
    eg.setAttribute('color', new THREE.Float32BufferAttribute(ec, 3));
    group.add(new THREE.LineSegments(eg, new THREE.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.62 })));

    /* nodes */
    var ball = new THREE.SphereGeometry(1, 20, 14);
    placed.nodes.forEach(function (nd) {
      var m = new THREE.Mesh(ball, new THREE.MeshLambertMaterial({
        color: new THREE.Color(nd.colour) }));
      m.position.copy(nd.pos);
      m.scale.setScalar(nd.r);
      m.userData.node = nd;
      nd.mesh = m;
      group.add(m);
      meshes.push(m);

      /* Allocation as an open ring. A node that carries the whole of its
         process gets no ring at all - drawing a full circle on every node
         would make the exception invisible, which is the opposite of the
         point. */
      if (Math.abs(nd.alloc - 1) > 1e-6 && nd.alloc > 0) {
        var rg = new THREE.RingGeometry(nd.r * 1.55, nd.r * 1.95, 40, 1,
                                        Math.PI / 2,
                                        Math.max(0.06, nd.alloc) * Math.PI * 2);
        var rm = new THREE.Mesh(rg, new THREE.MeshBasicMaterial({
          color: new THREE.Color(nd.colour), side: THREE.DoubleSide,
          transparent: true, opacity: 0.85, depthWrite: false }));
        rm.position.copy(nd.pos);
        rm.userData.billboard = true;
        nd.ring = rm;
        group.add(rm);
      }
    });

    scene.add(group);
    lastLabels = null;
    touch();

    var span = (n - 1) * SPACING + GLOBE_GAP + GLOBE_R * 2;
    HOME = { az: 0.62, el: 0.30, dist: span * 1.12,
             target: new THREE.Vector3(-GLOBE_GAP * 0.34, -0.35, 0) };
    if (!build.been) { resetView(true); build.been = true; }
    else { view.want.target.copy(HOME.target); }
    selected = null;
    showSelection(null);
  }

  function disposeGroup(g) {
    g.traverse(function (o) {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        (Array.isArray(o.material) ? o.material : [o.material])
          .forEach(function (m) { m.dispose(); });
      }
    });
  }

  function resetView(now) {
    if (!HOME) return;
    view.want.az = HOME.az; view.want.el = HOME.el;
    view.want.dist = HOME.dist; view.want.target.copy(HOME.target);
    if (now) {
      view.az = HOME.az; view.el = HOME.el; view.dist = HOME.dist;
      view.target.copy(HOME.target);
    }
    touch();
  }

  /* ------------------------------------------------------------- camera -- */
  /* The scene is static unless somebody is moving it. A requestAnimationFrame
     loop that renders unconditionally keeps a GPU and a core busy drawing the
     same frame forever, which on a laptop is a fan spinning up for a picture
     that is not changing. Anything that can alter the image marks the scene
     dirty; the loop renders while it is dirty and while the camera is still
     easing towards where it was sent, and then stops. */
  var dirty = true;
  function touch() { dirty = true; }

  function settled() {
    return Math.abs(view.want.az - view.az) < 1e-4 &&
           Math.abs(view.want.el - view.el) < 1e-4 &&
           Math.abs(view.want.dist - view.dist) < 1e-3 &&
           view.target.distanceToSquared(view.want.target) < 1e-6;
  }

  function applyCamera() {
    var k = 0.14;
    view.az += (view.want.az - view.az) * k;
    view.el += (view.want.el - view.el) * k;
    view.dist += (view.want.dist - view.dist) * k;
    view.target.lerp(view.want.target, k);
    var ce = Math.cos(view.el);
    camera.position.set(
      view.target.x + view.dist * ce * Math.sin(view.az),
      view.target.y + view.dist * Math.sin(view.el),
      view.target.z + view.dist * ce * Math.cos(view.az));
    camera.lookAt(view.target);
  }

  function focus(nd) {
    if (!nd) { resetView(false); return; }
    view.want.target.copy(nd.pos);
    touch();
    var reach = 0;
    (function walk(x) {
      reach = Math.max(reach, x.pos.distanceTo(nd.pos));
      x.kids.forEach(walk);
    })(nd);
    view.want.dist = Math.max(2.4, reach * 2.6 + nd.r * 8);
  }

  /* ------------------------------------------------------------ picking -- */
  var ray = new THREE.Raycaster();
  function pick(cx, cy) {
    if (!sceneOK || !meshes.length) return null;
    var b = canvas.getBoundingClientRect();
    var v = new THREE.Vector2(((cx - b.left) / b.width) * 2 - 1,
                              -((cy - b.top) / b.height) * 2 + 1);
    ray.setFromCamera(v, camera);
    var hit = ray.intersectObjects(meshes, false);
    return hit.length ? hit[0].object.userData.node : null;
  }

  /* ------------------------------------------------------------- labels -- */
  /* Project, sort by importance, place greedily, drop what will not fit.
     Dropping a label is a loss; drawing it across another one loses both.

     Two things earn most of the legibility. Stage labels alternate above and
     below the spine, because seven names on one horizontal line at an oblique
     angle will always collide - the spine is foreshortened but the text is
     not. And every label gets a short ladder of vertical offsets to try before
     it is given up on, which recovers most of the rest.

     This is written as a pure function of camera and viewport so that the
     test harness can measure the real placer rather than a copy of it. A copy
     is a thing that passes while the page fails. */
  var pv = new THREE.Vector3();
  var LADDER = [0, -15, 15, -30, 30, -46, 46];

  /* Label widths are MEASURED, not counted. The old estimate was
     (name.length + 6) * 6.6 for a spine label and * 6.1 for the rest, and
     free() below refuses any label whose box would cross the frame - so the
     bounds rule was correct and only its input was wrong. The guess ran
     short at 960 and #labels, which hides its overflow and draws no
     ellipsis, cut a stage name in half.

     Measured through a hidden element carrying the label's own classes and
     its own markup, because the CSS is what decides the width: .lab.geo is
     uppercased with letter-spacing, and the spine labels carry a bold run.
     DO NOT replace this with a canvas measureText. It is the obvious
     optimisation - one context, no layout, no reflow - and it was the first
     thing tried here. It measures a string in a font. It does not apply
     text-transform, so .lab.geo's uppercase run is measured in lowercase; it
     does not apply letter-spacing, so .lab.geo loses .06em on every
     character; and it takes one font, so the bold number inside a spine
     label is measured as regular. All three under-measure, and an
     under-measured width is the defect this block exists to fix: the pins
     came out short enough to be nudged past the left edge, which is the same
     bug on the other side of the frame. A hidden element in the real
     stylesheet is slower per string and correct for all three, and the cache
     below makes the cost paid once.

     Cached by class and string - labelPlan runs on every frame, and the
     strings repeat. If the panel is display:none (the List tab) the
     measurement is 0 and the old estimate stands in, which costs nothing
     because nothing is drawn then. */
  var measEl = null, measCache = Object.create(null);
  function labelBox(html, cls, fallbackW) {
    var key = cls + '|' + html;
    var v = measCache[key];
    if (v) return v;
    if (!measEl) { measEl = document.createElement('div'); labels.appendChild(measEl); }
    measEl.className = 'lab ' + cls;
    measEl.style.cssText = 'position:absolute;visibility:hidden;left:-9999px;'
                         + 'top:0;transform:none;white-space:nowrap';
    measEl.innerHTML = html;
    var r = measEl.getBoundingClientRect();
    if (!(r.width > 0)) return { w: fallbackW, h: 15 };
    // three pixels of air either side, two above and below
    v = { w: r.width + 6, h: r.height + 4 };
    measCache[key] = v;
    return v;
  }

  function labelPlan(cam, W, H, sel, hov) {
    var out = [], taken = [];

    function project(p) {
      pv.copy(p).project(cam);
      if (pv.z > 1) return null;
      return { x: (pv.x * 0.5 + 0.5) * W, y: (-pv.y * 0.5 + 0.5) * H };
    }
    function free(x, y, w, h) {
      if (x - w / 2 < 2 || x + w / 2 > W - 2 ||
          y - h / 2 < 2 || y + h / 2 > H - 2) return false;
      for (var i = 0; i < taken.length; i++) {
        var t = taken[i];
        if (Math.abs(x - t.x) * 2 < w + t.w && Math.abs(y - t.y) * 2 < h + t.h)
          return false;
      }
      return true;
    }
    function put(x, y, w, text, cls, node, hh) {
      /* h was 15 for every label until 2026-09-10, the same guess the widths
         carried and with the same consequence one axis over: the collision
         ladder packed rows tighter than the labels actually are, and pairs
         overlapped at 1024 and 390 on the shipped page. Measured now, with
         15 left as the fallback for when the panel is not displayed. */
      var h = hh || 15;
      /* THE RULE: a label may move only so far as its box still covers its
         own node's x. Position is what says which node a label belongs to in
         this diagram, so a label that has left its node's column is not a
         displaced label, it is a wrong one.

         w / 2 below is a consequence of that rule and not the reason for it.
         Nudging at all is worth it: at 960 the Consumer stage lost its name
         outright without it. Nudging without the bound is not - it put End of
         life 131px from its own node and 10px from Consumer's at 1024, which
         reads as a false number against a stage. An incomplete view is
         recoverable; a wrong one is not, and nothing on the page tells a
         reader which they have.

         A label that cannot satisfy the rule is refused here, and End of life
         is refused at 1024, 960 and 390 as a result. That it cannot be placed
         legibly at those widths is a fact about the layout, not about this
         parameter, and displacement cannot fix it in either direction; a
         leader line or room for the last stage can. */
      var x0 = x;
      if (w + 4 <= W) x = Math.max(w / 2 + 2, Math.min(x, W - w / 2 - 2));
      if (Math.abs(x - x0) > w / 2) return false;
      for (var i = 0; i < LADDER.length; i++) {
        var yy = y + LADDER[i];
        if (!free(x, yy, w, h)) continue;
        taken.push({ x: x, y: yy, w: w, h: h });
        out.push({ x: x, y: yy, w: w, h: h, text: text, cls: cls,
                   node: node });
        return true;
      }
      return false;
    }

    /* the two pins, hidden when they are on the far side of the globe */
    if (globeGrp && globeGrp.userData.pins) {
      var gc = globeGrp.position;
      var toCam = cam.position.clone().sub(gc).normalize();
      globeGrp.userData.pins.forEach(function (pin) {
        var local = lonlat(pin.lon, pin.lat, GLOBE_R * 1.015);
        if (local.clone().normalize().dot(toCam) < 0.05) return;
        var s = project(local.clone().add(gc));
        if (!s) return;
        var pb = labelBox(pin.text, 'geo',
                          pin.text.replace(/&middot;/g, '.').length * 5.6);
        put(s.x, s.y - 16, pb.w, pin.text, 'geo', null, pb.h);
      });
    }
    if (!placed) return out;

    var order = placed.nodes.slice().sort(function (a, b) {
      var w = function (n) {
        return (n === sel ? 1e12 : 0) + (n === hov ? 1e11 : 0) +
               (n.spine ? 1e9 : 0) + Math.abs(n.total);
      };
      return w(b) - w(a);
    });

    var shown = 0;
    for (var i = 0; i < order.length && shown < 36; i++) {
      var nd = order[i];
      if (!nd.spine && nd !== sel && nd !== hov &&
          Math.abs(nd.total) < placed.maxAbs * 0.05) continue;
      var s2 = project(nd.pos);
      if (!s2) continue;
      // stages alternate above and below the line they sit on
      var lift = nd.spine
        ? (nd.idx % 2 ? (nd.r * 46 + 20) : -(nd.r * 46 + 16))
        : -(nd.r * 40 + 11);
      var txt = esc(nd.name) + ' <b>' + fmt(nd.total) + '</b>';
      var cls2 = (nd.spine ? 'spine' : '') + (nd === sel ? ' sel' : '');
      var b2 = labelBox(txt, cls2,
                        (nd.name.length + 6) * (nd.spine ? 6.6 : 6.1));
      if (put(s2.x, s2.y + lift, b2.w, txt, cls2, nd, b2.h))
        shown++;
    }
    return out;
  }

  var lastLabels = null;
  function drawLabels() {
    var b = canvas.getBoundingClientRect();
    var html = labelPlan(camera, b.width, b.height, selected, picked)
      .map(function (l) {
        return '<div class="lab ' + l.cls + '" style="left:' +
               l.x.toFixed(1) + 'px;top:' + l.y.toFixed(1) + 'px">' +
               l.text + '</div>';
      }).join('');
    // innerHTML runs the HTML parser. Doing that sixty times a second to
    // produce a string identical to the one already there is most of what an
    // idle scene costs.
    if (html === lastLabels) return;
    lastLabels = html;
    labels.innerHTML = html;
  }

  /* --------------------------------------------------------------- loop -- */
  function resize() {
    if (!hasTHREE) return;
    var b = canvas.getBoundingClientRect();
    if (!b.width || !b.height) return;
    if (sceneOK) renderer.setSize(b.width, b.height, false);
    lastLabels = null;
    touch();
    camera.aspect = b.width / b.height;
    camera.updateProjectionMatrix();
  }

  function frame() {
    requestAnimationFrame(frame);
    if (document.getElementById('list').classList.contains('on')) return;
    if (!dirty && settled()) return;
    // The camera and the dirty bookkeeping run whether or not there is a
    // renderer behind them. Putting them after the WebGL guard made the idle
    // state impossible to observe without a GPU, which is to say impossible to
    // test - and an untested idle path is one that quietly starts spinning
    // again the next time somebody adds an event handler.
    dirty = !settled();
    if (!hasTHREE) return;
    applyCamera();
    if (!sceneOK) return;
    if (group) {
      group.children.forEach(function (o) {
        if (o.userData.billboard) o.quaternion.copy(camera.quaternion);
      });
    }
    renderer.render(scene, camera);
    drawLabels();
  }

  /* ---------------------------------------------------------- selection -- */
  function pathOf(nd) {
    var parts = [], x = nd;
    while (x) { parts.unshift(x.name); x = x.parent; }
    return parts.join('  >  ');
  }

  function showSelection(nd) {
    var el = document.getElementById('sel');
    if (!nd) {
      el.innerHTML = '<p class="why">Click any ball to read what it is, how ' +
        'much of it is charged to this product, and where it sits in the ' +
        'chain. Nothing is selected yet.</p>';
      return;
    }
    var share = res && res.total ? nd.total / res.total * 100 : 0;
    var qual = { A: 'A &middot; documented', B: 'B &middot; literature estimate',
                 C: 'C &middot; uncertain' }[nd.quality] || nd.quality || '';
    var qcls = nd.quality === 'A' ? 'a' : nd.quality === 'C' ? 'c' : '';
    var own = nd.total ? Math.abs(nd.direct) / Math.abs(nd.total) * 100 : 0;
    el.innerHTML =
      '<div class="nm">' + esc(nd.name) + '</div>' +
      (qual ? '<span class="pill ' + qcls + '">' + qual + '</span>' : '') +
      (nd.spine ? '<span class="pill">life-cycle stage</span>' : '') +
      '<dl>' +
      '<dt>Total</dt><dd>' + fmt(nd.total) + ' kg CO<sub>2</sub>e' +
        ' <span style="color:var(--dim)">(' + share.toFixed(1) +
        '% of the item)</span></dd>' +
      '<dt>Released here</dt><dd>' + fmt(nd.direct || 0) +
        ' <span style="color:var(--dim)">(' + own.toFixed(0) +
        '% of this branch; the rest is upstream)</span></dd>' +
      (nd.amount != null ?
        '<dt>Amount</dt><dd>' + fmt(nd.amount) + ' ' +
        esc(nd.unit || '') + '</dd>' : '') +
      (nd.alloc != null ?
        '<dt>Allocation</dt><dd>' + (nd.alloc * 100).toFixed(1) + '%' +
        (Math.abs(nd.alloc - 1) < 1e-6
          ? ' <span style="color:var(--dim)">(all of it)</span>' : '') +
        /* The basis is the judgement behind the number - economic, mass,
           physical - and it ships with the share rather than only in
           prose, so a share cannot be shown without saying what kind it
           is. Freight and capital-good stages carry no basis: theirs is
           a mass or a lifetime, not a split. */
        (nd.basis ? '<br><span style="color:var(--dim)">basis: ' +
                    esc(nd.basis) + '</span>' : '') +
        '</dd>' : '') +
      '<dt>Branches</dt><dd>' + nd.kids.length + '</dd>' +
      '</dl>' +
      (nd.note ? '<div class="why">' + esc(nd.note) + '</div>' : '') +
      '<div class="path">' + esc(pathOf(nd)) + '</div>';
  }

  function select(nd) {
    if (selected && selected.mesh)
      selected.mesh.material.emissive &&
        selected.mesh.material.emissive.setHex(0x000000);
    selected = nd;
    if (nd && nd.mesh && nd.mesh.material.emissive)
      nd.mesh.material.emissive.set(new THREE.Color(nd.colour))
        .multiplyScalar(0.55);
    showSelection(nd);
    focus(nd);
    touch();
  }

  /* ------------------------------------------------------------- events -- */
  var drag = null, moved = 0;
  canvas.addEventListener('pointerdown', function (e) {
    drag = { x: e.clientX, y: e.clientY };
    moved = 0;
    canvas.classList.add('drag');
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', function (e) {
    if (drag) {
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      moved += Math.abs(dx) + Math.abs(dy);
      view.want.az -= dx * 0.006;
      view.want.el = Math.max(-1.35, Math.min(1.35,
                              view.want.el + dy * 0.005));
      view.az = view.want.az; view.el = view.want.el;
      drag.x = e.clientX; drag.y = e.clientY;
      hoverEl.style.display = 'none';
      touch();
      return;
    }
    var nd = pick(e.clientX, e.clientY);
    if (nd !== picked) touch();
    picked = nd;
    if (!nd) { hoverEl.style.display = 'none'; canvas.style.cursor = 'grab';
               return; }
    canvas.style.cursor = 'pointer';
    var b = canvas.getBoundingClientRect();
    hoverEl.innerHTML =
      '<div class="h">' + esc(nd.name) + '</div>' +
      '<div><span class="v">' + fmt(nd.total) + '</span> kg CO<sub>2</sub>e' +
      (Math.abs(nd.alloc - 1) > 1e-6
        ? ' &middot; ' + (nd.alloc * 100).toFixed(0) + '% allocated' : '') +
      '</div>' +
      (nd.kids.length ? '<div class="n">' + nd.kids.length +
        ' branches below</div>' : '');
    hoverEl.style.display = 'block';
    var w = hoverEl.offsetWidth, h = hoverEl.offsetHeight;
    var x = e.clientX - b.left + 16, y = e.clientY - b.top + 16;
    if (x + w > b.width - 8) x = e.clientX - b.left - w - 16;
    if (y + h > b.height - 8) y = e.clientY - b.top - h - 16;
    hoverEl.style.left = Math.max(4, x) + 'px';
    hoverEl.style.top = Math.max(4, y) + 'px';
  });
  function endDrag(e) {
    if (!drag) return;
    var wasClick = moved < 5;
    drag = null;
    canvas.classList.remove('drag');
    if (wasClick) select(pick(e.clientX, e.clientY));
  }
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', function () { drag = null;
    canvas.classList.remove('drag'); });
  canvas.addEventListener('pointerleave', function () {
    hoverEl.style.display = 'none'; });
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    view.want.dist = Math.max(1.2, Math.min(60,
      view.want.dist * (1 + Math.sign(e.deltaY) * 0.12)));
    touch();
  }, { passive: false });

  /* Arrow keys walk the graph, which is the difference between a picture and
     a place: left and right along the chain, down into the largest branch,
     up back towards the spine. */
  /* The exemption list is every focusable control on the page, not just the
     selects. It read SELECT alone until 2026-09-10, and #life is an
     <input type="range">: focusing the vehicle-life slider and pressing an
     arrow walked the supply chain instead of moving the slider, because this
     handler is on window and calls preventDefault below. A control that eats
     its own keys is invisible to a mouse and total to a keyboard.
     skyline-app's handler exempts the same three tags for the same reason. */
  window.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (!placed || tag === 'SELECT' || tag === 'INPUT' || tag === 'BUTTON') return;
    var spine = placed.nodes.filter(function (n) { return n.spine; });
    var k = e.key;
    if (k === 'ArrowLeft' || k === 'ArrowRight') {
      var cur = selected;
      while (cur && !cur.spine) cur = cur.parent;
      var i = cur ? cur.idx : (k === 'ArrowRight' ? -1 : spine.length);
      i += (k === 'ArrowRight' ? 1 : -1);
      i = Math.max(0, Math.min(spine.length - 1, i));
      select(spine[i]);
    } else if (k === 'ArrowDown') {
      var from = selected || spine[0];
      if (from.kids.length) {
        select(from.kids.slice().sort(function (a, b) {
          return Math.abs(b.total) - Math.abs(a.total); })[0]);
      }
    } else if (k === 'ArrowUp') {
      if (selected && selected.parent) select(selected.parent);
      else select(null);
    } else if (k === 'Escape') { select(null); }
    else return;
    e.preventDefault();
  });

  document.getElementById('reset').addEventListener('click', function () {
    select(null); resetView(false);
  });

  var ro = window.ResizeObserver ? new ResizeObserver(resize) : null;
  if (ro) ro.observe(document.getElementById('stage'));
  window.addEventListener('resize', resize);
  if (window.matchMedia) {
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var onScheme = function () { palette(); if (res) render(); };
    if (mq.addEventListener) mq.addEventListener('change', onScheme);
  }

  /* ---------------------------------------------------------- the list -- */
  function branchHTML(n, max) {
    var kids = (n.children || []).slice().sort(function (a, b) {
      return Math.abs(b.total) - Math.abs(a.total); });
    var pct = max ? Math.min(100, Math.abs(n.total) / max * 100) : 0;
    var showAlloc = Math.abs(n.alloc - 1) > 1e-9;
    return '<li class="n"><div class="row"><span class="lbl">' +
      '<i class="dot" style="background:' + colourOf(n) + '"></i>' +
      esc(n.name) +
      (showAlloc ? '<span class="alloc" title="share charged to the product">' +
        '&times;' + n.alloc.toFixed(2) + '</span>' : '') +
      '<span class="amt">' + fmt(n.amount) + ' ' + esc(n.unit || '') +
      '</span>' +
      (n.quality ? '<span class="q" title="A documented, B literature ' +
        'estimate, C uncertain">' + n.quality + '</span>' : '') +
      '</span><span class="val">' + fmt(n.total) + '</span></div>' +
      (n.note ? '<div class="leafnote">' + esc(n.note) + '</div>' : '') +
      (kids.length ? '<ul class="tree">' +
        kids.map(function (k) { return branchHTML(k, max); }).join('') +
        '</ul>' : '') +
      '</li>';
  }

  function renderList(r) {
    var max = Math.max.apply(null, r.spine.map(function (s) {
      return Math.abs(s.total); }));
    document.getElementById('list').innerHTML = r.spine.map(function (s) {
      var kids = (s.children || []).slice().sort(function (a, b) {
        return Math.abs(b.total) - Math.abs(a.total); });
      var share = r.total ? s.total / r.total * 100 : 0;
      return '<div class="stagehead"><h3>' + esc(s.name) + '</h3>' +
        '<span class="val">' + fmt(s.total) + ' kg &middot; ' +
        share.toFixed(1) + '%</span>' +
        (s.basis ? '<span class="alloc" title="share charged to the product, and on what basis">' +
          '&times;' + s.alloc.toFixed(2) + ' ' + esc(s.basis) + '</span>' : '') +
        '</div>' +
        (s.note ? '<div class="leafnote">' + esc(s.note) + '</div>' : '') +
        (kids.length ? '<ul class="tree">' +
          kids.map(function (k) { return branchHTML(k, max); }).join('') +
          '</ul>' : '');
    }).join('');
  }

  /* ----------------------------------------------------------------- ui -- */
  function fill(sel, entries, value) {
    sel.innerHTML = entries.map(function (e) {
      return '<option value="' + e[0] + '">' + esc(e[1]) + '</option>';
    }).join('');
    if (value != null) sel.value = value;
  }

  /* Twenty items in one flat list is a list nobody reads to the bottom of.
     Grouped, it also says something the flat version hides: that the model is
     being asked the same question about a tomato, a flight and a pair of
     jeans, and that the answers are on the same axis. */
  function fillGrouped(sel, groups, value) {
    sel.innerHTML = groups.map(function (g) {
      return '<optgroup label="' + esc(g[0]) + '">' +
        g[1].map(function (e) {
          return '<option value="' + e[0] + '">' + esc(e[1]) + '</option>';
        }).join('') + '</optgroup>';
    }).join('');
    if (value != null) sel.value = value;
  }

  /* The lifetime slider runs on a log scale between the product's stated
     bounds, because the interesting range spans an order of magnitude and a
     linear slider would spend most of its travel in territory nobody is
     asking about. The value shown is always the real one. */
  function lifeValue(p) {
    var lt = p.lifetime;
    if (!lt) return null;
    var t = (+document.getElementById('life').value) / 100;
    return Math.exp(Math.log(lt.min) + t * (Math.log(lt.max) - Math.log(lt.min)));
  }
  function lifePos(lt, v) {
    return 100 * (Math.log(v) - Math.log(lt.min)) /
                 (Math.log(lt.max) - Math.log(lt.min));
  }
  function syncLife(p, reset) {
    var wrap = document.getElementById('lifewrap');
    var lt = p.lifetime;
    if (!lt) { wrap.style.display = 'none'; return; }
    wrap.style.display = '';
    document.getElementById('lifelabel').textContent = lt.label;
    if (reset)
      document.getElementById('life').value = lifePos(lt, lt.default).toFixed(1);
    var v = lifeValue(p);
    var pretty = lt.unit === 'km'
      ? Math.round(v / 1000).toLocaleString() + ' thousand km'
      : (v >= 1e9 ? (v / 1e9).toFixed(2) + ' billion '
                  : (v / 1e6).toFixed(0) + ' million ') + 'passenger-km';
    var off = v / lt.default;
    document.getElementById('lifeval').textContent = pretty +
      (Math.abs(off - 1) < 0.02 ? '  (as published)'
        : '  (' + (off > 1 ? '×' + off.toFixed(2) + ' the default'
                           : '×' + off.toFixed(2) + ' the default') + ')');
  }

  function render() {
    var item = document.getElementById('item').value;
    var o = document.getElementById('origin').value;
    var d = document.getElementById('dest').value;
    var m = document.getElementById('mode').value;
    var p = D.products[item];
    var r = model(item, o, d, m, lifeValue(p));

    document.getElementById('tot').textContent = fmt(r.total);
    document.getElementById('unit').textContent = p.unit.replace(/^1 /, '');
    document.getElementById('route').textContent =
      D.regions[o].name + ' to ' + D.regions[d].name + ', ' +
      Math.round(r.km).toLocaleString() + ' km by ' + D.transport[m].name;
    document.getElementById('itemnote').textContent =
      p.note + (p.lifetime ? '  ' + p.lifetime.note : '');

    // widest published food footprint in the set, as a common ruler
    var scale = 60;
    document.getElementById('totbar').style.width =
      Math.min(100, Math.abs(r.total) / scale * 100).toFixed(1) + '%';

    /* A sense of scale, since a kilogram of carbon dioxide is not a thing
       anybody can picture. Comparing a car journey to a car journey is not a
       comparison, so for road transport the yardstick becomes the flight
       instead. */
    var road = p.group === 'Transport' && p.category === 'Road';
    var yard = road ? 0.214 : 0.171;      // kg CO2e per km: short flight, car
    var kmCar = r.total / yard;
    document.getElementById('compare').textContent =
      'About the same as ' + (road ? 'flying ' : 'driving ') +
      (kmCar < 10 ? kmCar.toFixed(1) : Math.round(kmCar).toLocaleString()) +
      ' km' + (road ? ' on a short-haul flight' : ' in an average car') +
      '. Grid: ' + D.regions[o].grid.toFixed(2) +
      ' kg/kWh where it is made, ' + D.regions[d].grid.toFixed(2) +
      ' where it is eaten.' +
      (r.cut ? ' ' + fmt(r.cut) + ' kg dropped below the ' +
        (CUT * 100).toFixed(2) + '% cutoff.' : '');

    renderList(r);
    build(r);
  }

  /* tabs */
  var t3d = document.getElementById('t3d'), tls = document.getElementById('tls');
  function showList(on) {
    document.getElementById('list').classList.toggle('on', on);
    t3d.classList.toggle('on', !on);
    tls.classList.toggle('on', on);
    document.getElementById('labels').style.display = on ? 'none' : '';
    document.getElementById('hint').style.display = on ? 'none' : '';
    document.getElementById('reset').style.display = on ? 'none' : '';
    if (!on) resize();
  }
  t3d.addEventListener('click', function () { showList(false); });
  tls.addEventListener('click', function () { showList(true); });

  /* boot */
  var GROUP_ORDER = ['Food', 'Transport', 'Clothing'];
  var byGroup = {};
  Object.keys(D.items).forEach(function (k) {
    var g = D.items[k].group || 'Food';
    (byGroup[g] = byGroup[g] || []).push([k, D.items[k].name]);
  });
  var itemGroups = GROUP_ORDER
    .filter(function (g) { return byGroup[g]; })
    .concat(Object.keys(byGroup).filter(function (g) {
      return GROUP_ORDER.indexOf(g) < 0; }))
    .map(function (g) {
      byGroup[g].sort(function (a, b) { return a[1] < b[1] ? -1 : 1; });
      return [g, byGroup[g]];
    });
  var regions = Object.keys(D.regions).map(function (k) {
    return [k, D.regions[k].name]; })
    .sort(function (a, b) { return a[1] < b[1] ? -1 : 1; });
  var modes = Object.keys(D.transport).map(function (k) {
    return [k, D.transport[k].name]; });

  fillGrouped(document.getElementById('item'), itemGroups, 'tomato_field');
  fill(document.getElementById('origin'), regions, D.items.tomato_field.origin);
  fill(document.getElementById('dest'), regions, D.items.tomato_field.dest);
  fill(document.getElementById('mode'), modes, D.items.tomato_field.mode);

  /* Changing the item resets the route to that item's default, because a
     default is a claim about where the thing usually comes from and carrying
     the previous item's route across would quietly discard it. */
  document.getElementById('item').addEventListener('change', function () {
    var it = D.items[this.value];
    document.getElementById('origin').value = it.origin;
    document.getElementById('dest').value = it.dest;
    document.getElementById('mode').value = it.mode;
    syncLife(D.products[this.value], true);
    render();
  });
  ['origin', 'dest', 'mode'].forEach(function (id) {
    document.getElementById(id).addEventListener('change', render);
  });
  document.getElementById('life').addEventListener('input', function () {
    syncLife(D.products[document.getElementById('item').value], false);
    render();
  });
  syncLife(D.products.tomato_field, true);

  /* A particular question can be linked to, which is also how the figures
     on the page behind this one are captured from the live tool rather than
     drawn a second time: ?item=car_petrol&from=DE&to=US-TX&mode=sea&life=100000 */
  (function () {
    var q = new URLSearchParams(location.search);
    var it = q.get('item');
    if (it && D.products[it]) {
      document.getElementById('item').value = it;
      var dflt = D.items[it];
      document.getElementById('origin').value = dflt.origin;
      document.getElementById('dest').value = dflt.dest;
      document.getElementById('mode').value = dflt.mode;
      syncLife(D.products[it], true);
    }
    if (q.get('from') && D.regions[q.get('from')])
      document.getElementById('origin').value = q.get('from');
    if (q.get('to') && D.regions[q.get('to')])
      document.getElementById('dest').value = q.get('to');
    if (q.get('mode') && D.transport[q.get('mode')])
      document.getElementById('mode').value = q.get('mode');
    var life = parseFloat(q.get('life'));
    var pnow = D.products[document.getElementById('item').value];
    if (life > 0 && pnow.lifetime) {
      document.getElementById('life').value =
        lifePos(pnow.lifetime, life).toFixed(1);
      syncLife(pnow, false);
    }
  })();

  var ok = initGL();
  if (!ok) {
    document.getElementById('nogl').style.display = 'flex';
    canvas.style.display = 'none';
  }
  render();
  if (ok) { resize(); frame(); } else { showList(true); }

  // for the test harness: the engine, the layout, and the constants the
  // layout is measured against, so a test cannot silently drift from the
  // numbers the page actually uses.
  window.__lca = {
    model: model, layout: layout, labelPlan: labelPlan,
    camera: function () { return camera; },
    resetView: resetView, applyCamera: applyCamera,
    frame: frame, isDirty: function () { return dirty || !settled(); },
    touch: touch,
    placed: function () { return placed; },
    result: function () { return res; },
    home: function () { return HOME; },
    consts: { GLOBE_R: GLOBE_R, SPACING: SPACING, GLOBE_GAP: GLOBE_GAP }
  };
})();
