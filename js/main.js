(function () {
  var btn = document.querySelector('.burger');
  var nav = document.getElementById('menu');
  if (!btn || !nav) return;

  function setOpen(open) {
    nav.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
  }
  btn.addEventListener('click', function () { setOpen(!nav.classList.contains('open')); });
  nav.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('open')) { setOpen(false); btn.focus(); }
  });
  window.addEventListener('resize', function () { if (window.innerWidth > 980) setOpen(false); });

  var page = location.pathname.split('/').pop() || 'index.html';
  nav.querySelectorAll('a').forEach(function (a) {
    if (a.getAttribute('href') === page) a.setAttribute('aria-current', 'page');
  });
})();

/* Filtres des actualités */
(function () {
  var tiles = document.querySelectorAll('.theme');
  var arts = document.querySelectorAll('.art[data-cat]');
  var mag = document.querySelector('.mag');
  if (!tiles.length || !mag) return;
  tiles.forEach(function (t) {
    t.addEventListener('click', function () {
      var f = t.getAttribute('data-filter');
      tiles.forEach(function (o) { o.setAttribute('aria-pressed', o === t ? 'true' : 'false'); });
      var shown = 0;
      arts.forEach(function (a) {
        var ok = f === 'tous' || a.getAttribute('data-cat') === f;
        a.hidden = !ok;
        if (ok) shown++;
      });
      mag.classList.toggle('one', f !== 'tous');
      var live = document.getElementById('live');
      if (live) live.textContent = shown + (shown > 1 ? ' articles affichés' : ' article affiché');
    });
  });
})();

/* Formulaire de contact : validation puis récapitulatif prêt à envoyer */
(function () {
  var form = document.getElementById('form-devis');
  if (!form) return;
  var TEL = '+33665955926', MAIL = 'contact@arpegepaysages.com';
  var recap = document.getElementById('recap'), out = document.getElementById('recap-text');
  var status = document.getElementById('copy-status');
  function field(id) { return document.getElementById(id); }
  function setErr(id, msg) {
    var f = field(id), e = field('err-' + id);
    e.textContent = msg || '';
    if (msg) f.setAttribute('aria-invalid', 'true'); else f.removeAttribute('aria-invalid');
    return !msg;
  }
  function check() {
    var ok = true, first = null;
    var nom = field('nom').value.trim(), tel = field('tel').value.replace(/[\s.\-]/g, ''), com = field('commune').value.trim(), bes = field('besoin').value;
    var res = [
      ['nom', nom.length < 2 ? 'Indiquez votre nom.' : ''],
      ['tel', !/^(?:\+33|0033|0)[1-9]\d{8}$/.test(tel) ? 'Indiquez un numéro valide, par exemple 06 12 34 56 78.' : ''],
      ['commune', com.length < 2 ? 'Indiquez votre commune.' : ''],
      ['besoin', !bes ? 'Choisissez votre besoin.' : '']
    ];
    res.forEach(function (r) { var good = setErr(r[0], r[1]); if (!good && !first) first = r[0]; ok = ok && good; });
    if (first) field(first).focus();
    return ok;
  }
  ['nom', 'tel', 'commune', 'besoin'].forEach(function (id) {
    field(id).addEventListener('input', function () { if (field(id).getAttribute('aria-invalid')) setErr(id, ''); });
  });
  function message() {
    var m = field('message').value.trim();
    return 'Bonjour, je souhaite un devis.\n' +
      'Nom : ' + field('nom').value.trim() + '\n' +
      'Téléphone : ' + field('tel').value.trim() + '\n' +
      'Commune : ' + field('commune').value.trim() + '\n' +
      'Besoin : ' + field('besoin').value + (m ? '\nMessage : ' + m : '');
  }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!check()) return;
    var txt = message();
    out.textContent = txt;
    document.getElementById('bt-sms').href = 'sms:' + TEL + '?body=' + encodeURIComponent(txt);
    document.getElementById('bt-mail').href = 'mailto:' + MAIL + '?subject=' + encodeURIComponent('Demande de devis') + '&body=' + encodeURIComponent(txt);
    status.textContent = '';
    recap.hidden = false;
    recap.scrollIntoView({ behavior: 'smooth', block: 'center' });
    recap.focus();
  });
  document.getElementById('bt-copy').addEventListener('click', function () {
    var txt = out.textContent;
    function fallback() {
      var r = document.createRange(); r.selectNodeContents(out);
      var s = getSelection(); s.removeAllRanges(); s.addRange(r);
      status.textContent = 'Texte sélectionné : copiez-le avec Ctrl+C ou le menu de votre téléphone.';
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(function () { status.textContent = 'Texte copié.'; }, fallback);
    } else fallback();
  });
})();
