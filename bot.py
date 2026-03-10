import telebot
from telebot import types
import json
import os

# ==================== SOZLAMALAR ====================
BOT_TOKEN = ("8721836937:AAEfOxXl64VA6DXBR_SYwtWywu8UMZeOwlQ" ) # @BotFather dan olgan tokeningiz
ADMIN_IDS = [7384088509]  # O'z Telegram ID ingizni kiriting

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== DATABASE ====================
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},      # barcha foydalanuvchilar
        "teachers": {},   # o'qituvchilar
        "students": {},   # o'quvchilar
        "tests": [],      # testlar
        "results": {}     # natijalar
    }

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Vaqtinchalik ma'lumotlar (FSM o'rniga)
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
    return None

def main_menu(user_id):
    role = get_user_role(user_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "admin":
        markup.add("👨‍🏫 O'qituvchilar", "👨‍🎓 O'quvchilar")
        markup.add("➕ O'quvchi qo'shish", "📊 Statistika")
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

    # Admin
    if user_id in ADMIN_IDS:
        if uid not in db["users"]:
            db["users"][uid] = {"name": message.from_user.full_name, "phone": "Admin", "role": "admin"}
            save_db(db)
        bot.send_message(message.chat.id,
            "👋 Xush kelibsiz, <b>Admin</b>!\n\n"
            "Quyidagi paneldan foydalaning:",
            parse_mode="HTML",
            reply_markup=main_menu(user_id))
        return

    # Ro'yxatdan o'tgan foydalanuvchi
    if uid in db["users"]:
        role = get_user_role(user_id)
        role_text = {"teacher": "O'qituvchi", "student": "O'quvchi"}.get(role, "Foydalanuvchi")
        bot.send_message(message.chat.id,
            f"👋 Qaytib keldingiz, <b>{db['users'][uid]['name']}</b>!\n"
            f"🎭 Rolingiz: {role_text}",
            parse_mode="HTML",
            reply_markup=main_menu(user_id))
        return

    # Yangi foydalanuvchi - ism so'rash
    user_states[user_id] = "waiting_name"
    bot.send_message(message.chat.id,
        "🇩🇪 <b>Nemis tili o'rgatuvchi botga xush kelibsiz!</b>\n\n"
        "Ro'yxatdan o'tish uchun:\n"
        "👤 Ismingizni kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove())

# ==================== RO'YXATDAN O'TISH ====================
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_name")
def get_name(message):
    user_id = message.from_user.id
    user_data[user_id] = {"name": message.text.strip()}
    user_states[user_id] = "waiting_phone"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
    bot.send_message(message.chat.id,
        f"✅ Ism saqlandi: <b>{message.text.strip()}</b>\n\n"
        "📱 Telefon raqamingizni yuboring:",
        parse_mode="HTML",
        reply_markup=markup)

@bot.message_handler(content_types=["contact"],
                     func=lambda m: user_states.get(m.from_user.id) == "waiting_phone")
def get_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    user_data[user_id]["phone"] = phone
    user_states[user_id] = "choosing_role"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👨‍🎓 O'quvchi", "👨‍🏫 O'qituvchi")
    bot.send_message(message.chat.id,
        f"✅ Raqam saqlandi: <b>{phone}</b>\n\n"
        "🎭 Rolingizni tanlang:",
        parse_mode="HTML",
        reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_phone" and m.content_type == "text")
def get_phone_text(message):
    user_id = message.from_user.id
    phone = message.text.strip()
    user_data[user_id]["phone"] = phone
    user_states[user_id] = "choosing_role"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👨‍🎓 O'quvchi", "👨‍🏫 O'qituvchi")
    bot.send_message(message.chat.id,
        f"✅ Raqam saqlandi: <b>{phone}</b>\n\n"
        "🎭 Rolingizni tanlang:",
        parse_mode="HTML",
        reply_markup=markup)

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "choosing_role")
def choose_role(message):
    user_id = message.from_user.id
    uid = str(user_id)
    db = load_db()

    name = user_data[user_id]["name"]
    phone = user_data[user_id]["phone"]

    if message.text == "👨‍🎓 O'quvchi":
        db["users"][uid] = {"name": name, "phone": phone, "role": "student"}
        db["students"][uid] = {"name": name, "phone": phone, "teacher_id": None}
        save_db(db)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
            f"👤 Ism: <b>{name}</b>\n"
            f"📱 Raqam: <b>{phone}</b>\n"
            f"🎭 Rol: <b>O'quvchi</b>",
            parse_mode="HTML",
            reply_markup=main_menu(user_id))

    elif message.text == "👨‍🏫 O'qituvchi":
        db["users"][uid] = {"name": name, "phone": phone, "role": "teacher"}
        db["teachers"][uid] = {"name": name, "phone": phone, "students": [], "tests": []}
        save_db(db)
        del user_states[user_id]
        bot.send_message(message.chat.id,
            f"🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
            f"👤 Ism: <b>{name}</b>\n"
            f"📱 Raqam: <b>{phone}</b>\n"
            f"🎭 Rol: <b>O'qituvchi</b>",
            parse_mode="HTML",
            reply_markup=main_menu(user_id))
    else:
        bot.send_message(message.chat.id, "❗ Iltimos, tugmalardan birini tanlang.")

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
        text += f"{i}. {t['name']} | 📱 {t['phone']} | ID: <code>{tid}</code>\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👨‍🎓 O'quvchilar" and m.from_user.id in ADMIN_IDS)
