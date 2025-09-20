import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

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
        "portfolio": "📸 Портфолио: отправлю примеры работ и проекты похожие на ваш.",
        "showroom": "🏢 Шоурум: адрес и часы работы. Хотите записаться на визит?",
        "contacts": "📞 Контакты: телефон, WhatsApp, email. Чем удобно связаться?",
        "help": "🤖 Задайте любой вопрос — постараюсь помочь!",
        "start": build_welcome_text(update.effective_user.first_name if update.effective_user else None),
    }
    if cmd == "design":
        # Для /design запускаем квиз с выбором категорий
        await design_quiz(update, context)
        return
    reply = mapping.get(cmd, "Команда не распознана. Нажмите кнопку ниже или отправьте /start.")
    # Для всех команд просто отправляем текст
    await update.message.reply_text(reply)


# =============================
# Квиз: выбор категорий и слайдов
# =============================

# Коды категорий и отображаемые названия
CATEGORY_DISPLAY: dict[str, str] = {
    "kitchen": "🍽 КУХНЯ",
    "living": "🛋 ГОСТИНАЯ",
    "wardrobe": "🧥 ГАРДЕРОБНАЯ",
    "cabinets": "📚 ШКАФЫ",
    "library": "📖 БИБЛИОТЕКА",
    "other": "✏️ ДРУГОЕ",
}

CATEGORY_ORDER: list[str] = [
    "kitchen",
    "living",
    "wardrobe",
    "cabinets",
    "library",
    "other",
]

def _build_categories_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    # Две колонки
    row: list[InlineKeyboardButton] = []
    for idx, code in enumerate(CATEGORY_ORDER):
        title = CATEGORY_DISPLAY[code]
        is_selected = code in selected
        label = ("✅ " + title) if is_selected else title
        row.append(InlineKeyboardButton(text=label, callback_data=f"cat:{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    # Кнопка Готово
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="cat_done")])
    return InlineKeyboardMarkup(buttons)


async def design_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Старт квиза: мультивыбор категорий мебели."""
    # Инициализировать выбранные категории
    selected: set[str] = set()
    context.user_data["selected_categories"] = selected

    text = (
        "🎨 Дизайн‑проект: пришлите план и пожелания, подготовим концепт.\n\n"
        "Какая мебель вас интересует?"
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=_build_categories_keyboard(selected))
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, reply_markup=_build_categories_keyboard(selected))


async def on_category_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия на категорию: переключение выбора и обновление клавиатуры."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    code = query.data.split(":", maxsplit=1)[1]
    selected: set[str] = context.user_data.get("selected_categories", set())
    if code in selected:
        selected.remove(code)
    else:
        selected.add(code)
    context.user_data["selected_categories"] = selected

    # Обновить клавиатуру текущего сообщения
    if query.message:
        try:
            await query.message.edit_reply_markup(reply_markup=_build_categories_keyboard(selected))
        except Exception as exc:  # noqa: BLE001 - логируем и продолжаем
            logging.warning("Не удалось обновить клавиатуру: %s", exc)


def _slides_count_for_category(code: str) -> int:
    if code == "kitchen":
        return 6
    if code == "other":
        return 1
    return 4


def _build_slides_keyboard(code: str) -> InlineKeyboardMarkup:
    total = _slides_count_for_category(code)
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i in range(1, total + 1):
        row.append(InlineKeyboardButton(text=f"Слайд {i}", callback_data=f"slide:{code}:{i}"))
        if len(row) == 3:  # 3 кнопки в ряд для компактности
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def on_category_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пользователь завершил выбор категорий: отправляем клавиатуры выбора слайдов по каждой."""
    query = update.callback_query
    if not query:
        return
    selected: set[str] = context.user_data.get("selected_categories", set())
    if not selected:
        await query.answer("Выберите хотя бы одну категорию", show_alert=True)
        return
    await query.answer("Категории выбраны")

    # Зафиксировать выбор в сообщении и убрать клавиатуру
    if query.message:
        chosen_titles = ", ".join(CATEGORY_DISPLAY[c] for c in CATEGORY_ORDER if c in selected)
        try:
            await query.message.edit_text(
                f"Вы выбрали: {chosen_titles}\n\nПоказываю примеры слайдов по категориям:")
        except Exception:
            pass

    # Отправить медиагруппы с изображениями для каждой выбранной категории
    for code in CATEGORY_ORDER:
        if code not in selected:
            continue
        title = CATEGORY_DISPLAY[code]
        limit = _slides_count_for_category(code)
        paths = _list_slide_paths(code, limit)
        if not paths:
            await query.message.reply_text(f"{title}: не нашлось файлов в папке.")
            continue
        # Если файлов несколько — отправим медиагруппу, иначе одиночное фото
        if len(paths) > 1:
            medias: list[InputMediaPhoto] = [InputMediaPhoto(media=FSInputFile(str(p))) for p in paths]
            # Подпись только на первом
            medias[0].caption = f"{title}: примеры"
            messages = await query.message.reply_media_group(media=medias)
            # Кэшируем file_id
            cache: dict[str, str] = context.application.bot_data.setdefault("file_id_cache", {})
            for p, m in zip(paths, messages):
                if m.photo:
                    cache[str(p)] = m.photo[-1].file_id
        else:
            p = paths[0]
            cache: dict[str, str] = context.application.bot_data.setdefault("file_id_cache", {})
            key = str(p)
            if key in cache:
                await query.message.reply_photo(photo=cache[key], caption=f"{title}: пример")
            else:
                m = await query.message.reply_photo(photo=FSInputFile(key), caption=f"{title}: пример")
                if m.photo:
                    cache[key] = m.photo[-1].file_id


