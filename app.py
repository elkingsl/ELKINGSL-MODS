import base64
import hashlib
import json
import time
from flask import Flask, request, make_response, redirect, url_for, render_template_string

app = Flask(__name__)

# ── IN-MEMORY STATE ──────────────────────────────────────────────────────────
players      = {}   # username -> score
solved_flags = {}   # username -> [flag_keys]
player_reg   = {}   # username -> timestamp

FLAGS = {
    "flag1": {"points": 10,  "value": "CTF{gh0st_1n_th3_h34d3r5}"},
    "flag2": {"points": 20,  "value": "CTF{r0b0ts_k33p_s3cr3ts}"},
    "flag3": {"points": 35,  "value": "CTF{s0urc3_c0d3_sp34ks}"},
    "flag4": {"points": 50,  "value": "CTF{c00k13_d0ct0r}"},
    "flag5": {"points": 65,  "value": "CTF{3nc0d1ng_1s_n0t_3ncrypt10n}"},
    "flag6": {"points": 80,  "value": "CTF{p4th_trav3rs4l_w1ns}"},
    "flag7": {"points": 95,  "value": "CTF{1d0r_3xp0s3d}"},
    "flag8": {"points": 120, "value": "CTF{t1m1ng_s1d3_ch4nn3l}"},
}

# ── STYLES & BASE ─────────────────────────────────────────────────────────────
STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

:root {
  --bg:       #030712;
  --bg2:      #0d1117;
  --bg3:      #111827;
  --border:   #1f6feb;
  --glow:     #58a6ff;
  --accent:   #f78166;
  --green:    #3fb950;
  --yellow:   #d29922;
  --dim:      #8b949e;
  --text:     #e6edf3;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Share Tech Mono', monospace;
  min-height: 100vh;
  overflow-x: hidden;
}

/* scanline overlay */
body::before {
  content: '';
  position: fixed; inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,.15) 2px,
    rgba(0,0,0,.15) 4px
  );
  pointer-events: none;
  z-index: 9999;
}

/* scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* HEADER */
header {
  border-bottom: 1px solid var(--border);
  padding: 14px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg2);
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 0 30px rgba(88,166,255,.08);
}

.logo {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 1.1rem;
  color: var(--glow);
  letter-spacing: .15em;
  text-shadow: 0 0 20px rgba(88,166,255,.6);
}

.logo span { color: var(--accent); }

nav a {
  color: var(--dim);
  text-decoration: none;
  font-size: .8rem;
  margin-left: 20px;
  letter-spacing: .1em;
  transition: color .2s;
}
nav a:hover { color: var(--glow); }

/* MAIN WRAP */
.wrap {
  max-width: 940px;
  margin: 0 auto;
  padding: 32px 20px 80px;
}

/* STATUS BAR */
.statusbar {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 10px 18px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 4px;
  margin-bottom: 28px;
  font-size: .8rem;
  color: var(--dim);
}
.statusbar .tag { color: var(--glow); }
.statusbar .score { color: var(--green); font-weight: bold; }
.statusbar .accent { color: var(--accent); }

/* PANEL */
.panel {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 22px 24px;
  margin-bottom: 22px;
  position: relative;
  overflow: hidden;
}
.panel::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--glow), transparent);
  opacity: .4;
}

.panel h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: .85rem;
  letter-spacing: .18em;
  color: var(--glow);
  margin-bottom: 16px;
  text-transform: uppercase;
}

/* CHALLENGE GRID */
.chall-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 14px;
}

.chall-card {
  background: var(--bg3);
  border: 1px solid #1c2d3f;
  border-radius: 4px;
  padding: 16px;
  position: relative;
  transition: border-color .25s, box-shadow .25s;
}
.chall-card:hover {
  border-color: var(--border);
  box-shadow: 0 0 18px rgba(88,166,255,.12);
}
.chall-card.solved {
  border-color: #1b3a2a;
  background: #0d1f16;
}
.chall-card.solved::after {
  content: '✓ SOLVED';
  position: absolute; top: 10px; right: 12px;
  font-size: .65rem;
  color: var(--green);
  letter-spacing: .1em;
}

