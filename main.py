import telebot

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot ishlayapti ✅")

@bot.message_handler(commands=['test'])
def test(message):
    bot.reply_to(message, "TEST OK ✅")

print("Bot ishga tushdi...")
bot.infinity_polling()