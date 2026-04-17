#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  bagbot_web.py  —  Interface web de gestion BagBot
#  Lance avec : python3 bagbot_web.py
#  Accessible sur : http://IP_VM:5000
# ─────────────────────────────────────────────

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pathlib import Path
from functools import wraps
from datetime import timedelta
from collections import defaultdict
import ast
import time
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Configuration ─────────────────────────────
WEB_PASSWORD          = "password"   # ← modifier ce mot de passe
SESSION_LIFETIME_H    = 4            # expiration de session en heures
MAX_FAILED_ATTEMPTS   = 5            # tentatives max avant blocage
BRUTE_FORCE_WINDOW_S  = 300          # fenêtre de blocage en secondes (5 min)

SETTINGS_FILE    = Path("bagbot_settings.py")
OVERRIDES_FILE   = Path("bagbot_settings_overrides.py")
SUBNETS_FILE     = Path("bagbot_subnets.py")   # géré exclusivement par cette interface

# ── Protection brute force ────────────────────
_failed_attempts = defaultdict(list)  # { ip: [timestamp, ...] }

def is_blocked(ip: str) -> bool:
    """Retourne True si l'IP a dépassé le nombre de tentatives autorisées."""
    now = time.time()
    # Ne garder que les tentatives dans la fenêtre de temps
    _failed_attempts[ip] = [t for t in _failed_attempts[ip] if now - t < BRUTE_FORCE_WINDOW_S]
    return len(_failed_attempts[ip]) >= MAX_FAILED_ATTEMPTS

def record_failure(ip: str):
    """Enregistre une tentative échouée pour cette IP."""
    _failed_attempts[ip].append(time.time())

def reset_failures(ip: str):
    """Réinitialise le compteur après un login réussi."""
    _failed_attempts.pop(ip, None)

def remaining_lockout(ip: str) -> int:
    """Retourne le nombre de secondes restantes avant déblocage."""
    if not _failed_attempts.get(ip):
        return 0
    oldest = min(_failed_attempts[ip])
    remaining = int(BRUTE_FORCE_WINDOW_S - (time.time() - oldest))
    return max(0, remaining)

# ── Session ───────────────────────────────────
@app.before_request
def check_session_expiry():
    """Vérifie l'expiration de session à chaque requête."""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=SESSION_LIFETIME_H)

# ── Auth ──────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    ip    = request.remote_addr
    error = None

    if request.method == 'POST':
        if is_blocked(ip):
            secs = remaining_lockout(ip)
            error = f"Trop de tentatives. Réessayez dans {secs}s."
        elif request.form.get('password') == WEB_PASSWORD:
            session.permanent = True
            session['logged_in'] = True
            reset_failures(ip)
            return redirect(url_for('index'))
        else:
            record_failure(ip)
            remaining = MAX_FAILED_ATTEMPTS - len(_failed_attempts[ip])
            if remaining > 0:
                error = f"Mot de passe incorrect ({remaining} tentative(s) restante(s))"
            else:
                error = f"Trop de tentatives. Réessayez dans {BRUTE_FORCE_WINDOW_S}s."

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Lecture / écriture config ─────────────────

def _parse_file(path):
    """Parse un fichier Python settings via AST et retourne ses variables."""
    result = {}
    if not path.exists():
        return result
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return result
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    result[target.id] = ast.literal_eval(node.value)
                except Exception:
                    pass
    return result


def load_subnets():
    """Lit SUBNET_SETTINGS depuis bagbot_subnets.py uniquement."""
    data = _parse_file(SUBNETS_FILE)
    if 'SUBNET_SETTINGS' in data:
        return data['SUBNET_SETTINGS']
    # Fallback si bagbot_subnets.py n'existe pas encore
    base = _parse_file(SETTINGS_FILE)
    base.update(_parse_file(OVERRIDES_FILE))
    return base.get('SUBNET_SETTINGS', {})


def load_settings():
    """Config fusionnée pour l'affichage (lecture seule)."""
    s = _parse_file(SETTINGS_FILE)
    s.update(_parse_file(OVERRIDES_FILE))
    s.update(_parse_file(SUBNETS_FILE))
    return s


