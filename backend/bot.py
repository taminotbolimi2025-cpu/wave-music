import os
import html
import logging
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    MenuButtonWebApp,
    MenuButtonDefault
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


@bot.message_handler(commands=['myid', 'id'])
def handle_myid(message):
    user_id = message.from_user.id
    user_name = html.escape(message.from_user.first_name or "друг")
    is_adm = access_control.is_admin(user_id)
    is_alw = access_control.is_allowed(user_id)

    if is_adm:
        status_str = "👑 <b>Главный Администратор</b>"
    elif is_alw:
        status_str = "✅ <b>Пользователь с доступом</b>"
    else:
        status_str = "🔒 <b>Гость (доступ закрыт)</b>"

    bot.reply_to(
        message,
        f"👤 <b>Пользователь:</b> {user_name}\n"
        f"🆔 <b>Ваш Telegram ID:</b> <code>{user_id}</code>\n"
        f"📊 <b>Текущий статус:</b> {status_str}\n\n"
        f"<i>Основной ID владельца в системе: <code>{config.ADMIN_ID}</code></i>",
        parse_mode="HTML"
    )


@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = html.escape(message.from_user.first_name or "друг")
    current_url = get_current_url()

    # Check permission
    if not access_control.is_allowed(user_id):
        # Reset menu button for unauthorized user to default
        try:
            bot.set_chat_menu_button(chat_id=message.chat.id, menu_button=MenuButtonDefault())
        except Exception:
            pass

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
                f"🔒 <b>Доступ ограничен</b>\n\n"
                f"Здравствуйте, {user_name}! Этот музыкальный плеер является персональным.\n"
                f"Ваш Telegram ID: <code>{user_id}</code>\n\n"
                f"Нажмите кнопку ниже, чтобы отправить запрос владельцу бота на получение доступа."
            ),
            reply_markup=markup,
            parse_mode="HTML"
        )
        return

    # User IS allowed (Admin or Whitelisted)
    if access_control.is_admin(user_id):
        welcome_text = (
            f"👑 <b>Здравствуйте, Администратор ({user_name})!</b>\n\n"
            f"Ваш плеер активен в приватном режиме.\n"
            f"• Нажмите кнопку ниже для запуска плеера.\n"
            f"• Напишите любое название песни в чат, чтобы получить трек прямо сюда.\n"
            f"• Используйте /admin для управления пользователями."
        )
    else:
        welcome_text = (
            f"👋 <b>Здравствуйте, {user_name}!</b>\n\n"
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
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('req_access_'))
def handle_request_access(call):
    user_id = int(call.data.split('_')[2])
    first_name = html.escape(call.from_user.first_name or "Пользователь")
    username = f"@{call.from_user.username}" if call.from_user.username else "нет юзернейма"

    # Confirm to user
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="⏳ <b>Запрос отправлен администратору!</b>\nОжидайте решения. Вам придет сообщение, когда доступ откроют.",
        parse_mode="HTML"
    )

    # Notify admins
    admins = access_control.get_admins()
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="✅ Разрешить доступ", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")
    )

    admin_text = (
        f"🔔 <b>Новый запрос на доступ к музыке:</b>\n\n"
        f"👤 <b>Имя:</b> {first_name}\n"
        f"🔗 <b>Юзернейм:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
        f"Разрешить этому человеку использовать плеер?"
    )

    for admin_id in admins:
        try:
            bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=markup, parse_mode="HTML")
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
        text=f"✅ <b>Доступ успешно выдан!</b> (ID: <code>{target_id}</code> добавлен в белый список).",
        parse_mode="HTML"
    )

    # Set webapp menu button for the approved user
    try:
        bot.set_chat_menu_button(
            chat_id=target_id,
            menu_button=MenuButtonWebApp(type="web_app", text="🎵 Музыка", web_app=WebAppInfo(url=get_current_url()))
        )
    except Exception as e:
        logger.warning(f"Could not set menu button for user {target_id}: {e}")

    # Notify the approved user
    try:
        bot.send_message(
            chat_id=target_id,
            text=(
                f"🎉 <b>Администратор одобрил ваш доступ!</b>\n\n"
                f"Теперь вы можете слушать любые треки, плейлисты и Мою Волну.\n"
                f"Нажмите кнопку ниже, чтобы открыть плеер:"
            ),
            reply_markup=get_webapp_keyboard(),
            parse_mode="HTML"
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

    # Reset menu button for the rejected user
    try:
        bot.set_chat_menu_button(chat_id=target_id, menu_button=MenuButtonDefault())
    except Exception:
        pass

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"❌ <b>Запрос пользователя <code>{target_id}</code> отклонен.</b>",
        parse_mode="HTML"
    )

    try:
        bot.send_message(
            chat_id=target_id,
            text="❌ <b>К сожалению, администратор отклонил вашу заявку на доступ.</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_id}: {e}")