def admin_students(message):
    db = load_db()
    if not db["students"]:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilar yo'q.")
        return
    text = "👨‍🎓 <b>O'quvchilar ro'yxati:</b>\n\n"
    for i, (sid, s) in enumerate(db["students"].items(), 1):
        text += f"{i}. {s['name']} | 📱 {s['phone']}\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "➕ O'quvchi qo'shish" and m.from_user.id in ADMIN_IDS)
def admin_add_student(message):
    db = load_db()
    user_states[message.from_user.id] = "admin_add_student"
    user_data[message.from_user.id] = {}
    bot.send_message(message.chat.id,
        "👨‍🎓 <b>Yangi o'quvchi qo'shish</b>\n\n"
        "👤 O'quvchining ismini kiriting:",
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

    # O'qituvchilar ro'yxatini ko'rsatish
    if not db["teachers"]:
        # O'qituvchisiz ham qo'shish
        new_id = f"adm_{len(db['students'])+1}"
        db["students"][new_id] = {"name": name, "phone": phone, "teacher_id": None}
        db["users"][new_id] = {"name": name, "phone": phone, "role": "student"}
        save_db(db)
        del user_states[uid]
        bot.send_message(message.chat.id,
            f"✅ <b>{name}</b> o'quvchi qo'shildi!\n📱 {phone}\n⚠️ O'qituvchi yo'q, keyinroq biriktiring.",
            parse_mode="HTML", reply_markup=main_menu(uid))
        return

    user_data[uid]["phone"] = phone
    user_states[uid] = "admin_add_student_teacher"
    markup = types.InlineKeyboardMarkup()
    for tid, t in db["teachers"].items():
        markup.add(types.InlineKeyboardButton(f"👨‍🏫 {t['name']}", callback_data=f"assign_teacher_{tid}"))
    markup.add(types.InlineKeyboardButton("➖ O'qituvchisiz qo'shish", callback_data="assign_teacher_none"))
    bot.send_message(message.chat.id,
        f"✅ Tel: <b>{phone}</b>\n\n👨‍🏫 O'qituvchini tanlang:",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("assign_teacher_") and user_states.get(c.from_user.id) == "admin_add_student_teacher")
def admin_assign_teacher(call):
    uid = call.from_user.id
    db = load_db()
    name = user_data[uid]["name"]
    phone = user_data[uid]["phone"]
    tid = call.data.replace("assign_teacher_", "")
    teacher_id = None if tid == "none" else tid

    new_id = f"adm_{len(db['students'])+1}_{uid}"
    db["students"][new_id] = {"name": name, "phone": phone, "teacher_id": teacher_id}
    db["users"][new_id] = {"name": name, "phone": phone, "role": "student"}
    if teacher_id and teacher_id in db["teachers"]:
        db["teachers"][teacher_id]["students"].append(new_id)
    save_db(db)

    teacher_name = db["teachers"][teacher_id]["name"] if teacher_id else "Biriktirilmagan"
    del user_states[uid]
    bot.edit_message_text(
        f"✅ <b>{name}</b> o'quvchi muvaffaqiyatli qo'shildi!\n\n"
        f"📱 Tel: {phone}\n👨‍🏫 O'qituvchi: {teacher_name}",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")
    bot.send_message(call.message.chat.id, "Bosh menyu:", reply_markup=main_menu(uid))

# ==================== O'QITUVCHINI O'CHIRISH ====================
@bot.message_handler(func=lambda m: m.text == "🗑 O'qituvchini o'chirish" and m.from_user.id in ADMIN_IDS)
def admin_delete_teacher_list(message):
    db = load_db()
    if not db["teachers"]:
        bot.send_message(message.chat.id, "📭 Hali o'qituvchilar yo'q.")
        return
    markup = types.InlineKeyboardMarkup()
    for tid, t in db["teachers"].items():
        markup.add(types.InlineKeyboardButton(
            f"🗑 {t['name']} | {t['phone']}",
            callback_data=f"del_teacher_{tid}"
        ))
    bot.send_message(message.chat.id,
        "👨‍🏫 <b>Qaysi o'qituvchini o'chirmoqchisiz?</b>\n\n⚠️ O'chirilgan o'qituvchining barcha testlari ham o'chadi!",
        parse_mode="HTML",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_teacher_"))
def confirm_delete_teacher(call):
    tid = call.data.replace("del_teacher_", "")
    db = load_db()
    teacher = db["teachers"].get(tid)
    if not teacher:
        bot.answer_callback_query(call.id, "O'qituvchi topilmadi!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_del_teacher_{tid}"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_del")
    )
    bot.edit_message_text(
        f"⚠️ <b>Rostdan ham o'chirasizmi?</b>\n\n"
        f"👨‍🏫 {teacher['name']}\n"
        f"📱 {teacher['phone']}\n"
        f"👨‍🎓 O'quvchilar: {len(teacher.get('students', []))} ta",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_del_teacher_"))
def do_delete_teacher(call):
    tid = call.data.replace("confirm_del_teacher_", "")
    db = load_db()
    teacher = db["teachers"].get(tid)
    if not teacher:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    name = teacher["name"]
    # O'quvchilardan teacher_id ni tozalash
    for sid in teacher.get("students", []):
        if sid in db["students"]:
            db["students"][sid]["teacher_id"] = None
    # O'qituvchi testlarini o'chirish
    db["tests"] = [t for t in db["tests"] if t["teacher_id"] != tid]
    # O'qituvchini o'chirish
    del db["teachers"][tid]
    if tid in db["users"]:
        del db["users"][tid]
    save_db(db)
    bot.edit_message_text(
        f"✅ <b>{name}</b> o'qituvchi muvaffaqiyatli o'chirildi!\n"
        f"📝 Uning testlari ham o'chirildi.",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")
    try:
        bot.send_message(int(tid), "⚠️ Sizning o'qituvchi hisobingiz admin tomonidan o'chirildi.")
    except:
        pass

# ==================== O'QUVCHINI O'CHIRISH ====================
@bot.message_handler(func=lambda m: m.text == "🗑 O'quvchini o'chirish" and m.from_user.id in ADMIN_IDS)
def admin_delete_student_list(message):
    db = load_db()
    if not db["students"]:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilar yo'q.")
        return
    markup = types.InlineKeyboardMarkup()
    for sid, s in db["students"].items():
        teacher_name = db["teachers"].get(s.get("teacher_id",""), {}).get("name", "—")
        markup.add(types.InlineKeyboardButton(
            f"🗑 {s['name']} | {teacher_name}",
            callback_data=f"del_student_{sid}"
        ))
    bot.send_message(message.chat.id,
        "👨‍🎓 <b>Qaysi o'quvchini o'chirmoqchisiz?</b>",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_student_"))
def confirm_delete_student(call):
    sid = call.data.replace("del_student_", "")
    db = load_db()
    student = db["students"].get(sid)
    if not student:
        bot.answer_callback_query(call.id, "O'quvchi topilmadi!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_del_student_{sid}"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_del")
    )
    bot.edit_message_text(
        f"⚠️ <b>Rostdan ham o'chirasizmi?</b>\n\n"
        f"👨‍🎓 {student['name']}\n"
        f"📱 {student['phone']}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_del_student_"))
def do_delete_student(call):
    sid = call.data.replace("confirm_del_student_", "")
    db = load_db()
    student = db["students"].get(sid)
    if not student:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    name = student["name"]
    # O'qituvchi ro'yxatidan o'chirish
    tid = student.get("teacher_id")
    if tid and tid in db["teachers"]:
        if sid in db["teachers"][tid]["students"]:
            db["teachers"][tid]["students"].remove(sid)
    # Natijalarni o'chirish
    if sid in db.get("results", {}):
        del db["results"][sid]
    del db["students"][sid]
    if sid in db["users"]:
        del db["users"][sid]
    save_db(db)
    bot.edit_message_text(
        f"✅ <b>{name}</b> o'quvchi muvaffaqiyatli o'chirildi!",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")
    try:
        bot.send_message(int(sid), "⚠️ Sizning o'quvchi hisobingiz admin tomonidan o'chirildi.")
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data == "cancel_del")
def cancel_delete(call):
    bot.edit_message_text("❌ Bekor qilindi.", call.message.chat.id, call.message.message_id)

# ==================== ADMIN O'QITUVCHI QO'SHISH ====================
@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "admin_add_teacher")
def admin_add_teacher_id(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga qaytdingiz.", reply_markup=main_menu(message.from_user.id))
        return
    try:
        teacher_id = str(int(message.text.strip()))
        db = load_db()
        if teacher_id in db["teachers"]:
            bot.send_message(message.chat.id, "⚠️ Bu foydalanuvchi allaqachon o'qituvchi!")
        elif teacher_id in db["users"]:
            db["users"][teacher_id]["role"] = "teacher"
            if teacher_id not in db["teachers"]:
                db["teachers"][teacher_id] = {
                    "name": db["users"][teacher_id]["name"],
                    "phone": db["users"][teacher_id]["phone"],
                    "students": [],
                    "tests": []
                }
            save_db(db)
            bot.send_message(message.chat.id, f"✅ O'qituvchi muvaffaqiyatli qo'shildi!")
            try:
                bot.send_message(int(teacher_id), "🎉 Siz o'qituvchi sifatida tasdiqlndingiz! /start bosing.")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ Bu ID bilan foydalanuvchi topilmadi. Avval botga /start bosishi kerak.")
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bosh menyu:", reply_markup=main_menu(message.from_user.id))
    except:
        bot.send_message(message.chat.id, "❌ Noto'g'ri ID. Faqat raqam kiriting.")

# ==================== O'QITUVCHI PANEL ====================
@bot.message_handler(func=lambda m: m.text == "➕ O'quvchi qo'shish" and get_user_role(m.from_user.id) == "teacher")
def teacher_add_student(message):
    user_states[message.from_user.id] = "teacher_add_student_id"
    bot.send_message(message.chat.id,
        "👨‍🎓 O'quvchi qo'shish uchun uning <b>Telegram ID</b>sini kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga"))

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "teacher_add_student_id")
def teacher_add_student_id(message):
    if message.text == "🔙 Orqaga":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "🔙 Orqaga.", reply_markup=main_menu(message.from_user.id))
        return
    try:
        student_id = str(int(message.text.strip()))
        db = load_db()
        teacher_id = str(message.from_user.id)
        if student_id not in db["students"]:
            bot.send_message(message.chat.id, "❌ Bu ID bilan o'quvchi topilmadi. Avval botga /start bosishi kerak.")
        elif student_id in db["teachers"][teacher_id]["students"]:
            bot.send_message(message.chat.id, "⚠️ Bu o'quvchi allaqachon sizning ro'yxatingizda!")
        else:
            db["teachers"][teacher_id]["students"].append(student_id)
            db["students"][student_id]["teacher_id"] = teacher_id
            save_db(db)
            bot.send_message(message.chat.id,
                f"✅ <b>{db['students'][student_id]['name']}</b> o'quvchi sifatida qo'shildi!",
                parse_mode="HTML")
            try:
                bot.send_message(int(student_id),
                    f"🎉 Siz <b>{db['teachers'][teacher_id]['name']}</b> o'qituvchisining o'quvchisi sifatida qo'shildingiz!",
                    parse_mode="HTML")
            except:
                pass
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bosh menyu:", reply_markup=main_menu(message.from_user.id))
    except:
        bot.send_message(message.chat.id, "❌ Noto'g'ri ID. Faqat raqam kiriting.")

@bot.message_handler(func=lambda m: m.text == "👨‍🎓 O'quvchilarim" and get_user_role(m.from_user.id) == "teacher")
def teacher_my_students(message):
    db = load_db()
    teacher_id = str(message.from_user.id)
    student_ids = db["teachers"][teacher_id]["students"]
    if not student_ids:
        bot.send_message(message.chat.id, "📭 Hali o'quvchilaringiz yo'q.")
        return
    text = "👨‍🎓 <b>Mening o'quvchilarim:</b>\n\n"
    for i, sid in enumerate(student_ids, 1):
        s = db["students"].get(sid, {})
        text += f"{i}. {s.get('name','?')} | 📱 {s.get('phone','?')}\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== TEST QO'SHISH ====================
@bot.message_handler(func=lambda m: m.text == "📝 Test qo'shish" and get_user_role(m.from_user.id) == "teacher")
def teacher_add_test(message):
    user_states[message.from_user.id] = "test_topic"
    user_data[message.from_user.id] = {"questions": []}
    bot.send_message(message.chat.id,
        "📝 <b>Yangi test qo'shish</b>\n\n"
        "Test mavzusini kiriting (masalan: Nemis tilida salomlashish):",
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
        f"✅ Mavzu: <b>{message.text.strip()}</b>\n\n"
        "❓ 1-savolni kiriting:",
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
        f"❓ Savol: <b>{message.text.strip()}</b>\n\n"
        "📌 Variantlarni birin-ketin kiriting (A, B, C, D uchun 4 ta variant).\n"
        "1-variantni kiriting:",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "test_options")
def test_get_options(message):
    uid = message.from_user.id
    user_data[uid]["current_options"].append(message.text.strip())
    count = len(user_data[uid]["current_options"])
    if count < 4:
        bot.send_message(message.chat.id, f"{count+1}-variantni kiriting:")
    else:
        user_states[uid] = "test_answer"
        opts = user_data[uid]["current_options"]
        text = "✅ Variantlar saqlandi:\n"
        for i, o in enumerate(opts):
            text += f"  {'ABCD'[i]}) {o}\n"
        text += "\n🎯 To'g'ri javob harfini kiriting (A, B, C yoki D):"
        bot.send_message(message.chat.id, text)

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
        f"✅ Savol saqlandi! Jami: <b>{len(user_data[uid]['questions'])} ta savol</b>\n\n"
        "Davom etasizmi?",
        parse_mode="HTML",
        reply_markup=markup)

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
        teacher_id = str(uid)
        test = {
            "id": len(db["tests"]) + 1,
            "topic": user_data[uid]["topic"],
            "teacher_id": teacher_id,
            "teacher_name": db["teachers"][teacher_id]["name"],
            "questions": user_data[uid]["questions"]
        }
        db["tests"].append(test)
        if test["id"] not in db["teachers"][teacher_id].get("tests", []):
            db["teachers"][teacher_id].setdefault("tests", []).append(test["id"])
        save_db(db)
        del user_states[uid]
        del user_data[uid]
        bot.send_message(message.chat.id,
            f"🎉 Test muvaffaqiyatli saqlandi!\n\n"
            f"📚 Mavzu: <b>{test['topic']}</b>\n"
            f"❓ Savollar soni: <b>{len(test['questions'])} ta</b>",
            parse_mode="HTML",
            reply_markup=main_menu(uid))

# ==================== TESTLAR RO'YXATI (O'QITUVCHI) ====================
@bot.message_handler(func=lambda m: m.text == "📋 Testlarim" and get_user_role(m.from_user.id) == "teacher")
def teacher_my_tests(message):
    db = load_db()
    teacher_id = str(message.from_user.id)
    my_tests = [t for t in db["tests"] if t["teacher_id"] == teacher_id]
    if not my_tests:
        bot.send_message(message.chat.id, "📭 Hali testlaringiz yo'q.")
        return
    text = "📋 <b>Mening testlarim:</b>\n\n"
    for t in my_tests:
        text += f"🔹 #{t['id']} — {t['topic']} ({len(t['questions'])} ta savol)\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== O'QUVCHI PANEL ====================
@bot.message_handler(func=lambda m: m.text == "📝 Testlarni ko'rish" and get_user_role(m.from_user.id) == "student")
def student_view_tests(message):
    db = load_db()
    student_id = str(message.from_user.id)
    teacher_id = db["students"][student_id].get("teacher_id")
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
            f"📝 {t['topic']} ({len(t['questions'])} savol)",
            callback_data=f"take_test_{t['id']}"
        ))
    bot.send_message(message.chat.id, "📚 <b>Mavjud testlar:</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("take_test_"))
def start_test(call):
    test_id = int(call.data.split("_")[-1])
    db = load_db()
    test = next((t for t in db["tests"] if t["id"] == test_id), None)
    if not test:
        bot.answer_callback_query(call.id, "Test topilmadi!")
        return
    user_data[call.from_user.id] = {
        "test_id": test_id,
        "current_q": 0,
        "score": 0,
        "answers": []
    }
    user_states[call.from_user.id] = "taking_test"
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        f"📝 <b>{test['topic']}</b> testi boshlanmoqda!\n"
        f"Jami: {len(test['questions'])} ta savol",
        parse_mode="HTML")
    send_question(call.from_user.id, call.message.chat.id, test, 0)

