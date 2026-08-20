import re
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


# =========================================================
# تشغيل البوت
# =========================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

init_database()


# =========================================================
# أدوات مساعدة
# =========================================================

def normalize_phone(phone):

    if not phone:
        return None

    phone = phone.strip()

    if phone.startswith("00"):
        phone = "+" + phone[2:]

    phone = re.sub(r"[^\d+]", "", phone)

    if phone.count("+") > 1:
        return None

    if "+" in phone and not phone.startswith("+"):
        return None

    digits = phone.replace("+", "")

    if not digits.isdigit():
        return None

    if len(digits) < 7 or len(digits) > 15:
        return None

    return "+" + digits


def get_country(phone):

    countries = {
        "+967": "اليمن 🇾🇪",
        "+966": "السعودية 🇸🇦",
        "+971": "الإمارات 🇦🇪",
        "+974": "قطر 🇶🇦",
        "+965": "الكويت 🇰🇼",
        "+973": "البحرين 🇧🇭",
        "+968": "عُمان 🇴🇲",
        "+20": "مصر 🇪🇬",
        "+962": "الأردن 🇯🇴",
        "+964": "العراق 🇮🇶",
        "+963": "سوريا 🇸🇾",
        "+961": "لبنان 🇱🇧",
        "+90": "تركيا 🇹🇷",
        "+44": "بريطانيا 🇬🇧",
        "+33": "فرنسا 🇫🇷",
        "+49": "ألمانيا 🇩🇪",
        "+39": "إيطاليا 🇮🇹",
        "+91": "الهند 🇮🇳",
        "+92": "باكستان 🇵🇰",
        "+86": "الصين 🇨🇳",
        "+81": "اليابان 🇯🇵",
        "+82": "كوريا الجنوبية 🇰🇷",
        "+7": "روسيا / كازاخستان 🇷🇺"
    }

    for prefix, country in countries.items():

        if phone.startswith(prefix):
            return country

    return "غير معروف 🌍"


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

نسخة <b>{BOT_VERSION}</b> من مشروع دليل الأرقام.

يمكنك من خلال البوت:

🔎 البحث عن رقم
📱 معرفة معلومات أساسية عن الرقم
➕ تسجيل رقمك بموافقتك
🗑 حذف الرقم الذي سجلته
📊 مشاهدة إحصائيات الدليل

اختر الخدمة من القائمة 👇
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

    text = """
<b>ℹ️ مساعدة</b>

🔎 <b>بحث عن رقم</b>
أرسل رقمًا بصيغة دولية.

مثال:
<code>+967771234567</code>

➕ <b>إضافة رقمي</b>
يمكنك تسجيل رقمك واسمك في دليل البوت.

🗑 <b>حذف رقمي</b>
يمكنك حذف الرقم الذي سجلته بنفسك.

⚠️ البوت لا يعتمد على قواعد بيانات مسروقة أو بيانات خاصة غير مصرح بها.
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# أزرار القائمة
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    chat_id = call.message.chat.id

    # -----------------------------
    # البحث
    # -----------------------------

    if call.data == "search":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>🔎 بحث عن رقم</b>

أرسل الرقم الآن بصيغة دولية.

مثال:
<code>+967771234567</code>
"""
        )

        bot.register_next_step_handler(
            msg,
            process_search
        )

    # -----------------------------
    # معلومات الرقم
    # -----------------------------

    elif call.data == "info":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>📱 معلومات الرقم</b>

أرسل رقم الهاتف.

مثال:
<code>+966501234567</code>
"""
        )

        bot.register_next_step_handler(
            msg,
            process_info
        )

    # -----------------------------
    # إضافة رقم
    # -----------------------------

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

    # -----------------------------
    # حذف رقم
    # -----------------------------

    elif call.data == "delete":

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            chat_id,
            """
<b>🗑 حذف رقمك</b>

أرسل الرقم الذي تريد حذفه.

مثال:
<code>+967771234567</code>
"""
        )

        bot.register_next_step_handler(
            msg,
            process_delete
        )

    # -----------------------------
    # الإحصائيات
    # -----------------------------

    elif call.data == "stats":

        bot.answer_callback_query(call.id)

        text = f"""
<b>📊 إحصائيات البوت</b>

👥 المستخدمون:
<b>{count_users()}</b>

📞 الأرقام المسجلة:
<b>{count_numbers()}</b>

🔎 عمليات البحث:
<b>{count_searches()}</b>
"""

        bot.send_message(
            chat_id,
            text,
            reply_markup=main_keyboard()
        )

    # -----------------------------
    # المساعدة
    # -----------------------------

    elif call.data == "help":

        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            """
<b>ℹ️ المساعدة</b>

استخدم الأزرار للوصول إلى الخدمات.

يمكنك أيضًا استخدام:

/start
/help

📞 البحث يعمل بالأرقام الدولية.
""",
            reply_markup=main_keyboard()
        )


# =========================================================
# البحث
# =========================================================

def process_search(message):

    register_user(message)

    phone = normalize_phone(message.text)

    if not phone:

        bot.send_message(
            message.chat.id,
            """
