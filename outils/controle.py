"""Contrôle unique : python3 outils/controle.py [pages...] [--w 390,1280]
N'affiche que les anomalies, ou « tout est OK »."""
import sys, os, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
pages = args or ['index.html']
widths = [360, 414, 768, 980, 1280, 1920]
if '--w' in sys.argv:
    widths = [int(x) for x in sys.argv[sys.argv.index('--w') + 1].split(',')]
    pages = [a for a in pages if not a.replace(',', '').isdigit()]

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
H = functools.partial(Q, directory=ROOT)
srv = socketserver.TCPServer(('127.0.0.1', 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

JS = """() => {
  const out = [], vw = innerWidth, vh = innerHeight;
  const de = document.documentElement;
  if (de.scrollWidth > vw + 1) out.push('débordement horizontal ' + de.scrollWidth + '>' + vw);
  const seen = new Set();
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none') return;
    if (el.closest('.services') && cs.overflowX !== 'visible') {}
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && parseFloat(cs.fontSize) < 15.99) { const k = 'fs' + el.className + el.tagName; if (!seen.has(k)) { seen.add(k); out.push('texte ' + cs.fontSize + ' <' + el.tagName + '.' + el.className + '>'); } }
    if (own && el.scrollWidth > el.clientWidth + 1 && cs.overflowX !== 'visible' && cs.overflowX !== 'auto') out.push('texte coupé <' + el.tagName + '.' + el.className + '>');
    if (['A', 'BUTTON'].includes(el.tagName) && !el.closest('p')) {
      if ((r.height < 43.5 || r.width < 43.5)) { const k = 'tap' + el.textContent.trim().slice(0, 20); if (!seen.has(k)) { seen.add(k); out.push('cible ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' ' + el.textContent.trim().slice(0, 25)); } }
    }
    if (el.tagName === 'IMG') {
      if (el.naturalWidth && el.complete) {
        const ar = el.naturalWidth / el.naturalHeight, cr = r.width / r.height;
        const fit = cs.objectFit;
        if (fit === 'fill' && Math.abs(ar - cr) / ar > 0.03) out.push('image déformée ' + el.getAttribute('src'));
        if (r.width > el.naturalWidth * 1.02 && el.getAttribute('src').indexOf('logo') < 0 && el.getAttribute('src').indexOf('hero') < 0) out.push('image agrandie ' + el.getAttribute('src'));
      } else if (!el.complete || !el.naturalWidth) out.push('image non chargée ' + el.getAttribute('src'));
      if (!el.getAttribute('alt') && el.getAttribute('alt') !== '') out.push('alt manquant ' + el.getAttribute('src'));
    }
  });
  const secs = [...document.querySelectorAll('main > section')].map(s => [s.id || s.className.split(' ')[1], +(s.getBoundingClientRect().height / vh).toFixed(2)]);
  const foot = document.querySelector('.site-footer').getBoundingClientRect().height / vh;
  const nav = document.querySelector('.nav'), br = document.querySelector('.brand').getBoundingClientRect(), call = document.querySelector('.call').getBoundingClientRect();
  const burger = getComputedStyle(document.querySelector('.burger')).display;
  if (vw > 980 && burger !== 'none') out.push('burger visible > 980');
  if (vw <= 980 && burger === 'none') out.push('burger absent <= 980');
  if (vw <= 980) { const bt = document.querySelector('.brand span').getBoundingClientRect(), bg = document.querySelector('.burger').getBoundingClientRect(); if (bt.right > call.left - 2 || call.right > bg.left + 1) out.push('chevauchement barre mobile'); }
  if (vw > 980) { const links = [...nav.querySelectorAll('a')].map(a => a.getBoundingClientRect()); if (br.right > links[0].left - 4 || links[links.length - 1].right > call.left - 4) out.push('chevauchement barre'); }
  return {out, secs, foot: +foot.toFixed(2), h1: document.querySelectorAll('h1').length};
}"""

bad = 0
info = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for pg in pages:
        for w in widths + ([821, 981] if not '--w' in sys.argv else []):
            ctx = b.new_context(viewport={'width': w, 'height': 800 if w > 700 else 844})
            page = ctx.new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            page.goto(f'http://127.0.0.1:{port}/{pg}', wait_until='load')
            page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
            page.wait_for_timeout(300)
            r = page.evaluate(JS)
            if '--poids' not in sys.argv: pass
            probs = r['out'] + errs
            if r['h1'] != 1: probs.append('h1=%d' % r['h1'])
            if r['foot'] > 0.31 and w >= 768: probs.append('pied > 30 %% (%s)' % r['foot'])
            if w in (390, 414, 1280):
                info.append((pg, w, r['secs'], r['foot']))
            if probs:
                bad += 1
                print(f'[{pg} {w}px]', '; '.join(dict.fromkeys(probs)))
            ctx.close()
    b.close()

# liens relatifs + poids des images
import re
for pg in pages:
    html = open(os.path.join(ROOT, pg), encoding='utf-8').read()
    tot = 0
    for ref in set(re.findall(r'(?:src|href)="([^"#:]+?)(?:#[^"]*)?"', html)):
        if ref.startswith(('http', 'mailto', 'tel', 'sms')): continue
        f = os.path.join(ROOT, ref)
        if not os.path.exists(f):
            print(f'[{pg}] lien/fichier manquant: {ref}'); bad += 1
        elif ref.startswith('images/'):
            s = os.path.getsize(f); tot += s
            if s > 250 * 1024: print(f'[{pg}] image > 250 Ko: {ref} {s // 1024} Ko'); bad += 1
    if tot > 1.5 * 1024 * 1024: print(f'[{pg}] images > 1,5 Mo: {tot // 1024} Ko'); bad += 1
    for m in ['robots', 'description']:
        if f'name="{m}"' not in html: print(f'[{pg}] meta {m} manquante'); bad += 1

if '--info' in sys.argv:
    for i in info: print(i)
print('tout est OK' if not bad else f'{bad} anomalie(s)')
