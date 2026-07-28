(function () {
  var bg = "#fff7fa";
  var pink = "#d23b70";
  var muted = "#767a82";
  var rule = "#ead6dc";

  function setup(canvas) {
    var ctx = canvas.getContext("2d", { alpha: false });
    var start = performance.now();

    function resize() {
      var rect = canvas.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function point(t, phase, scale) {
      var r = Math.exp(Math.cos(t)) - 2 * Math.cos(4 * t) - Math.pow(Math.sin(t / 12), 5);
      var wobble = 1 + Math.sin(t * 3 + phase) * 0.045;
      return {
        x: Math.sin(t + phase * 0.22) * r * scale * wobble,
        y: -Math.cos(t) * r * scale * (1 + Math.cos(phase + t * 2) * 0.035)
      };
    }

    function drawPath(cx, cy, scale, phase, alpha, width) {
      var steps = 260;
      ctx.beginPath();
      for (var i = 0; i <= steps; i += 1) {
        var t = (i / steps) * Math.PI * 24;
        var p = point(t, phase, scale);
        var x = cx + p.x;
        var y = cy + p.y;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.globalAlpha = alpha;
      ctx.lineWidth = width;
      ctx.strokeStyle = pink;
      ctx.stroke();
    }

    function frame(now) {
      var rect = canvas.getBoundingClientRect();
      var w = rect.width;
      var h = rect.height;
      var cx = w * 0.5;
      var cy = h * 0.48;
      var s = Math.min(w, h) * 0.105;
      var phase = (now - start) * 0.001;

      ctx.globalAlpha = 1;
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      ctx.strokeStyle = rule;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, h * 0.14);
      ctx.lineTo(cx, h * 0.88);
      ctx.stroke();

      drawPath(cx, cy, s * 1.04, phase, 0.28, Math.max(1, w / 82));
      drawPath(cx, cy, s * 0.96, phase + 0.7, 0.82, Math.max(1.4, w / 54));
      drawPath(cx, cy, s * 0.82, phase + 1.5, 0.34, Math.max(1, w / 90));

      ctx.globalAlpha = 0.55;
      ctx.strokeStyle = muted;
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.arc(cx, cy + h * 0.29, Math.min(w, h) * 0.08, Math.PI * 0.08, Math.PI * 0.92);
      ctx.stroke();

      requestAnimationFrame(frame);
    }

    resize();
    if ("ResizeObserver" in window) new ResizeObserver(resize).observe(canvas);
    else window.addEventListener("resize", resize);
    requestAnimationFrame(frame);
  }

  document.querySelectorAll("canvas[data-organic]").forEach(setup);
}());
