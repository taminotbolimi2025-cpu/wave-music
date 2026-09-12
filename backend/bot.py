import os
import html
import logging
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    MenuButtonWebApp,
    MenuButtonDefault,
    InlineQueryResultArticle,
    InputTextMessageContent
)

import config
from config import BOT_TOKEN
import music_service
import access_control

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# In-memory dictionary to store searched tracks for 1-click downloads & inline mode
_searched_tracks_cache = {}


def get_current_url():
    url_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tunnel_url.txt"))
    base_url = config.WEBAPP_URL
    if os.path.exists(url_file):
        try:
            with open(url_file, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url.startswith("http"):
                    base_url = url
        except Exception:
            pass
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}v=3.0.0"


def get_webapp_keyboard():
    current_url = get_current_url()
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            text="🎵 Открыть Wave Music",
            web_app=WebAppInfo(url=current_url)
        )
    )
    wave_url = f"{current_url}#wave"
    markup.add(
        InlineKeyboardButton(
            text="🌊 Запустить Мою Волну",
            web_app=WebAppInfo(url=wave_url)
        )
    )
    return markup


def _send_track_to_chat(chat_id, track, status_msg_id=None):
    title = track.get('title', 'Трек')
    artist = track.get('artist', 'Wave Music')
    track_id = track.get('id', '')
    duration_sec = track.get('duration_sec', 0)

    audio_file = music_service.download_track_audio(track_id or f"{artist} {title}")
    if audio_file and os.path.exists(audio_file):
        try:
            caption = (
                f"🎵 <b>{html.escape(artist)} — {html.escape(title)}</b>\n\n"
                f"🎧 <a href='{get_current_url()}'>Открыть в Wave Music</a>"
            )
            with open(audio_file, "rb") as f:
                bot.send_audio(
                    chat_id=chat_id,
                    audio=f,
                    title=title,
                    performer=artist,
                    duration=duration_sec,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=get_webapp_keyboard()
                )
            if status_msg_id:
                try:
                    bot.delete_message(chat_id=chat_id, message_id=status_msg_id)
                except Exception:
                    pass
            return True
        finally:
            if audio_file and not audio_file.startswith(music_service.AUDIO_CACHE_DIR):
                try:
                    os.remove(audio_file)
                except Exception:
                    pass
    else:
        text = (
            f"🎵 <b>{html.escape(artist)} — {html.escape(title)}</b>\n"
            f"⏱ Длительность: {track.get('duration', '3:00')}\n\n"
            f"🎧 Нажмите кнопку ниже, чтобы слушать в плеере:"
        )
        if status_msg_id:
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg_id,
                    text=text,
                    reply_markup=get_webapp_keyboard(),
                    parse_mode="HTML"
                )
            except Exception:
                bot.send_message(chat_id, text, reply_markup=get_webapp_keyboard(), parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, reply_markup=get_webapp_keyboard(), parse_mode="HTML")
        return False


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


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_name = html.escape(message.from_user.first_name or "друг")
    current_url = get_current_url()

    # Check permission
    if not access_control.is_allowed(user_id):
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
            f"Ваш персональный плеер Wave Music активен:\n\n"
            f"• 🎵 Нажмите <b>«Открыть Wave Music»</b> для запуска MiniApp\n"
            f"• 🌊 Команда <b>/wave</b> — включить Мою Волну по настроению\n"
            f"• 🔥 Команда <b>/chart</b> — топ-10 лучших треков недели\n"
            f"• 🔍 Просто напишите название трека в чат, чтобы скачать файл\n"
            f"• 👑 Команда <b>/admin</b> — управление доступом пользователей"
        )
    else:
        welcome_text = (
            f"👋 <b>Здравствуйте, {user_name}!</b>\n\n"
            f"Ваш доступ активирован! Наслаждайтесь бесплатной музыкой без рекламы:\n\n"
            f"• 🎵 Нажмите кнопку ниже для запуска плеера Wave Music\n"
            f"• 🌊 <b>/wave</b> — включить «Мою Волну»\n"
            f"• 🔥 <b>/chart</b> — топ чарт недели\n"
            f"• 🔍 Напишите название любой песни, чтобы получить её прямо в чат"
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


@bot.message_handler(commands=['help'])
def handle_help(message):
    user_id = message.from_user.id
    if not access_control.is_allowed(user_id):
        handle_start(message)
        return

    help_text = (
        "🎵 <b>Возможности бота Wave Music:</b>\n\n"
        "1. <b>Полноценный Mini App:</b> нажмите кнопку «🎵 Открыть Wave Music» под чатом или напишите /start.\n"
        "2. <b>Мгновенный поиск музыки:</b> просто напишите имя исполнителя или трека в чат (например: <code>MACAN</code>, <code>Miyagi</code>).\n"
        "3. <b>/wave</b> — интерактивный подбор музыки «Моя Волна» по вашему настроению.\n"
        "4. <b>/chart</b> — топ-10 главных хитов с возможностью скачать любой трек в 1 клик.\n"
        "5. <b>/myid</b> — ваш личный ID в Telegram.\n"
        "6. <b>Ссылки YouTube / Shorts:</b> отправьте ссылку на видео, и бот извлечет аудиофайл в чат!"
    )
    bot.send_message(message.chat.id, help_text, reply_markup=get_webapp_keyboard(), parse_mode="HTML")


@bot.message_handler(commands=['chart', 'top'])
def handle_chart(message):
    user_id = message.from_user.id
    if not access_control.is_allowed(user_id):
        handle_start(message)
        return

    tracks = music_service.get_chart_tracks()
    if not tracks:
        bot.reply_to(message, "⚠️ Не удалось загрузить чарт. Попробуйте чуть позже.")
        return

    text = "🔥 <b>Главный чарт хитов (Топ-10)</b>\n\n<i>Нажмите на любой трек, чтобы бот прислал аудио прямо сюда:</i>"
    markup = InlineKeyboardMarkup(row_width=1)
    for i, t in enumerate(tracks[:10], start=1):
        markup.add(
            InlineKeyboardButton(
                text=f"{i}. {t['artist']} — {t['title']} ({t.get('duration', '3:00')})",
                callback_data=f"sendtrack_{t['id'][:20]}"
            )
        )
    markup.add(
        InlineKeyboardButton(text="🎵 Открыть плеер Wave Music", web_app=WebAppInfo(url=get_current_url()))
    )

    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(commands=['wave'])
def handle_wave(message):
    user_id = message.from_user.id
    if not access_control.is_allowed(user_id):
        handle_start(message)
        return

    text = (
        "🌊 <b>Моя Волна — выберите настроение:</b>\n\n"
        "Выберите вайб, и бот мгновенно пришлёт трек прямо в чат 👇"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="🔥 Драйв", callback_data="wave_drive"),
        InlineKeyboardButton(text="😌 Релакс", callback_data="wave_chill")
    )
    markup.add(
        InlineKeyboardButton(text="⚡️ Энергия", callback_data="wave_energy"),
        InlineKeyboardButton(text="❤️ Романтика", callback_data="wave_romantic")
    )
    markup.add(
        InlineKeyboardButton(text="💃 Танцевальная", callback_data="wave_dance"),
        InlineKeyboardButton(text="🎲 Случайный хит", callback_data="wave_all")
    )
    markup.add(
        InlineKeyboardButton(text="🌊 Запустить Мою Волну в плеере", web_app=WebAppInfo(url=f"{get_current_url()}#wave"))
    )

    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('wave_'))
