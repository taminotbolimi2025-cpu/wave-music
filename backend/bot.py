import os
import logging
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    MenuButtonWebApp
)

import config
from config import BOT_TOKEN
import music_service
import access_control

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)


def get_current_url():
    url_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tunnel_url.txt"))
    if os.path.exists(url_file):
        try:
            with open(url_file, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url.startswith("http"):
                    return url
        except Exception:
            pass
    return config.WEBAPP_URL


def get_webapp_keyboard():
    current_url = get_current_url()
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            text="🎵 Открыть Wave Music",
            web_app=WebAppInfo(url=current_url)
        )
    )
    markup.add(
        InlineKeyboardButton(
            text="🌊 Запустить Мою Волну",
            web_app=WebAppInfo(url=f"{current_url}#wave")
        )
    )
    return markup


@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "друг"
    current_url = get_current_url()

    # If no admins configured, the first user who starts is the Owner/Admin!
    admins = access_control.get_admins()
    if not admins:
        access_control.add_admin(user_id)
        logger.info(f"Первый пользователь {user_id} ({user_name}) зарегистрирован как Главный Админ!")
        bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"👑 *Вы назначены Администратором плеера!*\n\n"
                f"Бот переведён в *приватный режим*. Теперь никто другой не сможет слушать музыку без вашего подтверждения.\n"
                f"Когда кто-то напишет боту, вам придёт уведомление с кнопками *Разрешить / Отклонить*."
            ),
            parse_mode="Markdown"
        )

    # Check permission
    if not access_control.is_allowed(user_id):
        # User is NOT whitelisted
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                text="📩 Отправить запрос админу",
                callback_data=f"req_access_{user_id}"
            )
        )
        bot.send_message(
            chat_id=message.chat.id,
            text=(
                f"🔒 *Доступ ограничен*\n\n"
                f"Здравствуйте, {user_name}! Этот музыкальный плеер является персональным.\n\n"
                f"Нажмите кнопку ниже, чтобы отправить запрос владельцу бота на получение доступа."
            ),
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # User IS allowed (Admin or Whitelisted)
    welcome_text = (
        f"👋 *Здравствуйте, {user_name}!*\n\n"
        f"Ваш доступ активен. Нажмите кнопку ниже, чтобы открыть плеер, либо просто напишите название трека в чат:"
    )

    try:
        bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(type="web_app", text="🎵 Музыка", web_app=WebAppInfo(url=current_url))
        )
    except Exception as e:
        logger.warning(f"Could not set menu button: {e}")

    bot.send_message(
        chat_id=message.chat.id,
        text=welcome_text,
        reply_markup=get_webapp_keyboard(),
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('req_access_'))
def handle_request_access(call):
    user_id = int(call.data.split('_')[2])
    first_name = call.from_user.first_name or "Пользователь"
    username = f"@{call.from_user.username}" if call.from_user.username else "нет юзернейма"

    # Confirm to user
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="⏳ *Запрос отправлен администратору!*\nОжидайте решения. Вам придет сообщение, когда доступ откроют.",
        parse_mode="Markdown"
    )

    # Notify admins
    admins = access_control.get_admins()
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="✅ Разрешить доступ", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")
    )

    admin_text = (
        f"🔔 *Новый запрос на доступ к музыке:*\n\n"
        f"👤 *Имя:* {first_name}\n"
        f"🔗 *Юзернейм:* {username}\n"
        f"🆔 *ID:* `{user_id}`\n\n"
        f"Разрешить этому человеку использовать плеер?"
    )

    for admin_id in admins:
        try:
            bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def handle_approve(call):
    if not access_control.is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "У вас нет прав администратора!", show_alert=True)
        return

    target_id = int(call.data.split('_')[1])
    access_control.add_to_whitelist(target_id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ *Доступ успешно выдан!* (ID: `{target_id}` добавлен в белый список).",
        parse_mode="Markdown"
    )

    # Notify the approved user
    try:
        bot.send_message(
            chat_id=target_id,
            text=(
                f"🎉 *Администратор одобрил ваш доступ!*\n\n"
                f"Теперь вы можете слушать любые треки, плейлисты и Мою Волну.\n"
                f"Нажмите кнопку ниже, чтобы открыть плеер:"
            ),
            reply_markup=get_webapp_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_id}: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def handle_reject(call):
    if not access_control.is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "У вас нет прав администратора!", show_alert=True)
        return

    target_id = int(call.data.split('_')[1])
    access_control.remove_from_whitelist(target_id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"❌ *Запрос пользователя {target_id} отклонен.*",
        parse_mode="Markdown"
    )

    try:
        bot.send_message(
            chat_id=target_id,
            text="❌ *К сожалению, администратор отклонил вашу заявку на доступ.*",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_id}: {e}")


@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    if not access_control.is_admin(message.from_user.id):
        return

    whitelist = access_control.get_whitelist()
    bot.send_message(
        chat_id=message.chat.id,
        text=(
            f"👑 *Панель администратора Wave Music*\n\n"
            f"👥 Пользователей с доступом: *{len(whitelist)}*\n"
            f"🔒 Приватный режим: *Включен*\n\n"
            f"Все новые пользователи должны запросить разрешение у вас перед прослушиванием."
        ),
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=['text'])
def handle_text_search(message):
    user_id = message.from_user.id
    if not access_control.is_allowed(user_id):
        handle_start(message)
        return

    query = message.text.strip()
    if query.startswith('/'):
        return

    status_msg = bot.send_message(message.chat.id, f"🔍 Ищу *«{query}»*...", parse_mode="Markdown")

    try:
        tracks = music_service.search_tracks(query, limit=5)
        if not tracks:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ Ничего не найдено. Попробуйте уточнить название."
            )
            return

        top = tracks[0]
        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)

        stream_url = music_service.get_stream_url(top['id'])
        caption = f"🎵 *{top['title']}*\n👤 {top['artist']} • {top['duration']}\n\n🎧 [Открыть в Wave Music]({get_current_url()})"

        try:
            bot.send_audio(
                chat_id=message.chat.id,
                audio=stream_url,
                title=top['title'],
                performer=top['artist'],
                caption=caption,
                parse_mode="Markdown",
                reply_markup=get_webapp_keyboard()
            )
        except Exception as audio_err:
            logger.warning(f"Audio stream send failed: {audio_err}")
            bot.send_message(
                chat_id=message.chat.id,
                text=f"🎵 *{top['artist']} — {top['title']}*\n\n🎧 [Слушать трек]({stream_url})",
                reply_markup=get_webapp_keyboard(),
                parse_mode="Markdown"
            )

    except Exception as ex:
        logger.error(f"Error handling query {query}: {ex}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"⚠️ Ошибка при поиске: {ex}"
        )


def start_bot():
    logger.info("Starting Telegram Bot Polling...")
    bot.infinity_polling()


if __name__ == '__main__':
    start_bot()
