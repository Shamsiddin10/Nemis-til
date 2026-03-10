# 🇩🇪 Nemis Tili O'rgatuvchi Telegram Bot

## 🚀 Ishga tushirish

### 1. O'rnatish
```bash
pip install -r requirements.txt
```

### 2. Sozlash (bot.py faylini oching)
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # @BotFather dan token oling
ADMIN_IDS = [123456789]             # O'z Telegram ID ingizni kiriting
```

> 💡 O'z ID ingizni bilish uchun @userinfobot ga `/start` yuboring

### 3. Ishga tushirish
```bash
python bot.py
```

---

## 👥 Rollar

### 👑 Admin
- O'qituvchilar va o'quvchilar ro'yxatini ko'rish
- Yangi o'qituvchi qo'shish (Telegram ID orqali)
- Statistika ko'rish

### 👨‍🏫 O'qituvchi
- O'quvchi qo'shish (Telegram ID orqali)
- Yangi test yaratish (mavzu + savollar + variantlar)
- O'quvchilar va testlar ro'yxatini ko'rish

### 👨‍🎓 O'quvchi
- Testlarni ko'rish va topshirish
- Natijalarni ko'rish
- Profil ma'lumotlari

---

## 📝 Test yaratish ketma-ketligi
1. "📝 Test qo'shish" → mavzu kiriting
2. Savolni kiriting
3. 4 ta variant kiriting (A, B, C, D)
4. To'g'ri javob harfini kiriting
5. Yana savol qo'shish yoki saqlash

---

## 💾 Ma'lumotlar
Barcha ma'lumotlar `database.json` faylida saqlanadi.