.chall-num {
  font-size: .65rem;
  color: var(--dim);
  letter-spacing: .15em;
  margin-bottom: 6px;
}
.chall-name {
  font-family: 'Orbitron', sans-serif;
  font-size: .78rem;
  color: var(--text);
  margin-bottom: 4px;
}
.chall-cat {
  font-size: .68rem;
  color: var(--accent);
  letter-spacing: .1em;
  margin-bottom: 10px;
}
.chall-pts {
  font-size: .8rem;
  color: var(--yellow);
}
.chall-desc {
  font-size: .72rem;
  color: var(--dim);
  line-height: 1.5;
  margin-top: 8px;
}

/* SUBMIT FORM */
.flag-form {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.flag-input {
  flex: 1;
  min-width: 200px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-family: 'Share Tech Mono', monospace;
  font-size: .85rem;
  padding: 10px 14px;
  outline: none;
  transition: box-shadow .2s;
}
.flag-input:focus { box-shadow: 0 0 0 2px rgba(88,166,255,.3); }

.btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--glow);
  font-family: 'Share Tech Mono', monospace;
  font-size: .82rem;
  letter-spacing: .1em;
  padding: 10px 22px;
  border-radius: 4px;
  cursor: pointer;
  transition: background .2s, box-shadow .2s;
}
.btn:hover {
  background: rgba(88,166,255,.1);
  box-shadow: 0 0 16px rgba(88,166,255,.2);
}
.btn-danger { border-color: var(--accent); color: var(--accent); }
.btn-danger:hover { background: rgba(247,129,102,.1); }

