import sqlite3
from datetime import datetime, timedelta

DATABASE_NAME = 'psych_support_bot.db'
FREE_TRIAL_DAYS = 2
SUBSCRIPTION_DAYS_PER_PAYMENT = 30

def init_db():
    """
    Инициализирует базу данных: создает файл и таблицы, если они не существуют.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Создаем таблицу users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, -- Telegram User ID
            full_name TEXT,
            username TEXT,
            join_date TEXT, -- Храним дату как текст в формате ISO8601
            subscription_expiry_date TEXT
        )
    ''')

    # Создаем таблицу dialogues
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dialogues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_text TEXT,
            timestamp TEXT, -- Храним дату как текст в формате ISO8601
            sender TEXT, -- 'user' или 'bot'
            FOREIGN KEY (user_id) REFERENCES users(id) -- Связываем с таблицей users
        )
    ''')

    # Создаем таблицу payments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER, -- Сумма в минимальных единицах
            currency TEXT,
            timestamp TEXT, -- Храним дату как текст в формате ISO8601
            status TEXT,
            telegram_charge_id TEXT,
            provider_charge_id TEXT,
            invoice_payload TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) -- Связываем с таблицей users
        )
    ''')

    conn.commit()
    conn.close()
    print("База данных инициализирована.")

def add_user(user_id: int, full_name: str, username: str | None):
    """
    Добавляет нового пользователя в базу данных, если его там нет.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            now = datetime.now()
            now_iso = now.isoformat()
            expiry_date = now + timedelta(days=FREE_TRIAL_DAYS)
            expiry_date_iso = expiry_date.isoformat()
            cursor.execute("INSERT INTO users (id, full_name, username, join_date, subscription_expiry_date) VALUES (?, ?, ?, ?, ?)",
                           (user_id, full_name, username, now_iso, expiry_date_iso))
            conn.commit()
            print(f"Добавлен новый пользователь: {user_id}")
        else:
            print(f"Пользователь {user_id} уже существует.")

    except sqlite3.Error as e:
        print(f"Ошибка при добавлении пользователя: {e}")
    finally:
        conn.close()

def get_user(user_id: int):
    """
    Получает данные пользователя по его ID.
    Возвращает кортеж с данными или None, если пользователь не найден.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, full_name, username, join_date, subscription_expiry_date FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        return user_data
    except sqlite3.Error as e:
        print(f"Ошибка при получении пользователя: {e}")
        return None
    finally:
        conn.close()

def update_user_name(user_id: int, new_name: str):
    """
    Обновляет full_name пользователя в базе данных.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (new_name, user_id))
        conn.commit()
        print(f"Имя пользователя {user_id} обновлено на '{new_name}'.")
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении имени пользователя: {e}")
        return False
    finally:
        conn.close()

def get_recent_dialogue(user_id: int, limit: int = 20) -> list[tuple]:
    """
    Получает последние 'limit' сообщений диалога для пользователя из таблицы dialogues.
    Возвращает список кортежей (message_text, timestamp, sender), отсортированных по времени.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT message_text, timestamp, sender
            FROM dialogues
            WHERE user_id = ?
            ORDER BY timestamp DESC -- Получаем сначала самые новые
            LIMIT ? -- Ограничиваем количество
        """, (user_id, limit))
        dialogue_history = cursor.fetchall()
        dialogue_history.reverse() # Разворачиваем, чтобы получить в хронологическом порядке
        return dialogue_history
    except sqlite3.Error as e:
        print(f"Ошибка при получении истории диалога для пользователя {user_id}: {e}")
        return []
    finally:
        conn.close()

