from flask import Flask, render_template, request, jsonify
from services.ai_service import generate_ai_answer
from data.mock_data import products, orders, messages
from services.dashboard_service import get_dashboard_summary
from services.insight_service import generate_daily_insights

app = Flask(__name__)


@app.route("/")
def dashboard():
    summary = get_dashboard_summary(products, orders, messages)
    insights = generate_daily_insights(products, orders, messages)

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        products=products,
        orders=orders,
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
        orders=orders
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
    return render_template(
        "messages.html",
        active_page="messages",
        messages=messages
    )


@app.route("/reports")
def reports_page():
    summary = get_dashboard_summary(products, orders, messages)
    insights = generate_daily_insights(products, orders, messages)

    return render_template(
        "reports.html",
        active_page="reports",
        summary=summary,
        insights=insights
    )


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

    answer = generate_ai_answer(question, products, orders, messages)

    return jsonify({
        "answer": answer
    })


if __name__ == "__main__":
    app.run(debug=True)