def send_question(user_id, chat_id, test, q_index):
    q = test["questions"][q_index]
    markup = types.InlineKeyboardMarkup()
    for i, opt in enumerate(q["options"]):
        markup.add(types.InlineKeyboardButton(
            f"{'ABCD'[i]}) {opt}",
            callback_data=f"ans_{test['id']}_{q_index}_{'ABCD'[i]}"
        ))
    bot.send_message(chat_id,
        f"❓ <b>Savol {q_index+1}/{len(test['questions'])}:</b>\n\n{q['question']}",
        parse_mode="HTML",
        reply_markup=markup)

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
        # Test tugadi
        score = user_data[uid]["score"]
        total = len(test["questions"])
        percent = round(score / total * 100)

        # Natijani saqlash
        sid = str(uid)
        if "results" not in db:
            db["results"] = {}
        if sid not in db["results"]:
            db["results"][sid] = []
        db["results"][sid].append({
            "test_id": test_id,
            "topic": test["topic"],
            "score": score,
            "total": total,
            "percent": percent
        })
        save_db(db)

        del user_states[uid]
        del user_data[uid]

        emoji = "🏆" if percent >= 80 else "👍" if percent >= 50 else "📚"
        bot.send_message(call.message.chat.id,
            f"{emoji} <b>Test yakunlandi!</b>\n\n"
            f"📚 Mavzu: {test['topic']}\n"
            f"✅ To'g'ri: {score}/{total}\n"
            f"📊 Natija: {percent}%",
            parse_mode="HTML",
            reply_markup=main_menu(uid))

