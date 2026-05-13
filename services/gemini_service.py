import os
import sys

_model = None
_init_error = None
_last_call_error = None


def _log(message):
    print(f"[GEMINI] {message}", file=sys.stderr, flush=True)


def _get_model():
    global _model, _init_error

    if _model is not None:
        return _model

    if _init_error is not None:
        return None

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        _init_error = "no_api_key"
        return None

    try:
        import google.generativeai as genai
    except ImportError:
        _init_error = "sdk_not_installed"
        return None

    try:
        genai.configure(api_key=api_key)
        requested = os.environ.get("GEMINI_MODEL", "").strip()
        resolved = _resolve_model_name(genai, requested)

        if resolved is None:
            _init_error = "no_supported_model_found"
            _log("Hiçbir generateContent destekli model bulunamadı.")
            return None

        _model = genai.GenerativeModel(resolved)
        os.environ["GEMINI_MODEL"] = resolved
        _log(f"Model initialized: {resolved}")
        return _model
    except Exception as exc:
        _init_error = f"init_failed: {exc}"
        _log(f"Init failed: {exc}")
        return None


def _resolve_model_name(genai, requested):
    try:
        models = list(genai.list_models())
    except Exception as exc:
        _log(f"list_models hatası, istenen model ile devam: {exc}")
        return requested or "gemini-2.5-flash"

    usable = []
    for m in models:
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            name = m.name.split("/")[-1] if "/" in m.name else m.name
            usable.append(name)

    _log(f"Kullanılabilir modeller: {', '.join(usable) if usable else '(yok)'}")

    if requested:
        for name in usable:
            if name == requested or name.endswith("/" + requested):
                return name
        _log(f"İstenen '{requested}' bulunamadı, otomatik seçim yapılıyor.")

    preferred_order = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-pro",
    ]

    for pref in preferred_order:
        for name in usable:
            if name == pref:
                return name

    flash_candidates = [n for n in usable if "flash" in n]
    if flash_candidates:
        return flash_candidates[0]

    return usable[0] if usable else None


def is_available():
    return _get_model() is not None


def get_status():
    model = _get_model()

    if model is not None:
        status = {
            "configured": True,
            "model": os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            "reason": "ok"
        }
        if _last_call_error:
            status["last_call_error"] = _last_call_error
        return status

    reason_map = {
        "no_api_key": ".env içinde GEMINI_API_KEY boş veya yok",
        "sdk_not_installed": "google-generativeai paketi kurulu değil (pip install -r requirements.txt)",
    }

    error = _init_error or "unknown"
    reason = reason_map.get(error, error)

    return {
        "configured": False,
        "model": os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
        "reason": reason
    }


def _build_business_context(products, orders, messages):
    lines = []

    lines.append("ÜRÜNLER:")
    for product in products:
        lines.append(
            f"- {product['name']}: {product['stock']} adet stokta, "
            f"fiyat {product['price']} TL, durum: {product['status']}"
        )

    lines.append("")
    lines.append("SİPARİŞLER:")
    for order in orders[:20]:
        lines.append(
            f"- {order['order_no']} | {order['customer']} | {order['total']} TL | {order['status']}"
        )

    lines.append("")
    lines.append("BEKLEYEN MÜŞTERİ MESAJLARI:")
    unread = [m for m in messages if not m.get("is_read", False)]
    if unread:
        for message in unread:
            lines.append(f"- {message['customer']}: {message['text']}")
    else:
        lines.append("- (Bekleyen mesaj yok)")

    return "\n".join(lines)


def _extract_text(response):
    candidates = getattr(response, "candidates", None) or []

    if not candidates:
        prompt_feedback = getattr(response, "prompt_feedback", None)
        block_reason = getattr(prompt_feedback, "block_reason", None) if prompt_feedback else None
        return None, f"no_candidates (block_reason={block_reason})"

    candidate = candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)

    content = getattr(candidate, "content", None)
    parts = getattr(content, "parts", None) if content else None

    if not parts:
        return None, f"no_parts (finish_reason={finish_reason})"

    text_chunks = []
    for part in parts:
        part_text = getattr(part, "text", None)
        if part_text:
            text_chunks.append(part_text)

    full = "".join(text_chunks).strip()

    if not full:
        return None, f"empty_text (finish_reason={finish_reason})"

    return full, None


def generate_answer(question, products, orders, messages):
    global _last_call_error

    model = _get_model()

    if model is None:
        return None

    context = _build_business_context(products, orders, messages)

    prompt = (
        "Sen KOOPILOT adlı bir operasyon panelinin AI asistanısın. "
        "Küçük bir Türk işletmesine sadece kendi işletme verisi hakkında yardım ediyorsun.\n\n"
        "KESİN KURALLAR:\n"
        "1) SADECE şu konularda cevap ver: ürünler, stok, fiyatlar, siparişler, "
        "müşteri mesajları, satış/ciro özetleri ve genel işletme operasyonları.\n"
        "2) Hava durumu, haberler, spor, genel kültür, kişisel sorular, hesaplama, "
        "kodlama, çeviri veya başka HİÇBİR konuya cevap verme.\n"
        "3) Konu dışı bir soru gelirse SADECE şu cümleyi yaz (başka hiçbir şey ekleme): "
        "\"Üzgünüm, sadece işletmenizdeki ürün, stok, sipariş ve müşteri mesajları "
        "hakkında yardımcı olabilirim.\"\n"
        "4) Aşağıdaki işletme verisinde olmayan bilgileri ASLA uydurma. "
        "Bilmiyorsan dürüstçe söyle.\n"
        "5) Cevap kısa olsun, 1-3 cümle, samimi Türkçe.\n\n"
        f"İŞLETME VERİSİ:\n{context}\n\n"
        f"KULLANICININ SORUSU: {question}\n\n"
        "CEVAP:"
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 1024,
            },
        )
    except Exception as exc:
        _last_call_error = f"{type(exc).__name__}: {exc}"
        _log(f"generate_content exception: {_last_call_error}")
        return None

    text, error = _extract_text(response)

    if text is None:
        _last_call_error = error
        _log(f"extract failed: {error}")
        return None

    _last_call_error = None
    _log(f"OK ({len(text)} chars)")
    return text
