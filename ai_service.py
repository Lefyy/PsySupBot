import google.generativeai as genai
import os
from db import get_recent_dialogue

# --- Контекст / Системные инструкции для нейросети ---
# Этот текст не виден пользователю, но определяет поведение бота.
AI_PERSONA_CONTEXT = """
Ты дружелюбный и поддерживающий ИИ-помощник для студентов.
Твоя главная цель – выслушать, понять и предложить эмоциональную и информационную поддержку в их академических и личных переживаниях, связанных с учебой в ВУЗе.
Будь эмпатичным, проявляй терпение и понимание.
Используй поддерживающий и ободряющий тон.
Избегай:
- Давать конкретные директивные советы ("Тебе нужно сделать X"). Вместо этого предлагай варианты или задавай наводящие вопросы ("Возможно, стоит рассмотреть вариант X?").
- Давать медицинские, психиатрические, юридические или финансовые консультации.
- Делать диагностические заключения.
- Использовать сарказм, грубость, критику.
- Отвечать односложно. Стремись к развернутым и осмысленным ответам.
Ответы должны быть на русском языке.
Если тема выходит за рамки твоей компетенции (например, срочный кризис, медицинский вопрос), вежливо перенаправь пользователя к специалистам или другим ресурсам.
"""

# --- Получение API ключа ---
# Ключ лучше хранить не в коде, а в переменной окружения, например GEMINI_API_KEY
# Перед запуском бота нужно установить эту переменную в системе:
# export GEMINI_API_KEY='ТВОЙ_API_КЛЮЧ' (для Linux/macOS)
# set GEMINI_API_KEY=ТВОЙ_API_КЛЮЧ (для Windows)
# Или использовать файлы .env и библиотеки вроде python-dotenv
API_KEY = os.getenv("GEMINI_API")

if not API_KEY:
    print("Ошибка: Переменная окружения GEMINI_API не установлена!")
    # В реальном приложении тут нужно более серьезная обработка или выход
    # Для учебы можно пока захардкодить ключ здесь НА ВРЕМЯ РАЗРАБОТКИ,
    # но НИКОГДА не оставляй его так в готовом коде!
    # API_KEY = "ТВОЙ_СЕКРЕТНЫЙ_КЛЮЧ_GEMINI_ДЛЯ_РАЗРАБОТКИ"
    pass # Оставляем pass, чтобы не упасть сразу, но функция ниже вернет ошибку


# Настройка Gemini API
genai.configure(api_key=API_KEY)

# Можно выбрать модель, например 'gemini-1.5-flash-latest' или 'gemini-1.5-pro-latest'
# Проверь актуальные названия моделей в документации Google
GEMINI_MODEL = 'gemini-2.5-flash-preview-04-17'


async def get_ai_response(user_id: int, current_message_text: str) -> str | None:
    """
    Отправляет сообщение пользователя и историю диалога в Gemini API
    и возвращает ответ нейросети.
    """
    if not API_KEY:
        print("AI Service Error: API Key is not set.")
        return "Произошла ошибка конфигурации AI сервиса (нет API ключа)." # Сообщение об ошибке для пользователя

    try:
        dialogue_history = get_recent_dialogue(user_id, limit=10)

        # --- 2. Формируем промпт / запрос для Gemini ---
        # Формат запроса зависит от выбранной модели и библиотеки.
        # Для моделей Gemini и библиотеки google-generativeai удобно использовать формат чата.
        # История передается как список сообщений с ролями 'user' и 'model'.
        # Системные инструкции передаются отдельно или включаются в первое сообщение.

        chat_messages = []
        for msg_text, timestamp, sender in dialogue_history:
             role = 'user' if sender == 'user' else 'model' # Сопоставляем sender из БД с ролью для API
             chat_messages.append({'role': role, 'parts': [msg_text]})

        # Если история нечетная (последнее сообщение от пользователя),
        # добавим его как последний элемент истории, а current_message_text не добавляем пока.
        # Если история четная или пустая, первое сообщение пользователя будет current_message_text

        history_for_api = []

        for msg_text, timestamp, sender in dialogue_history:
            api_role = 'user' if sender == 'user' else 'model'
            history_for_api.append({'role': api_role, 'parts': [{'text': msg_text}]})

        model = genai.GenerativeModel(model_name=GEMINI_MODEL, system_instruction=AI_PERSONA_CONTEXT)
        chat = model.start_chat(history=history_for_api)

        print(f"Sending message to Gemini for user {user_id}: {current_message_text}")
        response = await chat.send_message(current_message_text)
        print(f"Received response from Gemini for user {user_id}.")

        ai_response_text = None
        try:
            # Ответы могут содержать несколько частей. Берем текст.
            ai_response_text = response.text
        except ValueError:
             # Если ответ пустой или не содержит текст (например, только Function Call или Blocked)
             print(f"Gemini response did not contain text parts: {response}")


        return ai_response_text

    except Exception as e:
        print(f"Ошибка при вызове Gemini API для пользователя {user_id}: {e}")
        return None