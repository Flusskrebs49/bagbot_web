# ─────────────────────────────────────────────
#  influx_reporter.py  —  Envoi des métriques BagBot vers InfluxDB 1.8
# ─────────────────────────────────────────────

import requests
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────
INFLUX_URL      = "http://192.xxx.xxx.xxx:8086"
INFLUX_DB       = "xxxxxxxx"
INFLUX_USER     = "xxxxxxxx"
INFLUX_PASSWORD = "xxxxxxxx"

# ── Cache prix TAO/USDT ───────────────────────
BINANCE_URL          = "https://api.binance.com/api/v3/ticker/price?symbol=TAOUSDT"
TAO_USDT_CACHE_TTL   = 60      # secondes entre chaque appel Binance
_tao_usdt_price      = None    # dernière valeur connue
_tao_usdt_last_fetch = 0.0     # timestamp du dernier fetch


def _get_tao_usdt_price() -> float:
    """
    Retourne le prix TAO/USDT depuis Binance.
    Utilise un cache de 60 secondes pour éviter de surcharger l'API.
    Retourne la dernière valeur connue en cas d'erreur.
    """
    global _tao_usdt_price, _tao_usdt_last_fetch

    now = time.time()
    if now - _tao_usdt_last_fetch < TAO_USDT_CACHE_TTL and _tao_usdt_price is not None:
        return _tao_usdt_price  # cache encore valide

    try:
        resp = requests.get(BINANCE_URL, timeout=5)
        resp.raise_for_status()
        price = float(resp.json()["price"])
        _tao_usdt_price      = price
        _tao_usdt_last_fetch = now
        logger.debug(f"[Binance] TAO/USDT mis à jour : {price:.2f}")
        return price
    except Exception as e:
        logger.warning(f"[Binance] Impossible de récupérer TAO/USDT : {e}")
        return _tao_usdt_price if _tao_usdt_price is not None else 0.0


def _build_line(measurement: str, tags: dict, fields: dict, timestamp_ns: int) -> str:
    """
    Construit une ligne au format InfluxDB Line Protocol.
    measurement,tag1=val1,tag2=val2 field1=val1,field2=val2 timestamp
    """
    tag_str   = ",".join(f"{k}={v}" for k, v in tags.items())
    field_str = ",".join(
        f"{k}={v}i" if isinstance(v, int) else f"{k}={v}"
        for k, v in fields.items()
    )
    return f"{measurement},{tag_str} {field_str} {timestamp_ns}"


