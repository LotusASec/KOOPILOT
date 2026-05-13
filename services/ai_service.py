from services.gemini_service import generate_answer as gemini_generate_answer


CONNECTION_ERROR_MESSAGE = (
    "Bağlantı hatası: AI asistanına şu an ulaşılamıyor. "
    "Lütfen birkaç saniye sonra tekrar deneyin."
)


def generate_ai_answer(question, products, orders, messages):
    answer, _ = generate_ai_answer_with_source(question, products, orders, messages)
    return answer


def generate_ai_answer_with_source(question, products, orders, messages):
    answer = gemini_generate_answer(question, products, orders, messages)

    if answer:
        return answer, "gemini"

    return CONNECTION_ERROR_MESSAGE, "error"
