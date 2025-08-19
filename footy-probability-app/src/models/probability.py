import math
from typing import List, Optional, Tuple

def _form_score(last5: List[str]) -> float:
    # Weighted recent results: W=3, D=1, L=0 with recency weights
    weights = [3, 2, 1, 1, 1]
    vals = []
    for i, res in enumerate(last5[-5:][::-1]):  # most recent first
        if res == 'W':
            v = 3
        elif res == 'D':
            v = 1
        else:
            v = 0
        vals.append(v * weights[i if i < len(weights) else -1])
    return sum(vals) / (3 * sum(weights))  # normalize to 0..1

def _position_anchor(pos: Optional[int]) -> float:
    if not pos or pos <= 0:
        return 0.5
    # Lower position is better; map 1..20 to 1..0 linearly
    league_size = 20
    pos = min(pos, league_size)
    return 1 - (pos - 1) / (league_size - 1)

def _discipline_penalty(y: float, r: float) -> float:
    # Penalize aggressive teams slightly
    penalty = 0.02 * y + 0.1 * r
    return max(0.0, 1.0 - penalty)

def _injury_penalty(key_starters_out: int) -> float:
    # 11 starters; each missing starter reduces by ~3%
    return max(0.7, 1.0 - 0.03 * key_starters_out)

def _softmax3(a: float, b: float, c: float) -> Tuple[float,float,float]:
    ma = max(a, b, c)
    ea, eb, ec = math.exp(a - ma), math.exp(b - ma), math.exp(c - ma)
    s = ea + eb + ec
    return ea/s, eb/s, ec/s

def predict_probabilities(
    home_form: List[str],
    away_form: List[str],
    home_pos: Optional[int],
    away_pos: Optional[int],
    home_cards: Optional[tuple[float,float]] = None,  # (yellow_per_match, red_per_match)
    away_cards: Optional[tuple[float,float]] = None,
    home_inj_starters: int = 0,
    away_inj_starters: int = 0,
    home_advantage: float = 0.25,  # base home edge on logit scale
) -> dict:
    # Base strength from form + position
    hf = _form_score(home_form)
    af = _form_score(away_form)
    hp = _position_anchor(home_pos)
    ap = _position_anchor(away_pos)

    # Convert to a log-strength
    h_strength = 0.6*hf + 0.4*hp
    a_strength = 0.6*af + 0.4*ap

    # Discipline / injuries
    if home_cards:
        h_strength *= _discipline_penalty(*home_cards)
    if away_cards:
        a_strength *= _discipline_penalty(*away_cards)
    h_strength *= _injury_penalty(home_inj_starters)
    a_strength *= _injury_penalty(away_inj_starters)

    # Translate to scores: home gets baseline advantage
    home_score = h_strength + home_advantage
    away_score = a_strength
    draw_bias = 0.65  # encourage reasonable draw probability

    ph, pd, pa = _softmax3(home_score, draw_bias * (h_strength + a_strength)/2, away_score)

    # Calibrate slight smoothing
    eps = 1e-6
    ph = max(eps, min(0.95, ph))
    pd = max(eps, min(0.7, pd))
    pa = max(eps, min(0.95, pa))

    # Normalize after clipping
    s = ph + pd + pa
    return {"home_win": ph/s, "draw": pd/s, "away_win": pa/s,
            "explain": {
                "home_strength": h_strength, "away_strength": a_strength,
                "inputs": {
                    "home_form": home_form, "away_form": away_form,
                    "home_pos": home_pos, "away_pos": away_pos,
                    "home_cards": home_cards, "away_cards": away_cards,
                    "home_inj_starters": home_inj_starters,
                    "away_inj_starters": away_inj_starters
                }}}