def add_dialogue_message(user_id: int, message_text: str, sender: str):
    """
    Добавляет сообщение диалога в базу данных.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        timestamp = datetime.now().isoformat()
        cursor.execute("INSERT INTO dialogues (user_id, message_text, timestamp, sender) VALUES (?, ?, ?, ?)",
                       (user_id, message_text, timestamp, sender))
        conn.commit()
        print(f"Добавлено сообщение от {sender} для пользователя {user_id}")
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении сообщения диалога: {e}")
    finally:
        conn.close()

def is_subscription_expired(user_id: int) -> bool:
    """
    Проверяет, истекла ли подписка пользователя (т.е., текущая дата >= subscription_expiry_date).
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT subscription_expiry_date FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result is None:
            print(f"DEBUG: is_subscription_expired: Пользователь {user_id} не найден.")
            return True

        expiry_date_str = result[0]

        # Если subscription_expiry_date NULL или пустая строка, считаем, что истек
        if not expiry_date_str:
            print(f"DEBUG: is_subscription_expired: subscription_expiry_date для пользователя {user_id} = NULL/пусто.")
            return True

        # Парсим дату истечения
        try:
            expiry_date = datetime.fromisoformat(expiry_date_str)
        except (ValueError, TypeError):
             print(f"DEBUG: is_subscription_expired: Некорректный формат subscription_expiry_date для пользователя {user_id}: {expiry_date_str}")
             return True

        # Сравниваем текущее время с датой истечения
        now = datetime.now()
        return now >= expiry_date # Подписка истекла, если текущее время >= времени истечения

    except sqlite3.Error as e:
        print(f"DEBUG: is_subscription_expired: Ошибка БД для пользователя {user_id}: {e}")
        return True # В случае ошибки БД тоже считаем, что истек
    finally:
        conn.close()

def extend_subscription(user_id: int, days_to_add: int) -> datetime | None:
    """
    Продлевает подписку пользователя на указанное количество дней.
    Продление начинается с текущей даты истечения, если она в будущем,
    иначе - с текущей даты.
    Возвращает новую дату истечения (datetime) или None в случае ошибки.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT subscription_expiry_date FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result is None:
            print(f"DEBUG: extend_subscription: Пользователь {user_id} не найден.")
            return None

        current_expiry_date_str = result[0]
        now = datetime.now()

        # Определяем, с какой даты начинать продление
        start_date_for_extension = now # По умолчанию начинаем с текущей даты

        if current_expiry_date_str:
            try:
                current_expiry_date = datetime.fromisoformat(current_expiry_date_str)
                # Если текущая дата истечения в будущем, продлеваем с нее
                if current_expiry_date > now:
                    start_date_for_extension = current_expiry_date
            except (ValueError, TypeError):
                print(f"DEBUG: extend_subscription: Некорректный формат текущей даты истечения для {user_id}: {current_expiry_date_str}")
                # Если формат некорректен, начинаем продление с текущей даты (start_date_for_extension уже = now)


        # Вычисляем новую дату истечения
        new_expiry_date = start_date_for_extension + timedelta(days=days_to_add)
        new_expiry_date_iso = new_expiry_date.isoformat()

        # Обновляем дату истечения в БД
        cursor.execute("UPDATE users SET subscription_expiry_date = ? WHERE id = ?", (new_expiry_date_iso, user_id))
        conn.commit()
        print(f"DEBUG: Подписка пользователя {user_id} продлена. Новая дата истечения: {new_expiry_date_iso}.")
        return new_expiry_date

    except sqlite3.Error as e:
        print(f"DEBUG: Ошибка БД при продлении подписки пользователя {user_id}: {e}")
        return None
    finally:
        conn.close()

def add_payment(user_id: int, amount: int, currency: str, status: str,
                telegram_charge_id: str | None = None, provider_charge_id: str | None = None,
                invoice_payload: str | None = None):
    """
    Добавляет запись о платеже в базу данных.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO payments (user_id, amount, currency, timestamp, status,
                                 telegram_charge_id, provider_charge_id, invoice_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, amount, currency, timestamp, status,
              telegram_charge_id, provider_charge_id, invoice_payload))
        conn.commit()
        print(f"Добавлена запись о платеже для пользователя {user_id} со статусом {status}")
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении записи о платеже: {e}")
    finally:
        conn.close()