@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    if not access_control.is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ У вас нет прав администратора.", parse_mode="HTML")
        return

    args = message.text.strip().split()
    if len(args) >= 3:
        cmd = args[1].lower()
        try:
            target_id = int(args[2])
            if cmd == "add":
                access_control.add_to_whitelist(target_id)
                bot.reply_to(message, f"✅ Пользователь <code>{target_id}</code> добавлен в белый список!", parse_mode="HTML")
                return
            elif cmd == "remove":
                if access_control.remove_from_whitelist(target_id):
                    bot.reply_to(message, f"🗑 Пользователь <code>{target_id}</code> удален из белого списка.", parse_mode="HTML")
                else:
                    bot.reply_to(message, f"⚠️ Не удалось удалить <code>{target_id}</code> (не найден или является владельцем).", parse_mode="HTML")
                return
        except ValueError:
            bot.reply_to(message, "⚠️ Неверный формат ID. Пример: <code>/admin add 123456789</code>", parse_mode="HTML")
            return

    whitelist = access_control.get_whitelist()
    admins = access_control.get_admins()

    admin_ids_str = ", ".join(f"<code>{a}</code>" for a in admins)
    wl_ids_str = "\n".join(f"• <code>{uid}</code>" for uid in whitelist) or "<i>список пуст</i>"

    bot.send_message(
        chat_id=message.chat.id,
        text=(
            f"👑 <b>Панель администратора Wave Music</b>\n\n"
            f"👑 <b>Администраторы:</b> {admin_ids_str}\n"
            f"👥 <b>Пользователей с доступом ({len(whitelist)}):</b>\n{wl_ids_str}\n\n"
            f"📌 <b>Команды управления:</b>\n"
            f"• <code>/admin add ID</code> — выдать доступ по ID\n"
            f"• <code>/admin remove ID</code> — забрать доступ по ID\n"
            f"• <code>/myid</code> — узнать свой ID"
        ),
        parse_mode="HTML"
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

    status_msg = bot.send_message(
        chat_id=message.chat.id,
        text=f"🔍 Ищу <b>«{html.escape(query)}»</b>...",
        parse_mode="HTML"
    )

    try:
        tracks = music_service.search_tracks(query, limit=5)
        if not tracks:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ <b>Ничего не найдено.</b> Попробуйте уточнить название.",
                parse_mode="HTML"
            )
            return

        top = tracks[0]
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"⏳ <i>Загружаю трек «{html.escape(top['artist'])} — {html.escape(top['title'])}» в Telegram...</i>",
            parse_mode="HTML"
        )

        # Download audio track
        audio_file = music_service.download_track_audio(top['id'])

        if audio_file and os.path.exists(audio_file):
            try:
                caption = (
                    f"🎵 <b>{html.escape(top['artist'])} — {html.escape(top['title'])}</b>\n\n"
                    f"🎧 <a href='{get_current_url()}'>Открыть в Wave Music</a>"
                )
                with open(audio_file, "rb") as f:
                    bot.send_audio(
                        chat_id=message.chat.id,
                        audio=f,
                        title=top['title'],
                        performer=top['artist'],
                        duration=top.get('duration_sec', 0),
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=get_webapp_keyboard()
                    )
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
                except Exception:
                    pass
            finally:
                try:
                    os.remove(audio_file)
                except Exception:
                    pass
        else:
            # Fallback to direct WebApp stream card
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=(
                    f"🎵 <b>{html.escape(top['artist'])} — {html.escape(top['title'])}</b>\n"
                    f"⏱ Длительность: {top.get('duration', '3:00')}\n\n"
                    f"🎧 Нажмите кнопку ниже, чтобы слушать в плеере:"
                ),
                reply_markup=get_webapp_keyboard(),
                parse_mode="HTML"
            )

    except Exception as ex:
        logger.error(f"Error handling query {query}: {ex}")
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"⚠️ Ошибка при обработке: {html.escape(str(ex))}",
                parse_mode="HTML"
            )
        except Exception:
            pass


def start_bot():
    logger.info("Starting Telegram Bot Polling...")
    bot.infinity_polling()


if __name__ == '__main__':
    start_bot()