@bot.message_handler(func=lambda m: m.text == "📊 Natijalarim" and get_user_role(m.from_user.id) == "student")
def student_results(message):
    db = load_db()
    sid = str(message.from_user.id)
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
    sid = str(message.from_user.id)
    s = db["students"][sid]
    teacher = db["teachers"].get(s.get("teacher_id", ""), {})
    results = db.get("results", {}).get(sid, [])
    bot.send_message(message.chat.id,
        f"ℹ️ <b>Mening profilim:</b>\n\n"
        f"👤 Ism: <b>{s['name']}</b>\n"
        f"📱 Tel: <b>{s['phone']}</b>\n"
        f"👨‍🏫 O'qituvchi: <b>{teacher.get('name', 'Biriktirilmagan')}</b>\n"
        f"📝 Topshirilgan testlar: <b>{len(results)} ta</b>",
        parse_mode="HTML")

# ==================== DAVOMAT ====================
from datetime import date

def today():
    return str(date.today())

# --- USTOZ: Davomatni ochish ---
@bot.message_handler(func=lambda m: m.text == "📅 Davomatni ochish" and get_user_role(m.from_user.id) == "teacher")
def teacher_open_attendance(message):
    db = load_db()
    tid = str(message.from_user.id)
    student_ids = db["teachers"][tid].get("students", [])
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

    # O'quvchilarga xabar yuborish
    sent = 0
    for sid in student_ids:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ Keldim", callback_data=f"att_came_{tid}_{d}"),
                types.InlineKeyboardButton("❌ Kelmadim", callback_data=f"att_absent_{tid}_{d}")
            )
            bot.send_message(int(sid),
                f"📅 <b>Bugungi davomat ochildi!</b>\n"
                f"📆 Sana: {d}\n\n"
                f"Keldingizmi?",
                parse_mode="HTML", reply_markup=markup)
            sent += 1
        except:
            pass

    bot.send_message(message.chat.id,
        f"✅ <b>Davomat ochildi!</b>\n📆 {d}\n📨 {sent} ta o'quvchiga xabar yuborildi.\n\n"
        f"O'quvchilar \"Keldim\" yoki \"Kelmadim\" bosadi, siz tasdiqlaysiz.",
        parse_mode="HTML")