def send_metrics(bot_instance, stats: dict, trade_counts: dict, balance: float, watched_wallets: dict = None):
    """
    Envoie toutes les métriques du bot vers InfluxDB.
    À appeler à chaque tick depuis bagbot.py.

    bot_instance : instance de BittensorUtility
    stats        : self.stats  (prix, tao_in, alpha_in par subnet)
    trade_counts : self.trade_counts
    balance      : self.balance
    """
    try:
        import time
        ts_ns = int(time.time() * 1e9)  # timestamp en nanosecondes

        lines = []

        # ── 1. Solde global ───────────────────
        total_stake_value = sum(
            bot_instance.my_current_stake(netuid) * float(stats[netuid]['price'])
            for netuid in bot_instance.subnet_grids
            if netuid in stats and float(stats[netuid]['price']) > 0
        )

        tao_usdt = _get_tao_usdt_price()
        total_value_tao = float(balance + total_stake_value)

        lines.append(_build_line(
            measurement = "bagbot_wallet",
            tags        = {"bot": "bagbot"},
            fields      = {
                "balance_tao"        : float(balance),
                "total_stake_value"  : float(total_stake_value),
                "total_value"        : total_value_tao,
                "tao_usdt_price"     : float(tao_usdt),
                "balance_usdt"       : float(balance) * tao_usdt,
                "stake_value_usdt"   : float(total_stake_value) * tao_usdt,
                "total_value_usdt"   : total_value_tao * tao_usdt,
            },
            timestamp_ns = ts_ns
        ))

        # ── 2. Métriques par subnet ───────────
        for netuid in bot_instance.subnet_grids:
            if netuid not in stats:
                continue

            price      = float(stats[netuid]['price'])
            name       = stats[netuid].get('name', f'sn{netuid}')
            stake_amt  = float(bot_instance.my_current_stake(netuid))
            stake_val  = stake_amt * price
            max_alpha  = float(bot_instance.subnet_grids[netuid].get('max_alpha', 0))
            pct_filled = (stake_amt / max_alpha * 100.0) if max_alpha > 0 else 0.0

            buy_threshold  = bot_instance.get_subnet_buy_threshold(netuid)
            sell_threshold = bot_instance.get_subnet_sell_threshold(netuid)
            buy_lower  = bot_instance.subnet_grids[netuid].get('buy_lower',  0.0)
            buy_upper  = bot_instance.subnet_grids[netuid].get('buy_upper',  0.0)
            sell_lower = bot_instance.subnet_grids[netuid].get('sell_lower', 0.0)
            sell_upper = bot_instance.subnet_grids[netuid].get('sell_upper', sell_lower)

            counts     = trade_counts.get(netuid, {'buy': 0, 'sell': 0})

            fields = {
                "price"           : float(price),
                "alpha"           : float(stake_amt),
                "max_alpha"       : float(max_alpha),
                "pct_filled"      : float(pct_filled),
                "stake_value_tao" : float(stake_val),
                "stake_value_usdt": float(stake_val) * tao_usdt,
                "buy_lower"       : float(buy_lower),
                "buy_upper"       : float(buy_upper),
                "sell_lower"      : float(sell_lower),
                "sell_upper"      : float(sell_upper),
                "trades_buy"      : int(counts.get('buy',  0)),
                "trades_sell"     : int(counts.get('sell', 0)),
                "trades_total"    : int(counts.get('buy', 0) + counts.get('sell', 0)),
            }

            # Seuils dynamiques si disponibles
            if buy_threshold is not None:
                fields["curr_buy"] = float(buy_threshold)
            if sell_threshold is not None:
                fields["curr_sell"] = float(sell_threshold)

            # P&L latent
            if stake_amt > 0 and buy_threshold is not None:
                fields["pnl_latent"] = float((price - buy_threshold) * stake_amt)

            lines.append(_build_line(
                measurement  = "bagbot_subnet",
                tags         = {
                    "netuid": str(netuid),
                    "name"  : name.replace(" ", "_") if name else f"sn{netuid}",
                },
                fields       = fields,
                timestamp_ns = ts_ns
            ))

        # ── 3. Wallets externes (lecture seule) ──────────
        if watched_wallets:
            for label, data in watched_wallets.items():
                # data est un dict avec balance_tao, stake_value_tao, total_tao
                if not isinstance(data, dict):
                    continue
                bal_tao   = float(data.get('balance_tao',     0.0))
                stake_tao = float(data.get('stake_value_tao', 0.0))
                total_tao = float(data.get('total_tao',       0.0))
                lines.append(_build_line(
                    measurement  = "bagbot_watched_wallet",
                    tags         = {"label": label.replace(" ", "_")},
                    fields       = {
                        "balance_tao"     : bal_tao,
                        "balance_usdt"    : bal_tao   * tao_usdt,
                        "stake_value_tao" : stake_tao,
                        "stake_value_usdt": stake_tao * tao_usdt,
                        "total_tao"       : total_tao,
                        "total_usdt"      : total_tao * tao_usdt,
                    },
                    timestamp_ns = ts_ns
                ))

        # ── Envoi HTTP vers InfluxDB ──────────
        payload = "\n".join(lines)
        response = requests.post(
            f"{INFLUX_URL}/write",
            params  = {"db": INFLUX_DB, "precision": "ns"},
            data    = payload.encode("utf-8"),
            auth    = (INFLUX_USER, INFLUX_PASSWORD),
            timeout = 5,
            headers = {"Content-Type": "application/octet-stream"},
        )

        if response.status_code == 204:
            logger.debug(f"[InfluxDB] {len(lines)} métriques envoyées")
        else:
            logger.warning(f"[InfluxDB] Réponse inattendue {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        logger.warning("[InfluxDB] Impossible de joindre le serveur — données ignorées pour ce tick")
    except Exception as e:
        logger.error(f"[InfluxDB] Erreur envoi métriques: {e}")
