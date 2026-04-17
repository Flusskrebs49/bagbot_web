# ─────────────────────────────────────────────
#  bagbot_subnets.py — Géré par l'interface web BagBot
#  Ne pas éditer manuellement — utiliser http://IP_VM:5000
# ─────────────────────────────────────────────

SUBNET_SETTINGS = {
    # Exemple — remplacer par tes subnets réels
    # ou laisser vide et tout configurer via l'interface web
   11: {
        'buy_lower' : 0.00875,
        'buy_upper' : 0.01095,
        'sell_lower': 0.01735,
        'sell_upper': 0.02065,
        'max_alpha' : 32,
    },
}