# --- O'QUVCHI: Keldim tugmasi (reply keyboard orqali) ---
@bot.message_handler(func=lambda m: m.text == "✅ Keldim" and get_user_role(m.from_user.id) == "student")
def student_came_btn(message):
    db = load_db()
    sid = str(message.from_user.id)
    tid = db["students"][sid].get("teacher_id")
    d = today()
    if not tid or "attendance" not in db or d not in db["attendance"] or tid not in db["attendance"][d]:
        bot.send_message(message.chat.id, "⚠️ Hozirda davomat ochilmagan. O'qituvchingizni kuting.")
        return
    rec = db["attendance"][d][tid]["records"].get(sid)
    if rec and rec.get("status") == "came":
        bot.send_message(message.chat.id, "✅ Siz allaqachon \"Keldim\" deb belgilagansiz. Tasdiqlash kutilmoqda.")
        return
    db["attendance"][d][tid]["records"][sid] = {"status": "came", "confirmed": False}
    save_db(db)
    bot.send_message(message.chat.id, "✅ Yaxshi! O'qituvchingiz tasdiqlashini kuting.")
    # Ustozga xabar
    s_name = db["students"][sid]["name"]
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"att_confirm_{sid}_{d}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"att_reject_{sid}_{d}")
    )
    try:
        bot.send_message(int(tid),
            f"📍 <b>{s_name}</b> \"Keldim\" dedi!\n📆 {d}\n\nTasdiqlaysizmi?",
            parse_mode="HTML", reply_markup=markup)
    except:
        pass

