import telebot
from telebot import types

from config import BOT_TOKEN, BOT_NAME, BOT_VERSION

from database import (
    init_database,
    add_user,
    add_number,
    add_search,
    count_numbers,
    count_searches,
    count_users,
    delete_number
)

from phone_utils import analyze_phone
from data_sources import collect_phone_data


# =========================================================
# تشغيل البوت
# =========================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

init_database()


# =========================================================
# القائمة الرئيسية
# =========================================================

def main_keyboard():

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "🔎 بحث عن رقم",
            callback_data="search"
        ),
        types.InlineKeyboardButton(
            "📱 معلومات الرقم",
            callback_data="info"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "➕ إضافة رقمي",
            callback_data="add"
        ),
        types.InlineKeyboardButton(
            "🗑 حذف رقمي",
            callback_data="delete"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "📊 الإحصائيات",
            callback_data="stats"
        ),
        types.InlineKeyboardButton(
            "ℹ️ المساعدة",
            callback_data="help"
        )
    )

    return keyboard


# =========================================================
# تسجيل المستخدم
# =========================================================

def register_user(message):

    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )


# =========================================================
# /start
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    register_user(message)

    text = f"""
<b>📞 {BOT_NAME}</b>

<b>مرحباً {message.from_user.first_name} 👋</b>

الإصدار: <b>{BOT_VERSION}</b>

🔎 محرك أرقام متطور
🌍 تحليل الدولة
📱 نوع الرقم
📡 شركة الاتصالات
🔢 الصيغة الدولية
✅ التحقق من الرقم
👤 البحث في Numberbook
➕ تسجيل رقمك
🗑 حذف رقمك
📊 إحصائيات

اختر الخدمة من الأسفل 👇
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# /help
# =========================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    register_user(message)

    bot.send_message(
        message.chat.id,
        """
<b>ℹ️ طريقة الاستخدام</b>

🔎 <b>بحث عن رقم</b>

أرسل الرقم بصيغة دولية:

<code>+967771234567</code>

📱 <b>معلومات الرقم</b>

يعرض:

📞 الرقم
🌍 الدولة
📍 المنطقة
📱 نوع الرقم
📡 شركة الاتصالات
🔢 الصيغة الدولية
✅ حالة الرقم
👤 بيانات Numberbook عند توفرها

➕ <b>إضافة رقمي</b>

تسجيل رقمك في قاعدة Numberbook.

🗑 <b>حذف رقمي</b>

حذف الرقم الذي سجلته بنفسك.

⚠️ يعتمد النظام على البيانات المسموح باستخدامها ولا يعتمد على قواعد بيانات مسروقة.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# الأزرار
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    chat_id = call.message.chat.id

    # ---------------------------------------
    # البحث
    # ---------------------------------------

    if call.data == "search":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>🔎 البحث عن رقم</b>

أرسل رقم الهاتف.

مثال:

<code>+967771234567</code>
"""
        )

        bot.register_next_step_handler(
            msg,
            process_search
        )

    # ---------------------------------------
    # المعلومات
    # ---------------------------------------

    elif call.data == "info":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>📱 معلومات الرقم</b>

أرسل رقم الهاتف.

مثال:

<code>+967771234567</code>
"""
        )

        bot.register_next_step_handler(
            msg,
            process_info
        )

    # ---------------------------------------
    # إضافة رقم
    # ---------------------------------------

    elif call.data == "add":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>➕ إضافة رقمك</b>

أرسل رقمك بصيغة دولية.

مثال:

<code>+967771234567</code>
"""
        )

        bot.register_next_step_handler(
            msg,
            process_add_phone
        )

    # ---------------------------------------
    # حذف رقم
    # ---------------------------------------

    elif call.data == "delete":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>🗑 حذف رقمك</b>

أرسل الرقم الذي تريد حذفه.
"""
        )

        bot.register_next_step_handler(
            msg,
            process_delete
        )

    # ---------------------------------------
    # الإحصائيات
    # ---------------------------------------

    elif call.data == "stats":

        bot.answer_callback_query(call.id)

        text = f"""
<b>📊 إحصائيات Numberbook</b>

👥 المستخدمون:
<b>{count_users()}</b>

📞 الأرقام:
<b>{count_numbers()}</b>

🔎 عمليات البحث:
<b>{count_searches()}</b>
"""

        bot.send_message(
            chat_id,
            text,
            reply_markup=main_keyboard()
        )

    # ---------------------------------------
    # المساعدة
    # ---------------------------------------

    elif call.data == "help":

        bot.answer_callback_query(call.id)

        help_command(call.message)


