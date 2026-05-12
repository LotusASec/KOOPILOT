def normalize_text(text):
    text = text.lower()

    replacements = {
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def find_product(question, products):
    normalized_question = normalize_text(question)

    for product in products:
        normalized_product_name = normalize_text(product["name"])

        if normalized_product_name in normalized_question:
            return product

        product_words = normalized_product_name.split()

        for word in product_words:
            if len(word) > 3 and word in normalized_question:
                return product

    return None


def find_order(question, orders):
    normalized_question = normalize_text(question)

    for order in orders:
        order_no = order["order_no"]
        order_no_without_hash = order_no.replace("#", "")

        if order_no in question or order_no_without_hash in normalized_question:
            return order

    return None


def generate_stock_answer(product):
    if product["stock"] == 0:
        return f"{product['name']} şu anda stokta yok."

    if product["status"] == "Kritik Stok":
        return f"{product['name']} stokta var ama kritik seviyede. Şu anda {product['stock']} adet kaldı."

    return f"Evet, {product['name']} stokta var. Şu anda {product['stock']} adet mevcut."


def generate_order_answer(order):
    if order["status"] == "Kargoya Verildi":
        return f"{order['order_no']} numaralı sipariş kargoya verildi. Mevcut durum: {order['status']}."

    if order["status"] == "Teslim Edildi":
        return f"{order['order_no']} numaralı sipariş teslim edildi."

    return f"{order['order_no']} numaralı siparişin durumu: {order['status']}."


def generate_critical_stock_answer(products):
    critical_products = []

    for product in products:
        if product["status"] == "Kritik Stok" or product["status"] == "Stokta Yok":
            critical_products.append(f"{product['name']} ({product['stock']} adet)")

    if len(critical_products) == 0:
        return "Şu anda kritik stokta ürün görünmüyor."

    return "Kritik stokta olan ürünler: " + ", ".join(critical_products) + "."


def generate_daily_summary(products, orders, messages):
    total_orders = len(orders)

    unread_messages = 0
    for message in messages:
        if message["is_read"] is False:
            unread_messages += 1

    total_sales = 0
    for order in orders:
        total_sales += order["total"]

    critical_count = 0
    for product in products:
        if product["status"] == "Kritik Stok" or product["status"] == "Stokta Yok":
            critical_count += 1

    return (
        f"Bugün {total_orders} sipariş var. "
        f"{unread_messages} bekleyen mesaj bulunuyor. "
        f"{critical_count} ürün kritik stokta veya stokta yok. "
        f"Toplam tahmini satış {total_sales} TL."
    )


def generate_ai_answer(question, products, orders, messages):
    normalized_question = normalize_text(question)

    product = find_product(question, products)

    if product is not None:
        return generate_stock_answer(product)

    order = find_order(question, orders)

    if order is not None:
        return generate_order_answer(order)

    if "kritik" in normalized_question or "az kalan" in normalized_question or "stokta az" in normalized_question:
        return generate_critical_stock_answer(products)

    if "bugun" in normalized_question or "ozet" in normalized_question or "durum" in normalized_question:
        return generate_daily_summary(products, orders, messages)

    if "siparis" in normalized_question and "kac" in normalized_question:
        return f"Bugün toplam {len(orders)} sipariş var."

    if "mesaj" in normalized_question:
        unread_messages = 0

        for message in messages:
            if message["is_read"] is False:
                unread_messages += 1

        return f"Şu anda {unread_messages} bekleyen müşteri mesajı var."

    if "satis" in normalized_question or "gelir" in normalized_question:
        total_sales = 0

        for order in orders:
            total_sales += order["total"]

        return f"Bugünkü tahmini satış toplamı {total_sales} TL."

    return (
        "Bu soruyu cevaplamak için yeterli veri bulamadım. "
        "Ürün adı, sipariş numarası veya stok durumu ile tekrar sorabilirsiniz."
    )