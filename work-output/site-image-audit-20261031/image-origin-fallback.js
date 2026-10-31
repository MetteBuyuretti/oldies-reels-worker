(function () {
  'use strict';
  function fallback(img) {
    if (!img || img.tagName !== 'IMG' || img.dataset.oldiesOriginFallback) return;
    var u;
    try { u = new URL(img.currentSrc || img.src, document.baseURI); } catch (_) { return; }
    if (!/^i[0-3]\.wp\.com$/.test(u.hostname) || u.pathname.indexOf('/oldiesradyo.com/wp-content/uploads/') !== 0) return;
    var origin = 'https://oldiesradyo.com' + u.pathname.slice('/oldiesradyo.com'.length);
    img.dataset.oldiesOriginFallback = '1';
    img.removeAttribute('srcset');
    img.removeAttribute('sizes');
    var picture = img.closest('picture');
    if (picture) picture.querySelectorAll('source').forEach(function (s) { s.removeAttribute('srcset'); });
    img.src = origin;
  }
  document.addEventListener('error', function (event) { fallback(event.target); }, true);
  function scan() {
    document.querySelectorAll('img').forEach(function (img) {
      if (img.complete && img.naturalWidth === 0) fallback(img);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan, { once: true });
  else scan();
})();
