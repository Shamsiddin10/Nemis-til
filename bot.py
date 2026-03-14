import os
import telebot
from telebot import types
import json
from flask import Flask
from threading import Thread
from datetime import date
import time

# ==================== RENDER UCHUN SERVER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = ("8721836937:AAGBJzt0_AKXf2Dl7zP68n6I3qV_VA82GvM")
ADMIN_IDS = [7384088509]

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== DATABASE ====================
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},
        "teachers": {},
        "students": {},
        "tests": [],
        "results": {},
        "attendance": {},
        "homeworks": {}
    }

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def today():
    return str(date.today())

user_states = {}
user_data = {}

# ==================== YORDAMCHI FUNKSIYALAR ====================
def get_user_role(user_id):
    db = load_db()
    uid = str(user_id)
    if user_id in ADMIN_IDS:
        return "admin"
    if uid in db["teachers"]:
        return "teacher"
    if uid in db["students"]:
        return "student"
    for tid, t in db["teachers"].items():
        if str(t.get("telegram_id", "")) == uid:
            return "teacher"
    for sid, s in db["students"].items():
        if str(s.get("telegram_id", "")) == uid:
            return "student"
    return None

def get_real_id(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db["teachers"]:
        return uid, "teacher"
    if uid in db["students"]:
        return uid, "student"
    for tid, t in db["teachers"].items():
        if str(t.get("telegram_id", "")) == uid:
            return tid, "teacher"
    for sid, s in db["students"].items():
        if str(s.get("telegram_id", "")) == uid:
            return sid, "student"
    return None, None

def main_menu(user_id):
    role = get_user_role(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "admin":
        markup.add("👨‍🏫 O'qituvchilar", "👨‍🎓 O'quvchilar")
        markup.add("➕ O'quvchi qo'shish", "➕ O'qituvchi qo'shish")
        markup.add("📊 Statistika", "🔗 O'quvchini biriktirish")
        markup.add("🗑 O'qituvchini o'chirish", "🗑 O'quvchini o'chirish")
    elif role == "teacher":
        markup.add("➕ O'quvchi qo'shish", "📝 Test qo'shish")
        markup.add("👨‍🎓 O'quvchilarim", "📋 Testlarim")
        markup.add("📅 Davomatni ochish", "📊 Davomat hisoboti")
        markup.add("📚 Uy vazifalari")
    elif role == "student":
        markup.add("📝 Testlarni ko'rish", "📊 Natijalarim")
        markup.add("✅ Keldim", "📚 Uy vazifa topshirish")
        markup.add("ℹ️ Profilim")
    return markup

# ==================== /start ====================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    uid = str(user_id)
    db = load_db()

    if user_id in ADMIN_IDS:
        if uid not in db["users"]:
            db["users"][uid] = {"name": message.from_user.full_name, "phone": "Admin", "role": "admin"}
            save_db(db)
        bot.send_message(message.chat.id,
            "👋 Xush kelibsiz, <b>Admin</b>!\n\nQuyidagi paneldan foydalaning:",
            parse_mode="HTML", reply_markup=main_menu(user_id))
        return

    if uid in db["users"]:
        role = get_user_role(user_id)
        role_text = {"teacher": "O'qituvchi", "student": "O'quvchi"}.get(role, "Foydalanuvchi")
        bot.send_message(message.chat.id,
            f"👋 Qaytib keldingiz, <b>{db['users'][uid]['name']}</b>!\n🎭 Rolingiz: {role_text}",
            parse_mode="HTML", reply_markup=main_menu(user_id))
        return

    user_states[user_id] = "waiting_fullname"
    bot.send_message(message.chat.id,
        "🇩🇪 <b>Nemis tili o'rgatuvchi botga xush kelibsiz!</b>\n\n"
        "✍️ Ism va Familyangizni kiriting:\n<i>Masalan: Ali Valiyev</i>",
        parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())

# ==================== RO'YXATDAN O'TISH ====================
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_fullname")
def get_fullname(message):
    user_id = message.from_user.id
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        bot.send_message(message.chat.id,
            "⚠️ Iltimos <b>Ism va Familyangizni</b> to'liq kiriting!\n<i>Masalan: Ali Valiyev</i>",
            parse_mode="HTML")
        return
    user_data[user_id] = {"name": full_name}
    user_states[user_id] = "waiting_phone"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
    bot.send_message(message.chat.id,
        f"✅ Ism: <b>{full_name}</b>\n\n📱 Telefon raqamingizni yuboring yoki qo'lda kiriting:",
        parse_mode="HTML", reply_markup=markup)

@bot.message_handler(content_types=["contact"],
                     func=lambda m: user_states.get(m.from_user.id) == "waiting_phone")
def get_contact(message):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    process_phone_login(message, phone)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_phone" and m.content_type == "text")
def get_phone_text(message):
    if message.text == "🔄 Qayta urinish":
        bot.send_message(message.chat.id, "📱 Telefon raqamingizni kiriting:")
        return
    process_phone_login(message, message.text.strip())

def process_phone_login(message, phone):
    user_id = message.from_user.id
    uid = str(user_id)
    db = load_db()
    full_name = user_data.get(user_id, {}).get("name", message.from_user.full_name)

    def phones_match(p1, p2):
        return p1.replace(" ","").replace("-","").lstrip("+") == p2.replace(" ","").replace("-","").lstrip("+")

    found_role = None
    found_id = None

    for sid, s in db["students"].items():
        if phones_match(s.get("phone", ""), phone):
            found_role = "student"
            found_id = sid
            break

    if not found_role:
        for tid, t in db["teachers"].items():
            if phones_match(t.get("phone", ""), phone):
                found_role = "teacher"
                found_id = tid
                break

    if found_role == "student":
        db["students"][found_id]["telegram_id"] = uid
        db["students"][found_id]["name"] = full_name
        db["users"][uid] = {"name": full_name, "phone": phone, "role": "student"}
        teacher_id = db["students"][found_id].get("teacher_id")
        if teacher_id and teacher_id in db["teachers"]:
            if found_id not in db["teachers"][teacher_id]["students"]:
                db["teachers"][teacher_id]["students"].append(found_id)
        save_db(db)
        del user_states[user_id]
        if user_id in user_data:
            del user_data[user_id]
        teacher_name = db["teachers"].get(teacher_id, {}).get("name", "Biriktirilmagan") if teacher_id else "Biriktirilmagan"
        bot.send_message(message.chat.id,
            f"🎉 <b>Xush kelibsiz, {full_name}!</b>\n\n✅ Hisobingiz topildi!\n"
            f"🎭 Rol: <b>O'quvchi</b>\n👨‍🏫 O'qituvchi: <b>{teacher_name}</b>",
            parse_mode="HTML", reply_markup=main_menu(user_id))

    elif found_role == "teacher":
        db["teachers"][found_id]["telegram_id"] = uid
        db["teachers"][found_id]["name"] = full_name
        db["users"][uid] = {"name": full_name, "phone": phone, "role": "teacher"}
        save_db(db)
        del user_states[user_id]
        if user_id in user_data:
            del user_data[user_id]
        bot.send_message(message.chat.id,
            f"🎉 <b>Xush kelibsiz, {full_name}!</b>\n\n✅ Hisobingiz topildi!\n🎭 Rol: <b>O'qituvchi</b>",
            parse_mode="HTML", reply_markup=main_menu(user_id))

    else:
        bot.send_message(message.chat.id,
            f"❌ <b>Kechirasiz, {full_name}!</b>\n\n📱 <b>{phone}</b> raqami bazada topilmadi.\n\n"
            "O'qituvchingiz yoki admindan ro'yxatga kiritishini so'rang.",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔄 Qayta urinish"))
        user_states[user_id] = "waiting_phone"

# ==================== ADMIN PANEL ====================
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id in ADMIN_IDS)
def admin_stats(message):
    db = load_db()
    bot.send_message(message.chat.id,
        f"📊 <b>Statistika:</b>\n\n"
        f"👨‍🏫 O'qituvchilar: <b>{len(db['teachers'])}</b>\n"
        f"👨‍🎓 O'quvchilar: <b>{len(db['students'])}</b>\n"
        f"📝 Testlar: <b>{len(db['tests'])}</b>",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👨‍🏫 O'qituvchilar" and m.from_user.id in ADMIN_IDS)
def admin_teachers(message):
    db = load_db()
    if not db["teachers"]:
        bot.send_message(message.chat.id, "📭 Hali o'qituvchilar yo'q.")
        return
    text = "👨‍🏫 <b>O'qituvchilar ro'yxati:</b>\n\n"
    for i, (tid, t) in enumerate(db["teachers"].items(), 1):
        text += f"{i}. <b>{t['name']}</b> | 📱 {t['phone']}\n   👨‍🎓 O'quvchilar: {len(t.get('students',[]))} ta\n\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👨‍🎓 O'quvchilar" and m.from_user.id in ADMIN_IDS)
def admin_students(message):
    db = load_db()
    if not db["students"]:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilar yo'q.")
        return
    text = "👨‍🎓 <b>O'quvchilar ro'yxati:</b>\n\n"
    for i, (sid, s) in enumerate(db["students"].items(), 1):
        teacher = db["teachers"].get(s.get("teacher_id",""), {}).get("name", "Biriktirilmagan")
        text += f"{i}. <b>{s['name']}</b> | 📱 {s['phone']}\n   👨‍🏫 {teacher}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== ADMIN: O'QITUVCHI QO'SHISH ====================
@bot.message_handler(func=lambda m: m.text == "➕ O'qituvchi qo'shish" and m.from_user.id in ADMIN_IDS)
def admin_add_teacher(message):
    user_states[message.from_user.id] = "admin_add_teacher_name"
    user_data[message.from_user.id] = {}
    bot.send_message(message.chat.id,
        "👨‍🏫 <b>Yangi o'qituvchi qo'shish</b>\n\n👤 O'qituvchining ism familyasini kiriting:\n<i>Masalan: Jasur Karimov</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "admin_add_teacher_name")
def admin_add_teacher_name(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    name = message.text.strip()
    if len(name.split()) < 2:
        bot.send_message(message.chat.id,
            "⚠️ Iltimos <b>Ism va Familyani</b> to'liq kiriting!\n<i>Masalan: Jasur Karimov</i>",
            parse_mode="HTML")
        return
    user_data[message.from_user.id]["name"] = name
    user_states[message.from_user.id] = "admin_add_teacher_phone"
    bot.send_message(message.chat.id,
        f"✅ Ism familya: <b>{name}</b>\n\n📱 Telefon raqamini kiriting:\n<i>Masalan: +998901234567</i>",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "admin_add_teacher_phone")
def admin_add_teacher_phone(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    phone = message.text.strip()
    name = user_data[uid]["name"]
    db = load_db()

    # Telefon raqami allaqachon bormi?
    for tid, t in db["teachers"].items():
        existing = t.get("phone","").replace(" ","").replace("-","").lstrip("+")
        new_p = phone.replace(" ","").replace("-","").lstrip("+")
        if existing == new_p:
            bot.send_message(message.chat.id,
                f"⚠️ Bu telefon raqam allaqachon bazada bor!\n👨‍🏫 <b>{t['name']}</b>",
                parse_mode="HTML")
            return

    new_id = f"teacher_{len(db['teachers'])+1}"
    db["teachers"][new_id] = {
        "name": name,
        "phone": phone,
        "students": [],
        "tests": []
    }
    db["users"][new_id] = {"name": name, "phone": phone, "role": "teacher"}
    save_db(db)
    del user_states[uid]
    if uid in user_data:
        del user_data[uid]
    bot.send_message(message.chat.id,
        f"✅ <b>O'qituvchi muvaffaqiyatli qo'shildi!</b>\n\n"
        f"👤 Ism familya: <b>{name}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n\n"
        f"ℹ️ O'qituvchi /start bosib, ushbu raqam bilan ro'yxatdan o'tishi kerak.",
        parse_mode="HTML", reply_markup=main_menu(uid))

# ==================== ADMIN: O'QUVCHI QO'SHISH ====================
@bot.message_handler(func=lambda m: m.text == "➕ O'quvchi qo'shish" and m.from_user.id in ADMIN_IDS)
def admin_add_student(message):
    user_states[message.from_user.id] = "admin_add_student"
    user_data[message.from_user.id] = {}
    bot.send_message(message.chat.id,
        "👨‍🎓 <b>Yangi o'quvchi qo'shish</b>\n\n👤 O'quvchining ismini kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "admin_add_student")
def admin_add_student_name(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    user_data[message.from_user.id]["name"] = message.text.strip()
    user_states[message.from_user.id] = "admin_add_student_phone"
    bot.send_message(message.chat.id,
        f"✅ Ism: <b>{message.text.strip()}</b>\n\n📱 Telefon raqamini kiriting:",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "admin_add_student_phone")
def admin_add_student_phone(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    db = load_db()
    name = user_data[uid]["name"]
    phone = message.text.strip()
    if not db["teachers"]:
        new_id = f"adm_{len(db['students'])+1}"
        db["students"][new_id] = {"name": name, "phone": phone, "teacher_id": None}
        db["users"][new_id] = {"name": name, "phone": phone, "role": "student"}
        save_db(db)
        del user_states[uid]
        bot.send_message(message.chat.id,
            f"✅ <b>{name}</b> qo'shildi!\n📱 {phone}\n⚠️ O'qituvchi yo'q, keyinroq biriktiring.",
            parse_mode="HTML", reply_markup=main_menu(uid))
        return
    user_data[uid]["phone"] = phone
    user_states[uid] = "admin_add_student_teacher"
    markup = types.InlineKeyboardMarkup()
    for tid, t in db["teachers"].items():
        markup.add(types.InlineKeyboardButton(f"👨‍🏫 {t['name']}", callback_data=f"asgn_t_{tid}"))
    markup.add(types.InlineKeyboardButton("➖ O'qituvchisiz qo'shish", callback_data="asgn_t_none"))
    bot.send_message(message.chat.id,
        f"✅ Tel: <b>{phone}</b>\n\n👨‍🏫 O'qituvchini tanlang:",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("asgn_t_") and user_states.get(c.from_user.id) == "admin_add_student_teacher")
def admin_assign_teacher_new(call):
    uid = call.from_user.id
    db = load_db()
    name = user_data[uid]["name"]
    phone = user_data[uid]["phone"]
    tid = call.data.replace("asgn_t_", "")
    teacher_id = None if tid == "none" else tid
    new_id = f"adm_{len(db['students'])+1}"
    db["students"][new_id] = {"name": name, "phone": phone, "teacher_id": teacher_id}
    db["users"][new_id] = {"name": name, "phone": phone, "role": "student"}
    if teacher_id and teacher_id in db["teachers"]:
        db["teachers"][teacher_id]["students"].append(new_id)
    save_db(db)
    teacher_name = db["teachers"][teacher_id]["name"] if teacher_id else "Biriktirilmagan"
    del user_states[uid]
    bot.edit_message_text(
        f"✅ <b>{name}</b> muvaffaqiyatli qo'shildi!\n📱 {phone}\n👨‍🏫 O'qituvchi: {teacher_name}",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")
    bot.send_message(call.message.chat.id, "Bosh menyu:", reply_markup=main_menu(uid))

# --- O'quvchini o'qituvchiga biriktirish ---
@bot.message_handler(func=lambda m: m.text == "🔗 O'quvchini biriktirish" and m.from_user.id in ADMIN_IDS)
def admin_assign_start(message):
    db = load_db()
    if not db["students"]:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilar yo'q.")
        return
    if not db["teachers"]:
        bot.send_message(message.chat.id, "📭 Hali o'qituvchilar yo'q.")
        return
    markup = types.InlineKeyboardMarkup()
    for sid, s in db["students"].items():
        tid = s.get("teacher_id")
        teacher_name = db["teachers"].get(tid,{}).get("name","Biriktirilmagan") if tid else "Biriktirilmagan"
        markup.add(types.InlineKeyboardButton(
            f"👨‍🎓 {s['name']} | 👨‍🏫 {teacher_name}", callback_data=f"apick_s_{sid}"))
    bot.send_message(message.chat.id,
        "👨‍🎓 <b>Qaysi o'quvchini biriktirmoqchisiz?</b>",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("apick_s_"))
def admin_assign_pick_student(call):
    sid = call.data.replace("apick_s_", "")
    db = load_db()
    student = db["students"].get(sid)
    if not student:
        bot.answer_callback_query(call.id, "O'quvchi topilmadi!")
        return
    markup = types.InlineKeyboardMarkup()
    for tid, t in db["teachers"].items():
        is_current = student.get("teacher_id") == tid
        label = f"{'✅ ' if is_current else ''}👨‍🏫 {t['name']} | {t['phone']}"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"ado_{sid}_{tid}"))
    markup.add(types.InlineKeyboardButton("❌ Biriktirishni bekor qilish", callback_data=f"ado_{sid}_none"))
    bot.edit_message_text(
        f"👨‍🎓 O'quvchi: <b>{student['name']}</b>\n\n👨‍🏫 Qaysi o'qituvchiga biriktirasiz?",
        call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ado_"))
def admin_assign_do(call):
    parts = call.data.split("_")
    sid = parts[1]
    new_tid = parts[2]
    db = load_db()
    student = db["students"].get(sid)
    if not student:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    old_tid = student.get("teacher_id")
    if old_tid and old_tid in db["teachers"]:
        if sid in db["teachers"][old_tid]["students"]:
            db["teachers"][old_tid]["students"].remove(sid)
    if new_tid == "none":
        db["students"][sid]["teacher_id"] = None
        save_db(db)
        bot.edit_message_text(f"✅ <b>{student['name']}</b> hech qaysi o'qituvchiga biriktirilmadi.",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        return
    db["students"][sid]["teacher_id"] = new_tid
    if sid not in db["teachers"][new_tid]["students"]:
        db["teachers"][new_tid]["students"].append(sid)
    save_db(db)
    teacher_name = db["teachers"][new_tid]["name"]
    bot.edit_message_text(
        f"✅ <b>{student['name']}</b> → <b>{teacher_name}</b> ga biriktirildi!",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")
    tg_id = student.get("telegram_id")
    if tg_id:
        try:
            bot.send_message(int(tg_id),
                f"🎉 <b>{student['name']}</b>, siz <b>{teacher_name}</b> o'qituvchisiga biriktirildiingiz!",
                parse_mode="HTML")
        except:
            pass

# --- O'qituvchini o'chirish ---
@bot.message_handler(func=lambda m: m.text == "🗑 O'qituvchini o'chirish" and m.from_user.id in ADMIN_IDS)
def admin_delete_teacher_list(message):
    db = load_db()
    if not db["teachers"]:
        bot.send_message(message.chat.id, "📭 Hali o'qituvchilar yo'q.")
        return
    markup = types.InlineKeyboardMarkup()
    for tid, t in db["teachers"].items():
        markup.add(types.InlineKeyboardButton(f"🗑 {t['name']} | {t['phone']}", callback_data=f"del_t_{tid}"))
    bot.send_message(message.chat.id,
        "👨‍🏫 <b>Qaysi o'qituvchini o'chirmoqchisiz?</b>",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_t_"))
def confirm_delete_teacher(call):
    tid = call.data.replace("del_t_", "")
    db = load_db()
    teacher = db["teachers"].get(tid)
    if not teacher:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"cdt_{tid}"),
        types.InlineKeyboardButton("❌ Bekor", callback_data="cancel_del"))
    bot.edit_message_text(
        f"⚠️ <b>Rostdan ham o'chirasizmi?</b>\n\n👨‍🏫 {teacher['name']}\n📱 {teacher['phone']}",
        call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cdt_"))
def do_delete_teacher(call):
    tid = call.data.replace("cdt_", "")
    db = load_db()
    teacher = db["teachers"].get(tid)
    if not teacher:
        return
    for sid in teacher.get("students", []):
        if sid in db["students"]:
            db["students"][sid]["teacher_id"] = None
    db["tests"] = [t for t in db["tests"] if t["teacher_id"] != tid]
    del db["teachers"][tid]
    if tid in db["users"]:
        del db["users"][tid]
    save_db(db)
    bot.edit_message_text(f"✅ <b>{teacher['name']}</b> o'chirildi!",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")

# --- O'quvchini o'chirish ---
@bot.message_handler(func=lambda m: m.text == "🗑 O'quvchini o'chirish" and m.from_user.id in ADMIN_IDS)
def admin_delete_student_list(message):
    db = load_db()
    if not db["students"]:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilar yo'q.")
        return
    markup = types.InlineKeyboardMarkup()
    for sid, s in db["students"].items():
        markup.add(types.InlineKeyboardButton(f"🗑 {s['name']} | {s['phone']}", callback_data=f"del_s_{sid}"))
    bot.send_message(message.chat.id, "👨‍🎓 <b>Qaysi o'quvchini o'chirmoqchisiz?</b>",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_s_"))
def confirm_delete_student(call):
    sid = call.data.replace("del_s_", "")
    db = load_db()
    student = db["students"].get(sid)
    if not student:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"cds_{sid}"),
        types.InlineKeyboardButton("❌ Bekor", callback_data="cancel_del"))
    bot.edit_message_text(
        f"⚠️ <b>Rostdan ham o'chirasizmi?</b>\n\n👨‍🎓 {student['name']}\n📱 {student['phone']}",
        call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("cds_"))
def do_delete_student(call):
    sid = call.data.replace("cds_", "")
    db = load_db()
    student = db["students"].get(sid)
    if not student:
        return
    tid = student.get("teacher_id")
    if tid and tid in db["teachers"]:
        if sid in db["teachers"][tid]["students"]:
            db["teachers"][tid]["students"].remove(sid)
    if sid in db.get("results", {}):
        del db["results"][sid]
    del db["students"][sid]
    if sid in db["users"]:
        del db["users"][sid]
    save_db(db)
    bot.edit_message_text(f"✅ <b>{student['name']}</b> o'chirildi!",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_del")
def cancel_delete(call):
    bot.edit_message_text("❌ Bekor qilindi.", call.message.chat.id, call.message.message_id)

# ==================== O'QITUVCHI: O'QUVCHI QO'SHISH ====================
@bot.message_handler(func=lambda m: m.text == "➕ O'quvchi qo'shish" and get_user_role(m.from_user.id) == "teacher")
def teacher_add_student(message):
    user_states[message.from_user.id] = "t_add_s_name"
    user_data[message.from_user.id] = {}
    bot.send_message(message.chat.id,
        "👨‍🎓 <b>Yangi o'quvchi qo'shish</b>\n\n👤 O'quvchining ismini kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "t_add_s_name")
def teacher_add_student_name(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    user_data[message.from_user.id]["name"] = message.text.strip()
    user_states[message.from_user.id] = "t_add_s_phone"
    bot.send_message(message.chat.id,
        f"✅ Ism: <b>{message.text.strip()}</b>\n\n📱 Telefon raqamini kiriting:",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "t_add_s_phone")
def teacher_add_student_phone(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    real_id, _ = get_real_id(uid)
    tid = real_id or str(uid)
    db = load_db()
    name = user_data[uid]["name"]
    phone = message.text.strip()
    new_sid = f"t{tid}_s{len(db['students'])+1}"
    db["students"][new_sid] = {"name": name, "phone": phone, "teacher_id": tid}
    db["users"][new_sid] = {"name": name, "phone": phone, "role": "student"}
    if tid in db["teachers"]:
        db["teachers"][tid]["students"].append(new_sid)
    save_db(db)
    del user_states[uid]
    if uid in user_data:
        del user_data[uid]
    bot.send_message(message.chat.id,
        f"✅ <b>{name}</b> o'quvchi sifatida qo'shildi!\n📱 Tel: <b>{phone}</b>",
        parse_mode="HTML", reply_markup=main_menu(uid))

@bot.message_handler(func=lambda m: m.text == "👨‍🎓 O'quvchilarim" and get_user_role(m.from_user.id) == "teacher")
def teacher_my_students(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    tid = real_id or str(message.from_user.id)
    student_ids = db["teachers"].get(tid, {}).get("students", [])
    if not student_ids:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilaringiz yo'q.")
        return
    text = "👨‍🎓 <b>Mening o'quvchilarim:</b>\n\n"
    for i, sid in enumerate(student_ids, 1):
        s = db["students"].get(sid, {})
        text += f"{i}. <b>{s.get('name','?')}</b> | 📱 {s.get('phone','?')}\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== TEST QO'SHISH ====================
@bot.message_handler(func=lambda m: m.text == "📝 Test qo'shish" and get_user_role(m.from_user.id) == "teacher")
def teacher_add_test(message):
    user_states[message.from_user.id] = "test_topic"
    user_data[message.from_user.id] = {"questions": []}
    bot.send_message(message.chat.id,
        "📝 <b>Yangi test qo'shish</b>\n\nTest mavzusini kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Bekor qilish"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "test_topic")
def test_get_topic(message):
    if message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    user_data[message.from_user.id]["topic"] = message.text.strip()
    user_states[message.from_user.id] = "test_question"
    bot.send_message(message.chat.id,
        f"✅ Mavzu: <b>{message.text.strip()}</b>\n\n❓ 1-savolni kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Bekor qilish"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "test_question")
def test_get_question(message):
    if message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    user_data[message.from_user.id]["current_question"] = message.text.strip()
    user_data[message.from_user.id]["current_options"] = []
    user_states[message.from_user.id] = "test_options"
    bot.send_message(message.chat.id,
        f"❓ Savol: <b>{message.text.strip()}</b>\n\n📌 1-variantni kiriting (A):",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "test_options")
def test_get_options(message):
    uid = message.from_user.id
    user_data[uid]["current_options"].append(message.text.strip())
    count = len(user_data[uid]["current_options"])
    if count < 4:
        labels = ["B", "C", "D"]
        bot.send_message(message.chat.id, f"{count+1}-variantni kiriting ({labels[count-1]}):")
    else:
        user_states[uid] = "test_answer"
        opts = user_data[uid]["current_options"]
        text = "✅ Variantlar:\n"
        for i, o in enumerate(opts):
            text += f"  {'ABCD'[i]}) {o}\n"
        text += "\n🎯 To'g'ri javob harfini kiriting:"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("A", "B", "C", "D")
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "test_answer")
def test_get_answer(message):
    uid = message.from_user.id
    answer = message.text.strip().upper()
    if answer not in ["A", "B", "C", "D"]:
        bot.send_message(message.chat.id, "❌ Faqat A, B, C yoki D kiriting!")
        return
    q = {
        "question": user_data[uid]["current_question"],
        "options": user_data[uid]["current_options"],
        "answer": answer
    }
    user_data[uid]["questions"].append(q)
    user_states[uid] = "test_more"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Yana savol qo'shish", "✅ Testni saqlash")
    bot.send_message(message.chat.id,
        f"✅ Savol saqlandi! Jami: <b>{len(user_data[uid]['questions'])} ta savol</b>\n\nDavom etasizmi?",
        parse_mode="HTML", reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "test_more")
def test_more_or_save(message):
    uid = message.from_user.id
    if message.text == "➕ Yana savol qo'shish":
        user_states[uid] = "test_question"
        qn = len(user_data[uid]["questions"]) + 1
        bot.send_message(message.chat.id, f"❓ {qn}-savolni kiriting:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Bekor qilish"))
    elif message.text == "✅ Testni saqlash":
        db = load_db()
        real_id, _ = get_real_id(uid)
        teacher_id = real_id or str(uid)
        test = {
            "id": len(db["tests"]) + 1,
            "topic": user_data[uid]["topic"],
            "teacher_id": teacher_id,
            "teacher_name": db["teachers"].get(teacher_id, {}).get("name", ""),
            "questions": user_data[uid]["questions"]
        }
        db["tests"].append(test)
        db["teachers"][teacher_id].setdefault("tests", []).append(test["id"])
        save_db(db)
        del user_states[uid]
        del user_data[uid]
        bot.send_message(message.chat.id,
            f"🎉 Test saqlandi!\n\n📚 Mavzu: <b>{test['topic']}</b>\n❓ Savollar: <b>{len(test['questions'])} ta</b>",
            parse_mode="HTML", reply_markup=main_menu(uid))

@bot.message_handler(func=lambda m: m.text == "📋 Testlarim" and get_user_role(m.from_user.id) == "teacher")
def teacher_my_tests(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    teacher_id = real_id or str(message.from_user.id)
    my_tests = [t for t in db["tests"] if t["teacher_id"] == teacher_id]
    if not my_tests:
        bot.send_message(message.chat.id, "📭 Hali testlaringiz yo'q.")
        return
    text = "📋 <b>Mening testlarim:</b>\n\n"
    for t in my_tests:
        text += f"🔹 #{t['id']} — <b>{t['topic']}</b> ({len(t['questions'])} ta savol)\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== O'QUVCHI: TEST ====================
@bot.message_handler(func=lambda m: m.text == "📝 Testlarni ko'rish" and get_user_role(m.from_user.id) == "student")
def student_view_tests(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    sid = real_id or str(message.from_user.id)
    teacher_id = db["students"].get(sid, {}).get("teacher_id")
    if not teacher_id:
        bot.send_message(message.chat.id, "⚠️ Siz hali hech qaysi o'qituvchiga biriktirilmagansiz.")
        return
    my_tests = [t for t in db["tests"] if t["teacher_id"] == teacher_id]
    if not my_tests:
        bot.send_message(message.chat.id, "📭 O'qituvchingiz hali test qo'shmagan.")
        return
    markup = types.InlineKeyboardMarkup()
    for t in my_tests:
        markup.add(types.InlineKeyboardButton(
            f"📝 {t['topic']} ({len(t['questions'])} savol)", callback_data=f"take_test_{t['id']}"))
    bot.send_message(message.chat.id, "📚 <b>Mavjud testlar:</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("take_test_"))
def start_test(call):
    test_id = int(call.data.split("_")[-1])
    db = load_db()
    test = next((t for t in db["tests"] if t["id"] == test_id), None)
    if not test:
        bot.answer_callback_query(call.id, "Test topilmadi!")
        return
    user_data[call.from_user.id] = {"test_id": test_id, "current_q": 0, "score": 0, "answers": []}
    user_states[call.from_user.id] = "taking_test"
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        f"📝 <b>{test['topic']}</b> testi boshlanmoqda!\nJami: {len(test['questions'])} ta savol",
        parse_mode="HTML")
    send_question(call.from_user.id, call.message.chat.id, test, 0)

def send_question(user_id, chat_id, test, q_index):
    q = test["questions"][q_index]
    markup = types.InlineKeyboardMarkup()
    for i, opt in enumerate(q["options"]):
        markup.add(types.InlineKeyboardButton(
            f"{'ABCD'[i]}) {opt}", callback_data=f"ans_{test['id']}_{q_index}_{'ABCD'[i]}"))
    bot.send_message(chat_id,
        f"❓ <b>Savol {q_index+1}/{len(test['questions'])}:</b>\n\n{q['question']}",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ans_"))
def answer_question(call):
    parts = call.data.split("_")
    test_id = int(parts[1])
    q_index = int(parts[2])
    chosen = parts[3]
    uid = call.from_user.id
    db = load_db()
    test = next((t for t in db["tests"] if t["id"] == test_id), None)
    correct = test["questions"][q_index]["answer"]
    user_data[uid]["answers"].append(chosen)
    if chosen == correct:
        user_data[uid]["score"] += 1
        bot.answer_callback_query(call.id, "✅ To'g'ri!")
    else:
        bot.answer_callback_query(call.id, f"❌ Noto'g'ri! To'g'ri javob: {correct}")
    next_q = q_index + 1
    if next_q < len(test["questions"]):
        user_data[uid]["current_q"] = next_q
        send_question(uid, call.message.chat.id, test, next_q)
    else:
        score = user_data[uid]["score"]
        total = len(test["questions"])
        percent = round(score / total * 100)
        real_id, _ = get_real_id(uid)
        sid = real_id or str(uid)
        if "results" not in db:
            db["results"] = {}
        if sid not in db["results"]:
            db["results"][sid] = []
        db["results"][sid].append({"test_id": test_id, "topic": test["topic"],
            "score": score, "total": total, "percent": percent})
        save_db(db)
        del user_states[uid]
        del user_data[uid]
        emoji = "🏆" if percent >= 80 else "👍" if percent >= 50 else "📚"
        bot.send_message(call.message.chat.id,
            f"{emoji} <b>Test yakunlandi!</b>\n\n📚 {test['topic']}\n✅ To'g'ri: {score}/{total}\n📊 Natija: {percent}%",
            parse_mode="HTML", reply_markup=main_menu(uid))

@bot.message_handler(func=lambda m: m.text == "📊 Natijalarim" and get_user_role(m.from_user.id) == "student")
def student_results(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    sid = real_id or str(message.from_user.id)
    results = db.get("results", {}).get(sid, [])
    if not results:
        bot.send_message(message.chat.id, "📭 Siz hali hech qanday test topshirmagansiz.")
        return
    text = "📊 <b>Mening natijalarim:</b>\n\n"
    for i, r in enumerate(results, 1):
        emoji = "🏆" if r["percent"] >= 80 else "👍" if r["percent"] >= 50 else "📚"
        text += f"{i}. {r['topic']}: {emoji} {r['score']}/{r['total']} ({r['percent']}%)\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "ℹ️ Profilim" and get_user_role(m.from_user.id) == "student")
def student_profile(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    sid = real_id or str(message.from_user.id)
    s = db["students"].get(sid, {})
    teacher = db["teachers"].get(s.get("teacher_id",""), {})
    results = db.get("results", {}).get(sid, [])
    bot.send_message(message.chat.id,
        f"ℹ️ <b>Mening profilim:</b>\n\n"
        f"👤 Ism: <b>{s.get('name','?')}</b>\n"
        f"📱 Tel: <b>{s.get('phone','?')}</b>\n"
        f"👨‍🏫 O'qituvchi: <b>{teacher.get('name','Biriktirilmagan')}</b>\n"
        f"📝 Topshirilgan testlar: <b>{len(results)} ta</b>",
        parse_mode="HTML")

# ==================== DAVOMAT ====================
@bot.message_handler(func=lambda m: m.text == "📅 Davomatni ochish" and get_user_role(m.from_user.id) == "teacher")
def teacher_open_attendance(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    tid = real_id or str(message.from_user.id)
    student_ids = db["teachers"].get(tid, {}).get("students", [])
    if not student_ids:
        bot.send_message(message.chat.id, "📭 O'quvchilaringiz yo'q.")
        return
    d = today()
    if "attendance" not in db:
        db["attendance"] = {}
    if d not in db["attendance"]:
        db["attendance"][d] = {}
    db["attendance"][d][tid] = {"open": True, "records": {}}
    save_db(db)
    sent = 0
    for sid in student_ids:
        tg_id = db["students"].get(sid, {}).get("telegram_id")
        if not tg_id:
            continue
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Keldim", callback_data=f"att_came_{tid}_{d}"),
                types.InlineKeyboardButton("❌ Kelmadim", callback_data=f"att_absent_{tid}_{d}"))
            bot.send_message(int(tg_id),
                f"📅 <b>Bugungi davomat ochildi!</b>\n📆 {d}\n\nKeldingizmi?",
                parse_mode="HTML", reply_markup=markup)
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id,
        f"✅ <b>Davomat ochildi!</b>\n📆 {d}\n📨 {sent} ta o'quvchiga xabar yuborildi.",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "✅ Keldim" and get_user_role(m.from_user.id) == "student")
def student_came_btn(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    sid = real_id or str(message.from_user.id)
    tid = db["students"].get(sid, {}).get("teacher_id")
    d = today()
    if not tid or "attendance" not in db or d not in db["attendance"] or tid not in db["attendance"][d]:
        bot.send_message(message.chat.id, "⚠️ Hozirda davomat ochilmagan.")
        return
    if sid in db["attendance"][d][tid]["records"]:
        bot.send_message(message.chat.id, "✅ Siz allaqachon belgilagansiz.")
        return
    db["attendance"][d][tid]["records"][sid] = {"status": "came", "confirmed": False}
    save_db(db)
    bot.send_message(message.chat.id, "✅ O'qituvchingiz tasdiqlashini kuting.")
    s_name = db["students"].get(sid, {}).get("name", "?")
    t_tg = db["teachers"].get(tid, {}).get("telegram_id") or tid
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"att_confirm_{sid}_{d}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"att_reject_{sid}_{d}"))
    try:
        bot.send_message(int(t_tg),
            f"📍 <b>{s_name}</b> \"Keldim\" dedi!\n📆 {d}\n\nTasdiqlaysizmi?",
            parse_mode="HTML", reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("att_came_") or c.data.startswith("att_absent_"))
def student_attendance_inline(call):
    parts = call.data.split("_", 3)
    action = parts[1]
    tid = parts[2]
    d = parts[3]
    uid = call.from_user.id
    real_id, _ = get_real_id(uid)
    sid = real_id or str(uid)
    db = load_db()
    if "attendance" not in db or d not in db["attendance"] or tid not in db["attendance"][d]:
        bot.answer_callback_query(call.id, "Davomat topilmadi!")
        return
    if sid in db["attendance"][d][tid]["records"]:
        bot.answer_callback_query(call.id, "Siz allaqachon javob bergansiz!")
        return
    if action == "came":
        db["attendance"][d][tid]["records"][sid] = {"status": "came", "confirmed": False}
        save_db(db)
        bot.edit_message_text("✅ Yaxshi! O'qituvchingiz tasdiqlashini kuting.",
            call.message.chat.id, call.message.message_id)
        s_name = db["students"].get(sid, {}).get("name", "?")
        t_tg = db["teachers"].get(tid, {}).get("telegram_id") or tid
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"att_confirm_{sid}_{d}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"att_reject_{sid}_{d}"))
        try:
            bot.send_message(int(t_tg),
                f"📍 <b>{s_name}</b> \"Keldim\" dedi!\n📆 {d}\n\nTasdiqlaysizmi?",
                parse_mode="HTML", reply_markup=markup)
        except:
            pass
    else:
        db["attendance"][d][tid]["records"][sid] = {"status": "absent", "confirmed": True, "reason": ""}
        save_db(db)
        user_states[uid] = f"att_reason_{tid}_{d}"
        bot.edit_message_text("❌ Sabab yozing:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("att_reason_"))
def student_write_reason(message):
    uid = message.from_user.id
    parts = user_states[uid].split("_")
    tid = parts[2]
    d = parts[3]
    real_id, _ = get_real_id(uid)
    sid = real_id or str(uid)
    db = load_db()
    db["attendance"][d][tid]["records"][sid]["reason"] = message.text.strip()
    save_db(db)
    del user_states[uid]
    bot.send_message(message.chat.id, f"📝 Sabab qabul qilindi: <b>{message.text.strip()}</b>", parse_mode="HTML")
    s_name = db["students"].get(sid, {}).get("name", "?")
    t_tg = db["teachers"].get(tid, {}).get("telegram_id") or tid
    try:
        bot.send_message(int(t_tg),
            f"❌ <b>{s_name}</b> kelmadi!\n📆 {d}\n📝 Sabab: {message.text.strip()}",
            parse_mode="HTML")
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("att_confirm_") or c.data.startswith("att_reject_"))
def teacher_confirm_attendance(call):
    parts = call.data.split("_", 3)
    action = parts[1]
    sid = parts[2]
    d = parts[3]
    real_id, _ = get_real_id(call.from_user.id)
    tid = real_id or str(call.from_user.id)
    db = load_db()
    s_name = db["students"].get(sid, {}).get("name", "?")
    s_tg = db["students"].get(sid, {}).get("telegram_id")
    if action == "confirm":
        db["attendance"][d][tid]["records"][sid]["confirmed"] = True
        save_db(db)
        bot.edit_message_text(f"✅ <b>{s_name}</b> — KELDI",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        if s_tg:
            try:
                bot.send_message(int(s_tg), "✅ O'qituvchingiz davomatingizni tasdiqladi!")
            except:
                pass
    else:
        db["attendance"][d][tid]["records"][sid] = {"status": "absent", "confirmed": True, "reason": "Ustoz rad etdi"}
        save_db(db)
        bot.edit_message_text(f"❌ <b>{s_name}</b> — KELMADI",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
        if s_tg:
            user_states[int(s_tg)] = f"att_reason_{tid}_{d}"
            try:
                bot.send_message(int(s_tg), "❌ O'qituvchingiz davomatingizni rad etdi.\n📝 Sabab yozing:")
            except:
                pass

@bot.message_handler(func=lambda m: m.text == "📊 Davomat hisoboti" and get_user_role(m.from_user.id) == "teacher")
def teacher_attendance_report(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    tid = real_id or str(message.from_user.id)
    attendance = db.get("attendance", {})
    dates = sorted([d for d in attendance if tid in attendance[d]], reverse=True)[:7]
    if not dates:
        bot.send_message(message.chat.id, "📭 Hali davomat ochilmagan.")
        return
    text = "📊 <b>Davomat hisoboti:</b>\n\n"
    for d in dates:
        records = attendance[d][tid].get("records", {})
        came = sum(1 for r in records.values() if r.get("status") == "came" and r.get("confirmed"))
        absent = sum(1 for r in records.values() if r.get("status") == "absent")
        text += f"📆 <b>{d}</b>: ✅ {came} keldi | ❌ {absent} kelmadi\n"
        for sid, r in records.items():
            if r.get("status") == "absent":
                s_name = db["students"].get(sid, {}).get("name", "?")
                text += f"   └ ❌ {s_name}: {r.get('reason','sabab ko\'rsatilmagan')}\n"
        text += "\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== UY VAZIFA ====================
@bot.message_handler(func=lambda m: m.text == "📚 Uy vazifalari" and get_user_role(m.from_user.id) == "teacher")
def teacher_homework_list(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Yangi uy vazifa berish", callback_data="hw_new"))
    markup.add(types.InlineKeyboardButton("📋 Topshirilganlarni ko'rish", callback_data="hw_view_submissions"))
    bot.send_message(message.chat.id, "📚 <b>Uy vazifalar:</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "hw_new")
def teacher_new_homework(call):
    user_states[call.from_user.id] = "hw_title"
    user_data[call.from_user.id] = {}
    bot.send_message(call.message.chat.id,
        "📚 <b>Yangi uy vazifa</b>\n\nVazifa sarlavhasini kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Bekor qilish"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "hw_title")
def hw_get_title(message):
    if message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    user_data[message.from_user.id]["title"] = message.text.strip()
    user_states[message.from_user.id] = "hw_desc"
    bot.send_message(message.chat.id,
        f"✅ Sarlavha: <b>{message.text.strip()}</b>\n\nVazifa mazmunini kiriting:",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "hw_desc")
def hw_get_desc(message):
    if message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    user_data[message.from_user.id]["desc"] = message.text.strip()
    user_states[message.from_user.id] = "hw_deadline"
    bot.send_message(message.chat.id, "📅 Topshirish muddatini kiriting (masalan: 2025-01-20):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "hw_deadline")
def hw_get_deadline(message):
    if message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    db = load_db()
    real_id, _ = get_real_id(uid)
    tid = real_id or str(uid)
    if "homeworks" not in db:
        db["homeworks"] = {}
    hw_id = f"hw_{len(db['homeworks'])+1}_{today()}"
    title = user_data[uid]["title"]
    desc = user_data[uid]["desc"]
    db["homeworks"][hw_id] = {
        "id": hw_id, "title": title, "desc": desc,
        "deadline": message.text.strip(), "teacher_id": tid,
        "created": today(), "submissions": {}
    }
    save_db(db)
    del user_states[uid]
    student_ids = db["teachers"].get(tid, {}).get("students", [])
    sent = 0
    for sid in student_ids:
        tg_id = db["students"].get(sid, {}).get("telegram_id")
        if not tg_id:
            continue
        try:
            bot.send_message(int(tg_id),
                f"📚 <b>Yangi uy vazifa!</b>\n\n📌 <b>{title}</b>\n📝 {desc}\n⏰ Muddat: {message.text.strip()}\n\n"
                "\"📚 Uy vazifa topshirish\" tugmasini bosing!",
                parse_mode="HTML")
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id,
        f"✅ <b>Uy vazifa yuborildi!</b>\n📌 {title}\n📨 {sent} ta o'quvchiga xabar ketdi.",
        parse_mode="HTML", reply_markup=main_menu(uid))
    if uid in user_data:
        del user_data[uid]

@bot.callback_query_handler(func=lambda c: c.data == "hw_view_submissions")
def teacher_view_submissions(call):
    db = load_db()
    real_id, _ = get_real_id(call.from_user.id)
    tid = real_id or str(call.from_user.id)
    homeworks = {k: v for k, v in db.get("homeworks", {}).items() if v.get("teacher_id") == tid}
    if not homeworks:
        bot.answer_callback_query(call.id, "Vazifalar yo'q!")
        return
    markup = types.InlineKeyboardMarkup()
    for hw_id, hw in homeworks.items():
        markup.add(types.InlineKeyboardButton(
            f"📋 {hw['title']} ({len(hw.get('submissions',{}))} topshirdi)",
            callback_data=f"hw_subs_{hw_id}"))
    bot.send_message(call.message.chat.id, "📋 <b>Qaysi vazifani ko'rmoqchisiz?</b>",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("hw_subs_"))
def teacher_hw_submissions_detail(call):
    hw_id = call.data.replace("hw_subs_", "")
    db = load_db()
    hw = db.get("homeworks", {}).get(hw_id)
    if not hw:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    real_id, _ = get_real_id(call.from_user.id)
    tid = real_id or str(call.from_user.id)
    subs = hw.get("submissions", {})
    all_students = db["teachers"].get(tid, {}).get("students", [])
    text = f"📚 <b>{hw['title']}</b>\n⏰ {hw['deadline']}\n✅ {len(subs)}/{len(all_students)} topshirdi\n\n"
    for sid in all_students:
        s_name = db["students"].get(sid, {}).get("name", "?")
        if sid in subs:
            sub = subs[sid]
            text += f"✅ {s_name} — {sub.get('date','')}\n"
            if sub.get("text"):
                text += f"   📝 {sub['text'][:80]}\n"
            if sub.get("file"):
                text += f"   📎 Fayl\n"
        else:
            text += f"❌ {s_name} — topshirmagan\n"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "📚 Uy vazifa topshirish" and get_user_role(m.from_user.id) == "student")
def student_submit_homework(message):
    db = load_db()
    real_id, _ = get_real_id(message.from_user.id)
    sid = real_id or str(message.from_user.id)
    tid = db["students"].get(sid, {}).get("teacher_id")
    if not tid:
        bot.send_message(message.chat.id, "⚠️ O'qituvchingiz biriktirilmagan.")
        return
    homeworks = [hw for hw in db.get("homeworks", {}).values() if hw.get("teacher_id") == tid]
    if not homeworks:
        bot.send_message(message.chat.id, "📭 Hozirda uy vazifa yo'q.")
        return
    markup = types.InlineKeyboardMarkup()
    for hw in homeworks:
        already = sid in hw.get("submissions", {})
        markup.add(types.InlineKeyboardButton(
            f"{'✅' if already else '📝'} {hw['title']} (muddat: {hw['deadline']})",
            callback_data=f"submit_hw_{hw['id']}"))
    bot.send_message(message.chat.id, "📚 <b>Qaysi vazifani topshirmoqchisiz?</b>",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("submit_hw_"))
def student_select_homework(call):
    hw_id = call.data.replace("submit_hw_", "")
    db = load_db()
    hw = db.get("homeworks", {}).get(hw_id)
    if not hw:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    user_states[call.from_user.id] = f"submitting_hw_{hw_id}"
    bot.send_message(call.message.chat.id,
        f"📚 <b>{hw['title']}</b>\n📝 {hw['desc']}\n⏰ {hw['deadline']}\n\nJavobingizni yozing yoki fayl/rasm yuboring:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Bekor qilish"))

@bot.message_handler(
    content_types=["text", "document", "photo"],
    func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("submitting_hw_"))
def student_hw_answer(message):
    if message.content_type == "text" and message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    hw_id = user_states[uid].replace("submitting_hw_", "")
    real_id, _ = get_real_id(uid)
    sid = real_id or str(uid)
    db = load_db()
    hw = db.get("homeworks", {}).get(hw_id)
    if not hw:
        bot.send_message(message.chat.id, "Xato yuz berdi.")
        return
    submission = {"date": today(), "text": "", "file": None}
    if message.content_type == "text":
        submission["text"] = message.text.strip()
    elif message.content_type == "document":
        submission["file"] = message.document.file_id
        submission["text"] = message.caption or ""
    elif message.content_type == "photo":
        submission["file"] = message.photo[-1].file_id
        submission["text"] = message.caption or ""
    db["homeworks"][hw_id]["submissions"][sid] = submission
    save_db(db)
    del user_states[uid]
    bot.send_message(message.chat.id,
        f"✅ <b>Uy vazifa topshirildi!</b>\n📌 {hw['title']}\n📅 {today()}",
        parse_mode="HTML", reply_markup=main_menu(uid))
    s_name = db["students"].get(sid, {}).get("name", "?")
    tid = hw["teacher_id"]
    t_tg = db["teachers"].get(tid, {}).get("telegram_id") or tid
    try:
        if submission["file"] and message.content_type == "photo":
            bot.send_photo(int(t_tg), submission["file"],
                caption=f"📚 <b>{s_name}</b> uy vazifa topshirdi!\n📌 {hw['title']}\n📝 {submission['text']}",
                parse_mode="HTML")
        elif submission["file"]:
            bot.send_document(int(t_tg), submission["file"],
                caption=f"📚 <b>{s_name}</b> uy vazifa topshirdi!\n📌 {hw['title']}\n📝 {submission['text']}",
                parse_mode="HTML")
        else:
            bot.send_message(int(t_tg),
                f"📚 <b>{s_name}</b> uy vazifa topshirdi!\n📌 {hw['title']}\n📝 {submission['text']}",
                parse_mode="HTML")
    except:
        pass

# ==================== NOMA'LUM XABAR ====================
@bot.message_handler(func=lambda m: True)
def unknown(message):
    role = get_user_role(message.from_user.id)
    if role:
        bot.send_message(message.chat.id, "❓ Tugmalardan foydalaning.", reply_markup=main_menu(message.from_user.id))
    else:
        bot.send_message(message.chat.id, "Iltimos /start bosing.")

# ==================== ISHGA TUSHIRISH ====================
if __name__ == "__main__":
    try:
        bot.remove_webhook()
        bot.close()
    except:
        pass

    time.sleep(3)

    t = Thread(target=run_server)
    t.daemon = True
    t.start()
    time.sleep(1)

    print("🚀 Bot Render'da 24/7 rejimida ishga tushdi!")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)