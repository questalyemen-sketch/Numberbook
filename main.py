import asyncio
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

from data_sources import (
    collect_phone_data
)

# =========================================================
# 🕵️ Sherlock
# =========================================================

from sherlock_service import (
    search_username_async,
    format_results,
    split_message,
    clean_username
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

    # =====================================================
    # 🕵️ Sherlock
    # =====================================================

    keyboard.add(
        types.InlineKeyboardButton(
            "🕵️ Sherlock",
            callback_data="sherlock"
        )
    )

    return keyboard


# =========================================================
# تسجيل المستخدم
# =========================================================

def register_user(message):

    if not message.from_user:
        return

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
👤 Numberbook
🌐 مصادر بيانات خارجية
🕵️ Sherlock Username Search
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

🌐 يتم استخدام مصادر بيانات خارجية عند توفرها.

🕵️ <b>Sherlock</b>

يبحث عن اسم مستخدم في المواقع والخدمات
التي يدعمها Sherlock.

مثال:

<code>/sherlock username</code>

أو اضغط زر 🕵️ Sherlock.

➕ <b>إضافة رقمي</b>

تسجيل رقمك في قاعدة Numberbook.

🗑 <b>حذف رقمي</b>

حذف الرقم الذي سجلته بنفسك.

⚠️ يعتمد النظام على البيانات المسموح باستخدامها.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# 🕵️ أمر Sherlock
# =========================================================

@bot.message_handler(commands=["sherlock"])
def sherlock_command(message):

    register_user(message)

    # -----------------------------------------------------
    # إذا كان الأمر بالشكل:
    # /sherlock username
    # -----------------------------------------------------

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) > 1:

        username = parts[1].strip()

        process_sherlock_username(
            message,
            username
        )

        return

    # -----------------------------------------------------
    # إذا لم يكتب Username
    # -----------------------------------------------------

    msg = bot.send_message(
        message.chat.id,
        """
<b>🕵️ Sherlock Username Search</b>

أرسل اسم المستخدم الذي تريد البحث عنه.

مثال:

<code>github</code>

أو:

<code>@github</code>

⏳ بعد الإرسال سيبدأ البحث.
"""
    )

    bot.register_next_step_handler(
        msg,
        process_sherlock
    )


# =========================================================
# 🕵️ استقبال Username من المستخدم
# =========================================================

def process_sherlock(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل Username صحيحًا.",
            reply_markup=main_keyboard()
        )

        return

    process_sherlock_username(
        message,
        message.text.strip()
    )


# =========================================================
# 🔎 تنفيذ بحث Sherlock
# =========================================================