# --- O'QUVCHI: Inline Keldim/Kelmadim ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("att_came_") or c.data.startswith("att_absent_"))
def student_attendance_inline(call):
    parts = call.data.split("_")
    action = parts[1]  # came yoki absent
    tid = parts[2]
    d = parts[3]
    sid = str(call.from_user.id)
    db = load_db()

    if "attendance" not in db or d not in db["attendance"] or tid not in db["attendance"][d]:
        bot.answer_callback_query(call.id, "Davomat topilmadi!")
        return

    rec = db["attendance"][d][tid]["records"].get(sid)
    if rec:
        bot.answer_callback_query(call.id, "Siz allaqachon javob bergansiz!")
        return

    if action == "came":
        db["attendance"][d][tid]["records"][sid] = {"status": "came", "confirmed": False}
        save_db(db)
        bot.edit_message_text("✅ Yaxshi! O'qituvchingiz tasdiqlashini kuting.", call.message.chat.id, call.message.message_id)
        s_name = db["students"][sid]["name"]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"att_confirm_{sid}_{d}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"att_reject_{sid}_{d}")
        )
        try:
            bot.send_message(int(tid),
                f"📍 <b>{s_name}</b> \"Keldim\" dedi!\n📆 {d}\n\nTasdiqlaysizmi?",
                parse_mode="HTML", reply_markup=markup)
        except:
            pass
    else:
        # Kelmadim - sabab so'rash
        db["attendance"][d][tid]["records"][sid] = {"status": "absent", "confirmed": True, "reason": ""}
        save_db(db)
        user_states[call.from_user.id] = f"att_reason_{tid}_{d}"
        bot.edit_message_text("❌ Sabab yozing (masalan: kasal, shaxsiy):", call.message.chat.id, call.message.message_id)

# --- O'QUVCHI: Sabab yozish ---
@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("att_reason_"))
def student_write_reason(message):
    uid = message.from_user.id
    state_val = user_states[uid]
    parts = state_val.split("_")
    tid = parts[2]
    d = parts[3]
    sid = str(uid)
    db = load_db()
    db["attendance"][d][tid]["records"][sid]["reason"] = message.text.strip()
    save_db(db)
    del user_states[uid]
    bot.send_message(message.chat.id, f"📝 Sabab qabul qilindi: <b>{message.text.strip()}</b>", parse_mode="HTML")
    # Ustozga xabar
    s_name = db["students"][sid]["name"]
    try:
        bot.send_message(int(tid),
            f"❌ <b>{s_name}</b> kelmadi!\n📆 {d}\n📝 Sabab: {message.text.strip()}",
            parse_mode="HTML")
    except:
        pass

