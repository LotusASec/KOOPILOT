"""
Geçmiş 1 yıllık sipariş verisini Supabase'e yükler.
Sadece bir kez çalıştır: python3 data/seed.py
"""

import random
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from data.db import get_connection

TODAY = date(2026, 5, 13)
HISTORY_DAYS = 365

CUSTOMERS = [
    "Zeynep A.", "Mehmet K.", "Selin G.", "Ayşe Y.", "Can D.",
    "Elif T.", "Burak S.", "Fatma N.", "Emre Ö.", "Deniz P.",
    "Hatice K.", "Murat B.", "Pınar U.", "Onur L.", "Gül M."
]

PRICE_POOL = [45, 75, 85, 120, 150, 180, 200, 240, 270, 300, 350, 395, 420]


def status_for_age(days_old):
    random_val = random.random()
    if days_old == 0:
        if random_val < 0.7:
            return "Hazırlanıyor", "badge-orange"
        return "Kargoya Verildi", "badge-blue"
    if days_old <= 2:
        if random_val < 0.6:
            return "Kargoya Verildi", "badge-blue"
        return "Hazırlanıyor", "badge-orange"
    if days_old <= 6:
        if random_val < 0.7:
            return "Teslim Edildi", "badge-green"
        return "Kargoya Verildi", "badge-blue"
    return "Teslim Edildi", "badge-green"


def main():
    random.seed(42)

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orders")
            count = cur.fetchone()["count"]

        if count > 0:
            print(f"Orders tablosunda zaten {count} satır var, seed atlanıyor.")
            print("Temizleyip yeniden yüklemek için önce: DELETE FROM orders;")
            return

        rows = []
        counter = 1000
        start = TODAY - timedelta(days=HISTORY_DAYS)
        cursor = start

        while cursor <= TODAY:
            days_old = (TODAY - cursor).days
            weekday = cursor.weekday()
            base = 4 if weekday >= 5 else 2
            count = max(0, base + random.randint(-2, 4))

            for _ in range(count):
                counter += 1
                total = random.choice(PRICE_POOL)
                for _ in range(random.randint(0, 2)):
                    total += random.choice(PRICE_POOL)

                status, status_class = status_for_age(days_old)

                rows.append((
                    f"#{counter}",
                    random.choice(CUSTOMERS),
                    total,
                    status,
                    status_class,
                    cursor.isoformat()
                ))

            cursor += timedelta(days=1)

        print(f"{len(rows)} sipariş ekleniyor...")

        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO orders (order_no, customer, total, status, status_class, date)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                rows
            )

        conn.commit()
        print(f"Tamamlandı. {len(rows)} sipariş başarıyla eklendi.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
