import asyncio
import re
import logging
import os
from datetime import datetime
from aiogram import Bot, Router, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.exceptions import TelegramNetworkError
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot")

# Константы
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "8086981587:AAFTmTf7H-sMNtWyrBpqyu3Qq4Ds0oFAibs")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "1386655173")
SUPPORT_USERNAME = "@yasikvirtss"
REVIEWS_CHANNEL = "https://t.me/yasikvirtsotzivi"
PAYOP_TEST_LINK = "https://payop.com/test"

# Инициализация бота и маршрутизатора
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
router = Router()

# Определение состояний для FSM (Finite State Machine)
class OrderForm(StatesGroup):
    action = State()
    project = State()
    server = State()
    amount = State()
    payment_type = State()
    confirm = State()

# Данные о проектах и серверах
PROJECT_SERVERS = {
    "GTA5RP": [
        "Downtown", "Burton", "Strawberry", "Rockford", "Vinewood", "Alta", "Blackberry",
        "Del Perro", "Insquad", "Davis", "Sunrise", "Harmony", "Rainbow", "Redwood",
        "Richman", "Hawick", "Eclipse", "Grapeseed", "La Mesa", "Murrieta", "Vespucci"
    ],
    "Majestic": [
        "New York", "San Diego", "Detroit", "Los Angeles", "Miami", "Washington", "Dallas",
        "Las Vegas", "Chicago", "Atlanta", "San Francisco", "Houston", "Seattle", "Boston"
    ]
}
PROJECTS = list(PROJECT_SERVERS.keys())

# Кнопка "Назад"
BACK_BUTTON = types.KeyboardButton(text="⬅ Назад")

# Команда /start
@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started the bot")
    await state.clear()

    welcome_message = (
        "👋 Привет, ты попал в лучший магазин виртов! 👑😎\n\n"
        "Я помогу тебе купить или продать вирты для GTA 5 RP и Majestic RP."
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=welcome_message
    )

    await asyncio.sleep(1)

    await state.set_state(OrderForm.action)
    await bot.send_message(
        chat_id=message.chat.id,
        text="🎮 Выбери, что хочешь сделать:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="💸 Купить"), types.KeyboardButton(text="💰 Продать")],
                [types.KeyboardButton(text="📝 Отзывы"), types.KeyboardButton(text="📞 Поддержка")],
                [BACK_BUTTON]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

# Обработка выбора действия
@router.message(OrderForm.action)
async def process_action(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅ Назад":
        await state.clear()
        await bot.send_message(
            chat_id=message.chat.id,
            text="🔄 Чтобы начать заново, отправь /start",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    if text == "📝 Отзывы":
        logger.info(f"User {user_id} requested reviews")
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"📝 Ознакомьтесь с отзывами: {REVIEWS_CHANNEL}\n\n"
                 "🔄 Чтобы начать заново, отправь /start",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
        return

    if text == "📞 Поддержка":
        logger.info(f"User {user_id} requested support")
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"📞 Свяжитесь с поддержкой: {SUPPORT_USERNAME}\n\n"
                 "🔄 Чтобы начать заново, отправь /start",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
        return

    valid_actions = ["💸 Купить", "💰 Продать"]
    if text not in valid_actions:
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Пожалуйста, выбери действие из меню.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="💸 Купить"), types.KeyboardButton(text="💰 Продать")],
                    [types.KeyboardButton(text="📝 Отзывы"), types.KeyboardButton(text="📞 Поддержка")],
                    [BACK_BUTTON]
                ],
            resize_keyboard=True,
            one_time_keyboard=True
            )
        )
        return

    action = text.replace("💸 ", "").replace("💰 ", "")
    logger.info(f"User {user_id} selected action: {action}")
    await state.update_data(action=action)
    await state.set_state(OrderForm.project)

    project_buttons = [[types.KeyboardButton(text=project) for project in PROJECTS]]
    project_buttons.append([BACK_BUTTON])

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"✅ Ты выбрал действие: *{action}*.\n"
             "🌐 Выбери нужный проект:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=project_buttons,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

# Обработка выбора проекта
@router.message(OrderForm.project)
async def process_project(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅ Назад":
        await state.set_state(OrderForm.action)
        await bot.send_message(
            chat_id=message.chat.id,
            text="🎮 Выбери, что хочешь сделать:",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="💸 Купить"), types.KeyboardButton(text="💰 Продать")],
                    [types.KeyboardButton(text="📝 Отзывы"), types.KeyboardButton(text="📞 Поддержка")],
                    [BACK_BUTTON]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    if text not in PROJECTS:
        project_buttons = [[types.KeyboardButton(text=project) for project in PROJECTS]]
        project_buttons.append([BACK_BUTTON])
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Пожалуйста, выбери проект из меню.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=project_buttons,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    project = text
    logger.info(f"User {user_id} selected project: {project}")
    await state.update_data(project=project)
    await state.set_state(OrderForm.server)

    servers = PROJECT_SERVERS[project]
    server_buttons = []
    for i in range(0, len(servers), 2):
        row = [types.KeyboardButton(text=server) for server in servers[i:i+2]]
        server_buttons.append(row)
    server_buttons.append([BACK_BUTTON])

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"✅ Ты выбрал проект: *{project}*.\n"
             "🌍 Теперь выбери сервер:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=server_buttons,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

