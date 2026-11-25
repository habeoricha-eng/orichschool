"""Répétition espacée : algorithme SM-2 (SuperMemo 2)."""
from datetime import date, timedelta

# Boutons de l'interface -> qualité SM-2 (0 à 5)
GRADES = {"again": 1, "hard": 3, "good": 4, "easy": 5}

def review(ease: float, interval: int, reps: int, quality: int):
    """Retourne (ease, interval, reps, prochaine_date)."""
    if quality < 3:                      # échec : on repart du début
        reps, interval = 0, 1
    else:
        reps += 1
        interval = 1 if reps == 1 else 6 if reps == 2 else round(interval * ease)
    ease = max(1.3, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return ease, interval, reps, (date.today() + timedelta(days=interval)).isoformat()