def process_sherlock_username(
    message,
    username
):

    register_user(message)

    # -----------------------------------------------------
    # تنظيف Username
    # -----------------------------------------------------

    try:

        username = clean_username(
            username
        )

    except ValueError as error:

        bot.send_message(
            message.chat.id,
            f"""
❌ <b>Username غير صالح</b>

{error}
""",
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # رسالة الانتظار
    # -----------------------------------------------------

    waiting_message = bot.send_message(
        message.chat.id,
        f"""
🕵️ <b>Sherlock</b>

👤 Username:
<code>{username}</code>

🔎 جارٍ البحث...

⏳ يتم فحص المواقع المتاحة.
قد يستغرق البحث بعض الوقت.
"""
    )

    try:

        # =================================================
        # تشغيل Sherlock بدون تجميد البوت
        # =================================================

        results = asyncio.run(
            search_username_async(
                username,
                timeout=20
            )
        )

        # =================================================
        # تحويل النتائج إلى رسالة
        # =================================================

        text = format_results(
            username,
            results
        )

        # =================================================
        # حذف رسالة الانتظار
        # =================================================

        try:

            bot.delete_message(
                message.chat.id,
                waiting_message.message_id
            )

        except Exception:
            pass

        # =================================================
        # تقسيم الرسالة إذا كانت طويلة
        # =================================================

        chunks = split_message(
            text,
            max_length=4000
        )

        for index, chunk in enumerate(
            chunks
        ):

            is_last = (
                index == len(chunks) - 1
            )

            bot.send_message(
                message.chat.id,
                chunk,
                reply_markup=(
                    main_keyboard()
                    if is_last
                    else None
                )
            )

    # =====================================================
    # Username غير صالح
    # =====================================================

    except ValueError as error:

        try:

            bot.delete_message(
                message.chat.id,
                waiting_message.message_id
            )

        except Exception:
            pass

        bot.send_message(
            message.chat.id,
            f"""
❌ <b>Username غير صالح</b>

{error}
""",
            reply_markup=main_keyboard()
        )

    # =====================================================
    # خطأ عام
    # =====================================================

    except Exception as error:

        print(
            "❌ Sherlock Error:"
        )

        print(
            repr(error)
        )

        try:

            bot.delete_message(
                message.chat.id,
                waiting_message.message_id
            )

        except Exception:
            pass

        bot.send_message(
            message.chat.id,
            """
⚠️ <b>حدث خطأ أثناء تشغيل Sherlock.</b>

قد يكون السبب:

• مشكلة في تشغيل Sherlock
• مشكلة في أحد مصادر البحث
• انتهاء مهلة الاتصال
• تعذر الوصول لبعض المواقع
• مشكلة في تثبيت إحدى المكتبات

📋 راجع Railway Logs لمعرفة الخطأ بالتحديد.
""",
            reply_markup=main_keyboard()
        )


# =========================================================
# الأزرار
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):

    chat_id = call.message.chat.id

    # -----------------------------------------------------
    # البحث
    # -----------------------------------------------------

    if call.data == "search":

        bot.answer_callback_query(
            call.id
        )

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

    # -----------------------------------------------------
    # المعلومات
    # -----------------------------------------------------

    elif call.data == "info":

        bot.answer_callback_query(
            call.id
        )

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

    # -----------------------------------------------------
    # إضافة رقم
    # -----------------------------------------------------

    elif call.data == "add":

        bot.answer_callback_query(
            call.id
        )

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

    # -----------------------------------------------------
    # حذف رقم
    # -----------------------------------------------------

    elif call.data == "delete":

        bot.answer_callback_query(
            call.id
        )

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

    # -----------------------------------------------------
    # الإحصائيات
    # -----------------------------------------------------

    elif call.data == "stats":

        bot.answer_callback_query(
            call.id
        )

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

    # -----------------------------------------------------
    # المساعدة
    # -----------------------------------------------------

    elif call.data == "help":

        bot.answer_callback_query(
            call.id
        )

        help_command(
            call.message
        )

    # -----------------------------------------------------
    # 🕵️ Sherlock
    # -----------------------------------------------------

    elif call.data == "sherlock":

        bot.answer_callback_query(
            call.id
        )

        msg = bot.send_message(
            chat_id,
            """
<b>🕵️ Sherlock Username Search</b>

أرسل Username الذي تريد البحث عنه.

مثال:

<code>github</code>

أو:

<code>@github</code>

⏳ سيتم البحث في المواقع التي يدعمها Sherlock.
"""
        )

        bot.register_next_step_handler(
            msg,
            process_sherlock
        )


# =========================================================
# بناء نتيجة البحث من Data Sources
# =========================================================

def build_search_result(phone):

    data = collect_phone_data(
        phone,
        default_region="YE"
    )

    sources = data.get(
        "sources",
        []
    )

    phone_source = None
    numberbook_source = None
    veriphone_source = None

    # -----------------------------------------------------
    # استخراج المصادر
    # -----------------------------------------------------

    for source in sources:

        source_name = source.get(
            "source"
        )

        if source_name == "Phone Engine":

            phone_source = source

        elif source_name == "Numberbook":

            numberbook_source = source

        elif source_name == "Veriphone":

            veriphone_source = source

    # -----------------------------------------------------
    # حماية
    # -----------------------------------------------------

    if not phone_source:

        return None

    # -----------------------------------------------------
    # البيانات الأساسية
    # -----------------------------------------------------

    e164 = phone_source.get(
        "phone"
    )

    country = phone_source.get(
        "country",
        "غير معروف"
    )

    number_type = phone_source.get(
        "type",
        "غير معروف"
    )

    carrier_name = phone_source.get(
        "carrier",
        "غير متوفر"
    )

    international = phone_source.get(
        "international",
        "غير متوفر"
    )

    valid = phone_source.get(
        "valid",
        False
    )

    # -----------------------------------------------------
    # Numberbook
    # -----------------------------------------------------

    registered_name = "غير مسجل"

    numberbook_found = False

    if numberbook_source:

        if numberbook_source.get("found"):

            numberbook_found = True

            registered_name = (
                numberbook_source.get("name")
                or
                "غير مسجل"
            )

    # -----------------------------------------------------
    # Veriphone
    # -----------------------------------------------------

    veriphone_ok = False

    veriphone_country = None
    veriphone_type = None
    veriphone_carrier = None
    veriphone_valid = None

    if veriphone_source:

        if veriphone_source.get("success"):

            veriphone_ok = True

            veriphone_country = (
                veriphone_source.get(
                    "country"
                )
            )

            veriphone_type = (
                veriphone_source.get(
                    "type"
                )
            )

            veriphone_carrier = (
                veriphone_source.get(
                    "carrier"
                )
            )

            veriphone_valid = (
                veriphone_source.get(
                    "valid"
                )
            )

    return {
        "phone": e164,
        "country": country,
        "type": number_type,
        "carrier": carrier_name,
        "international": international,
        "valid": valid,

        "name": registered_name,
        "numberbook_found": numberbook_found,

        "veriphone_ok": veriphone_ok,
        "veriphone_country": veriphone_country,
        "veriphone_type": veriphone_type,
        "veriphone_carrier": veriphone_carrier,
        "veriphone_valid": veriphone_valid
    }


