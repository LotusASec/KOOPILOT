def generate_daily_insights(products, orders, messages):
    insights = []

    for product in products:
        if product["status"] == "Stokta Yok":
            insights.append({
                "title": "Stokta olmayan ürün",
                "text": f"{product['name']} şu anda stokta yok. Yeni üretim veya tedarik planlanmalı.",
                "type": "danger"
            })

        elif product["status"] == "Kritik Stok":
            insights.append({
                "title": "Kritik stok uyarısı",
                "text": f"{product['name']} stoğu kritik seviyede. Şu anda {product['stock']} adet kaldı.",
                "type": "warning"
            })

    unread_message_count = 0

    for message in messages:
        if message["is_read"] is False:
            unread_message_count += 1

    if unread_message_count > 0:
        insights.append({
            "title": "Bekleyen müşteri mesajı",
            "text": f"{unread_message_count} müşteri mesajı cevap bekliyor.",
            "type": "info"
        })

    total_sales = 0

    for order in orders:
        total_sales += order["total"]

    insights.append({
        "title": "Günlük satış özeti",
        "text": f"Bugünkü tahmini satış toplamı {total_sales} TL.",
        "type": "success"
    })

    return insights