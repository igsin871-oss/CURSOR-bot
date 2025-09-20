import os
import logging
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Загрузить переменные окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Читаем токен из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Убедитесь, что в файле .env есть строка BOT_TOKEN=\"ВАШ_ТОКЕН\"")

def build_welcome_text(first_name: str | None) -> str:
    user_name = first_name or "друг"
    return (
        f"🏠 Добро пожаловать в мебельную студию Еврособа, {user_name}!\n\n"
        "Мы создаем премиальную мебель на заказ для тех, кто ценит качество, стиль и индивидуальный подход.\n\n"
        "🎯 Что вас интересует?\n\n"
        "📏 Заказать профессиональный замер — /measure\n"
        "💰 Узнать стоимость проекта — /price\n"
        "🎨 Запросить дизайн-проект — /design\n"
        "📸 Посмотреть портфолио работ — /portfolio\n"
        "🏢 Записаться в шоурум — /showroom\n"
        "📞 Получить контакты — /contacts\n"
        "🤖 Умный помощник (ответит на любой вопрос) — /help\n\n"
        "💬 Или просто опишите ваш проект — я пойму и помогу выбрать лучший вариант!"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    if not update.message:
        return
    text = build_welcome_text(update.effective_user.first_name if update.effective_user else None)
    await update.message.reply_text(text)


async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Единый обработчик для текстовых команд."""
    if not update.message:
        return
    cmd = update.message.text.lstrip("/").split()[0]
    # Сопоставляем с теми же текстами, что и для кнопок
    mapping = {
        "measure": "📏 Профессиональный замер: оставьте адрес и удобное время, мы свяжемся.",
        "price": "💲 Стоимость проекта: опишите задачу и материалы — рассчитаем смету.",
        "design": "🎨 Дизайн‑проект: пришлите план и пожелания, подготовим концепт.",
        "portfolio": "📸 Портфолио: отправлю примеры работ и проекты похожие на ваш.",
        "showroom": "🏢 Шоурум: адрес и часы работы. Хотите записаться на визит?",
        "contacts": "📞 Контакты: телефон, WhatsApp, email. Чем удобно связаться?",
        "help": "🤖 Задайте любой вопрос — постараюсь помочь!",
        "start": build_welcome_text(update.effective_user.first_name if update.effective_user else None),
    }
    reply = mapping.get(cmd, "Команда не распознана. Нажмите кнопку ниже или отправьте /start.")
    # Для всех команд просто отправляем текст
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Принимает фото и отправляет его обратно тем же сообщением."""
    if not update.message or not update.message.photo:
        return
    largest_photo = update.message.photo[-1]
    caption = update.message.caption or ""
    await update.message.reply_photo(photo=largest_photo.file_id, caption=caption)

SUPPORTED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}

def _has_supported_ext(filename: str | None) -> bool:
    if not filename:
        return False
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in SUPPORTED_EXTENSIONS)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Принимает документ (PDF/PPT/PPTX) и отправляет обратно как файл."""
    if not update.message or not update.message.document:
        return
    doc = update.message.document
    if not _has_supported_ext(doc.file_name):
        await update.message.reply_text(
            "Пожалуйста, пришлите файл формата PDF, PPT или PPTX."
        )
        return
    caption = update.message.caption or ""
    await update.message.reply_document(document=doc.file_id, caption=caption)

def main() -> None:
    """Основная функция для запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    # Команды текстом
    application.add_handler(CommandHandler(["measure","price","design","portfolio","showroom","contacts","help"], on_command))
    
    # Убираем обработчик кнопок
    # application.add_handler(CallbackQueryHandler(on_button))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Зарегистрировать команды бота в меню клиента
    async def _set_commands(app: Application) -> None:
        await app.bot.set_my_commands([
            BotCommand("start", "Главное меню"),
            BotCommand("measure", "Профессиональный замер"),
            BotCommand("price", "Стоимость проекта"),
            BotCommand("design", "Дизайн‑проект"),
            BotCommand("portfolio", "Портфолио работ"),
            BotCommand("showroom", "Шоурум"),
            BotCommand("contacts", "Контакты"),
            BotCommand("help", "Помощь"),
        ])

    application.post_init = _set_commands

    # Запускаем бота
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling()

if __name__ == '__main__':
    main()