# Обработка выбора сервера
@router.message(OrderForm.server)
async def process_server(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅ Назад":
        await state.set_state(OrderForm.project)
        project_buttons = [[types.KeyboardButton(text=project) for project in PROJECTS]]
        project_buttons.append([BACK_BUTTON])

        data = await state.get_data()
        action = data.get("action", "не выбрано")

        await bot.send_message(
            chat_id=message.chat.id,
            text=f"✅ Ты выбрал действие: *{action}*.\n"
                 "🌐 Выбери нужный проект:",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=project_buttons,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    data = await state.get_data()
    project = data.get("project")
    valid_servers = PROJECT_SERVERS.get(project, [])
    if text not in valid_servers:
        servers = PROJECT_SERVERS[project]
        server_buttons = []
        for i in range(0, len(servers), 2):
            row = [types.KeyboardButton(text=server) for server in servers[i:i+2]]
            server_buttons.append(row)
        server_buttons.append([BACK_BUTTON])
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Пожалуйста, выбери сервер из меню.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=server_buttons,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    server = text
    logger.info(f"User {user_id} selected server: {server}")
    await state.update_data(server=server)
    await state.set_state(OrderForm.amount)

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"✅ Ты выбрал сервер: *{server}*.\n"
             "💵 Теперь введи сумму (от 1кк до 100кк, например, 12кк):",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[BACK_BUTTON]],
            resize_keyboard=True
        )
    )

# Обработка ввода суммы
@router.message(OrderForm.amount)
async def process_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅ Назад":
        await state.set_state(OrderForm.server)
        data = await state.get_data()
        project = data.get("project")
        servers = PROJECT_SERVERS[project]
        server_buttons = []
        for i in range(0, len(servers), 2):
            row = [types.KeyboardButton(text=server) for server in servers[i:i+2]]
            server_buttons.append(row)
        server_buttons.append([BACK_BUTTON])

        await bot.send_message(
            chat_id=message.chat.id,
            text=f"🌍 Выбери сервер для проекта *{project}*:",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=server_buttons,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    match = re.match(r'^(\d{1,3})кк$', text)
    if not match:
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Пожалуйста, введи сумму от 1кк до 100кк (например, 12кк).",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[BACK_BUTTON]],
                resize_keyboard=True
            )
        )
        return

    amount_kk = int(match.group(1))
    if not 1 <= amount_kk <= 100:
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Сумма должна быть от 1кк до 100кк.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[BACK_BUTTON]],
                resize_keyboard=True
            )
        )
        return

    logger.info(f"User {user_id} entered amount: {amount_kk}кк")
    await state.update_data(amount_kk=amount_kk)
    data = await state.get_data()
    if data['action'] == "Купить":
        price_rub = amount_kk * 1600
    else:
        price_rub = amount_kk * 900
    await state.update_data(price_rub=price_rub)

    await state.set_state(OrderForm.payment_type)

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"✅ Ты ввёл сумму: *{amount_kk}кк*.\n"
             f"💳 Теперь выбери тип оплаты:",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="💳 Карта"), types.KeyboardButton(text="📱 СБП")],
                [types.KeyboardButton(text="💲 USDT"), types.KeyboardButton(text="₿ BTC")],
                [BACK_BUTTON]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

# Обработка выбора типа оплаты
@router.message(OrderForm.payment_type)
async def process_payment_type(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅ Назад":
        await state.set_state(OrderForm.amount)
        data = await state.get_data()
        amount_kk = data.get("amount_kk", "не указано")
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"💵 Введи сумму (от 1кк до 100кк, например, 12кк). Текущая сумма: *{amount_kk}кк*.",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[BACK_BUTTON]],
                resize_keyboard=True
            )
        )
        return

    valid_payments = ["💳 Карта", "📱 СБП", "💲 USDT", "₿ BTC"]
    if text not in valid_payments:
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Пожалуйста, выбери тип оплаты из меню.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="💳 Карта"), types.KeyboardButton(text="📱 СБП")],
                    [types.KeyboardButton(text="💲 USDT"), types.KeyboardButton(text="₿ BTC")],
                    [BACK_BUTTON]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    payment_type = text.replace("💳 ", "").replace("📱 ", "").replace("💲 ", "").replace("₿ ", "")
    logger.info(f"User {user_id} selected payment type: {payment_type}")
    await state.update_data(payment_type=payment_type)
    await state.update_data(user_id=user_id)
    await state.update_data(username=message.from_user.username or "No username")

    data = await state.get_data()
    order_text = (
        f"📋 Проверь заказ:\n\n"
        f"Действие: *{data['action']}*\n"
        f"Проект: *{data['project']}*\n"
        f"Сервер: *{data['server']}*\n"
        f"Сумма: *{data['amount_kk']}кк*\n"
        f"Цена: *{data['price_rub']} RUB*\n"
        f"Оплата: *{data['payment_type']}*"
    )
    await bot.send_message(
        chat_id=message.chat.id,
        text=order_text,
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="✅ Подтвердить"), types.KeyboardButton(text="❌ Отмена")],
                [BACK_BUTTON]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(OrderForm.confirm)