def write_subnets(subnet_settings):
    """Écrit UNIQUEMENT bagbot_subnets.py. Ne touche jamais aux autres fichiers."""
    lines = []
    lines.append("# ─────────────────────────────────────────────\n")
    lines.append("#  bagbot_subnets.py — Géré par l'interface web BagBot\n")
    lines.append("#  Ne pas éditer manuellement\n")
    lines.append("# ─────────────────────────────────────────────\n\n")
    lines.append("SUBNET_SETTINGS = {\n")
    for netuid in sorted(subnet_settings.keys()):
        s = subnet_settings[netuid]
        lines.append(f"    {netuid}: {{\n")
        lines.append(f"        'buy_lower' : {s['buy_lower']},\n")
        lines.append(f"        'buy_upper' : {s['buy_upper']},\n")
        lines.append(f"        'sell_lower': {s['sell_lower']},\n")
        lines.append(f"        'sell_upper': {s['sell_upper']},\n")
        lines.append(f"        'max_alpha' : {s['max_alpha']},\n")
        lines.append(f"    }},\n")
    lines.append("}\n")
    SUBNETS_FILE.write_text("".join(lines), encoding="utf-8")


def validate_subnet(data):
    """Retourne un message d'erreur ou None si valide."""
    try:
        buy_lower  = float(data['buy_lower'])
        buy_upper  = float(data['buy_upper'])
        sell_lower = float(data['sell_lower'])
        sell_upper = float(data['sell_upper'])
        max_alpha  = float(data['max_alpha'])
    except (KeyError, ValueError):
        return "Tous les champs sont requis et doivent être des nombres"
    if buy_upper > sell_lower:
        return f"buy_upper ({buy_upper}) doit être inférieur à sell_lower ({sell_lower})"
    if sell_upper < sell_lower:
        return f"sell_upper ({sell_upper}) doit être supérieur à sell_lower ({sell_lower})"
    if buy_lower > buy_upper:
        return f"buy_lower ({buy_lower}) doit être inférieur à buy_upper ({buy_upper})"
    if max_alpha <= 0:
        return "max_alpha doit être supérieur à 0"
    return None


# ── Routes ────────────────────────────────────

@app.route('/')
@login_required
def index():
    subnet_grids = load_subnets()
    return render_template('index.html', subnets=subnet_grids)


@app.route('/api/subnets', methods=['GET'])
@login_required
def api_get_subnets():
    return jsonify(load_subnets())


@app.route('/api/subnet/save', methods=['POST'])
@login_required
def api_save_subnet():
    """Ajoute ou modifie un subnet."""
    data = request.get_json()
    try:
        netuid = int(data.get('netuid'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'netuid invalide'}), 400

    if netuid == 0:
        return jsonify({'success': False, 'error': 'netuid 0 non supporté'}), 400

    err = validate_subnet(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    subnet_grids = load_subnets()

    subnet_grids[netuid] = {
        'buy_lower' : float(data['buy_lower']),
        'buy_upper' : float(data['buy_upper']),
        'sell_lower': float(data['sell_lower']),
        'sell_upper': float(data['sell_upper']),
        'max_alpha' : float(data['max_alpha']),
    }

    write_subnets(subnet_grids)
    return jsonify({'success': True, 'message': f'SN{netuid} sauvegardé'})


@app.route('/api/subnet/delete', methods=['POST'])
@login_required
def api_delete_subnet():
    """Supprime un subnet."""
    data = request.get_json()
    try:
        netuid = int(data.get('netuid'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'netuid invalide'}), 400

    subnet_grids = load_subnets()

    if netuid not in subnet_grids:
        return jsonify({'success': False, 'error': f'SN{netuid} introuvable'}), 404

    del subnet_grids[netuid]
    write_subnets(subnet_grids)
    return jsonify({'success': True, 'message': f'SN{netuid} supprimé'})


# ── Lancement ─────────────────────────────────

if __name__ == '__main__':
    # Crée le dossier templates si nécessaire
    Path("templates").mkdir(exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
