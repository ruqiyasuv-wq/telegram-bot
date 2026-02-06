import telebot

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
ADMIN_ID = 6736873215

bot = telebot.TeleBot(TOKEN)

# ====== DATA ======
rules = {}  # so'z: javob
users = set()  # foydalanuvchi idlari

# ====== Transliteration ======
def to_kiril(text):
    # oddiy misol translit (kerak bo'lsa kengaytiramiz)
    mapping = {'a':'а','b':'б','d':'д','e':'е','f':'ф','g':'г','h':'х','i':'и','j':'ж','k':'к','l':'л','m':'м','n':'н','o':'о','p':'п','q':'қ','r':'р','s':'с','t':'т','u':'у','v':'в','x':'х','y':'й','z':'з'}
    return ''.join([mapping.get(c,c) for c in text.lower()])

def to_latin(text):
    mapping = {'а':'a','б':'b','д':'d','е':'e','ф':'f','г':'g','х':'h','и':'i','ж':'j','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','қ':'q','р':'r','с':'s','т':'t','у':'u','в':'v','й':'y','з':'z'}
    return ''.join([mapping.get(c,c) for c in text.lower()])

# ====== ADMIN COMMANDS ======
@bot.message_handler(commands=['add'])
def add_rule(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        text = message.text.replace("/add","",1).strip()
        key, value = text.split("|",1)
        rules[key.strip().lower()] = value.strip()
        bot.reply_to(message, f"✅ Qo‘shildi: {key.strip()} → {value.strip()}")
    except:
        bot.reply_to(message, "❌ Format: /add so‘z | javob")

@bot.message_handler(commands=['del'])
def del_rule(message):
    if message.from_user.id != ADMIN_ID:
        return
    key = message.text.replace("/del","",1).strip().lower()
    if key in rules:
        del rules[key]
        bot.reply_to(message, f"🗑 {key} o‘chirildi")
    else:
        bot.reply_to(message, "Topilmadi")

@bot.message_handler(commands=['list'])
def list_rules(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not rules:
        bot.reply_to(message, "Ro‘yxat bo‘sh")
    else:
        msg = "\n".join([f"{k} → {v}" for k,v in rules.items()])
        bot.reply_to(message, msg)

# ====== BROADCAST ======
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/broadcast","",1).strip()
    for user_id in users:
        try:
            bot.send_message(user_id, text)
        except:
            pass
    bot.reply_to(message, "✅ Habar jo‘natildi")

# ====== USER HANDLER ======
@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    users.add(message.from_user.id)
    text = message.text.lower()

    # alifboga qarab javob
    for key, reply in rules.items():
        if key in text:
            # kiril yoki lotin
            if any("а" <= c <= "я" for c in message.text.lower()):
                bot.reply_to(message, to_kiril(reply))
            else:
                bot.reply_to(message, to_latin(reply))
            break

# ====== START ======
@bot.message_handler(commands=['start'])
def start_msg(message):
    users.add(message.from_user.id)
    bot.reply_to(message, "Salom! Bot ishlayapti ✅")

print("Bot ishga tushdi...")
bot.infinity_polling()