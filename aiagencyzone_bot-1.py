import logging
import os
import json
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ===================== USER DATABASE =====================
USERS_FILE = "users.json"

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def register_user(user) -> bool:
    """Foydalanuvchini saqlaydi. Yangi bo'lsa True qaytaradi."""
    users = load_users()
    uid = str(user.id)
    is_new = uid not in users
    users[uid] = {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username or "",
        "joined": users.get(uid, {}).get("joined", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_users(users)
    return is_new

# ===================== CONFIG =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== STATES =====================
(
    MAIN_MENU,
    CATEGORY_MENU,
    SERVICE_DETAIL,
    ORDER_NAME,
    ORDER_PHONE,
    ORDER_DESCRIPTION,
    ORDER_CONFIRM,
    CALC_CATEGORY,
    CALC_EXTRAS,
    ADMIN_MENU,
    ADMIN_BROADCAST,
) = range(11)

# ===================== DATA =====================
CATEGORIES = {
    "website": {
        "name": "🌐 Website Yaratish",
        "emoji": "🌐",
        "desc": "Professional web-saytlar — landing page, korporativ sayt, do'kon",
        "services": {
            "landing": {
                "name": "Landing Page",
                "price": "300,000 – 800,000 so'm",
                "time": "2–4 kun",
                "desc": "Bir sahifali reklama sayt. Konversiyaga yo'naltirilgan dizayn, mobil mos.",
                "features": ["Responsive dizayn", "SEO asoslari", "Telegram/WhatsApp bog'lanish", "Hosting yo'riqnomasi"],
            },
            "corporate": {
                "name": "Korporativ Sayt",
                "price": "800,000 – 2,000,000 so'm",
                "time": "5–10 kun",
                "desc": "Ko'p sahifali professional sayt. Kompaniya uchun ideal.",
                "features": ["5+ sahifa", "Admin panel", "Blog/yangiliklar", "Xarita integratsiyasi"],
            },
            "store": {
                "name": "Online Do'kon",
                "price": "1,500,000 – 4,000,000 so'm",
                "time": "10–20 kun",
                "desc": "To'liq e-commerce sayt. Mahsulot katalogi, buyurtma tizimi.",
                "features": ["Mahsulot katalogi", "Savat & buyurtma", "To'lov integratsiyasi", "Admin panel"],
            },
        },
    },
    "telegram": {
        "name": "🤖 Telegram Bot",
        "emoji": "🤖",
        "desc": "Biznesingiz uchun aqlli Telegram botlar",
        "services": {
            "simple_bot": {
                "name": "Oddiy Bot",
                "price": "200,000 – 500,000 so'm",
                "time": "1–3 kun",
                "desc": "Buyurtma qabul qilish, FAQ, ma'lumot berish boti.",
                "features": ["Buyurtma tizimi", "Admin xabarnomasi", "Inline tugmalar", "Uzbek/Rus tili"],
            },
            "shop_bot": {
                "name": "Do'kon Boti",
                "price": "500,000 – 1,200,000 so'm",
                "time": "3–7 kun",
                "desc": "Mahsulot katalogi, savat, to'lov — barchasi Telegram'da.",
                "features": ["Katalog & savat", "Click to'lov", "Admin panel", "Statistika"],
            },
            "mini_app": {
                "name": "Telegram Mini App",
                "price": "1,000,000 – 3,000,000 so'm",
                "time": "7–15 kun",
                "desc": "Telegram ichida to'liq web-ilova. Eng zamonaviy yechim.",
                "features": ["To'liq UI/UX", "Ma'lumotlar bazasi", "To'lov tizimi", "Real-time yangilanish"],
            },
        },
    },
    "ai": {
        "name": "🧠 AI Chatbot",
        "emoji": "🧠",
        "desc": "Sun'iy intellekt asosidagi chatbotlar va assistantlar",
        "services": {
            "ai_assistant": {
                "name": "AI Assistant Bot",
                "price": "800,000 – 2,000,000 so'm",
                "time": "5–10 kun",
                "desc": "GPT asosidagi aqlli chatbot. Savollariga javob beradi, konsultatsiya qiladi.",
                "features": ["GPT-4 integratsiya", "O'z bazangiz", "Ko'p til", "24/7 ishlaydi"],
            },
            "ai_crm": {
                "name": "AI + CRM tizimi",
                "price": "2,000,000 – 5,000,000 so'm",
                "time": "14–21 kun",
                "desc": "Mijozlar bilan ishlash va AI ni birlashtirgan professional tizim.",
                "features": ["Mijozlar bazasi", "AI tahlil", "Avtomatik javoblar", "Hisobotlar"],
            },
        },
    },
    "automation": {
        "name": "⚙️ Avtomatizatsiya",
        "emoji": "⚙️",
        "desc": "Biznes jarayonlarni avtomatlashtiramiz",
        "services": {
            "auto_post": {
                "name": "Avto-Post Boti",
                "price": "200,000 – 400,000 so'm",
                "time": "1–2 kun",
                "desc": "Kanalga avtomatik post yuborish, jadval bilan.",
                "features": ["Jadval bilan post", "Foto/video/matn", "Bir necha kanal", "Admin boshqaruv"],
            },
            "integration": {
                "name": "Tizim Integratsiyasi",
                "price": "500,000 – 2,000,000 so'm",
                "time": "3–10 kun",
                "desc": "Google Sheets, CRM, to'lov tizimlari va boshqalar bilan bog'lash.",
                "features": ["API integratsiya", "Google Sheets", "Webhook", "Real-time sync"],
            },
        },
    },
}

PORTFOLIO = [
    {
        "title": "Tima Fashion Shop",
        "category": "🌐 Website",
        "desc": "Instagram do'kon uchun to'liq e-commerce sayt. Telegram orqali buyurtma tizimi.",
        "url": "https://timafashionshop.netlify.app",
        "tech": "HTML/CSS/JS + Telegram Bot",
    },
    {
        "title": "AI Agency Zone Bot",
        "category": "🤖 Telegram Bot",
        "desc": "AI agentlik uchun professional Telegram bot. Buyurtma, narx kalkulyatori, admin panel.",
        "url": "t.me/aiagencyzone_bot",
        "tech": "Python + python-telegram-bot",
    },
    {
        "title": "Avto-Post Tizimi",
        "category": "⚙️ Avtomatizatsiya",
        "desc": "5 ta kanal uchun jadval asosida post yuboruvchi bot.",
        "url": None,
        "tech": "Python + APScheduler",
    },
]

FAQ_LIST = [
    ("💰 Narxlar qanday belgilanadi?", "Narx loyiha murakkabligiga qarab belgilanadi. Biz bilan bog'laning — bepul konsultatsiya beramiz va aniq narx aytamiz."),
    ("⏱ Qancha vaqtda tayyor bo'ladi?", "Oddiy loyihalar 1–3 kun, murakkab loyihalar 7–21 kun. Har bir loyiha uchun aniq muddat kelishiladi."),
    ("💳 To'lov qanday amalga oshiriladi?", "50% avans, 50% tayyor bo'lgandan keyin. UzCard, Humo, Click, Payme orqali to'lash mumkin."),
    ("🔧 Tayyor bo'lgandan keyin qo'llab-quvvatlash?", "Har bir loyihaga 1 oylik bepul texnik yordam kiritilgan. Undan keyin oylik xizmat shartnomasi tuzish mumkin."),
    ("🌍 Faqat Uzbekistonda ishlaymizmi?", "Yo'q! Dunyo bo'ylab onlayn ishlashimiz mumkin. Telegram orqali bog'laning."),
    ("📦 Nima kerak loyiha boshlash uchun?", "Faqat g'oyangizni aytish yetarli. Qolgan hamma narsani biz hal qilamiz."),
]

CALC_PRICES = {
    "website": {"base": 300000, "name": "Sayt"},
    "telegram": {"base": 200000, "name": "Telegram Bot"},
    "ai": {"base": 800000, "name": "AI Chatbot"},
    "automation": {"base": 200000, "name": "Avtomatizatsiya"},
}

CALC_EXTRAS = {
    "payment": ("💳 To'lov integratsiyasi", 300000),
    "admin": ("🖥 Admin panel", 200000),
    "multilang": ("🌐 Ko'p tillilik", 150000),
    "design": ("🎨 Premium dizayn", 250000),
    "seo": ("🔍 SEO optimallashtirish", 200000),
    "hosting": ("☁️ Hosting sozlash", 100000),
}

# ===================== KEYBOARDS =====================

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠 Xizmatlar", callback_data="services"),
         InlineKeyboardButton("💼 Portfolio", callback_data="portfolio")],
        [InlineKeyboardButton("🧮 Narx Kalkulyator", callback_data="calc"),
         InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("📞 Bog'lanish", callback_data="contact"),
         InlineKeyboardButton("📝 Buyurtma berish", callback_data="order_start")],
    ])

