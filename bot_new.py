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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - ТОЛЬКО ТЕКСТ, БЕЗ КНОПОК"""
    if not update.message:
        return
    
    user_name = update.effective_user.first_name if update.effective_user else "друг"
    text = (
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
    
    await update.message.reply_text(text)

async def measure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Профессиональный замер"""
    await update.message.reply_text("📏 Профессиональный замер: оставьте адрес и удобное время, мы свяжемся.")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Стоимость проекта"""
    await update.message.reply_text("💲 Стоимость проекта: опишите задачу и материалы — рассчитаем смету.")

async def design(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Дизайн-проект"""
    await update.message.reply_text("🎨 Дизайн‑проект: пришлите план и пожелания, подготовим концепт.")

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Портфолио"""
    await update.message.reply_text("📸 Портфолио: отправлю примеры работ и проекты похожие на ваш.")

async def showroom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Шоурум"""
    await update.message.reply_text("🏢 Шоурум: адрес и часы работы. Хотите записаться на визит?")

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Контакты"""
    await update.message.reply_text("📞 Контакты: телефон, WhatsApp, email. Чем удобно связаться?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Помощь"""
    await update.message.reply_text("🤖 Задайте любой вопрос — постараюсь помочь!")

def main() -> None:
    """Основная функция для запуска бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики - ТОЛЬКО КОМАНДЫ, БЕЗ КНОПОК
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("measure", measure))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("design", design))
    application.add_handler(CommandHandler("portfolio", portfolio))
    application.add_handler(CommandHandler("showroom", showroom))
    application.add_handler(CommandHandler("contacts", contacts))
    application.add_handler(CommandHandler("help", help_command))
    
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
