// A link to #r2n_xxx opens the dropdown (<details>) that holds that function and scrolls to it.
function openTarget() {
  var id = decodeURIComponent(location.hash.slice(1));
  if (!id) return;
  var el = document.getElementById(id);
  if (!el) return;
  var d = el.closest('details');
  if (!d) {
    var n = el.parentElement;
    while (n && !d) { n = n.nextElementSibling; if (n && n.tagName === 'DETAILS') d = n; if (n && n.querySelector && !d) d = n.querySelector('details'); break; }
  }
  if (d) { d.open = true; setTimeout(function () { (d.previousElementSibling || d).scrollIntoView({ block: 'start' }); }, 0); }
}
window.addEventListener('hashchange', openTarget);
document.addEventListener('DOMContentLoaded', openTarget);
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[href^="#r2n_"]');
  if (a && a.getAttribute('href') === location.hash) setTimeout(openTarget, 0);
});