# =========================================================
# 🔎 البحث عن رقم
# =========================================================

def process_search(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل رقم هاتف صحيح.",
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # التحليل الأولي لتوحيد الرقم
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
            "❌ الرقم غير محتمل وفق نظام الترقيم.",
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
    # Data Sources Engine
    # -----------------------------------------------------

    try:

        search_result = build_search_result(
            phone
        )

    except Exception as error:

        print(
            f"❌ Data Sources Error: {error}"
        )

        bot.send_message(
            message.chat.id,
            """
⚠️ حدث خطأ أثناء جمع البيانات.

تم الاحتفاظ بمحرك البحث الأساسي ويمكنك المحاولة مرة أخرى.
""",
            reply_markup=main_keyboard()
        )

        return

    if not search_result:

        bot.send_message(
            message.chat.id,
            "❌ تعذر تحليل الرقم.",
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # حالة الرقم
    # -----------------------------------------------------

    valid_status = (
        "✅ رقم صالح"
        if search_result["valid"]
        else
        "❌ رقم غير صالح"
    )

    # -----------------------------------------------------
    # حالة Numberbook
    # -----------------------------------------------------

    if search_result["numberbook_found"]:

        numberbook_status = (
            "✅ الرقم موجود في Numberbook"
        )

    else:

        numberbook_status = (
            "❌ الرقم غير موجود في Numberbook"
        )

    # -----------------------------------------------------
    # بناء الرسالة
    # -----------------------------------------------------

    text = f"""
<b>🔎 نتيجة البحث</b>

📞 <b>الرقم:</b>
<code>{search_result["phone"]}</code>

🌍 <b>الدولة:</b>
{search_result["country"]}

📱 <b>نوع الرقم:</b>
{search_result["type"]}

📡 <b>شركة الاتصالات:</b>
{search_result["carrier"]}

🔢 <b>الصيغة الدولية:</b>
<code>{search_result["international"]}</code>

<b>{valid_status}</b>

━━━━━━━━━━━━━━

👤 <b>الاسم في Numberbook:</b>
{search_result["name"]}

{numberbook_status}
"""

    # -----------------------------------------------------
    # Veriphone
    # -----------------------------------------------------

    if search_result["veriphone_ok"]:

        text += """

━━━━━━━━━━━━━━

🌐 <b>Veriphone</b>

"""

        if search_result["veriphone_country"]:

            text += (
                f"🌍 الدولة: "
                f"{search_result['veriphone_country']}\n"
            )

        if search_result["veriphone_type"]:

            text += (
                f"📱 النوع: "
                f"{search_result['veriphone_type']}\n"
            )

        if search_result["veriphone_carrier"]:

            text += (
                f"📡 الشركة: "
                f"{search_result['veriphone_carrier']}\n"
            )

        if search_result["veriphone_valid"] is not None:

            external_valid = (
                "✅ صالح"
                if search_result["veriphone_valid"]
                else
                "❌ غير صالح"
            )

            text += (
                f"🔍 التحقق الخارجي: "
                f"{external_valid}\n"
            )

    # -----------------------------------------------------
    # مصادر المعلومات
    # -----------------------------------------------------

    text += """

━━━━━━━━━━━━━━

📚 <b>مصادر المعلومات:</b>

📱 Phone Engine
👤 Numberbook
"""

    if search_result["veriphone_ok"]:

        text += "🌐 Veriphone\n"

    else:

        text += (
            "🌐 Veriphone: "
            "غير متاح حاليًا\n"
        )

    # -----------------------------------------------------
    # إرسال النتيجة
    # -----------------------------------------------------

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
            "❌ أرسل رقم هاتف صحيح.",
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
            "❌ الرقم غير صالح أو غير مفهوم.",
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

    # -----------------------------------------------------
    # Data Sources
    # -----------------------------------------------------

    try:

        search_result = build_search_result(
            result["e164"]
        )

    except Exception as error:

        print(
            f"❌ Data Sources Error: {error}"
        )

        search_result = None

    # -----------------------------------------------------
    # إذا تعذر المصدر الجديد
    # -----------------------------------------------------

    if not search_result:

        valid = (
            "✅ صالح"
            if result["valid"]
            else
            "❌ غير صالح"
        )

        possible = (
            "✅ محتمل"
            if result["possible"]
            else
            "❌ غير محتمل"
        )

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

📚 <b>المصدر:</b>
📱 Phone Engine
"""

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # النتيجة
    # -----------------------------------------------------

    valid = (
        "✅ صالح"
        if search_result["valid"]
        else
        "❌ غير صالح"
    )

    text = f"""
<b>📱 معلومات الرقم</b>

📞 الرقم:
<code>{search_result["phone"]}</code>

🌍 الدولة:
<b>{search_result["country"]}</b>

📱 نوع الرقم:
<b>{search_result["type"]}</b>

📡 شركة الاتصالات:
<b>{search_result["carrier"]}</b>

🔢 الصيغة الدولية:
<code>{search_result["international"]}</code>

━━━━━━━━━━━━━━

🔍 التحقق:
{valid}

👤 الاسم في Numberbook:
<b>{search_result["name"]}</b>
"""

    if search_result["veriphone_ok"]:

        external_status = "غير متوفر"

        if search_result["veriphone_valid"] is True:
            external_status = "✅ صالح"

        elif search_result["veriphone_valid"] is False:
            external_status = "❌ غير صالح"

        text += f"""

🌐 <b>Veriphone</b>

📱 النوع:
{search_result["veriphone_type"] or "غير متوفر"}

📡 الشركة:
{search_result["veriphone_carrier"] or "غير متوفر"}

🔍 التحقق الخارجي:
{external_status}
"""

    text += """

━━━━━━━━━━━━━━

📚 <b>مصادر المعلومات:</b>

📱 Phone Engine
👤 Numberbook
"""

    if search_result["veriphone_ok"]:

        text += "🌐 Veriphone"

    else:

        text += "🌐 Veriphone: غير متاح"

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
            "❌ أرسل رقم هاتف صحيح.",
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
# حفظ الرقم
# =========================================================

def save_number(
    message,
    phone,
    country
):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ الاسم غير صالح.",
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
# 🗑 حذف الرقم
# =========================================================

def process_delete(message):

    register_user(message)

    if not message.text:

        bot.send_message(
            message.chat.id,
            "❌ أرسل رقم هاتف صحيح.",
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

    if not message.text:

        return

    # -----------------------------------------------------
    # لا نعالج الأوامر كأرقام هاتف
    # -----------------------------------------------------

    if message.text.startswith("/"):

        return

    # -----------------------------------------------------
    # إذا كان النص رقم هاتف
    # -----------------------------------------------------

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if result and result["possible"]:

        process_search(message)

        return

    # -----------------------------------------------------
    # رسالة غير معروفة
    # -----------------------------------------------------

    bot.send_message(
        message.chat.id,
        """
❓ لم أفهم طلبك.

استخدم:

/start

لفتح القائمة الرئيسية.

أو:

/sherlock username

للبحث عن Username باستخدام Sherlock.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# التشغيل
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print(f"📞 {BOT_NAME}")
    print(f"🚀 Version: {BOT_VERSION}")
    print("📱 Phone Engine: ACTIVE")
    print("👤 Numberbook: ACTIVE")
    print("🌐 Veriphone: CONNECTED")
    print("🔎 Data Sources Engine: ACTIVE")
    print("🕵️ Sherlock: ACTIVE")
    print("🤖 Bot is running...")
    print("=" * 60)

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )