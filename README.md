import telebot

# Sizning Telegram bot tokeningiz
TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215  # Sizning Telegram ID'ingiz

bot = telebot.TeleBot(TOKEN)

rules = {}
user_state = {}

# Faqat egami tekshirish
def is_owner(message):
    return message.from_user.id == OWNER_ID

@bot.message_handler(func=lambda m: m.text == "add" and is_owner(m))
def add_start(message):
    user_state[message.chat.id] = {"step": "trigger"}
    bot.send_message(message.chat.id, "📝 So‘z yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "trigger")
def add_trigger(message):
    user_state[message.chat.id]["trigger"] = message.text.lower()
    user_state[message.chat.id]["step"] = "reply"
    bot.send_message(message.chat.id, "💬 Javob yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "reply")
def add_reply(message):
    trigger = user_state[message.chat.id]["trigger"]
    rules[trigger] = message.text
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, f"✅ Qo‘shildi:\n{trigger}")

@bot.message_handler(func=lambda m: m.text == "list" and is_owner(m))
def list_rules(message):
    if not rules:
        bot.send_message(message.chat.id, "📭 Hozircha qoida yo‘q")
        return

    msg = "📋 So‘zlar ro‘yxati:\n"
    for k in rules:
        msg += f"- {k}\n"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "del" and is_owner(m))
def del_start(message):
    user_state[message.chat.id] = {"step": "delete"}
    bot.send_message(message.chat.id, "❌ Qaysi so‘zni o‘chiramiz?")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "delete")
def delete_rule(message):
    key = message.text.lower()
    if key in rules:
        del rules[key]
        bot.send_message(message.chat.id, f"🗑 O‘chirildi: {key}")
    else:
        bot.send_message(message.chat.id, "❌ Bunday so‘z yo‘q")
    user_state.pop(message.chat.id)

@bot.message_handler(content_types=['text'])
def group_reply(message):
    if message.chat.type in ['group', 'supergroup']:
        text = message.text.lower()
        for trigger, reply in rules.items():
            if trigger in text:
                bot.reply_to(message, reply)
                break

bot.infinity_polling()