def handle_wave_pick(call):
    if not access_control.is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Доступ закрыт", show_alert=True)
        return

    mood = call.data.split('_')[1]
    mood_names = {
        'drive': '🔥 Драйв', 'chill': '😌 Релакс', 'energy': '⚡️ Энергия',
        'romantic': '❤️ Романтика', 'dance': '💃 Танцы', 'all': '🎲 Случайный хит'
    }
    mood_label = mood_names.get(mood, '🌊 Моя Волна')
    bot.answer_callback_query(call.id, f"Подбираю {mood_label}...")

    status_msg = bot.send_message(call.message.chat.id, f"🌊 <i>Подбираю лучший трек под настроение «{mood_label}»...</i>", parse_mode="HTML")
    tracks = music_service.get_wave_tracks(mood)
    if not tracks:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=status_msg.message_id, text="⚠️ Не удалось найти трек под это настроение.")
        return

    import random
    top = random.choice(tracks[:6])
    _send_track_to_chat(call.message.chat.id, top, status_msg_id=status_msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('sendtrack_'))
def handle_send_chart_track(call):
    if not access_control.is_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "Доступ закрыт", show_alert=True)
        return

    track_id = call.data.split('_')[1]
    bot.answer_callback_query(call.id, "⏳ Загружаю трек...")

    status_msg = bot.send_message(call.message.chat.id, "⏳ <i>Загружаю выбранный трек в Telegram...</i>", parse_mode="HTML")

    # Look up in searched tracks cache first, then chart or new releases
    target = _searched_tracks_cache.get(track_id)
    if not target:
        all_cached = music_service.get_chart_tracks() + music_service.get_new_releases()
        target = next((t for t in all_cached if t['id'].startswith(track_id)), None)
    if not target:
        target = {'id': track_id, 'title': 'Музыкальный трек', 'artist': 'Wave Music', 'duration_sec': 0}

    _send_track_to_chat(call.message.chat.id, target, status_msg_id=status_msg.message_id)


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

    try:
        bot.set_chat_menu_button(
            chat_id=target_id,
            menu_button=MenuButtonWebApp(type="web_app", text="🎵 Музыка", web_app=WebAppInfo(url=get_current_url()))
        )
    except Exception as e:
        logger.warning(f"Could not set menu button for user {target_id}: {e}")

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
    if len(args) >= 2 and args[1].lower() in ['update', 'refresh', 'sync']:
        wait_msg = bot.reply_to(message, "⏳ <i>Запускаю принудительное обновление чартов и новинок...</i>", parse_mode="HTML")
        try:
            chart, releases = music_service.update_all_daily_playlists()
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text=(
                    f"✅ <b>Плейлисты успешно обновлены!</b>\n\n"
                    f"🔥 Главный чарт: <b>{len(chart)}</b> свежих треков\n"
                    f"✨ Новинки музыки: <b>{len(releases)}</b> треков\n\n"
                    f"<i>(Фоновое автообновление также работает каждые 12 часов)</i>"
                ),
                parse_mode="HTML"
            )
        except Exception as err:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text=f"⚠️ Ошибка обновления: {html.escape(str(err))}",
                parse_mode="HTML"
            )
        return

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
            f"• <code>/admin update</code> — обновить чарты и плейлисты прямо сейчас\n"
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
                text="❌ <b>Ничего не найдено.</b> Попробуйте уточнить название или имя исполнителя.",
                parse_mode="HTML"
            )
            return

        for t in tracks:
            _searched_tracks_cache[t['id']] = t

        top = tracks[0]
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"⏳ <i>Загружаю аудио: «{html.escape(top['artist'])} — {html.escape(top['title'])}»...</i>",
            parse_mode="HTML"
        )

        # Send top track directly into chat
        _send_track_to_chat(message.chat.id, top, status_msg_id=status_msg.message_id)

        # If there are additional matches, offer 1-click download buttons for them
        if len(tracks) > 1:
            more_text = f"🔍 <b>Другие результаты по запросу «{html.escape(query)}»:</b>\n\n"
            markup = InlineKeyboardMarkup(row_width=1)
            for idx, t in enumerate(tracks[1:5], start=2):
                more_text += f"{idx}. 🎵 <b>{html.escape(t['artist'])}</b> — {html.escape(t['title'])} <i>({t.get('duration', '3:00')})</i>\n"
                markup.add(
                    InlineKeyboardButton(
                        text=f"⬇️ {idx}. {t['artist'][:18]} — {t['title'][:20]}",
                        callback_data=f"sendtrack_{t['id'][:20]}"
                    )
                )
            markup.add(
                InlineKeyboardButton(text="🎵 Открыть в Wave Music", web_app=WebAppInfo(url=get_current_url()))
            )
            bot.send_message(message.chat.id, more_text, reply_markup=markup, parse_mode="HTML")

    except Exception as ex:
        logger.error(f"Error handling query {query}: {ex}")
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"⚠️ Ошибка при поиске: {html.escape(str(ex))}",
                parse_mode="HTML"
            )
        except Exception:
            pass