# --- USTOZ: Tasdiqlash / Rad etish ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("att_confirm_") or c.data.startswith("att_reject_"))
def teacher_confirm_attendance(call):
    parts = call.data.split("_")
    action = parts[1]  # confirm yoki reject
    sid = parts[2]
    d = parts[3]
    tid = str(call.from_user.id)
    db = load_db()

    if d not in db.get("attendance", {}) or tid not in db["attendance"][d]:
        bot.answer_callback_query(call.id, "Davomat topilmadi!")
        return

    s_name = db["students"].get(sid, {}).get("name", "Noma'lum")
    rec = db["attendance"][d][tid]["records"].get(sid, {})

    if action == "confirm":
        db["attendance"][d][tid]["records"][sid]["confirmed"] = True
        save_db(db)
        bot.edit_message_text(f"✅ <b>{s_name}</b> tasdiqlandi — KELDI", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        try:
            bot.send_message(int(sid), "✅ O'qituvchingiz davomatingizni tasdiqladi!")
        except:
            pass
    else:
        db["attendance"][d][tid]["records"][sid] = {"status": "absent", "confirmed": True, "reason": "Ustoz rad etdi"}
        save_db(db)
        bot.edit_message_text(f"❌ <b>{s_name}</b> — KELMADI (rad etildi)", call.message.chat.id, call.message.message_id, parse_mode="HTML")
        user_states[int(sid)] = f"att_reason_{tid}_{d}"
        try:
            bot.send_message(int(sid), "❌ O'qituvchingiz davomatingizni rad etdi.\n📝 Iltimos, sabab yozing:")
        except:
            pass

# --- USTOZ: Davomat hisoboti ---
@bot.message_handler(func=lambda m: m.text == "📊 Davomat hisoboti" and get_user_role(m.from_user.id) == "teacher")
def teacher_attendance_report(message):
    db = load_db()
    tid = str(message.from_user.id)
    attendance = db.get("attendance", {})
    if not attendance:
        bot.send_message(message.chat.id, "📭 Hali davomat ma'lumoti yo'q.")
        return

    # So'nggi 7 kun
    dates = sorted(attendance.keys(), reverse=True)[:7]
    text = "📊 <b>Davomat hisoboti (so'nggi kunlar):</b>\n\n"
    for d in dates:
        if tid not in attendance[d]:
            continue
        records = attendance[d][tid].get("records", {})
        came = sum(1 for r in records.values() if r.get("status") == "came" and r.get("confirmed"))
        absent = sum(1 for r in records.values() if r.get("status") == "absent")
        text += f"📆 <b>{d}</b>: ✅ {came} keldi | ❌ {absent} kelmadi\n"
        for sid, r in records.items():
            s_name = db["students"].get(sid, {}).get("name", "?")
            if r.get("status") == "absent":
                reason = r.get("reason", "sabab ko'rsatilmagan")
                text += f"   └ ❌ {s_name}: {reason}\n"
        text += "\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== UY VAZIFA ====================

# --- USTOZ: Uy vazifalarini ko'rish ---
@bot.message_handler(func=lambda m: m.text == "📚 Uy vazifalari" and get_user_role(m.from_user.id) == "teacher")
def teacher_homework_list(message):
    db = load_db()
    tid = str(message.from_user.id)
    homeworks = db.get("homeworks", {})
    my_hw = {k: v for k, v in homeworks.items() if v.get("teacher_id") == tid}

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Yangi uy vazifa berish", callback_data="hw_new"))
    if my_hw:
        markup.add(types.InlineKeyboardButton("📋 Topshirilganlarni ko'rish", callback_data="hw_view_submissions"))
    bot.send_message(message.chat.id, "📚 <b>Uy vazifalar:</b>", parse_mode="HTML", reply_markup=markup)

# --- USTOZ: Yangi uy vazifa ---
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
    uid = message.from_user.id
    user_data[uid]["desc"] = message.text.strip()
    user_states[uid] = "hw_deadline"
    bot.send_message(message.chat.id,
        "📅 Topshirish muddatini kiriting (masalan: 2025-01-20):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "hw_deadline")
def hw_get_deadline(message):
    if message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    db = load_db()
    tid = str(uid)
    if "homeworks" not in db:
        db["homeworks"] = {}
    hw_id = f"hw_{len(db['homeworks'])+1}_{today()}"
    db["homeworks"][hw_id] = {
        "id": hw_id,
        "title": user_data[uid]["title"],
        "desc": user_data[uid]["desc"],
        "deadline": message.text.strip(),
        "teacher_id": tid,
        "created": today(),
        "submissions": {}
    }
    save_db(db)
    del user_states[uid]

    # O'quvchilarga yuborish
    student_ids = db["teachers"][tid].get("students", [])
    sent = 0
    for sid in student_ids:
        try:
            bot.send_message(int(sid),
                f"📚 <b>Yangi uy vazifa!</b>\n\n"
                f"📌 <b>{user_data[uid]['title']}</b>\n"
                f"📝 {user_data[uid]['desc']}\n"
                f"⏰ Muddat: {message.text.strip()}\n\n"
                f"\"📚 Uy vazifa topshirish\" tugmasini bosing!",
                parse_mode="HTML")
            sent += 1
        except:
            pass

    bot.send_message(message.chat.id,
        f"✅ <b>Uy vazifa yuborildi!</b>\n📌 {user_data[uid]['title']}\n📨 {sent} ta o'quvchiga xabar ketdi.",
        parse_mode="HTML", reply_markup=main_menu(uid))
    del user_data[uid]

# --- USTOZ: Topshirilganlarni ko'rish ---
@bot.callback_query_handler(func=lambda c: c.data == "hw_view_submissions")
def teacher_view_submissions(call):
    db = load_db()
    tid = str(call.from_user.id)
    homeworks = {k: v for k, v in db.get("homeworks", {}).items() if v.get("teacher_id") == tid}
    if not homeworks:
        bot.answer_callback_query(call.id, "Vazifalar yo'q!")
        return
    markup = types.InlineKeyboardMarkup()
    for hw_id, hw in homeworks.items():
        sub_count = len(hw.get("submissions", {}))
        markup.add(types.InlineKeyboardButton(
            f"📋 {hw['title']} ({sub_count} topshirdi)",
            callback_data=f"hw_subs_{hw_id}"
        ))
    bot.send_message(call.message.chat.id, "📋 <b>Qaysi vazifani ko'rmoqchisiz?</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("hw_subs_"))
def teacher_hw_submissions_detail(call):
    hw_id = call.data.replace("hw_subs_", "")
    db = load_db()
    hw = db.get("homeworks", {}).get(hw_id)
    if not hw:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    subs = hw.get("submissions", {})
    tid = str(call.from_user.id)
    all_students = db["teachers"].get(tid, {}).get("students", [])
    text = f"📚 <b>{hw['title']}</b>\n⏰ Muddat: {hw['deadline']}\n\n"
    text += f"✅ Topshirdi: {len(subs)}/{len(all_students)}\n\n"
    for sid in all_students:
        s_name = db["students"].get(sid, {}).get("name", "?")
        if sid in subs:
            sub = subs[sid]
            text += f"✅ {s_name} — {sub.get('date','')}\n"
            if sub.get("text"):
                text += f"   📝 {sub['text'][:100]}\n"
            if sub.get("file"):
                text += f"   📎 Fayl yuborilgan\n"
        else:
            text += f"❌ {s_name} — topshirmagan\n"
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

# --- O'QUVCHI: Uy vazifa topshirish ---
@bot.message_handler(func=lambda m: m.text == "📚 Uy vazifa topshirish" and get_user_role(m.from_user.id) == "student")
def student_submit_homework(message):
    db = load_db()
    sid = str(message.from_user.id)
    tid = db["students"][sid].get("teacher_id")
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
        label = f"{'✅' if already else '📝'} {hw['title']} (muddat: {hw['deadline']})"
        markup.add(types.InlineKeyboardButton(label, callback_data=f"submit_hw_{hw['id']}"))
    bot.send_message(message.chat.id, "📚 <b>Qaysi vazifani topshirmoqchisiz?</b>", parse_mode="HTML", reply_markup=markup)

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
        f"📚 <b>{hw['title']}</b>\n📝 {hw['desc']}\n⏰ Muddat: {hw['deadline']}\n\n"
        f"Javobingizni yozing yoki fayl/rasm yuboring:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Bekor qilish"))

@bot.message_handler(
    content_types=["text", "document", "photo"],
    func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("submitting_hw_")
)
def student_hw_answer(message):
    if message.content_type == "text" and message.text == "🔙 Bekor qilish":
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=main_menu(message.from_user.id))
        return
    uid = message.from_user.id
    state_val = user_states[uid]
    hw_id = state_val.replace("submitting_hw_", "")
    sid = str(uid)
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

    # Ustozga xabar
    s_name = db["students"][sid]["name"]
    tid = hw["teacher_id"]
    try:
        if submission["file"] and message.content_type == "photo":
            bot.send_photo(int(tid), submission["file"],
                caption=f"📚 <b>{s_name}</b> uy vazifa topshirdi!\n📌 {hw['title']}\n📝 {submission['text']}",
                parse_mode="HTML")
        elif submission["file"]:
            bot.send_document(int(tid), submission["file"],
                caption=f"📚 <b>{s_name}</b> uy vazifa topshirdi!\n📌 {hw['title']}\n📝 {submission['text']}",
                parse_mode="HTML")
        else:
            bot.send_message(int(tid),
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
    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