def categories_kb(back=True):
    buttons = []
    row = []
    for key, cat in CATEGORIES.items():
        row.append(InlineKeyboardButton(cat["name"], callback_data=f"cat_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if back:
        buttons.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def services_kb(cat_key):
    cat = CATEGORIES[cat_key]
    buttons = []
    for svc_key, svc in cat["services"].items():
        buttons.append([InlineKeyboardButton(
            f"{svc['name']} — {svc['price']}",
            callback_data=f"svc_{cat_key}_{svc_key}"
        )])
    buttons.append([
        InlineKeyboardButton("◀️ Kategoriyalar", callback_data="services"),
        InlineKeyboardButton("📝 Buyurtma", callback_data=f"order_cat_{cat_key}")
    ])
    return InlineKeyboardMarkup(buttons)

def service_detail_kb(cat_key, svc_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Shu xizmatni buyurtma qilish", callback_data=f"order_svc_{cat_key}_{svc_key}")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data=f"cat_{cat_key}")],
    ])

def back_main_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_main")]])

def confirm_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="order_confirm"),
         InlineKeyboardButton("❌ Bekor qilish", callback_data="order_cancel")],
    ])

# ===================== HELPERS =====================

def format_number(n):
    return f"{n:,}".replace(",", " ")

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    text = (
        "🚀 *AI Agency Zone*\n\n"
        "Xush kelibsiz! Biz sizning biznesingizni raqamli olamga olib chiqamiz.\n\n"
        "🌐 Website • 🤖 Telegram Bot • 🧠 AI Chatbot • ⚙️ Avtomatizatsiya\n\n"
        "Quyidagi menyu orqali xizmatlarimiz bilan tanishing:"
    )
    if edit:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_kb())
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_kb())