async def on_slide_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора конкретного слайда по категории."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    # Текущий флоу больше не использует кнопки слайдов; просто очищаем уведомление.
    try:
        if query.message:
            await query.message.delete()
    except Exception:
        pass


SUPPORTED_IMAGE_EXTS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")

def _slides_dir_for(code: str) -> Path:
    return Path(__file__).resolve().parent / "slides" / code

def _resolve_slide_path(code: str, idx: int) -> Path | None:
    """Находит путь к слайду по соглашению имен или порядковому номеру в папке.

    1) Ищем `slides/<code>/<code>_<idx>.<ext>` среди SUPPORTED_IMAGE_EXTS
    2) Если не нашли — берём (idx)‑й файл по алфавиту среди поддерживаемых расширений
    """
    base = _slides_dir_for(code)
    if not base.exists() or not base.is_dir():
        return None

    # Попытка по шаблону имени
    for ext in SUPPORTED_IMAGE_EXTS:
        candidate = base / f"{code}_{idx}{ext}"
        if candidate.exists():
            return candidate

    # Фоллбек: n‑й файл по сортировке
    files = [p for p in base.iterdir() if p.suffix.lower() in SUPPORTED_IMAGE_EXTS and p.is_file()]
    files.sort(key=lambda p: p.name.lower())
    if 1 <= idx <= len(files):
        return files[idx - 1]
    return None


def _list_slide_paths(code: str, limit: int) -> list[Path]:
    """Возвращает список путей к слайдам для категории, максимум limit.

    Предпочтение — именам `<code>_1.ext ... <code>_N.ext`. Если некоторых нет,
    добираем алфавитной выборкой поддерживаемых изображений.
    """
    result: list[Path] = []
    base = _slides_dir_for(code)
    if not base.exists():
        return result
    # Сначала по шаблону
    for i in range(1, limit + 1):
        p = _resolve_slide_path(code, i)
        if p and p.exists():
            result.append(p)
    if len(result) >= limit:
        return result[:limit]
    # Добор алфавитными файлами
    files = [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTS]
    files.sort(key=lambda p: p.name.lower())
    for p in files:
        if p not in result:
            result.append(p)
            if len(result) >= limit:
                break
    return result[:limit]

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
    # Команды
    application.add_handler(CommandHandler("design", design_quiz))
    application.add_handler(CommandHandler(["measure","price","portfolio","showroom","contacts","help"], on_command))
    
    # Callback кнопки квиза
    application.add_handler(CallbackQueryHandler(on_category_toggle, pattern=r"^cat:"))
    application.add_handler(CallbackQueryHandler(on_category_done, pattern=r"^cat_done$"))
    application.add_handler(CallbackQueryHandler(on_slide_selected, pattern=r"^slide:"))
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