# Обработка подтверждения заказа
@router.message(OrderForm.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text

    if text == "⬅ Назад":
        await state.set_state(OrderForm.payment_type)
        await bot.send_message(
            chat_id=message.chat.id,
            text="💳 Выбери тип оплаты:",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="💳 Карта"), types.KeyboardButton(text="📱 СБП")],
                    [types.KeyboardButton(text="💲 USDT"), types.KeyboardButton(text="₿ BTC")],
                    [BACK_BUTTON]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    if text == "❌ Отмена":
        logger.info(f"User {user_id} cancelled the order")
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Заказ отменён.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
        return

    if text != "✅ Подтвердить":
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Пожалуйста, выбери 'Подтвердить' или 'Отмена'.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="✅ Подтвердить"), types.KeyboardButton(text="❌ Отмена")],
                    [BACK_BUTTON]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return

    # Собираем данные заказа
    data = await state.get_data()
    action = data['action']
    project = data['project']
    server = data['server']
    amount_kk = data['amount_kk']
    price_rub = data['price_rub']
    payment_type = data['payment_type']
    username = data['username']
    order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Отправляем пользователю ссылку на оплату
    payment_status = "Ожидает оплаты (Payop тест)"
    await bot.send_message(
        chat_id=message.chat.id,
        text=f"🔗 Перейди для оплаты (тест): {PAYOP_TEST_LINK}",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # Формируем сообщение для админа
    admin_message = (
        f"🔔 *Новый заказ #ID{user_id}*\n\n"
        f"📅 *Дата и время*: {order_time}\n"
        f"👤 *Пользователь*: @{username} (ID: {user_id})\n"
        f"🎯 *Действие*: {action}\n"
        f"🎮 *Проект*: {project}\n"
        f"🌍 *Сервер*: {server}\n"
        f"💰 *Сумма*: {amount_kk}кк\n"
        f"💸 *Цена*: {price_rub} RUB\n"
        f"💳 *Тип оплаты*: {payment_type}\n"
        f"📊 *Статус*: {payment_status}\n\n"
        f"🔗 *Ссылка на оплату*: [Payop Test]({PAYOP_TEST_LINK})"
    )

    # Отправляем сообщение админу
    try:
        logger.info(f"Sending order notification to admin (chat_id: {ADMIN_CHAT_ID})")
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"Order notification sent to admin successfully")
    except Exception as e:
        logger.error(f"Failed to send notification to admin: {e}")
        await bot.send_message(
            chat_id=message.chat.id,
            text="⚠️ Заказ принят, но возникла проблема с уведомлением админа. Мы разберёмся!"
        )

    # Подтверждаем пользователю
    logger.info(f"User {user_id} confirmed the order")
    await bot.send_message(
        chat_id=message.chat.id,
        text="✅ Заказ принят! Оплата в тестовом режиме."
    )

    # Предлагаем начать новый заказ
    await bot.send_message(
        chat_id=message.chat.id,
        text="🔄 Хочешь сделать новый заказ?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="/start")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.clear()

# Команда /help
@router.message(Command("help"))
async def help_command(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested help")
    await bot.send_message(
        chat_id=message.chat.id,
        text="ℹ️ Бот для покупки и продажи виртов GTA 5 RP и Majestic RP.\n"
             "Команды:\n"
             "/start — Начать\n"
             "/help — Справка\n\n"
             "📋 Выбери Купить/Продать, затем проект, сервер, сумму (1кк–100кк).\n"
             "💳 Оплата через Payop (тестовый режим)."
    )

# Функция для попытки удаления вебхука с повторными попытками
async def delete_webhook_with_retries(max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted successfully")
            return True
        except TelegramNetworkError as e:
            logger.error(f"Failed to delete webhook (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
    return False

# Основная функция для polling
async def main():
    from aiogram import Dispatcher
    dp = Dispatcher(bot=bot, storage=storage)
    dp.include_router(router)

    # Пытаемся удалить вебхук с повторными попытками
    if not await delete_webhook_with_retries():
        logger.error("Failed to delete webhook after all retries. Continuing anyway...")

    # Запускаем polling с обработкой ошибок
    while True:
        try:
            await dp.start_polling(allowed_updates=["message"])
        except TelegramNetworkError as e:
            logger.error(f"Network error during polling: {e}")
            await asyncio.sleep(15)  # Увеличенная пауза перед перезапуском
        except Exception as e:
            logger.error(f"Unexpected error during polling: {e}")
            logger.info("Bot stopped, restarting...")
            await asyncio.sleep(10)  # Пауза перед перезапуском

if __name__ == "__main__":
    asyncio.run(main())
