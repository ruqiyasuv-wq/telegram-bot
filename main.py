import telebot

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
ADMIN_ID = 6736873215

bot = telebot.TeleBot(TOKEN)

rules = {
    "suv": "Suv iching!",
    "salom": "Salom! Qalaysiz?"
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot ishlayapti ✅")

@bot.message_handler(func=lambda message: True)
def answer_rules(message):
    text = message.text.lower()
    for word, reply in rules.items():
        if word in text:
            bot.reply_to(message, reply)
            break

print("Bot ishga tushdi...")
bot.infinity_polling()