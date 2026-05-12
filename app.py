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
        products=products,
        orders=orders,
        messages=messages,
        summary=summary,
        insights=insights
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