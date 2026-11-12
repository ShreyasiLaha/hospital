/**
 * CarePlus Hospital - WebGL2 Interactive Cursor Grid Background
 * Adapted from CursorGrid WebGL2 component for Vanilla JavaScript.
 */
(function () {
  'use strict';

  var INTRO_SECONDS = 1.4;
  var STYLES = { lines: 0, dashed: 1, dots: 2, crosses: 3 };

  var FALLOFF_CURVES = {
    linear: function (t) { return t; },
    smooth: function (t) { return t * t * (3 - 2 * t); },
    sharp: function (t) { return t * t * t; }
  };

  var VERTEX = '#version 300 es\n' +
    'void main() {\n' +
    '  vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));\n' +
    '  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);\n' +
    '}';

  var FRAGMENT = '#version 300 es\n' +
    'precision highp float;\n' +
    'precision highp int;\n' +
    'uniform vec2 uResolution;\n' +
    'uniform vec2 uOffset;\n' +
    'uniform float uCellSize;\n' +
    'uniform sampler2D uState;\n' +
    'uniform ivec2 uCells;\n' +
    'uniform vec3 uColor;\n' +
    'uniform vec3 uGridColor;\n' +
    'uniform float uLineWidth;\n' +
    'uniform float uMaxOpacity;\n' +
    'uniform float uFillOpacity;\n' +
    'uniform float uGridOpacity;\n' +
    'uniform float uCellRadius;\n' +
    'uniform float uCellGap;\n' +
    'uniform int uGridStyle;\n' +
    'uniform vec2 uMouse;\n' +
    'uniform float uRadius;\n' +
    'uniform float uSpotlight;\n' +
    'uniform float uPresence;\n' +
    'uniform float uEdgeFade;\n' +
    'uniform float uReveal;\n' +
    'out vec4 outColor;\n' +
    'float level(vec2 cell) {\n' +
    '  if (cell.x < 0.0 || cell.y < 0.0 || cell.x >= float(uCells.x) || cell.y >= float(uCells.y)) return 0.0;\n' +
    '  float v = texelFetch(uState, ivec2(cell), 0).r;\n' +
    '  return v * v * (3.0 - 2.0 * v);\n' +
    '}\n' +
    'float line(float d, float width) {\n' +
    '  float w = max(width, 1.0);\n' +
    '  return clamp(w * 0.5 + 0.5 - d, 0.0, 1.0) * (width / w);\n' +
    '}\n' +
    'float roundBox(vec2 p, vec2 b, float r) {\n' +
    '  vec2 q = abs(p) - b + r;\n' +
    '  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;\n' +
    '}\n' +
    'void main() {\n' +
    '  vec2 pos = vec2(gl_FragCoord.x, uResolution.y - gl_FragCoord.y);\n' +
    '  vec2 g = (pos - uOffset) / uCellSize;\n' +
    '  vec2 cell = floor(g);\n' +
    '  vec2 f = g - cell;\n' +
    '  vec2 edge = min(f, 1.0 - f) * uCellSize;\n' +
    '  float vx = line(edge.x, uLineWidth);\n' +
    '  float vy = line(edge.y, uLineWidth);\n' +
    '  if (uGridStyle == 1) {\n' +
    '    float dash = uCellSize / 6.0;\n' +
    '    vx *= step(0.5, fract((pos.y - uOffset.y) / dash + 0.25));\n' +
    '    vy *= step(0.5, fract((pos.x - uOffset.x) / dash + 0.25));\n' +
    '  } else if (uGridStyle == 2) {\n' +
    '    float r = max(uLineWidth * 1.25, 1.2);\n' +
    '    float d = length(edge);\n' +
    '    vx = clamp(r + 0.5 - d, 0.0, 1.0);\n' +
    '    vy = 0.0;\n' +
    '  } else if (uGridStyle == 3) {\n' +
    '    float arm = uCellSize * 0.1 + uLineWidth;\n' +
    '    vx *= step(edge.y, arm);\n' +
    '    vy *= step(edge.x, arm);\n' +
    '  }\n' +
    '  float mark = max(vx, vy);\n' +
    '  vec2 toMouse = pos - uMouse;\n' +
    '  float spot = exp(-dot(toMouse, toMouse) / max(uRadius * uRadius, 1.0) * 1.6) * uSpotlight * uPresence;\n' +
    '  vec2 center = uResolution * 0.5;\n' +
    '  float reach = length(center);\n' +
    '  float shown = smoothstep(uReveal * (reach + uCellSize * 2.0), uReveal * (reach + uCellSize * 2.0) - uCellSize * 2.0, length(pos - center));\n' +
    '  shown = uReveal >= 1.0 ? 1.0 : shown;\n' +
    '  float fade = 1.0;\n' +
    '  if (uEdgeFade > 0.0) {\n' +
    '    vec2 norm = pos / uResolution;\n' +
    '    vec2 a = clamp(norm / uEdgeFade, 0.0, 1.0);\n' +
    '    vec2 b = clamp((1.0 - norm) / uEdgeFade, 0.0, 1.0);\n' +
    '    vec2 sa = a * a * a * (a * (a * 6.0 - 15.0) + 10.0);\n' +
    '    vec2 sb = b * b * b * (b * (b * 6.0 - 15.0) + 10.0);\n' +
    '    fade = sa.x * sa.y * sb.x * sb.y;\n' +
    '  }\n' +
    '  float own = level(cell);\n' +
    '  float gridAlpha = mark * min(uGridOpacity + spot * 0.45, 1.0) * fade * shown;\n' +
    '  float litAlpha = 0.0;\n' +
    '  float fillAlpha = 0.0;\n' +
    '  if (uCellGap <= 0.0 && uCellRadius <= 0.0) {\n' +
    '    vec2 side = step(0.5, f) * 2.0 - 1.0;\n' +
    '    float nx = level(cell + vec2(side.x, 0.0));\n' +
    '    float ny = level(cell + vec2(0.0, side.y));\n' +
    '    float nc = level(cell + side);\n' +
    '    float ex = max(own, nx);\n' +
    '    float ey = max(own, ny);\n' +
    '    float joint = max(max(ex, ey), nc);\n' +
    '    float lit;\n' +
    '    if (uGridStyle == 2) lit = vx * joint;\n' +
    '    else if (uGridStyle == 3) lit = max(vx * (edge.y < uLineWidth ? joint : ex), vy * (edge.x < uLineWidth ? joint : ey));\n' +
    '    else lit = max(vx * (edge.y < uLineWidth ? joint : ex), vy * (edge.x < uLineWidth ? joint : ey));\n' +
    '    litAlpha = lit * uMaxOpacity;\n' +
    '    fillAlpha = own * uFillOpacity;\n' +
    '  } else if (own > 0.0) {\n' +
    '    vec2 local = (f - 0.5) * uCellSize;\n' +
    '    float halfSize = uCellSize * 0.5 - max(uCellGap, 0.0);\n' +
    '    float radius = min(uCellRadius, halfSize);\n' +
    '    float sd = roundBox(local, vec2(halfSize), radius);\n' +
    '    float inside = clamp(0.5 - sd, 0.0, 1.0);\n' +
    '    float border = line(abs(sd + uLineWidth * 0.5), uLineWidth) * inside;\n' +
    '    litAlpha = border * own * uMaxOpacity;\n' +
    '    fillAlpha = inside * own * uFillOpacity;\n' +
    '  }\n' +
    '  litAlpha *= fade;\n' +
    '  fillAlpha *= fade;\n' +
    '  float cellAlpha = clamp(max(litAlpha, fillAlpha), 0.0, 1.0);\n' +
    '  float alpha = cellAlpha + gridAlpha * (1.0 - cellAlpha);\n' +
    '  vec3 premul = uColor * cellAlpha + uGridColor * gridAlpha * (1.0 - cellAlpha);\n' +
    '  outColor = vec4(premul, alpha);\n' +
    '}';

  function clamp(v, min, max) { return Math.min(max, Math.max(min, v)); }

  function compile(gl, type, source) {
    var shader = gl.createShader(type);
    if (!shader) return null;
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return shader;
    gl.deleteShader(shader);
    return null;
  }

  function link(gl) {
    var vertex = compile(gl, gl.VERTEX_SHADER, VERTEX);
    var fragment = compile(gl, gl.FRAGMENT_SHADER, FRAGMENT);
    var program = gl.createProgram();
    if (!vertex || !fragment || !program) return null;
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    gl.deleteShader(vertex);
    gl.deleteShader(fragment);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      gl.deleteProgram(program);
      return null;
    }
    var uniforms = {};
    var count = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
    for (var i = 0; i < count; i++) {
      var info = gl.getActiveUniform(program, i);
      if (info) uniforms[info.name] = gl.getUniformLocation(program, info.name);
    }
    return { program: program, uniforms: uniforms };
  }

  function parseHex(hex) {
    var h = String(hex || '#ffffff').replace('#', '').trim();
    if (h.length === 3 || h.length === 4) {
      h = h.slice(0, 3).split('').map(function (c) { return c + c; }).join('');
    }
    var num = parseInt(h.slice(0, 6), 16);
    if (isNaN(num)) return [1, 1, 1];
    return [((num >> 16) & 255) / 255, ((num >> 8) & 255) / 255, (num & 255) / 255];
  }

  function initCursorGrid(container, canvas, customOptions) {
    if (!container || !canvas) return;
    var gl = canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: true,
      antialias: false,
      depth: false,
      stencil: false
    });
    if (!gl) {
      console.warn('WebGL2 not supported, cursor grid inactive.');
      return;
    }

    var shader = link(gl);
    if (!shader) return;
    var u = shader.uniforms;
    var vao = gl.createVertexArray();
    var stateTexture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, stateTexture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);

    var opts = Object.assign({
      cellSize: 46,
      color: '#0D9488',       // CarePlus Medical Teal
      gridColor: '#94A3B8',   // Clean Slate Grey for Grid
      radius: 155,
      falloff: 'smooth',
      highlight: 'area',
      holdTime: 380,
      fadeDuration: 750,
      lineWidth: 1.15,
      maxOpacity: 0.85,
      fillOpacity: 0.08,
      gridOpacity: 0.22,
      gridStyle: STYLES.lines,
      cellRadius: 0,
      cellGap: 0,
      spotlight: 0.65,
      clickPulse: true,
      pulseSpeed: 620,
      ambient: 0.15,
      edgeFade: 0.15,
      intro: true
    }, customOptions || {});

    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var view = { width: 1, height: 1, ratio: 1, cellSize: 0 };
    var grid = { cols: 0, rows: 0, offX: 0, offY: 0 };
    var pointer = { x: 0, y: 0, inside: false };
    var mouse = { x: 0, y: 0 };
    var pulses = [];
    var levels = new Float32Array(0);
    var waves = new Float32Array(0);
    var targets = new Float32Array(0);
    var touched = new Float32Array(0);
    var pixels = new Uint8Array(0);
    var presence = 0;
    var clock = 0;
    var introClock = opts.intro && !reduce ? 0 : 1;
    var raf = 0;
    var last = 0;
    var visible = true;
    var dirty = true;

    function rebuild() {
      view.width = Math.max(1, container.clientWidth);
      view.height = Math.max(1, container.clientHeight);
      view.ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(view.width * view.ratio));
      canvas.height = Math.max(1, Math.round(view.height * view.ratio));
      var size = opts.cellSize;
      var cols = Math.ceil(view.width / size) + 1;
      var rows = Math.ceil(view.height / size) + 1;
      var resized = cols !== grid.cols || rows !== grid.rows || size !== view.cellSize;
      grid.cols = cols;
      grid.rows = rows;
      grid.offX = (view.width - cols * size) / 2;
      grid.offY = (view.height - rows * size) / 2;
      view.cellSize = size;
      if (resized) {
        levels = new Float32Array(cols * rows);
        waves = new Float32Array(cols * rows);
        targets = new Float32Array(cols * rows);
        touched = new Float32Array(cols * rows).fill(-1e9);
        pixels = new Uint8Array(cols * rows);
        gl.bindTexture(gl.TEXTURE_2D, stateTexture);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.R8, cols, rows, 0, gl.RED, gl.UNSIGNED_BYTE, pixels);
      }
      dirty = true;
    }

    function light(index, value) {
      if (value > targets[index]) targets[index] = value;
      touched[index] = clock;
    }

    function energize(x, y) {
      var size = opts.cellSize;
      if (opts.highlight === 'cell') {
        var col = Math.floor((x - grid.offX) / size);
        var row = Math.floor((y - grid.offY) / size);
        if (col >= 0 && row >= 0 && col < grid.cols && row < grid.rows) {
          light(row * grid.cols + col, 1);
        }
        return;
      }
      var r = opts.radius;
      var ease = FALLOFF_CURVES[opts.falloff] || FALLOFF_CURVES.linear;
      var minCol = Math.max(0, Math.floor((x - r - grid.offX) / size));
      var maxCol = Math.min(grid.cols - 1, Math.floor((x + r - grid.offX) / size));
      var minRow = Math.max(0, Math.floor((y - r - grid.offY) / size));
      var maxRow = Math.min(grid.rows - 1, Math.floor((y + r - grid.offY) / size));
      for (var row = minRow; row <= maxRow; row++) {
        for (var col = minCol; col <= maxCol; col++) {
          var cx = grid.offX + col * size + size / 2;
          var cy = grid.offY + row * size + size / 2;
          var dist = Math.hypot(cx - x, cy - y);
          if (dist > r) continue;
          var value = ease(1 - dist / r);
          if (value > 0) light(row * grid.cols + col, value);
        }
      }
    }

    function sweepPulses() {
      var size = opts.cellSize;
      var ahead = size * 0.6;
      var behind = size * 1.4;
      var far = Math.hypot(view.width, view.height);
      waves.fill(0);
      for (var k = pulses.length - 1; k >= 0; k--) {
        var pulse = pulses[k];
        var ringR = (clock - pulse.t0) * opts.pulseSpeed;
        if (ringR - behind * 2 > far) {
          pulses.splice(k, 1);
          continue;
        }
        if (ringR < 0) continue;
        var envelope = pulse.strength * Math.pow(Math.max(0, 1 - ringR / (far + behind)), 0.6);
        var outer = ringR + ahead * 2;
        var minCol = Math.max(0, Math.floor((pulse.x - outer - grid.offX) / size));
        var maxCol = Math.min(grid.cols - 1, Math.floor((pulse.x + outer - grid.offX) / size));
        var minRow = Math.max(0, Math.floor((pulse.y - outer - grid.offY) / size));
        var maxRow = Math.min(grid.rows - 1, Math.floor((pulse.y + outer - grid.offY) / size));
        for (var row = minRow; row <= maxRow; row++) {
          for (var col = minCol; col <= maxCol; col++) {
            var cx = grid.offX + col * size + size / 2;
            var cy = grid.offY + row * size + size / 2;
            var off = Math.hypot(cx - pulse.x, cy - pulse.y) - ringR;
            if (off > ahead * 2 || off < -behind * 2) continue;
            var t = off > 0 ? off / ahead : off / behind;
            var value = envelope * Math.exp(-t * t);
            var index = row * grid.cols + col;
            if (value > waves[index]) waves[index] = value;
          }
        }
      }
      dirty = true;
    }

    function draw() {
      var ratio = view.ratio;
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(shader.program);
      gl.bindVertexArray(vao);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, stateTexture);
      if (dirty) {
        for (var i = 0; i < levels.length; i++) {
          pixels[i] = Math.round(clamp(Math.max(levels[i], waves[i]), 0, 1) * 255);
        }
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, grid.cols, grid.rows, gl.RED, gl.UNSIGNED_BYTE, pixels);
        dirty = false;
      }
      var lineDevice = opts.lineWidth * ratio;
      var snap = Math.round(lineDevice) % 2 === 1 ? 0.5 : 0;
      gl.uniform1i(u.uState, 0);
      gl.uniform2f(u.uResolution, canvas.width, canvas.height);
      gl.uniform2f(u.uOffset, Math.round(grid.offX * ratio) + snap, Math.round(grid.offY * ratio) + snap);
      gl.uniform1f(u.uCellSize, opts.cellSize * ratio);
      gl.uniform2i(u.uCells, grid.cols, grid.rows);
      gl.uniform3fv(u.uColor, parseHex(opts.color));
      gl.uniform3fv(u.uGridColor, parseHex(opts.gridColor));
      gl.uniform1f(u.uLineWidth, lineDevice);
      gl.uniform1f(u.uMaxOpacity, opts.maxOpacity);
      gl.uniform1f(u.uFillOpacity, opts.fillOpacity);
      gl.uniform1f(u.uGridOpacity, opts.gridOpacity);
      gl.uniform1f(u.uCellRadius, opts.cellRadius * ratio);
      gl.uniform1f(u.uCellGap, opts.cellGap * ratio);
      gl.uniform1i(u.uGridStyle, opts.gridStyle);
      gl.uniform2f(u.uMouse, mouse.x * ratio, mouse.y * ratio);
      gl.uniform1f(u.uRadius, opts.radius * ratio);
      gl.uniform1f(u.uSpotlight, opts.spotlight);
      gl.uniform1f(u.uPresence, presence);
      gl.uniform1f(u.uEdgeFade, opts.edgeFade);
      gl.uniform1f(u.uReveal, introClock >= 1 ? 1 : 1 - Math.pow(1 - introClock, 2.2));
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      gl.bindVertexArray(null);
    }

    function frame(now) {
      raf = 0;
      if (!visible || document.hidden) return;
      var dt = last ? clamp((now - last) / 1000, 0, 1 / 20) : 1 / 60;
      last = now;
      clock += dt;
      if (introClock < 1) introClock = Math.min(1, introClock + dt / INTRO_SECONDS);

      var follow = 1 - Math.exp(-dt / 0.07);
      mouse.x += (pointer.x - mouse.x) * follow;
      mouse.y += (pointer.y - mouse.y) * follow;
      var presenceGoal = pointer.inside ? 1 : 0;
      presence += (presenceGoal - presence) * (1 - Math.exp(-dt / 0.25));

      if (opts.ambient > 0 && !reduce && levels.length) {
        var chance = opts.ambient * dt * levels.length * 0.04;
        var spawns = Math.floor(chance) + (Math.random() < chance % 1 ? 1 : 0);
        while (spawns-- > 0) {
          light(Math.floor(Math.random() * levels.length), 0.25 + Math.random() * 0.45);
        }
      }
      if (pulses.length) sweepPulses();
      else if (waves.length && waves.some(function (v) { return v > 0; })) {
        waves.fill(0);
        dirty = true;
      }

      var holdSeconds = opts.holdTime / 1000;
      var fadeStep = dt / (opts.fadeDuration / 1000);
      var attack = 1 - Math.exp(-dt / 0.045);
      var active = pulses.length > 0 || introClock < 1 || Math.abs(presence - presenceGoal) > 0.002;
      for (var i = 0; i < levels.length; i++) {
        var target = targets[i];
        if (target <= 0 && levels[i] <= 0) continue;
        if (clock - touched[i] > holdSeconds) target = Math.max(0, target - fadeStep);
        targets[i] = target;
        var before = levels[i];
        var next = target > before ? before + (target - before) * attack : target;
        levels[i] = next < 0.002 ? 0 : next;
        if (levels[i] !== before) dirty = true;
        if (levels[i] > 0 || targets[i] > 0) active = true;
      }
      if (Math.abs(mouse.x - pointer.x) + Math.abs(mouse.y - pointer.y) > 0.05 && presence > 0.002) active = true;
      if (opts.ambient > 0 && !reduce) active = true;

      draw();
      if (active) raf = requestAnimationFrame(frame);
    }

    function wake() {
      if (!raf && visible && !document.hidden) {
        last = 0;
        raf = requestAnimationFrame(frame);
      }
    }

    function locate(event) {
      var rect = container.getBoundingClientRect();
      var x = event.clientX - rect.left;
      var y = event.clientY - rect.top;
      return { x: x, y: y, inside: x >= 0 && y >= 0 && x <= rect.width && y <= rect.height };
    }

    function onPointerMove(event) {
      var loc = locate(event);
      var was = pointer.inside;
      pointer.inside = loc.inside;
      if (!loc.inside) {
        if (was) wake();
        return;
      }
      pointer.x = loc.x;
      pointer.y = loc.y;
      if (!was) {
        mouse.x = loc.x;
        mouse.y = loc.y;
      }
      energize(loc.x, loc.y);
      wake();
    }

    function onPointerDown(event) {
      var loc = locate(event);
      if (!loc.inside || !opts.clickPulse || reduce) return;
      pulses.push({ x: loc.x, y: loc.y, t0: clock, strength: 1 });
      wake();
    }

    function onPointerLeave() {
      pointer.inside = false;
      wake();
    }

    var resizeObserver = new ResizeObserver(function () {
      rebuild();
      draw();
      wake();
    });
    resizeObserver.observe(container);

    var intersection = new IntersectionObserver(function (entries) {
      visible = entries.some(function (entry) { return entry.isIntersecting; });
      if (visible) wake();
    });
    intersection.observe(container);

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('pointerdown', onPointerDown, { passive: true });
    document.documentElement.addEventListener('pointerleave', onPointerLeave);
    document.addEventListener('visibilitychange', function () { wake(); });

    rebuild();
    if (introClock < 1) pulses.push({ x: view.width / 2, y: view.height / 2, t0: 0.15, strength: 0.6 });
    draw();
    wake();
  }

  // Auto-initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', function () {
    var hero = document.getElementById('home');
    var canvas = document.getElementById('cpHeroCanvas');
    if (hero && canvas) {
      initCursorGrid(hero, canvas, {
        cellSize: 48,
        color: '#0D9488',       // CarePlus Medical Teal glow
        gridColor: '#CBD5E1',   // Soft Slate Grid Lines
        radius: 160,
        lineWidth: 1.2,
        gridOpacity: 0.22,
        maxOpacity: 0.85,
        fillOpacity: 0.08,
        spotlight: 0.6,
        clickPulse: true,
        ambient: 0.12
      });
    }
  });

  window.initCursorGrid = initCursorGrid;
})();
