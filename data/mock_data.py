import random
from datetime import date, timedelta

products = [
    {
        "name": "Lavanta Kesesi",
        "stock": 8,
        "price": 45,
        "status": "Stokta Var",
        "status_class": "badge-green"
    },
    {
        "name": "El Yapımı Sabun",
        "stock": 3,
        "price": 75,
        "status": "Kritik Stok",
        "status_class": "badge-orange"
    },
    {
        "name": "Örgü Çanta",
        "stock": 15,
        "price": 350,
        "status": "Stokta Var",
        "status_class": "badge-green"
    },
    {
        "name": "Ev Reçeli",
        "stock": 0,
        "price": 85,
        "status": "Stokta Yok",
        "status_class": "badge-red"
    },
    {
        "name": "Seramik Kase",
        "stock": 5,
        "price": 120,
        "status": "Kritik Stok",
        "status_class": "badge-orange"
    }
]


TODAY = date(2026, 5, 13)
_HISTORY_DAYS = 365

_CUSTOMERS = [
    "Zeynep A.", "Mehmet K.", "Selin G.", "Ayşe Y.", "Can D.",
    "Elif T.", "Burak S.", "Fatma N.", "Emre Ö.", "Deniz P.",
    "Hatice K.", "Murat B.", "Pınar U.", "Onur L.", "Gül M."
]

_PRICE_POOL = [45, 75, 85, 120, 150, 180, 200, 240, 270, 300, 350, 395, 420]


def _status_for_age(days_old):
    if days_old == 0:
        return random.choice([
            ("Hazırlanıyor", "badge-orange"),
            ("Hazırlanıyor", "badge-orange"),
            ("Kargoya Verildi", "badge-blue"),
        ])
    if days_old <= 2:
        return random.choice([
            ("Kargoya Verildi", "badge-blue"),
            ("Hazırlanıyor", "badge-orange"),
        ])
    if days_old <= 6:
        return random.choice([
            ("Kargoya Verildi", "badge-blue"),
            ("Teslim Edildi", "badge-green"),
            ("Teslim Edildi", "badge-green"),
        ])
    return ("Teslim Edildi", "badge-green")


def _generate_orders():
    random.seed(42)

    orders_list = []
    counter = 1000
    start = TODAY - timedelta(days=_HISTORY_DAYS)
    cursor = start

    while cursor <= TODAY:
        days_old = (TODAY - cursor).days

        weekday = cursor.weekday()
        if weekday >= 5:
            base = 4
        else:
            base = 2

        count = max(0, base + random.randint(-2, 4))

        for _ in range(count):
            counter += 1
            total_amount = random.choice(_PRICE_POOL)

            extra_items = random.randint(0, 2)
            for _ in range(extra_items):
                total_amount += random.choice(_PRICE_POOL)

            status, status_class = _status_for_age(days_old)

            orders_list.append({
                "order_no": f"#{counter}",
                "customer": random.choice(_CUSTOMERS),
                "total": total_amount,
                "status": status,
                "status_class": status_class,
                "date": cursor.isoformat()
            })

        cursor += timedelta(days=1)

    orders_list.sort(key=lambda o: (o["date"], o["order_no"]), reverse=True)
    return orders_list


orders = _generate_orders()


def get_todays_orders():
    today_iso = TODAY.isoformat()
    return [o for o in orders if o["date"] == today_iso]


def get_recent_orders(limit=5):
    return orders[:limit]


conversations = {
    1: {
        "id": 1,
        "customer": "Ayşe Y.",
        "unread": True,
        "messages": [
            {"sender": "customer", "text": "Lavanta kesesi stokta var mı?", "time": "10:24"}
        ]
    },
    2: {
        "id": 2,
        "customer": "Mehmet K.",
        "unread": True,
        "messages": [
            {"sender": "customer", "text": "Sipariş #1023 nerede?", "time": "11:02"}
        ]
    }
}


def get_inbox():
    inbox = []

    for conv in conversations.values():
        last_message = conv["messages"][-1]

        inbox.append({
            "id": conv["id"],
            "customer": conv["customer"],
            "text": last_message["text"],
            "time": last_message["time"],
            "is_read": not conv["unread"]
        })

    return inbox


def get_conversation(conversation_id):
    return conversations.get(conversation_id)


def append_message(conversation_id, sender, text, time):
    conversation = conversations.get(conversation_id)

    if conversation is None:
        return None

    conversation["messages"].append({
        "sender": sender,
        "text": text,
        "time": time
    })

    if sender == "owner":
        conversation["unread"] = False

    return conversation


def mark_read(conversation_id):
    conversation = conversations.get(conversation_id)

    if conversation is None:
        return

    conversation["unread"] = False