# =========================================================
# 🔎 البحث عن رقم
# =========================================================

def process_search(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل رقم هاتف فقط.",
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # التحليل الأولي
    # -----------------------------------------------------

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if not result:

        bot.send_message(
            message.chat.id,
            """
❌ لم أستطع فهم الرقم.

أرسل الرقم بصيغة دولية.

مثال:

<code>+967771234567</code>
""",
            reply_markup=main_keyboard()
        )

        return

    if not result["possible"]:

        bot.send_message(
            message.chat.id,
            """
❌ الرقم غير محتمل وفق نظام الترقيم.

تحقق من الرقم وحاول مرة أخرى.
""",
            reply_markup=main_keyboard()
        )

        return

    phone = result["e164"]

    # -----------------------------------------------------
    # تسجيل البحث
    # -----------------------------------------------------

    add_search(
        message.from_user.id,
        phone
    )

    # -----------------------------------------------------
    # 🔎 استدعاء محرك مصادر البيانات
    # -----------------------------------------------------

    data = collect_phone_data(
        phone,
        default_region="YE"
    )

    # -----------------------------------------------------
    # استخراج Phone Engine
    # -----------------------------------------------------

    phone_source = None

    numberbook_source = None

    for source in data.get("sources", []):

        if source.get("source") == "Phone Engine":

            phone_source = source

        elif source.get("source") == "Numberbook":

            numberbook_source = source

    # -----------------------------------------------------
    # حماية في حال تعذر مصدر الهاتف
    # -----------------------------------------------------

    if not phone_source:

        bot.send_message(
            message.chat.id,
            """
❌ تعذر الحصول على معلومات الرقم حاليًا.

حاول مرة أخرى لاحقًا.
""",
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # بيانات Numberbook
    # -----------------------------------------------------

    if numberbook_source:

        if numberbook_source.get("found"):

            name = (
                numberbook_source.get("name")
                or "غير معروف"
            )

            database_status = (
                "✅ الرقم موجود في Numberbook"
            )

        else:

            name = "غير مسجل"

            database_status = (
                "❌ الرقم غير موجود في Numberbook"
            )

    else:

        name = "غير مسجل"

        database_status = (
            "⚠️ تعذر الوصول إلى مصدر Numberbook"
        )

    # -----------------------------------------------------
    # بناء النتيجة
    # -----------------------------------------------------

    text = f"""
<b>🔎 نتيجة البحث</b>

📞 <b>الرقم:</b>
<code>{phone_source.get("phone")}</code>

🌍 <b>الدولة:</b>
{phone_source.get("country")}

📱 <b>نوع الرقم:</b>
{phone_source.get("type")}

📡 <b>شركة الاتصالات:</b>
{phone_source.get("carrier")}

🔢 <b>الصيغة الدولية:</b>
<code>{phone_source.get("international")}</code>

✅ <b>حالة الرقم:</b>
{phone_source.get("status")}

━━━━━━━━━━━━━━

👤 <b>الاسم في Numberbook:</b>
<b>{name}</b>

{database_status}

━━━━━━━━━━━━━━

📚 <b>مصادر المعلومات:</b>

📱 Phone Engine
👤 Numberbook
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# 📱 معلومات الرقم
# =========================================================

def process_info(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل رقم هاتف فقط.",
            reply_markup=main_keyboard()
        )

        return

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if not result:

        bot.send_message(
            message.chat.id,
            """
❌ الرقم غير صالح أو غير مفهوم.

مثال:

<code>+967771234567</code>
""",
            reply_markup=main_keyboard()
        )

        return

    data = collect_phone_data(
        result["e164"],
        default_region="YE"
    )

    phone_source = None
    numberbook_source = None

    for source in data.get("sources", []):

        if source.get("source") == "Phone Engine":

            phone_source = source

        elif source.get("source") == "Numberbook":

            numberbook_source = source

    if not phone_source:

        phone_source = result

    if numberbook_source and numberbook_source.get("found"):

        registered_name = (
            numberbook_source.get("name")
            or "غير معروف"
        )

    else:

        registered_name = "غير مسجل"

    text = f"""
<b>📱 معلومات الرقم</b>

📞 <b>الرقم:</b>
<code>{phone_source.get("phone", result["e164"])}</code>

🌍 <b>الدولة:</b>
{phone_source.get("country", result["country"])}

📍 <b>رمز المنطقة:</b>
{phone_source.get("region", result["region"])}

📱 <b>نوع الرقم:</b>
{phone_source.get("type", result["type"])}

📡 <b>شركة الاتصالات:</b>
{phone_source.get("carrier", result["carrier"])}

🔢 <b>الصيغة الدولية:</b>
<code>{phone_source.get("international", result["international"])}</code>

━━━━━━━━━━━━━━

🔍 <b>الحالة:</b>
{phone_source.get("status", "غير متوفر")}

📐 <b>إمكانية الرقم:</b>
{
    "✅ محتمل"
    if result["possible"]
    else
    "❌ غير محتمل"
}

👤 <b>الاسم في Numberbook:</b>
<b>{registered_name}</b>

━━━━━━━━━━━━━━

📚 <b>مصادر المعلومات:</b>

📱 Phone Engine
👤 Numberbook
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# ➕ إضافة رقم
# =========================================================

def process_add_phone(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل رقم هاتف فقط.",
            reply_markup=main_keyboard()
        )

        return

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if not result or not result["possible"]:

        bot.send_message(
            message.chat.id,
            "❌ الرقم غير صحيح.",
            reply_markup=main_keyboard()
        )

        return

    phone = result["e164"]

    from database import find_number

    existing = find_number(phone)

    if existing:

        bot.send_message(
            message.chat.id,
            """
⚠️ هذا الرقم موجود بالفعل في قاعدة Numberbook.
""",
            reply_markup=main_keyboard()
        )

        return

    msg = bot.send_message(
        message.chat.id,
        """
<b>👤 اسم صاحب الرقم</b>

أرسل الاسم الذي تريد تسجيله مع الرقم.
"""
    )

    bot.register_next_step_handler(
        msg,
        lambda m: save_number(
            m,
            phone,
            result["country"]
        )
    )


# =========================================================
# 💾 حفظ الرقم
# =========================================================

def save_number(message, phone, country):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل اسمًا صحيحًا.",
            reply_markup=main_keyboard()
        )

        return

    name = message.text.strip()

    if not name or len(name) > 100:

        bot.send_message(
            message.chat.id,
            "❌ الاسم غير صالح.",
            reply_markup=main_keyboard()
        )

        return

    success = add_number(
        phone,
        name,
        country,
        message.from_user.id
    )

    if success:

        bot.send_message(
            message.chat.id,
            f"""
<b>✅ تم تسجيل الرقم</b>

📞 <b>الرقم:</b>
<code>{phone}</code>

👤 <b>الاسم:</b>
<b>{name}</b>

🌍 <b>الدولة:</b>
<b>{country}</b>

يمكنك حذف الرقم لاحقًا من زر 🗑 حذف رقمي.
""",
            reply_markup=main_keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            "⚠️ الرقم مسجل بالفعل.",
            reply_markup=main_keyboard()
        )


# =========================================================
# 🗑 حذف الرقم
# =========================================================

def process_delete(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل رقم هاتف فقط.",
            reply_markup=main_keyboard()
        )

        return

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if not result:

        bot.send_message(
            message.chat.id,
            "❌ الرقم غير صحيح.",
            reply_markup=main_keyboard()
        )

        return

    deleted = delete_number(
        result["e164"],
        message.from_user.id
    )

    if deleted:

        bot.send_message(
            message.chat.id,
            f"""
<b>✅ تم حذف الرقم</b>

📞 <code>{result["e164"]}</code>
""",
            reply_markup=main_keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            """
❌ لم أجد رقمًا مسجلًا باسمك.

يمكنك حذف الأرقام التي سجلتها بنفسك فقط.
""",
            reply_markup=main_keyboard()
        )


# =========================================================
# 💬 الرسائل العادية
# =========================================================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            """
❓ أرسل رقم هاتف أو استخدم /start.
""",
            reply_markup=main_keyboard()
        )

        return

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if result and result["possible"]:

        process_search(message)

        return

    bot.send_message(
        message.chat.id,
        """
❓ لم أفهم طلبك.

استخدم:

/start

لفتح القائمة الرئيسية.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# 🚀 التشغيل
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print(f"📞 {BOT_NAME}")
    print(f"🚀 Version: {BOT_VERSION}")
    print("📱 Phone Engine: ACTIVE")
    print("👤 Numberbook Source: ACTIVE")
    print("🔎 Data Sources Engine: ACTIVE")
    print("🤖 Bot is running...")
    print("=" * 50)

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )