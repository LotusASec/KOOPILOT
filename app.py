from datetime import datetime, date, timedelta
from calendar import monthrange
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify, abort
from services.ai_service import generate_ai_answer_with_source
from services.gemini_service import get_status as get_gemini_status
from data.mock_data import (
    products,
    orders,
    TODAY,
    get_todays_orders,
    get_recent_orders,
    get_inbox,
    get_conversation,
    append_message,
    mark_read,
)
from services.dashboard_service import get_dashboard_summary
from services.insight_service import generate_daily_insights

app = Flask(__name__)


@app.route("/")
def dashboard():
    messages = get_inbox()
    todays_orders = get_todays_orders()
    recent_orders = get_recent_orders(5)

    summary = get_dashboard_summary(products, todays_orders, messages)
    insights = generate_daily_insights(products, todays_orders, messages)

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        products=products,
        orders=recent_orders,
        messages=messages,
        summary=summary,
        insights=insights
    )


@app.route("/products")
def products_page():
    return render_template(
        "products.html",
        active_page="products",
        products=products
    )


@app.route("/orders")
def orders_page():
    return render_template(
        "orders.html",
        active_page="orders",
        orders=orders[:50]
    )


@app.route("/stock")
def stock_page():
    critical_count = 0
    out_of_stock_count = 0
    total_units = 0

    for product in products:
        total_units += product["stock"]

        if product["status"] == "Kritik Stok":
            critical_count += 1

        if product["status"] == "Stokta Yok":
            out_of_stock_count += 1

    return render_template(
        "stock.html",
        active_page="stock",
        products=products,
        critical_count=critical_count,
        out_of_stock_count=out_of_stock_count,
        total_units=total_units
    )


@app.route("/messages")
def messages_page():
    inbox = get_inbox()

    return render_template(
        "messages.html",
        active_page="messages",
        inbox=inbox
    )


@app.route("/messages/<int:conversation_id>")
def message_thread(conversation_id):
    conversation = get_conversation(conversation_id)

    if conversation is None:
        abort(404)

    mark_read(conversation_id)

    return render_template(
        "dm.html",
        active_page="messages",
        conversation=conversation
    )


@app.route("/api/messages/<int:conversation_id>/send", methods=["POST"])
def send_message(conversation_id):
    data = request.get_json()
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Mesaj boş olamaz"}), 400

    time = datetime.now().strftime("%H:%M")

    conversation = append_message(conversation_id, "owner", text, time)

    if conversation is None:
        abort(404)

    return jsonify({
        "sender": "owner",
        "text": text,
        "time": time
    })


@app.route("/reports")
def reports_page():
    available_years = sorted({int(o["date"][:4]) for o in orders}, reverse=True)

    return render_template(
        "reports.html",
        active_page="reports",
        available_years=available_years,
        default_year=TODAY.year,
        default_month=TODAY.month
    )


def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _iso_week_of_month(d):
    first_day = d.replace(day=1)
    offset = first_day.weekday()
    return ((d.day - 1 + offset) // 7) + 1


@app.route("/api/reports/data")
def reports_data():
    granularity = (request.args.get("granularity") or "daily").lower()
    year = _parse_int(request.args.get("year"), TODAY.year)
    month = _parse_int(request.args.get("month"), TODAY.month)

    if granularity not in ("daily", "weekly", "monthly"):
        granularity = "daily"

    if granularity == "monthly":
        labels = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                  "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        order_buckets = [0] * 12
        revenue_buckets = [0] * 12

        for order in orders:
            order_year = int(order["date"][:4])
            if order_year != year:
                continue
            order_month = int(order["date"][5:7])
            order_buckets[order_month - 1] += 1
            revenue_buckets[order_month - 1] += order["total"]

        return jsonify({
            "granularity": granularity,
            "year": year,
            "month": month,
            "labels": labels,
            "orders": order_buckets,
            "revenue": revenue_buckets
        })

    if granularity == "weekly":
        days_in_month = monthrange(year, month)[1]
        first_day = date(year, month, 1)
        offset = first_day.weekday()
        week_count = ((days_in_month + offset - 1) // 7) + 1

        labels = [f"Hafta {i + 1}" for i in range(week_count)]
        order_buckets = [0] * week_count
        revenue_buckets = [0] * week_count

        for order in orders:
            order_date_str = order["date"]
            if int(order_date_str[:4]) != year or int(order_date_str[5:7]) != month:
                continue
            order_day = int(order_date_str[8:10])
            week_index = ((order_day - 1 + offset) // 7)
            order_buckets[week_index] += 1
            revenue_buckets[week_index] += order["total"]

        return jsonify({
            "granularity": granularity,
            "year": year,
            "month": month,
            "labels": labels,
            "orders": order_buckets,
            "revenue": revenue_buckets
        })

    days_in_month = monthrange(year, month)[1]
    labels = [str(i) for i in range(1, days_in_month + 1)]
    order_buckets = [0] * days_in_month
    revenue_buckets = [0] * days_in_month

    for order in orders:
        order_date_str = order["date"]
        if int(order_date_str[:4]) != year or int(order_date_str[5:7]) != month:
            continue
        order_day = int(order_date_str[8:10])
        order_buckets[order_day - 1] += 1
        revenue_buckets[order_day - 1] += order["total"]

    return jsonify({
        "granularity": granularity,
        "year": year,
        "month": month,
        "labels": labels,
        "orders": order_buckets,
        "revenue": revenue_buckets
    })


@app.route("/settings")
def settings_page():
    return render_template(
        "settings.html",
        active_page="settings"
    )


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    data = request.get_json()
    question = data.get("question", "")

    messages = get_inbox()
    answer, source = generate_ai_answer_with_source(question, products, orders, messages)

    return jsonify({
        "answer": answer,
        "source": source
    })


@app.route("/api/ai/status")
def ai_status():
    return jsonify(get_gemini_status())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