# ===================== HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = register_user(user)
    logger.info(f"{'New' if is_new else 'Return'} user: {user.id} - {user.full_name}")

    # Yangi user bo'lsa adminga xabar yuborish
    if is_new:
        users = load_users()
        count = len(users)
        admin_text = (
            f"👤 *Yangi foydalanuvchi!*\n\n"
            f"Ism: {user.full_name}\n"
            f"Username: @{user.username or 'yo\'q'}\n"
            f"ID: `{user.id}`\n"
            f"Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📊 Jami foydalanuvchilar: *{count}* ta"
        )
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Admin notify xato: {e}")

    await send_main_menu(update, context)
    return MAIN_MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # === MAIN MENU ===
    if data == "back_main":
        await send_main_menu(update, context, edit=True)
        return MAIN_MENU

    # === SERVICES / CATEGORIES ===
    elif data == "services":
        text = "🛠 *Xizmatlar kategoriyalari*\n\nQaysi yo'nalish qiziqtiradi?"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=categories_kb())
        return CATEGORY_MENU

    elif data.startswith("cat_"):
        cat_key = data[4:]
        cat = CATEGORIES[cat_key]
        text = f"{cat['emoji']} *{cat['name']}*\n\n{cat['desc']}\n\n📋 Xizmatlar:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=services_kb(cat_key))
        return CATEGORY_MENU

    elif data.startswith("svc_"):
        parts = data.split("_")
        cat_key, svc_key = parts[1], parts[2]
        svc = CATEGORIES[cat_key]["services"][svc_key]
        features_text = "\n".join([f"  ✅ {f}" for f in svc["features"]])
        text = (
            f"*{svc['name']}*\n\n"
            f"📝 {svc['desc']}\n\n"
            f"💰 *Narx:* {svc['price']}\n"
            f"⏱ *Muddat:* {svc['time']}\n\n"
            f"📦 *Nima kiradi:*\n{features_text}"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=service_detail_kb(cat_key, svc_key))
        return SERVICE_DETAIL

    # === PORTFOLIO ===
    elif data == "portfolio":
        text = "💼 *Portfolio — Bizning ishlarimiz*\n\n"
        for i, p in enumerate(PORTFOLIO, 1):
            text += f"*{i}. {p['title']}*\n"
            text += f"🏷 {p['category']}\n"
            text += f"📝 {p['desc']}\n"
            text += f"⚙️ {p['tech']}\n"
            if p["url"]:
                text += f"🔗 {p['url']}\n"
            text += "\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_main_kb())
        return MAIN_MENU

    # === FAQ ===
    elif data == "faq":
        text = "❓ *Ko'p so'raladigan savollar*\n\n"
        for q, a in FAQ_LIST:
            text += f"*{q}*\n{a}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=back_main_kb())
        return MAIN_MENU

    # === CONTACT ===
    elif data == "contact":
        text = (
            "📞 *Bog'lanish*\n\n"
            "👤 Menejer: @aiagencyzone_admin\n"
            "📱 Telegram: @aiagencyzone\n"
            "📸 Instagram: @aiagencyzone.uz\n\n"
            "⏰ Ish vaqti: 9:00 – 22:00 (Dushanba – Yakshanba)\n\n"
            "Yoki quyida *Buyurtma berish* tugmasini bosing — biz o'zimiz bog'lanamiz! 👇"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Buyurtma berish", callback_data="order_start")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_main")],
        ]))
        return MAIN_MENU

    # === CALCULATOR ===
    elif data == "calc":
        context.user_data["calc"] = {"extras": []}
        text = "🧮 *Narx Kalkulyatori*\n\nQaysi xizmat kerak?"
        buttons = [[InlineKeyboardButton(f"{v['name']}", callback_data=f"calc_cat_{k}")] for k, v in CALC_PRICES.items()]
        buttons.append([InlineKeyboardButton("◀️ Orqaga", callback_data="back_main")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return CALC_CATEGORY

    elif data.startswith("calc_cat_"):
        cat = data[9:]
        context.user_data["calc"]["category"] = cat
        context.user_data["calc"]["extras"] = []
        await show_calc_extras(query, context)
        return CALC_EXTRAS

    elif data.startswith("calc_extra_"):
        extra = data[11:]
        extras = context.user_data["calc"]["extras"]
        if extra in extras:
            extras.remove(extra)
        else:
            extras.append(extra)
        await show_calc_extras(query, context)
        return CALC_EXTRAS

    elif data == "calc_result":
        calc = context.user_data["calc"]
        cat = calc["category"]
        base = CALC_PRICES[cat]["base"]
        name = CALC_PRICES[cat]["name"]
        total = base
        details = [f"  • {name} (asosiy): {format_number(base)} so'm"]
        for extra_key in calc["extras"]:
            extra_name, extra_price = CALC_EXTRAS[extra_key]
            total += extra_price
            details.append(f"  • {extra_name}: +{format_number(extra_price)} so'm")
        details_text = "\n".join(details)
        text = (
            f"🧮 *Hisoblash natijasi*\n\n"
            f"{details_text}\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"💰 *Jami (taxminiy):* {format_number(total)} so'm\n\n"
            f"⚠️ Bu taxminiy narx. Aniq narx uchun biz bilan bog'laning!"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Buyurtma berish", callback_data="order_start")],
            [InlineKeyboardButton("🔄 Qayta hisoblash", callback_data="calc")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="back_main")],
        ]))
        return MAIN_MENU

    # === ORDER START ===
    elif data in ("order_start",) or data.startswith("order_cat_") or data.startswith("order_svc_"):
        if data.startswith("order_svc_"):
            parts = data.split("_")
            cat_key, svc_key = parts[2], parts[3]
            svc = CATEGORIES[cat_key]["services"][svc_key]
            context.user_data["order"] = {"service": svc["name"], "price": svc["price"]}
        elif data.startswith("order_cat_"):
            cat_key = data[10:]
            cat = CATEGORIES[cat_key]
            context.user_data["order"] = {"service": cat["name"]}
        else:
            context.user_data["order"] = {}

        await query.edit_message_text(
            "📝 *Buyurtma*\n\nIsm-familiyangizni kiriting:",
            parse_mode="Markdown"
        )
        return ORDER_NAME

    elif data == "order_confirm":
        order = context.user_data.get("order", {})
        user = update.effective_user
        admin_text = (
            f"🆕 *Yangi buyurtma!*\n\n"
            f"👤 Mijoz: {user.full_name} (@{user.username or 'yo\'q'})\n"
            f"🆔 ID: `{user.id}`\n"
            f"📦 Xizmat: {order.get('service', '—')}\n"
            f"👤 Ism: {order.get('name', '—')}\n"
            f"📱 Telefon: {order.get('phone', '—')}\n"
            f"📝 Izoh: {order.get('desc', '—')}"
        )
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, admin_text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Admin xabar yuborishda xato: {e}")

        await query.edit_message_text(
            "✅ *Buyurtmangiz qabul qilindi!*\n\n"
            "Tez orada menejerimiz siz bilan bog'lanadi.\n"
            "Odatda 30 daqiqa – 2 soat ichida javob beramiz. 😊",
            parse_mode="Markdown",
            reply_markup=back_main_kb()
        )
        context.user_data.clear()
        return MAIN_MENU

    elif data == "order_cancel":
        context.user_data.clear()
        await send_main_menu(update, context, edit=True)
        return MAIN_MENU

    return MAIN_MENU