❌ الرقم غير صحيح.

مثال صحيح:

<code>+967771234567</code>
""",
            reply_markup=main_keyboard()
        )

        return

    add_search(
        message.from_user.id,
        phone
    )

    result = find_number(phone)

    country = get_country(phone)

    if result:

        stored_phone = result[0]
        name = result[1]
        stored_country = result[2]

        if stored_country:
            country = stored_country

        text = f"""
<b>🔎 نتيجة البحث</b>

📞 الرقم:
<code>{stored_phone}</code>

👤 الاسم:
<b>{name}</b>

🌍 الدولة:
<b>{country}</b>

✅ الرقم موجود في دليل البوت.
"""

    else:

        text = f"""
<b>🔎 نتيجة البحث</b>

📞 الرقم:
<code>{phone}</code>

🌍 الدولة:
<b>{country}</b>

❌ لا يوجد اسم مسجل لهذا الرقم داخل دليل البوت.
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

    phone = normalize_phone(message.text)

    if not phone:

        bot.send_message(
            message.chat.id,
            "❌ الرقم غير صحيح.",
            reply_markup=main_keyboard()
        )

        return

    result = find_number(phone)

    country = get_country(phone)

    if result:

        name = result[1]

        registered = "نعم ✅"

    else:

        name = "غير متوفر"

        registered = "لا ❌"

    text = f"""
<b>📱 معلومات الرقم</b>

📞 الرقم:
<code>{phone}</code>

🌍 الدولة:
<b>{country}</b>

👤 الاسم:
<b>{name}</b>

📚 مسجل في الدليل:
<b>{registered}</b>
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# إضافة الرقم - الخطوة الأولى
# =========================================================

def process_add_phone(message):

    register_user(message)

    phone = normalize_phone(message.text)

    if not phone:

        bot.send_message(
            message.chat.id,
            "❌ الرقم غير صحيح.",
            reply_markup=main_keyboard()
        )

        return

    existing = find_number(phone)

    if existing:

        bot.send_message(
            message.chat.id,
            """
⚠️ هذا الرقم موجود بالفعل في الدليل.

إذا كان الرقم لك، يمكنك التواصل مع الإدارة للتحقق من الملكية.
""",
            reply_markup=main_keyboard()
        )

        return

    msg = bot.send_message(
        message.chat.id,
        """
<b>👤 الخطوة الأخيرة</b>

أرسل الاسم الذي تريد تسجيله مع الرقم.

مثال:
<code>صالح</code>
"""
    )

    bot.register_next_step_handler(
        msg,
        lambda m: save_new_number(m, phone)
    )


# =========================================================
# حفظ الرقم
# =========================================================

def save_new_number(message, phone):

    register_user(message)

    name = message.text.strip()

    if not name or len(name) > 100:

        bot.send_message(
            message.chat.id,
            "❌ الاسم غير صالح.",
            reply_markup=main_keyboard()
        )

        return

    country = get_country(phone)

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
<b>✅ تم تسجيل رقمك</b>

📞 الرقم:
<code>{phone}</code>

👤 الاسم:
<b>{name}</b>

🌍 الدولة:
<b>{country}</b>

يمكنك حذف الرقم لاحقًا من خلال زر 🗑 حذف رقمي.
""",
            reply_markup=main_keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            "⚠️ تعذر تسجيل الرقم لأنه موجود بالفعل.",
            reply_markup=main_keyboard()
        )


# =========================================================
# حذف الرقم
# =========================================================

def process_delete(message):

    register_user(message)

    phone = normalize_phone(message.text)

    if not phone:

        bot.send_message(
            message.chat.id,
            "❌ الرقم غير صحيح.",
            reply_markup=main_keyboard()
        )

        return

    deleted = delete_number(
        phone,
        message.from_user.id
    )

    if deleted:

        bot.send_message(
            message.chat.id,
            f"""
<b>✅ تم حذف الرقم</b>

<code>{phone}</code>

لن يظهر الرقم الآن في دليل البوت.
""",
            reply_markup=main_keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            """
❌ لم يتم العثور على رقم مسجل باسمك.

يمكنك حذف الأرقام التي قمت بتسجيلها فقط.
""",
            reply_markup=main_keyboard()
        )


# =========================================================
# الرسائل العادية
# =========================================================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    register_user(message)

    text = message.text.strip()

    if text.startswith("+") or text.isdigit():

        phone = normalize_phone(text)

        if phone:

            process_search(message)

            return

    bot.send_message(
        message.chat.id,
        """
❓ لم أفهم الأمر.

استخدم /start لفتح القائمة الرئيسية.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# تشغيل البوت
# =========================================================

if __name__ == "__main__":

    print("=" * 45)
    print(f"📞 {BOT_NAME}")
    print(f"🚀 Version: {BOT_VERSION}")
    print("🤖 Bot is running...")
    print("=" * 45)

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )