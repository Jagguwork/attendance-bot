import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from pytz import timezone

# Set Cambodia time zone
cambodia_tz = timezone('Asia/Phnom_Penh')

# Replace this with your actual Telegram bot token
bot = telebot.TeleBot("8379149531:AAFLX-FCE9NQEAnkZeyehHMGRUY5LDOPFl0")

user_data = {}

# Break options
break_options = {
    "smoke": "🚬 Smoke",
    "buy": "🛍️ Buy something",
    "toilet": "🚽 Toilet",
    "eat": "🍽️ Eat",
    "video_call": "🎥 Video call",
    "audio_call": "🔊 Audio call"
}

# /start or /hello
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /work to manage your attendance today.")

# /work command
@bot.message_handler(commands=['work'])
def send_attendance_buttons(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🟢 Start work", callback_data="start_work"),
        InlineKeyboardButton("🔴 Off work", callback_data="off_work")
    )
    for key, label in break_options.items():
        markup.add(InlineKeyboardButton(f"{label} (Start)", callback_data=f"start_break_{key}"))
    markup.add(InlineKeyboardButton("✅ Back to Work", callback_data="back_to_work"))
    bot.send_message(message.chat.id, "👇 Choose an option:", reply_markup=markup)

# Callback handling
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name
    now = datetime.now(cambodia_tz)  # Cambodia local time

    # Initialize user if needed
    if user_id not in user_data:
        user_data[user_id] = {
            "start_time": None,
            "end_time": None,
            "breaks": [],
            "current_break": None
        }

    data = user_data[user_id]

    # START WORK
    if call.data == "start_work":
        if data["start_time"] is not None:
            bot.send_message(call.message.chat.id,
                f"{user_name}, you already started work at {data['start_time'].strftime('%H:%M:%S')}.")
        else:
            data["start_time"] = now
            data["breaks"] = []
            data["current_break"] = None

            late_limit = now.replace(hour=14, minute=2, second=0, microsecond=0)
            if now > late_limit:
                bot.send_message(call.message.chat.id,
                    f"{user_name} started work at {now.strftime('%H:%M:%S')} ⚠️ Late! You are fined.")
            else:
                bot.send_message(call.message.chat.id,
                    f"{user_name} started work at {now.strftime('%H:%M:%S')} ✅")

    # END WORK
    elif call.data == "off_work":
        if data["start_time"] is None:
            bot.send_message(call.message.chat.id, "⚠️ You haven't started work yet.")
        elif data["current_break"] is not None:
            bot.send_message(call.message.chat.id, "⚠️ You are on a break. Please end break before ending work.")
        else:
            data["end_time"] = now

            total_break = timedelta()
            for start, end in data["breaks"]:
                total_break += (end - start)

            total_work = data["end_time"] - data["start_time"]
            net_time = total_work - total_break

            tb_hours, tb_rem = divmod(total_break.total_seconds(), 3600)
            tb_minutes = int(tb_rem // 60)

            nw_hours, nw_rem = divmod(net_time.total_seconds(), 3600)
            nw_minutes = int(nw_rem // 60)

            tw_hours, tw_rem = divmod(total_work.total_seconds(), 3600)
            tw_minutes = int(tw_rem // 60)

            bot.send_message(call.message.chat.id,
                f"🔚 {user_name} ended work at {now.strftime('%H:%M:%S')}\n"
                f"🕒 Total time: {int(tw_hours)}h {int(tw_minutes)}m\n"
                f"⏸️ Break time: {int(tb_hours)}h {int(tb_minutes)}m\n"
                f"✅ Net work: {int(nw_hours)}h {int(nw_minutes)}m")

    # START BREAK
    elif call.data.startswith("start_break_"):
        break_type = call.data.replace("start_break_", "")
        if data["start_time"] is None:
            bot.send_message(call.message.chat.id, "⚠️ You must start work before taking a break.")
        elif data["current_break"] is not None:
            bot.send_message(call.message.chat.id, "⚠️ You're already on a break. Click '✅ Back to Work'.")
        else:
            data["current_break"] = (now, break_type)
            bot.send_message(call.message.chat.id,
                f"{user_name} started {break_options[break_type]} break at {now.strftime('%H:%M:%S')}.")

    # END BREAK — BACK TO WORK
    elif call.data == "back_to_work":
        if data["current_break"] is None:
            bot.send_message(call.message.chat.id, "⚠️ You're not on a break.")
        else:
            start_time, break_type = data["current_break"]
            end_time = now
            data["breaks"].append((start_time, end_time))
            data["current_break"] = None
            mins = int((end_time - start_time).total_seconds() // 60)
            bot.send_message(call.message.chat.id,
                f"{user_name} returned from {break_options[break_type]} break.\n⏱️ Break duration: {mins} minutes.")

    bot.answer_callback_query(call.id)

# Start the bot
print("Bot is running using Cambodia time...")
bot.polling()
