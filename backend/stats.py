import json
from datetime import datetime
from pathlib import Path
from config import DATA_DIR

STATS_PATH = DATA_DIR / "stats.json"


def load_max():
    """Завантажити збережений max_people. Скидається, якщо дата змінилась."""
    if not STATS_PATH.exists():
        return 0
    try:
        with open(STATS_PATH, "r") as f:
            data = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        if data.get("date") == today:
            return data.get("max_people", 0)
    except Exception:
        pass
    return 0


def save_max(max_people):
    """Зберегти max_people з сьогоднішньою датою."""
    today = datetime.now().strftime("%Y-%m-%d")
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_PATH, "w") as f:
        json.dump({"max_people": max_people, "date": today}, f)