@bot.inline_handler(lambda query: len(query.query.strip()) > 1)
def handle_inline_query(inline_query):
    """Allows instant music search and sharing across PC, iPhone, and Android in any chat"""
    user_id = inline_query.from_user.id
    if not access_control.is_allowed(user_id):
        article = InlineQueryResultArticle(
            id="no_access",
            title="🔒 Доступ к музыке ограничен",
            description="Нажмите, чтобы запросить доступ у администратора",
            thumb_url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=100",
            input_message_content=InputTextMessageContent(
                message_text=f"🔒 <b>Доступ к Wave Music закрыт</b>\n\nОткройте бота @{config.BOT_USERNAME} и нажмите кнопку «📩 Отправить запрос админу», чтобы получить доступ.",
                parse_mode="HTML"
            )
        )
        bot.answer_inline_query(inline_query.id, [article], cache_time=5)
        return

    try:
        q = inline_query.query.strip()
        tracks = music_service.search_tracks(q, limit=8)
        results = []
        for idx, t in enumerate(tracks):
            _searched_tracks_cache[t['id']] = t
            share_text = (
                f"🎵 <b>{html.escape(t['artist'])} — {html.escape(t['title'])}</b>\n"
                f"⏱ Длительность: {t.get('duration', '3:00')}\n\n"
                f"🎧 Слушать онлайн в Wave Music:\n{get_current_url()}"
            )
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton(text="🎵 Слушать в Wave Music", web_app=WebAppInfo(url=get_current_url()))
            )
            results.append(
                InlineQueryResultArticle(
                    id=f"in_{t['id']}_{idx}",
                    title=f"{t['artist']} — {t['title']}",
                    description=f"⏱ {t.get('duration', '3:00')} | Wave Music",
                    thumb_url=t.get('cover'),
                    input_message_content=InputTextMessageContent(message_text=share_text, parse_mode="HTML"),
                    reply_markup=markup
                )
            )
        bot.answer_inline_query(inline_query.id, results, cache_time=300)
    except Exception as e:
        logger.error(f"Inline query error: {e}")


def start_bot():
    logger.info("Starting Telegram Bot Polling...")
    bot.infinity_polling()


if __name__ == '__main__':
    start_bot()
