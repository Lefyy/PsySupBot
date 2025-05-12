import sqlite3
from datetime import datetime

DATABASE_NAME = 'psych_support_bot.db'

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
            message_balance INTEGER DEFAULT 10
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
        # Проверяем, есть ли уже такой пользователь
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # Если пользователя нет, добавляем его
            join_date = datetime.now().isoformat() # Текущая дата и время в формате ISO8601
            cursor.execute("INSERT INTO users (id, full_name, username, join_date) VALUES (?, ?, ?, ?)",
                           (user_id, full_name, username, join_date))
            conn.commit()
            print(f"Добавлен новый пользователь: {user_id}")
        else:
            print(f"Пользователь {user_id} уже существует.") # Можно добавить для отладки

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
        cursor.execute("SELECT id, full_name, username, join_date, message_balance FROM users WHERE id = ?", (user_id,))
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

def decrement_balance(user_id: int) -> int | None:
    """
    Уменьшает message_balance пользователя на 1.
    Возвращает новый баланс или None в случае ошибки или если баланс уже 0.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT message_balance FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        if result is None:
            print(f"Ошибка: Пользователь с ID {user_id} не найден для уменьшения баланса.")
            return None

        current_balance = result[0]

        if current_balance > 0:
            new_balance = current_balance - 1
            cursor.execute("UPDATE users SET message_balance = ? WHERE id = ?", (new_balance, user_id))
            conn.commit()
            print(f"Баланс пользователя {user_id} уменьшен до {new_balance}.")
            return new_balance
        else:
            print(f"Баланс пользователя {user_id} уже 0 или меньше.")
            return current_balance

    except sqlite3.Error as e:
        print(f"Ошибка при уменьшении баланса пользователя {user_id}: {e}")
        return None # Возвращаем None в случае ошибки
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
