
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


# Данные авторизации
AUTHORIZED_USERS = {}  # Хранилище авторизованных пользователей {user_id: username}
VALID_CREDENTIALS = {"OTPsec": "otp_admin-2207"}  # Логины и пароли для авторизации

TELEGRAM_BOT_TOKEN = "7884636536:AAF57CwCyyy-u8yywBxmcQga1FLGURkwuH4"


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Welcome, {user.first_name}! To authorize, use:\n"
        f"/login <username>"
    )


# Команда /login <username>
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /login <username>")
        return

    username = context.args[0]
    user_id = update.effective_user.id

    if username in VALID_CREDENTIALS:
        context.user_data['username'] = username  # Сохраняем этап авторизации
        await update.message.reply_text("Username accepted! Now send your password using /password <password>")
    else:
        await update.message.reply_text("Invalid username. Try again.")


# Команда /password <password>
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'username' not in context.user_data:
        await update.message.reply_text("Please login first using /login <username>")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /password <password>")
        return

    password = context.args[0]
    username = context.user_data['username']
    user_id = update.effective_user.id

    if VALID_CREDENTIALS[username] == password:
        AUTHORIZED_USERS[user_id] = username
        del context.user_data['username']
        await update.message.reply_text(f"Welcome, {username}! You are now authorized.")
    else:
        await update.message.reply_text("Invalid password. Try again.")


# Обработка сообщений
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("You are not authorized. Please login using /login <username>")
        return

    username = AUTHORIZED_USERS[user_id]
    message = update.message.text

    print(f"Message from {username}: {message}")
    await update.message.reply_text("Your message has been received!")


# Основной код
def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("password", password))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()