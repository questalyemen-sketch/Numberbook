import telebot
from telebot import types

from config import BOT_TOKEN, BOT_NAME, BOT_VERSION

from database import (
    init_database,
    add_user,
    add_number,
    find_number,
    add_search,
    count_numbers,
    count_searches,
    count_users,
    delete_number
)

from phone_utils import analyze_phone


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
📡 شركة الاتصالات عند توفرها
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

🌍 الدولة
📱 نوع الرقم
📡 شركة الاتصالات
✅ صحة الرقم
🔢 الصيغة الدولية

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
# البحث عن رقم
# =========================================================

def process_search(message):

    register_user(message)

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
            "❌ الرقم غير محتمل وفق نظام الترقيم.",
            reply_markup=main_keyboard()
        )

        return

    phone = result["e164"]

    add_search(
        message.from_user.id,
        phone
    )

    database_result = find_number(phone)

    # اسم من قاعدة Numberbook
    if database_result:

        name = database_result[1]

        database_status = "✅ موجود في Numberbook"

    else:

        name = "غير مسجل"

        database_status = "❌ غير موجود في Numberbook"

    valid_status = (
        "✅ رقم صالح"
        if result["valid"]
        else
        "⚠️ الرقم غير صالح"
    )

    text = f"""
<b>🔎 نتيجة تحليل الرقم</b>

📞 <b>الرقم</b>
<code>{result["e164"]}</code>

🌍 <b>الدولة</b>
{result["country"]}

📱 <b>النوع</b>
{result["type"]}

📡 <b>شركة الاتصالات</b>
{result["carrier"]}

🔢 <b>الصيغة الدولية</b>
<code>{result["international"]}</code>

{valid_status}

━━━━━━━━━━━━━━

👤 <b>الاسم في Numberbook</b>
{name}

{database_status}
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# معلومات الرقم
# =========================================================

def process_info(message):

    register_user(message)

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if not result:

        bot.send_message(
            message.chat.id,
            "❌ الرقم غير صالح أو غير مفهوم.",
            reply_markup=main_keyboard()
        )

        return

    valid = "✅ صالح" if result["valid"] else "❌ غير صالح"

    possible = (
        "✅ محتمل"
        if result["possible"]
        else
        "❌ غير محتمل"
    )

    database_result = find_number(
        result["e164"]
    )

    if database_result:

        registered_name = database_result[1]

    else:

        registered_name = "غير مسجل"

    text = f"""
<b>📱 معلومات الرقم</b>

📞 الرقم:
<code>{result["e164"]}</code>

🌍 الدولة:
<b>{result["country"]}</b>

📍 المنطقة:
<b>{result["region"]}</b>

📱 نوع الرقم:
<b>{result["type"]}</b>

📡 شركة الاتصالات:
<b>{result["carrier"]}</b>

🔢 الصيغة الدولية:
<code>{result["international"]}</code>

━━━━━━━━━━━━━━

🔍 التحقق:
{valid}

📐 إمكانية الرقم:
{possible}

👤 الاسم في Numberbook:
<b>{registered_name}</b>
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# إضافة رقم
# =========================================================

def process_add_phone(message):

    register_user(message)

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
        lambda m: save_number(m, phone, result["country"])
    )


# =========================================================
# حفظ الرقم
# =========================================================

def save_number(message, phone, country):

    register_user(message)

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

📞 الرقم:
<code>{phone}</code>

👤 الاسم:
<b>{name}</b>

🌍 الدولة:
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
# حذف الرقم
# =========================================================

def process_delete(message):

    register_user(message)

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

<code>{result["e164"]}</code>
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
# الرسائل العادية
# =========================================================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    register_user(message)

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
# التشغيل
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print(f"📞 {BOT_NAME}")
    print(f"🚀 Version: {BOT_VERSION}")
    print("📱 Phone Engine: ACTIVE")
    print("🤖 Bot is running...")
    print("=" * 50)

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )