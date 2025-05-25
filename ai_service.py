import os
from openai import OpenAI
from db import get_recent_dialogue

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

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

DEEPSEEK_MODEL = 'deepseek-chat'

# --- Инициализация клиента DeepSeek API ---
# Создаем клиент OpenAI, но указываем ему базовый URL DeepSeek.
deepseek_client = None
if DEEPSEEK_API_KEY:
    try:
        deepseek_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        print("DeepSeek API клиент успешно инициализирован.")
    except Exception as e:
        print(f"Ошибка инициализации DeepSeek API клиента: {e}")
        deepseek_client = None # Убедимся, что клиент None в случае ошибки


async def get_ai_response(user_id: int, current_message_text: str) -> str | None:
    """
    Отправляет сообщение пользователя и историю диалога в DeepSeek API
    и возвращает ответ нейросети.
    """
    # Проверяем, инициализирован ли клиент DeepSeek.
    if deepseek_client is None:
        print("AI Service Error: DeepSeek API клиент не инициализирован (возможно, нет API ключа).")
        return "Произошла ошибка конфигурации AI сервиса (нет API ключа DeepSeek)."

    try:
        # Получаем последние 10 сообщений диалога из БД
        dialogue_history = get_recent_dialogue(user_id, limit=1)

        # Формируем список сообщений для DeepSeek API в формате OpenAI-совместимых чат-комплишенов.
        # Этот формат требует список словарей, каждый из которых имеет 'role' и 'content'.
        # Роли: 'system', 'user', 'assistant'.

        # Первое сообщение всегда должно быть системной инструкцией.
        messages = [{"role": "system", "content": AI_PERSONA_CONTEXT}]

        # Добавляем историю диалога.
        # 'user' из нашей БД соответствует 'user' для API.
        # 'bot' из нашей БД соответствует 'assistant' для API.
        for msg_text, timestamp, sender in dialogue_history:
            role = 'user' if sender == 'user' else 'assistant'
            messages.append({"role": role, "content": msg_text})

        # Добавляем текущее сообщение пользователя как последнее сообщение в диалоге.
        messages.append({"role": "user", "content": current_message_text})

        print(f"Отправляем сообщение в DeepSeek для пользователя {user_id} (длина истории: {len(dialogue_history)}).")
        # print(f"Сообщения для API: {messages}") # Можно включить для детальной отладки

        # Выполняем запрос к API DeepSeek.
        response = await deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.7, # Температура генерации (от 0 до 2.0). Выше - креативнее, ниже - точнее.
            max_tokens=500,  # Максимальное количество токенов в ответе от модели.
        )
        print(f"Получен ответ от DeepSeek для пользователя {user_id}.")

        ai_response_text = None
        # Извлекаем текст ответа из структуры ответа DeepSeek (OpenAI-совместимой).
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            ai_response_text = response.choices[0].message.content.strip()
        else:
            print(f"Ответ DeepSeek не содержал текстового контента: {response}")
            return "Не удалось получить текстовый ответ от нейросети. Пожалуйста, попробуйте еще раз."

        return ai_response_text

    except Exception as e:
        print(f"Ошибка при вызове DeepSeek API для пользователя {user_id}: {e}")
        return None