/* MESSAGES */
.msg {
  padding: 10px 14px;
  border-radius: 4px;
  font-size: .8rem;
  margin-bottom: 18px;
  letter-spacing: .05em;
}
.msg-ok  { background: #0d2818; border: 1px solid var(--green); color: var(--green); }
.msg-err { background: #2a0d0d; border: 1px solid var(--accent); color: var(--accent); }
.msg-warn{ background: #241a00; border: 1px solid var(--yellow); color: var(--yellow); }

/* SCOREBOARD */
.score-table { width: 100%; border-collapse: collapse; font-size: .82rem; }
.score-table th {
  text-align: left;
  color: var(--dim);
  font-size: .7rem;
  letter-spacing: .15em;
  padding: 8px 12px;
  border-bottom: 1px solid #1c2d3f;
}
.score-table td { padding: 10px 12px; border-bottom: 1px solid #0d1117; }
.score-table tr:hover td { background: var(--bg3); }
.rank-1 { color: #ffd700; }
.rank-2 { color: #c0c0c0; }
.rank-3 { color: #cd7f32; }

/* LOGIN PAGE */
.login-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.login-box {
  width: 100%;
  max-width: 380px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 36px 32px;
  box-shadow: 0 0 60px rgba(88,166,255,.08);
}
.login-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 900;
  color: var(--glow);
  text-align: center;
  letter-spacing: .2em;
  margin-bottom: 8px;
  text-shadow: 0 0 30px rgba(88,166,255,.5);
}
.login-sub {
  text-align: center;
  color: var(--dim);
  font-size: .72rem;
  letter-spacing: .12em;
  margin-bottom: 28px;
}
.field { margin-bottom: 14px; }
.field label { display: block; font-size: .7rem; color: var(--dim); letter-spacing: .12em; margin-bottom: 6px; }
.field input {
  width: 100%;
  background: var(--bg3);
  border: 1px solid #1c2d3f;
  border-radius: 4px;
  color: var(--text);
  font-family: 'Share Tech Mono', monospace;
  font-size: .88rem;
  padding: 10px 14px;
  outline: none;
  transition: border-color .2s, box-shadow .2s;
}
.field input:focus { border-color: var(--border); box-shadow: 0 0 0 2px rgba(88,166,255,.2); }
.btn-full { width: 100%; margin-top: 8px; text-align: center; }

/* UTIL */
a { color: var(--glow); text-decoration: none; }
a:hover { text-decoration: underline; }
.dim { color: var(--dim); font-size: .75rem; }
.mt { margin-top: 14px; }
hr { border: none; border-top: 1px solid #1c2d3f; margin: 20px 0; }
"""

# ── CHALLENGE METADATA (shown on board) ──────────────────────────────────────
CHALLENGES = [
    {"key":"flag1","num":"01","name":"GHOST SIGNAL",    "cat":"RECON",       "pts":10,  "desc":"Every response carries more than you think. Check what the server sends back before the body loads."},
    {"key":"flag2","num":"02","name":"CRAWL SPACE",     "cat":"RECON",       "pts":20,  "desc":"Bots are told where not to go. Humans should probably go there."},
    {"key":"flag3","num":"03","name":"INVISIBLE INK",   "cat":"RECON",       "pts":35,  "desc":"The page says one thing. The source says another. Read between the tags."},
    {"key":"flag4","num":"04","name":"SWEET OVERRIDE",  "cat":"COOKIE ABUSE","pts":50,  "desc":"Your session knows your rank. But rank is just a string someone decided to trust."},
    {"key":"flag5","num":"05","name":"LOST IN TRANSIT", "cat":"ENCODING",    "pts":65,  "desc":"A locked page exists at /vault. It speaks in a language older than encryption."},
    {"key":"flag6","num":"06","name":"WRONG DOOR",      "cat":"PATH ABUSE",  "pts":80,  "desc":"The file server serves files. Maybe more files than it should."},
    {"key":"flag7","num":"07","name":"USER ZERO",       "cat":"IDOR",        "pts":95,  "desc":"Profiles are numbered. Not all numbers are shown. Some accounts are more interesting than others."},
    {"key":"flag8","num":"08","name":"TICK TOCK",       "cat":"SIDE CHANNEL","pts":120, "desc":"The login doesn't leak words. But it leaks time. Listen carefully."},
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_user():
    return request.cookies.get('username')

def render_base(content_html, username=None, msg=None, msg_type='ok'):
    score = players.get(username, 0) if username else 0
    solved = solved_flags.get(username, [])
    solved_count = len(solved)

    msg_html = ''
    if msg:
        msg_html = f'<div class="msg msg-{msg_type}">{msg}</div>'

    nav_links = ''
    if username:
        nav_links = f'''
        <nav>
          <a href="/">[HOME]</a>
          <a href="/scoreboard">[BOARD]</a>
          <a href="/logout">[LOGOUT]</a>
        </nav>'''

    status_bar = ''
    if username:
        status_bar = f'''
        <div class="statusbar">
          <span><span class="tag">&gt; OPERATOR:</span> {username}</span>
          <span><span class="tag">SCORE:</span> <span class="score">{score} pts</span></span>
          <span><span class="tag">FLAGS:</span> <span class="accent">{solved_count}/8</span></span>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NETBREACH CTF</title>
<!-- FLAG_3_HINT: you're getting warmer... keep reading the source -->
<style>{STYLE}</style>
</head>
<body>
<header>
  <div class="logo">NET<span>BREACH</span> // CTF</div>
  {nav_links}
</header>
<div class="wrap">
  {status_bar}
  {msg_html}
  {content_html}
</div>
</body>
</html>'''

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    username = get_user()
    msg      = request.args.get('msg', '')
    mtype    = request.args.get('mt', 'ok')

    if not username:
        return redirect(url_for('login_page'))

    solved = solved_flags.get(username, [])

    cards = ''
    for c in CHALLENGES:
        s = 'solved' if c['key'] in solved else ''
        cards += f'''
        <div class="chall-card {s}">
          <div class="chall-num">CHALLENGE {c["num"]}</div>
          <div class="chall-name">{c["name"]}</div>
          <div class="chall-cat">{c["cat"]}</div>
          <div class="chall-pts">{c["pts"]} PTS</div>
          <div class="chall-desc">{c["desc"]}</div>
        </div>'''

    content = f'''
    <div class="panel">
      <h2>// ACTIVE TARGETS</h2>
      <div class="chall-grid">{cards}</div>
    </div>
    <div class="panel">
      <h2>// SUBMIT FLAG</h2>
      <div class="flag-form">
        <form method="POST" action="/submit" style="display:flex;gap:10px;flex:1;flex-wrap:wrap;">
          <input class="flag-input" type="text" name="flag" placeholder="CTF{{...}}" required autocomplete="off">
          <button class="btn" type="submit">[SUBMIT]</button>
        </form>
      </div>
    </div>'''

    resp = make_response(render_base(content, username=username, msg=msg, msg_type=mtype))
    # CHALLENGE 1 — flag in response header
    resp.headers['X-Operator-Token'] = FLAGS['flag1']['value']
    return resp


@app.route('/login', methods=['GET','POST'])
def login_page():
    err = ''
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        if not username or len(username) > 24:
            err = 'Invalid handle.'
        else:
            if username not in players:
                players[username]      = 0
                solved_flags[username] = []
                player_reg[username]   = time.time()
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('username', username, httponly=True)
            # role cookie is base64('operative') — challenge 4 expects 'root'
            resp.set_cookie('role', base64.b64encode(b'operative').decode(), httponly=False)
            return resp

    err_html = f'<div class="msg msg-err">{err}</div>' if err else ''
    body = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NETBREACH CTF</title>
<style>{STYLE}</style>
</head>
<body>
<div class="login-wrap">
  <div class="login-box">
    <div class="login-title">NETBREACH</div>
    <div class="login-sub">// CAPTURE THE FLAG ARENA</div>
    {err_html}
    <form method="POST" action="/login">
      <div class="field">
        <label>OPERATOR HANDLE</label>
        <input type="text" name="username" placeholder="enter callsign..." autocomplete="off" required>
      </div>
      <button class="btn btn-full" type="submit">[CONNECT TO ARENA]</button>
    </form>
    <p class="dim mt" style="text-align:center">No registration. No password. Just a name.</p>
  </div>
</div>
</body>
</html>'''
    return body


@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login_page')))
    resp.delete_cookie('username')
    resp.delete_cookie('role')
    return resp


@app.route('/submit', methods=['POST'])
def submit():
    username = get_user()
    if not username:
        return redirect(url_for('login_page'))

    submitted = request.form.get('flag','').strip()
    for key, data in FLAGS.items():
        if submitted == data['value']:
            if key in solved_flags[username]:
                return redirect(url_for('index', msg='Flag already captured.', mt='warn'))
            solved_flags[username].append(key)
            players[username] += data['points']
            return redirect(url_for('index', msg=f'Flag accepted. +{data["points"]} pts', mt='ok'))
    return redirect(url_for('index', msg='Invalid flag. Keep digging.', mt='err'))


@app.route('/scoreboard')
def scoreboard():
    username = get_user()
    if not username:
        return redirect(url_for('login_page'))

    ranked = sorted(players.items(), key=lambda x: x[1], reverse=True)
    rows = ''
    for i, (p, s) in enumerate(ranked, 1):
        cls = f'rank-{i}' if i <= 3 else ''
        medal = ['','🥇','🥈','🥉'][i] if i <= 3 else str(i)
        solved_count = len(solved_flags.get(p, []))
        rows += f'<tr><td class="{cls}">{medal}</td><td>{p}</td><td style="color:var(--green)">{s}</td><td style="color:var(--dim)">{solved_count}/8</td></tr>'

    content = f'''
    <div class="panel">
      <h2>// GLOBAL RANKINGS</h2>
      <table class="score-table">
        <thead><tr><th>#</th><th>OPERATOR</th><th>SCORE</th><th>FLAGS</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 2 — robots.txt ──────────────────────────────────────────────────
@app.route('/robots.txt')
def robots():
    return (
        "User-agent: *\n"
        "Disallow: /sys/core_dump\n"
        "Disallow: /admin\n"
        "Disallow: /backup\n"
    ), 200, {'Content-Type': 'text/plain'}

@app.route('/sys/core_dump')
def core_dump():
    username = get_user()
    content = f'''
    <div class="panel">
      <h2>// CORE DUMP — RESTRICTED</h2>
      <p style="color:var(--green);font-size:.9rem">You found the crawl space.</p>
      <p class="dim mt">Payload dump: <span style="color:var(--accent)">{FLAGS["flag2"]["value"]}</span></p>
    </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 3 — HTML comment in source ─────────────────────────────────────
# Flag is embedded as an HTML comment in the base render (see render_base)
# The comment <!-- FLAG_3_HINT --> leads players; actual flag is deeper:
@app.route('/terminal')
def terminal():
    username = get_user()
    # Flag hidden inside an HTML comment block in this page's source
    content = f'''
    <!-- SYSTEM_CACHE: {FLAGS["flag3"]["value"]} -->
    <div class="panel">
      <h2>// SYSTEM TERMINAL</h2>
      <p class="dim">Diagnostic interface. Nothing to see here.</p>
      <p class="dim mt">&gt; All systems nominal.</p>
      <p class="dim">&gt; No anomalies detected.</p>
      <p class="dim">&gt; Have a nice day.</p>
    </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 4 — cookie role abuse ──────────────────────────────────────────
@app.route('/ops/panel')
def ops_panel():
    username = get_user()
    if not username:
        return redirect(url_for('login_page'))

    role_b64 = request.cookies.get('role','')
    try:
        role = base64.b64decode(role_b64).decode()
    except Exception:
        role = ''

    if role == 'root':
        content = f'''
        <div class="panel">
          <h2>// ROOT SHELL ACTIVE</h2>
          <p style="color:var(--green)">Privilege escalation confirmed.</p>
          <p class="mt">Access token: <span style="color:var(--accent)">{FLAGS["flag4"]["value"]}</span></p>
        </div>'''
    else:
        content = f'''
        <div class="panel">
          <h2>// OPS PANEL — ACCESS DENIED</h2>
          <p style="color:var(--accent)">Insufficient clearance. Current role: <strong>{role or "unknown"}</strong></p>
          <p class="dim mt">Only <em>root</em> operators may proceed.</p>
        </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 5 — encoding (base64 encoded flag on /vault) ───────────────────
_vault_encoded = base64.b64encode(FLAGS['flag5']['value'].encode()).decode()

@app.route('/vault')
def vault():
    username = get_user()
    content = f'''
    <div class="panel">
      <h2>// ENCRYPTED VAULT</h2>
      <p class="dim">Archive access log:</p>
      <p class="mt" style="word-break:break-all;color:var(--yellow);font-size:.8rem">{_vault_encoded}</p>
      <p class="dim mt">Encoding level: ALPHA-1. Cipher: [REDACTED]</p>
    </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 6 — path traversal simulation ──────────────────────────────────
@app.route('/files')
def files():
    username = get_user()
    content = '''
    <div class="panel">
      <h2>// FILE SERVER</h2>
      <p class="dim">Available documents:</p>
      <ul style="margin-top:14px;list-style:none;line-height:2">
        <li><a href="/files/read?name=readme.txt">&gt; readme.txt</a></li>
        <li><a href="/files/read?name=changelog.txt">&gt; changelog.txt</a></li>
        <li><a href="/files/read?name=status.txt">&gt; status.txt</a></li>
      </ul>
    </div>'''
    return render_base(content, username=username)

_file_store = {
    "readme.txt":    "NETBREACH CTF v2.0 — welcome, operator.",
    "changelog.txt": "v2.0 — upgraded challenge set.\nv1.0 — initial deployment.",
    "status.txt":    "All systems operational.",
    # hidden — only reachable via traversal attempt (../ or direct name)
    "../secret/config.txt":  f"SYSTEM CONFIG\n---\n{FLAGS['flag6']['value']}\n---",
    "secret/config.txt":     f"SYSTEM CONFIG\n---\n{FLAGS['flag6']['value']}\n---",
    "config.txt":            f"SYSTEM CONFIG\n---\n{FLAGS['flag6']['value']}\n---",
}

@app.route('/files/read')
def file_read():
    username = get_user()
    name = request.args.get('name','')
    text = _file_store.get(name, None)
    if text is None:
        text = f"File not found: {name}"
    content = f'''
    <div class="panel">
      <h2>// FILE: {name}</h2>
      <pre style="color:var(--green);font-size:.8rem;white-space:pre-wrap">{text}</pre>
      <p class="dim mt"><a href="/files">[back]</a></p>
    </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 7 — IDOR: /profile/<id> ────────────────────────────────────────
_profiles = {
    "1": {"handle": "ghost_null",  "rank": "operative", "note": ""},
    "2": {"handle": "xr4y",        "rank": "operative", "note": ""},
    "3": {"handle": "static_void", "rank": "operative", "note": ""},
    "0": {"handle": "SYSTEM",      "rank": "root",      "note": FLAGS['flag7']['value']},
}

@app.route('/profile')
def profile_self():
    username = get_user()
    if not username:
        return redirect(url_for('login_page'))
    content = f'''
    <div class="panel">
      <h2>// YOUR PROFILE</h2>
      <p>Handle: <strong>{username}</strong></p>
      <p class="mt dim">Profile ID: <span style="color:var(--glow)">assigned dynamically</span></p>
      <p class="dim mt">Other operators: <a href="/profile/1">/profile/1</a>, <a href="/profile/2">/profile/2</a>, <a href="/profile/3">/profile/3</a></p>
    </div>'''
    return render_base(content, username=username)

@app.route('/profile/<pid>')
def profile_view(pid):
    username = get_user()
    p = _profiles.get(pid)
    if not p:
        content = '<div class="panel"><h2>// 404</h2><p class="dim">No such profile.</p></div>'
        return render_base(content, username=username)
    note_html = f'<p class="mt" style="color:var(--accent)">NOTE: {p["note"]}</p>' if p['note'] else ''
    content = f'''
    <div class="panel">
      <h2>// OPERATOR PROFILE #{pid}</h2>
      <p>Handle: <strong>{p["handle"]}</strong></p>
      <p>Rank: <span style="color:var(--yellow)">{p["rank"]}</span></p>
      {note_html}
    </div>'''
    return render_base(content, username=username)


# ── CHALLENGE 8 — timing side channel ────────────────────────────────────────
# Secret PIN — players must time requests to discover '0000' gives a longer response
_SECRET_PIN = "0000"

@app.route('/auth/pin', methods=['GET','POST'])
def pin_auth():
    username = get_user()
    result_html = ''
    if request.method == 'POST':
        pin = request.form.get('pin','')
        # Simulate a timing difference: correct prefix takes slightly longer
        match_len = 0
        for a, b in zip(pin, _SECRET_PIN):
            if a == b:
                match_len += 1
                time.sleep(0.04)   # 40ms per correct digit — measurable
            else:
                break
        if pin == _SECRET_PIN:
            result_html = f'<p style="color:var(--green)" class="mt">PIN accepted. Access token: <strong>{FLAGS["flag8"]["value"]}</strong></p>'
        else:
            result_html = f'<p style="color:var(--accent)" class="mt">PIN rejected. ({match_len}/4 correct)</p>'

    content = f'''
    <div class="panel">
      <h2>// PIN AUTHENTICATION TERMINAL</h2>
      <p class="dim">4-digit PIN required. 10000 possible combinations.</p>
      <p class="dim mt">Hint: measure what you cannot see.</p>
      <form method="POST" action="/auth/pin" style="margin-top:16px">
        <div class="flag-form">
          <input class="flag-input" type="text" name="pin" maxlength="4" placeholder="0000" style="max-width:120px" autocomplete="off">
          <button class="btn" type="submit">[SUBMIT PIN]</button>
        </div>
      </form>
      {result_html}
    </div>'''
    return render_base(content, username=username)


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