async def show_calc_extras(query, context):
    cat = context.user_data["calc"]["category"]
    selected = context.user_data["calc"]["extras"]
    base = CALC_PRICES[cat]["base"]
    name = CALC_PRICES[cat]["name"]
    total = base + sum(CALC_EXTRAS[e][1] for e in selected)

    buttons = []
    for key, (label, price) in CALC_EXTRAS.items():
        check = "✅" if key in selected else "⬜️"
        buttons.append([InlineKeyboardButton(
            f"{check} {label} (+{format_number(price)} so'm)",
            callback_data=f"calc_extra_{key}"
        )])
    buttons.append([InlineKeyboardButton(f"🧮 Hisoblash — {format_number(total)} so'm", callback_data="calc_result")])
    buttons.append([InlineKeyboardButton("◀️ Orqaga", callback_data="calc")])

    text = (
        f"🧮 *{name}* — asosiy: {format_number(base)} so'm\n\n"
        f"Qo'shimcha funksiyalarni belgilang:"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# === ORDER CONVERSATION ===

async def order_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["name"] = update.message.text.strip()
    await update.message.reply_text("📱 Telefon raqamingizni kiriting (masalan: +998901234567):")
    return ORDER_PHONE

async def order_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    context.user_data["order"]["phone"] = phone
    await update.message.reply_text(
        "📝 Loyiha haqida qisqacha ma'lumot bering:\n"
        "(Nima kerak, qanday ko'rinishda bo'lsin, biror namuna bormi?)"
    )
    return ORDER_DESCRIPTION

async def order_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"]["desc"] = update.message.text.strip()
    order = context.user_data["order"]
    text = (
        f"📋 *Buyurtmani tasdiqlash*\n\n"
        f"👤 Ism: {order.get('name')}\n"
        f"📱 Telefon: {order.get('phone')}\n"
        f"📦 Xizmat: {order.get('service', 'Ko\'rsatilmagan')}\n"
        f"📝 Izoh: {order.get('desc')}\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=confirm_kb())
    return ORDER_CONFIRM

# === ADMIN PANEL ===

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return

    users = load_users()
    count = len(users)
    text = (
        f"🔧 *Admin Panel*\n\n"
        f"👤 Jami foydalanuvchilar: *{count}* ta\n"
        f"🕐 Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👥 Foydalanuvchilar ({count} ta)", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast xabar", callback_data="admin_broadcast")],
    ])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    if query.data == "admin_users":
        users = load_users()
        if not users:
            await query.edit_message_text("📭 Hali foydalanuvchi yo'q.")
            return

        # Sahifalash — har safar 20 ta
        page = context.user_data.get("admin_page", 0)
        all_users = list(users.values())
        total = len(all_users)
        per_page = 20
        start_i = page * per_page
        end_i = min(start_i + per_page, total)
        page_users = all_users[start_i:end_i]

        lines = [f"👥 *Foydalanuvchilar* ({total} ta) — {page+1}-sahifa\n"]
        for i, u in enumerate(page_users, start_i + 1):
            uname = f"@{u['username']}" if u['username'] else "username yo'q"
            lines.append(f"{i}. {u['full_name']} | {uname} | `{u['id']}`\n   📅 {u['joined']}")

        text = "\n".join(lines)

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Oldingi", callback_data="admin_prev"))
        if end_i < total:
            nav_buttons.append(InlineKeyboardButton("Keyingi ▶️", callback_data="admin_next"))

        kb_rows = []
        if nav_buttons:
            kb_rows.append(nav_buttons)
        kb_rows.append([InlineKeyboardButton("🔙 Admin", callback_data="admin_back")])

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb_rows))

    elif query.data == "admin_prev":
        context.user_data["admin_page"] = max(0, context.user_data.get("admin_page", 0) - 1)
        # Qayta chaqirish
        query.data = "admin_users"
        await admin_callback(update, context)

    elif query.data == "admin_next":
        context.user_data["admin_page"] = context.user_data.get("admin_page", 0) + 1
        query.data = "admin_users"
        await admin_callback(update, context)

    elif query.data == "admin_back":
        users = load_users()
        count = len(users)
        text = (
            f"🔧 *Admin Panel*\n\n"
            f"👤 Jami foydalanuvchilar: *{count}* ta\n"
            f"🕐 Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"👥 Foydalanuvchilar ({count} ta)", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Broadcast xabar", callback_data="admin_broadcast")],
        ])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun /users komandasi — to'liq ro'yxat"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    users = load_users()
    if not users:
        await update.message.reply_text("📭 Hali foydalanuvchi yo'q.")
        return
    lines = [f"👥 *Barcha foydalanuvchilar* ({len(users)} ta)\n"]
    for i, u in enumerate(users.values(), 1):
        uname = f"@{u['username']}" if u['username'] else "—"
        lines.append(f"{i}. {u['full_name']} | {uname} | `{u['id']}` | {u['joined']}")
    text = "\n".join(lines)
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i+4000], parse_mode="Markdown")

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Tushunmadim 🤔 Bosh menyuga qaytish uchun /start bosing."
    )

# ===================== MAIN =====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            0: [CallbackQueryHandler(button_handler)],
            1: [CallbackQueryHandler(button_handler)],
            2: [CallbackQueryHandler(button_handler)],
            7: [CallbackQueryHandler(button_handler)],
            8: [CallbackQueryHandler(button_handler)],
            3: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_name),
                CallbackQueryHandler(button_handler),
            ],
            4: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_phone),
                CallbackQueryHandler(button_handler),
            ],
            5: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, order_description),
                CallbackQueryHandler(button_handler),
            ],
            6: [CallbackQueryHandler(button_handler)],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    logger.info("🚀 AI Agency Zone Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
