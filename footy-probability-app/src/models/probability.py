import math

def predict_probabilities(home_stats, away_stats, h2h=None, injuries=None, cards=None, top_scorers=None):
    """Simple probability model combining team stats, head-to-head, injuries, and cards."""

    # --- Base factors ---
    home_strength = home_stats.get("avg_goals_scored", 1.0) - home_stats.get("avg_goals_conceded", 1.0)
    away_strength = away_stats.get("avg_goals_scored", 1.0) - away_stats.get("avg_goals_conceded", 1.0)

    score = home_strength - away_strength

    # --- H2H factor ---
    if h2h:
        score += (h2h.get("home_wins", 0) - h2h.get("away_wins", 0)) * 0.1

    # --- Injuries penalty ---
    if injuries:
        home_inj = sum(1 for inj in injuries if inj["team"] == home_stats.get("team", ""))
        away_inj = sum(1 for inj in injuries if inj["team"] == away_stats.get("team", ""))
        score += (away_inj - home_inj) * 0.05

    # --- Cards / discipline ---
    if cards:
        home_cards = sum(c.get("cards", 0) for c in cards if c["team"] == home_stats.get("team", ""))
        away_cards = sum(c.get("cards", 0) for c in cards if c["team"] == away_stats.get("team", ""))
        score += (away_cards - home_cards) * 0.02

    # --- Top scorer bonus ---
    if top_scorers:
        for s in top_scorers:
            if s["team"] == home_stats.get("team", ""):
                score += 0.05
            elif s["team"] == away_stats.get("team", ""):
                score -= 0.05

    # --- Convert to probabilities (softmax) ---
    home_prob = 1 / (1 + math.exp(-score))
    away_prob = 1 - home_prob
    draw_prob = 0.25  # fixed draw baseline

    # Normalize to 1
    total = home_prob + away_prob + draw_prob
    return {
        "Home Win": round(home_prob / total, 2),
        "Draw": round(draw_prob / total, 2),
        "Away Win": round(away_prob / total, 2),
    }
