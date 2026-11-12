import json
import os
import requests
import time

TOKEN = "ВАШ_ТОКЕН_БОТА"  # замени на токен от @BotFather
API = f"https://api.telegram.org/bot{TOKEN}"

# Загружаем HTML виджета
with open("widget.html", encoding="utf-8") as f:
    WIDGET_HTML = f.read()

# Хранилище состояния (в реальном проекте лучше использовать БД)
counters = {}  # (chat_id, message_id) -> текущее значение

def call(method: str, **params):
    """Вызов метода Telegram Bot API"""
    r = requests.post(f"{API}/{method}", json=params, timeout=40)
    data = r.json()
    if not data.get("ok"):
        print(f"Ошибка {method}: {data.get('description')}")
        return None
    return data.get("result")

def send_widget(chat_id: int):
    """Отправляет виджет"""
    result = call(
        "sendWidget",
        chat_id=chat_id,
        html=WIDGET_HTML,
        chat_data=json.dumps({"n": 0}),
        allow_queries=True,
        caption="Нажми кнопку, чтобы увеличить счётчик"
    )
    if result:
        key = (chat_id, result["message_id"])
        counters[key] = 0
        print(f"Виджет отправлен в чат {chat_id}")

def handle_widget_query(query: dict):
    """Обрабатывает нажатия внутри виджета"""
    chat_id = query["chat"]["id"]
    message_id = query["message_id"]
    key = (chat_id, message_id)
    data = query.get("data", "")

    current = counters.get(key, 0)

    if data == "add":
        new_value = current + 1
        # Обновляем данные виджета
        edit = call(
            "editMessageWidgetData",
            chat_id=chat_id,
            message_id=message_id,
            chat_data=json.dumps({"n": new_value})
        )
        if edit:
            counters[key] = new_value
            current = new_value

    # Обязательно отвечаем на запрос (в течение 15 секунд)
    call(
        "answerWidgetQuery",
        widget_query_id=query["id"],
        data=json.dumps({"n": current})
    )

def main():
    print("Бот запущен...")
    offset = 0

    while True:
        try:
            updates = call(
                "getUpdates",
                offset=offset,
                timeout=30,
                allowed_updates=["message", "widget_query"]
            )

            if not updates:
                time.sleep(1)
                continue

            for update in updates:
                offset = update["update_id"] + 1

                # Команда /widget или /start
                message = update.get("message")
                if message:
                    text = (message.get("text") or "").strip()
                    chat_id = message["chat"]["id"]

                    if text in ("/widget", "/start", "/start@your_bot"):
                        send_widget(chat_id)

                # Нажатие внутри виджета
                widget_query = update.get("widget_query")
                if widget_query:
                    handle_widget_query(widget_query)

        except Exception as e:
            print("Ошибка:", e)
            time.sleep(3)

if name == "main":
    main()
