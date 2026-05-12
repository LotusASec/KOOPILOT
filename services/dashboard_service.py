def get_dashboard_summary(products, orders, messages):
    today_orders_count = len(orders)

    critical_stock_count = 0

    for product in products:
        if product["status"] == "Kritik Stok" or product["status"] == "Stokta Yok":
            critical_stock_count += 1

    unread_message_count = 0

    for message in messages:
        if message["is_read"] is False:
            unread_message_count += 1

    total_sales = 0

    for order in orders:
        total_sales += order["total"]

    return {
        "today_orders_count": today_orders_count,
        "critical_stock_count": critical_stock_count,
        "unread_message_count": unread_message_count,
        "total_sales": total_sales
    }