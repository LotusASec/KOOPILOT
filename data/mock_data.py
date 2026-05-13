from data.db import query, execute


def _row(r):
    d = dict(r)
    if "date" in d and d["date"] is not None and not isinstance(d["date"], str):
        d["date"] = d["date"].isoformat()
    if "total" in d and d["total"] is not None:
        d["total"] = float(d["total"])
    if "price" in d and d["price"] is not None:
        d["price"] = float(d["price"])
    return d


def get_products():
    rows = query("SELECT * FROM products ORDER BY id")
    return [_row(r) for r in rows]


def get_orders(limit=None):
    sql = "SELECT * FROM orders ORDER BY date DESC, id DESC"
    if limit:
        sql += f" LIMIT {limit}"
    rows = query(sql)
    return [_row(r) for r in rows]


def get_todays_orders():
    rows = query(
        "SELECT * FROM orders WHERE date = CURRENT_DATE ORDER BY id DESC"
    )
    return [_row(r) for r in rows]


def get_recent_orders(limit=5):
    return get_orders(limit=limit)


def get_orders_for_year(year):
    rows = query(
        "SELECT * FROM orders WHERE EXTRACT(YEAR FROM date) = %s ORDER BY date, id",
        (year,)
    )
    return [_row(r) for r in rows]


def get_available_years():
    rows = query(
        "SELECT DISTINCT EXTRACT(YEAR FROM date)::int AS yr FROM orders ORDER BY yr DESC"
    )
    return [r["yr"] for r in rows]


def get_inbox():
    rows = query("""
        SELECT DISTINCT ON (c.id)
            c.id,
            c.customer,
            c.unread,
            m.text,
            m.time
        FROM conversations c
        JOIN messages m ON m.conversation_id = c.id
        ORDER BY c.id, m.created_at DESC
    """)

    return [
        {
            "id": r["id"],
            "customer": r["customer"],
            "text": r["text"],
            "time": r["time"],
            "is_read": not r["unread"],
        }
        for r in rows
    ]


def get_conversation(conversation_id):
    rows = query(
        "SELECT * FROM conversations WHERE id = %s",
        (conversation_id,)
    )

    if not rows:
        return None

    conv = dict(rows[0])

    msg_rows = query(
        "SELECT * FROM messages WHERE conversation_id = %s ORDER BY created_at",
        (conversation_id,)
    )

    conv["messages"] = [dict(m) for m in msg_rows]
    return conv


def append_message(conversation_id, sender, text, time):
    execute(
        "INSERT INTO messages (conversation_id, sender, text, time) VALUES (%s, %s, %s, %s)",
        (conversation_id, sender, text, time)
    )

    if sender == "owner":
        execute(
            "UPDATE conversations SET unread = false WHERE id = %s",
            (conversation_id,)
        )

    return get_conversation(conversation_id)


def mark_read(conversation_id):
    execute(
        "UPDATE conversations SET unread = false WHERE id = %s",
        (conversation_id,)
    )
