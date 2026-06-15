import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
LOG_FILE = DATA_DIR / "analytics.csv"

HEADERS = ["date", "time_slot", "people", "level"]

SLOTS = [
    "11:30", "11:45", "12:00", "12:15", "12:30",
    "12:45", "13:00", "13:15", "13:30", "13:45", "14:00"
]


def _get_time_slot(dt: datetime) -> str:
    """Округлити час до 15-хвилинного слоту."""
    hour = dt.hour
    minute = (dt.minute // 15) * 15
    return f"{hour:02d}:{minute:02d}"


def log_state(people: int, level: str):
    """Записати точку даних у CSV."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    slot = _get_time_slot(now)
    row = [
        now.strftime("%Y-%m-%d"),
        slot,
        people,
        level
    ]
    file_exists = LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(HEADERS)
        writer.writerow(row)


def get_report(days: int = 7):
    """Повернути агреговану статистику по 15-хвилинних слотах (11:30–14:00)."""
    if not LOG_FILE.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    stats = defaultdict(lambda: {"total_people": 0, "count": 0, "full_count": 0})

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row_date = datetime.strptime(row["date"], "%Y-%m-%d")
            except ValueError:
                continue
            if row_date < cutoff:
                continue
            slot = row["time_slot"]
            if slot not in SLOTS:
                continue
            people = int(row["people"])
            level = row["level"]
            stats[slot]["total_people"] += people
            stats[slot]["count"] += 1
            if level == "full":
                stats[slot]["full_count"] += 1

    report = []
    for slot in SLOTS:
        s = stats.get(slot, {"total_people": 0, "count": 0, "full_count": 0})
        count = s["count"]
        avg = s["total_people"] / count if count > 0 else 0
        pct_full = (s["full_count"] / count * 100) if count > 0 else 0

        if count == 0:
            recommend = "Немає даних"
        elif avg < 2 and pct_full < 10:
            recommend = "Вільно, ідеальний час"
        elif avg < 4 and pct_full < 30:
            recommend = "Помірно"
        elif pct_full > 40:
            recommend = "Уникайте — завжди повна!"
        else:
            recommend = "Завантажено"

        report.append({
            "slot": slot,
            "avg_people": avg,
            "count": count,
            "pct_full": pct_full,
            "recommend": recommend
        })

    return report
