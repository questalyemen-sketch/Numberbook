import asyncio
import html

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
# Sherlock
# =========================================================

from sherlock_service import (
    clean_username,
    search_username_async,
    format_results,
    split_message,
    get_platforms
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
# جلسات Sherlock
# =========================================================

# chat_id -> قائمة المنصات المختارة
sherlock_sessions = {}


# =========================================================
# القائمة الرئيسية
# =========================================================

def main_keyboard():

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

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
            "🕵️ Sherlock",
            callback_data="sherlock"
        ),
        types.InlineKeyboardButton(
            "➕ إضافة رقمي",
            callback_data="add"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🗑 حذف رقمي",
            callback_data="delete"
        ),
        types.InlineKeyboardButton(
            "📊 الإحصائيات",
            callback_data="stats"
        )
    )

    keyboard.add(
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
<b>📞 {html.escape(str(BOT_NAME))}</b>

<b>مرحباً {html.escape(str(message.from_user.first_name or "صديقي"))} 👋</b>

الإصدار: <b>{html.escape(str(BOT_VERSION))}</b>

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

🕵️ <b>Sherlock</b>

ابحث عن Username في مجموعة من أشهر المنصات.

يمكنك اختيار المنصات التي تريد فحصها قبل بدء البحث.

مثال:

<code>github</code>

أو:

<code>@github</code>

➕ <b>إضافة رقمي</b>

تسجيل رقمك في قاعدة Numberbook.

🗑 <b>حذف رقمي</b>

حذف الرقم الذي سجلته بنفسك.

⚠️ نتائج Sherlock هي تطابقات محتملة لاسم المستخدم
ولا تثبت أن الحسابات تعود إلى نفس الشخص.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# Sherlock - لوحة اختيار المنصات
# =========================================================

def sherlock_keyboard(chat_id):

    platforms = get_platforms()

    selected = sherlock_sessions.get(
        chat_id,
        set()
    )

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    for platform_key, platform_name in platforms.items():

        if platform_key in selected:
            text = f"✅ {platform_name}"
        else:
            text = f"⬜ {platform_name}"

        keyboard.add(
            types.InlineKeyboardButton(
                text,
                callback_data=f"shp:{platform_key}"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ اختيار الكل",
            callback_data="shp_all"
        ),
        types.InlineKeyboardButton(
            "🧹 إلغاء الكل",
            callback_data="shp_none"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🚀 بدء البحث",
            callback_data="shp_start"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ إلغاء",
            callback_data="shp_cancel"
        )
    )

    return keyboard


# =========================================================
# Sherlock - رسالة اختيار المنصات
# =========================================================

def sherlock_selection_text(chat_id):

    selected = sherlock_sessions.get(
        chat_id,
        set()
    )

    platforms = get_platforms()

    if selected:

        names = []

        for key in selected:

            if key in platforms:
                names.append(
                    platforms[key]
                )

        selected_text = "
".join(
            f"• {name}"
            for name in names
        )

    else:

        selected_text = (
            "لا توجد منصات محددة حاليًا."
        )

    return f"""
🕵️ <b>Sherlock Username Search</b>

اختر المنصات التي تريد البحث فيها:

<b>المنصات المحددة:</b>

{selected_text}

━━━━━━━━━━━━━━━━━━

بعد اختيار المنصات اضغط:

🚀 <b>بدء البحث</b>
"""


# =========================================================
# بدء Sherlock
# =========================================================

def start_sherlock_selection(message):

    chat_id = message.chat.id

    sherlock_sessions[chat_id] = set()

    bot.send_message(
        chat_id,
        sherlock_selection_text(
            chat_id
        ),
        reply_markup=sherlock_keyboard(
            chat_id
        )
    )


# =========================================================
# /sherlock
# =========================================================

@bot.message_handler(commands=["sherlock"])
def sherlock_command(message):

    register_user(message)

    start_sherlock_selection(
        message
    )


# =========================================================
# طلب Username بعد اختيار المنصات
# =========================================================

def ask_sherlock_username(message):

    chat_id = message.chat.id

    selected = sherlock_sessions.get(
        chat_id,
        set()
    )

    if not selected:

        bot.send_message(
            chat_id,
            """
❌ لم تختر أي منصة.

اختر منصة واحدة على الأقل لبدء البحث.
""",
            reply_markup=sherlock_keyboard(
                chat_id
            )
        )

        return

    selected_count = len(
        selected
    )

    bot.send_message(
        chat_id,
        f"""
🕵️ <b>Sherlock Username Search</b>

تم اختيار <b>{selected_count}</b> منصة.

أرسل الآن Username الذي تريد البحث عنه.

مثال:

<code>github</code>

أو:

<code>@github</code>

⏳ سيتم فحص المنصات التي اخترتها فقط.
""",
        reply_markup=types.ReplyKeyboardRemove()
    )

    bot.register_next_step_handler(
        bot.send_message(
            chat_id,
            "👤 أرسل Username الآن:"
        ),
        process_sherlock_username
    )


# =========================================================
# تنفيذ Sherlock
# =========================================================

def process_sherlock_username(message):

    register_user(message)

    chat_id = message.chat.id

    if not message.text:

        bot.send_message(
            chat_id,
            "❌ أرسل Username نصيًا.",
            reply_markup=main_keyboard()
        )

        return

    try:

        username = clean_username(
            message.text
        )

    except ValueError as error:

        bot.send_message(
            chat_id,
            f"""
❌ <b>Username غير صالح</b>

{html.escape(str(error))}

مثال صحيح:

<code>github</code>
""",
            reply_markup=main_keyboard()
        )

        return

    selected = sherlock_sessions.get(
        chat_id,
        set()
    )

    if not selected:

        bot.send_message(
            chat_id,
            "❌ لم يتم اختيار أي منصة.",
            reply_markup=main_keyboard()
        )

        return

    # -----------------------------------------------------
    # أسماء المنصات
    # -----------------------------------------------------

    platforms = get_platforms()

    selected_names = []

    for key in selected:

        if key in platforms:

            selected_names.append(
                platforms[key]
            )

    # -----------------------------------------------------
    # رسالة الانتظار
    # -----------------------------------------------------

    selected_text = ", ".join(
        selected_names
    )

    waiting_message = bot.send_message(
        chat_id,
        f"""
🕵️ <b>Sherlock</b>

👤 Username:
<code>{html.escape(username)}</code>

🌐 المنصات:
{html.escape(selected_text)}

🔎 <b>جارٍ البحث...</b>

⏳ يتم فحص المنصات المحددة فقط.
"""
    )

    try:

        # -------------------------------------------------
        # تشغيل Sherlock
        # -------------------------------------------------

        results = asyncio.run(
            search_username_async(
                username,
                timeout=8,
                selected_platforms=list(
                    selected
                )
            )
        )

        # -------------------------------------------------
        # بناء النتيجة
        # -------------------------------------------------

        result_text = format_results(
            username,
            results
        )

        # -------------------------------------------------
        # إضافة معلومات البحث
        # -------------------------------------------------

        result_text += (
            "

"
            "🌐 <b>المنصات التي تم اختيارها:</b>
"
            + html.escape(
                selected_text
            )
        )

        # -------------------------------------------------
        # حذف رسالة الانتظار
        # -------------------------------------------------

        try:

            bot.delete_message(
                chat_id,
                waiting_message.message_id
            )

        except Exception:

            pass

        # -------------------------------------------------
        # تقسيم الرسالة إذا كانت طويلة
        # -------------------------------------------------

        chunks = split_message(
            result_text
        )

        for chunk in chunks:

            bot.send_message(
                chat_id,
                chunk
            )

        # -------------------------------------------------
        # زر العودة
        # -------------------------------------------------

        bot.send_message(
            chat_id,
            "اختر خدمة أخرى 👇",
            reply_markup=main_keyboard()
        )

    except Exception as error:

        print(
            "❌ Sherlock Error:",
            repr(error)
        )

        try:

            bot.delete_message(
                chat_id,
                waiting_message.message_id
            )

        except Exception:

            pass

        bot.send_message(
            chat_id,
            f"""
❌ <b>حدث خطأ أثناء تشغيل Sherlock</b>

لم يتمكن محرك البحث من إكمال العملية.

يمكنك المحاولة مرة أخرى.

<code>{html.escape(str(error)[:500])}</code>
""",
            reply_markup=main_keyboard()
        )

    finally:

        # -------------------------------------------------
        # تنظيف جلسة Sherlock
        # -------------------------------------------------

        sherlock_sessions.pop(
            chat_id,
            None
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

    if not phone_source:

        return None

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

    registered_name = "غير مسجل"

    numberbook_found = False

    if numberbook_source:

        if numberbook_source.get(
            "found"
        ):

            numberbook_found = True

            registered_name = (
                numberbook_source.get(
                    "name"
                )
                or
                "غير مسجل"
            )

    veriphone_ok = False

    veriphone_country = None
    veriphone_type = None
    veriphone_carrier = None
    veriphone_valid = None

    if veriphone_source:

        if veriphone_source.get(
            "success"
        ):

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

    valid_status = (
        "✅ رقم صالح"
        if search_result["valid"]
        else
        "❌ رقم غير صالح"
    )

    if search_result["numberbook_found"]:

        numberbook_status = (
            "✅ الرقم موجود في Numberbook"
        )

    else:

        numberbook_status = (
            "❌ الرقم غير موجود في Numberbook"
        )

    text = f"""
<b>🔎 نتيجة البحث</b>

📞 <b>الرقم:</b>
<code>{html.escape(str(search_result["phone"]))}</code>

🌍 <b>الدولة:</b>
{html.escape(str(search_result["country"]))}

📱 <b>نوع الرقم:</b>
{html.escape(str(search_result["type"]))}

📡 <b>شركة الاتصالات:</b>
{html.escape(str(search_result["carrier"]))}

🔢 <b>الصيغة الدولية:</b>
<code>{html.escape(str(search_result["international"]))}</code>

<b>{valid_status}</b>

━━━━━━━━━━━━━━

👤 <b>الاسم في Numberbook:</b>
{html.escape(str(search_result["name"]))}

{numberbook_status}
"""

    if search_result["veriphone_ok"]:

        text += """

━━━━━━━━━━━━━━

🌐 <b>Veriphone</b>

"""

        if search_result["veriphone_country"]:

            text += (
                "🌍 الدولة: "
                + html.escape(
                    str(
                        search_result[
                            "veriphone_country"
                        ]
                    )
                )
                + "
"
            )

        if search_result["veriphone_type"]:

            text += (
                "📱 النوع: "
                + html.escape(
                    str(
                        search_result[
                            "veriphone_type"
                        ]
                    )
                )
                + "
"
            )

        if search_result["veriphone_carrier"]:

            text += (
                "📡 الشركة: "
                + html.escape(
                    str(
                        search_result[
                            "veriphone_carrier"
                        ]
                    )
                )
                + "
"
            )

        if search_result[
            "veriphone_valid"
        ] is not None:

            external_valid = (
                "✅ صالح"
                if search_result[
                    "veriphone_valid"
                ]
                else
                "❌ غير صالح"
            )

            text += (
                "🔍 التحقق الخارجي: "
                + external_valid
                + "
"
            )

    text += """

━━━━━━━━━━━━━━

📚 <b>مصادر المعلومات:</b>

📱 Phone Engine
👤 Numberbook
"""

    if search_result["veriphone_ok"]:

        text += "🌐 Veriphone
"

    else:

        text += (
            "🌐 Veriphone: "
            "غير متاح حاليًا
"
        )

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

    try:

        search_result = build_search_result(
            result["e164"]
        )

    except Exception as error:

        print(
            f"❌ Data Sources Error: {error}"
        )

        search_result = None

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
<code>{html.escape(str(result["e164"]))}</code>

🌍 الدولة:
<b>{html.escape(str(result["country"]))}</b>

📍 المنطقة:
<b>{html.escape(str(result["region"]))}</b>

📱 نوع الرقم:
<b>{html.escape(str(result["type"]))}</b>

📡 شركة الاتصالات:
<b>{html.escape(str(result["carrier"]))}</b>

🔢 الصيغة الدولية:
<code>{html.escape(str(result["international"]))}</code>

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

    valid = (
        "✅ صالح"
        if search_result["valid"]
        else
        "❌ غير صالح"
    )

    text = f"""
<b>📱 معلومات الرقم</b>

📞 الرقم:
<code>{html.escape(str(search_result["phone"]))}</code>

🌍 الدولة:
<b>{html.escape(str(search_result["country"]))}</b>

📱 نوع الرقم:
<b>{html.escape(str(search_result["type"]))}</b>

📡 شركة الاتصالات:
<b>{html.escape(str(search_result["carrier"]))}</b>

🔢 الصيغة الدولية:
<code>{html.escape(str(search_result["international"]))}</code>

━━━━━━━━━━━━━━

🔍 التحقق:
{valid}

👤 الاسم في Numberbook:
<b>{html.escape(str(search_result["name"]))}</b>
"""

    if search_result["veriphone_ok"]:

        if search_result["veriphone_valid"] is True:

            external_status = "✅ صالح"

        elif search_result["veriphone_valid"] is False:

            external_status = "❌ غير صالح"

        else:

            external_status = "غير متوفر"

        text += f"""

🌐 <b>Veriphone</b>

📱 النوع:
{html.escape(str(search_result["veriphone_type"] or "غير متوفر"))}

📡 الشركة:
{html.escape(str(search_result["veriphone_carrier"] or "غير متوفر"))}

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
            "❌ أرسل رقمًا صحيحًا.",
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

    existing = find_number(
        phone
    )

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
<code>{html.escape(str(phone))}</code>

👤 الاسم:
<b>{html.escape(str(name))}</b>

🌍 الدولة:
<b>{html.escape(str(country))}</b>

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
            "❌ أرسل الرقم.",
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

<code>{html.escape(str(result["e164"]))}</code>
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
# الأزرار
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callback_handler(call):

    chat_id = call.message.chat.id

    # =====================================================
    # Sherlock
    # =====================================================

    if call.data == "sherlock":

        bot.answer_callback_query(
            call.id
        )

        start_sherlock_selection(
            call.message
        )

        return

    # =====================================================
    # اختيار منصة Sherlock
    # =====================================================

    if call.data.startswith(
        "shp:"
    ):

        bot.answer_callback_query(
            call.id
        )

        platform = call.data[
            4:
        ]

        if chat_id not in sherlock_sessions:

            sherlock_sessions[
                chat_id
            ] = set()

        selected = sherlock_sessions[
            chat_id
        ]

        if platform in selected:

            selected.remove(
                platform
            )

        else:

            selected.add(
                platform
            )

        try:

            bot.edit_message_text(
                sherlock_selection_text(
                    chat_id
                ),
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=sherlock_keyboard(
                    chat_id
                )
            )

        except Exception as error:

            print(
                "Sherlock keyboard update:",
                error
            )

        return

    # =====================================================
    # اختيار الكل
    # =====================================================

    if call.data == "shp_all":

        bot.answer_callback_query(
            call.id
        )

        sherlock_sessions[
            chat_id
        ] = set(
            get_platforms().keys()
        )

        try:

            bot.edit_message_text(
                sherlock_selection_text(
                    chat_id
                ),
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=sherlock_keyboard(
                    chat_id
                )
            )

        except Exception as error:

            print(
                "Sherlock all error:",
                error
            )

        return

    # =====================================================
    # إلغاء الكل
    # =====================================================

    if call.data == "shp_none":

        bot.answer_callback_query(
            call.id
        )

        sherlock_sessions[
            chat_id
        ] = set()

        try:

            bot.edit_message_text(
                sherlock_selection_text(
                    chat_id
                ),
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=sherlock_keyboard(
                    chat_id
                )
            )

        except Exception as error:

            print(
                "Sherlock none error:",
                error
            )

        return

    # =====================================================
    # بدء البحث
    # =====================================================

    if call.data == "shp_start":

        bot.answer_callback_query(
            call.id
        )

        selected = sherlock_sessions.get(
            chat_id,
            set()
        )

        if not selected:

            bot.answer_callback_query(
                call.id,
                "❌ اختر منصة واحدة على الأقل.",
                show_alert=True
            )

            return

        ask_sherlock_username(
            call.message
        )

        return

    # =====================================================
    # إلغاء Sherlock
    # =====================================================

    if call.data == "shp_cancel":

        bot.answer_callback_query(
            call.id,
            "تم إلغاء البحث."
        )

        sherlock_sessions.pop(
            chat_id,
            None
        )

        bot.send_message(
            chat_id,
            "❌ تم إلغاء Sherlock.",
            reply_markup=main_keyboard()
        )

        return

    # =====================================================
    # البحث عن رقم
    # =====================================================

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

        return

    # =====================================================
    # معلومات الرقم
    # =====================================================

    if call.data == "info":

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

        return

    # =====================================================
    # إضافة رقم
    # =====================================================

    if call.data == "add":

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

        return

    # =====================================================
    # حذف رقم
    # =====================================================

    if call.data == "delete":

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

        return

    # =====================================================
    # الإحصائيات
    # =====================================================

    if call.data == "stats":

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

        return

    # =====================================================
    # المساعدة
    # =====================================================

    if call.data == "help":

        bot.answer_callback_query(
            call.id
        )

        help_command(
            call.message
        )

        return


# =========================================================
# الرسائل العادية
# =========================================================

@bot.message_handler(
    func=lambda message: True
)
def handle_message(message):

    register_user(message)

    if not message.text:

        return

    result = analyze_phone(
        message.text,
        default_region="YE"
    )

    if result and result["possible"]:

        process_search(
            message
        )

        return

    bot.send_message(
        message.chat.id,
        """
❓ لم أفهم طلبك.

استخدم:

/start

لفتح القائمة الرئيسية.

أو:

/sherlock

لبحث Username.
""",
        reply_markup=main_keyboard()
    )


# =========================================================
# اختبار بسيط لـ Enrichment
# =========================================================

@bot.message_handler(commands=["testgithub"])
def test_github_simple(message):
    """
    اختبار بسيط جدًا: /testgithub <username>
    يعرض معلومات GitHub فقط
    """
    args = message.text.split()
    
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ اكتب: /testgithub <username>

مثال:
/testgithub torvalds",
            reply_markup=main_keyboard()
        )
        return
    
    username = args[1]
    
    bot.send_message(
        message.chat.id,
        f"🔎 جاري البحث عن <code>{html.escape(username)}</code> في GitHub...",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    async def get_github():
        from platform_enrichment import enrich_account
        
        result = await enrich_account("github", username, timeout=8)
        
        if result["found"]:
            text = f"""
✅ <b>GitHub - تم العثور على الحساب</b>

👤 الاسم: <code>{html.escape(str(result['display_name'] or 'غير متوفر'))}</code>

📝 النبذة: <code>{html.escape(str(result['bio'] or 'لا توجد'))}</code>

👥 المتابعون: <code>{result['followers']}</code>

📊 المشاريع: <code>{result['posts']}</code>

📍 الموقع: <code>{html.escape(str(result['location'] or 'غير متوفر'))}</code>

🔗 <a href="{html.escape(result['url'])}">{html.escape(result['url'])}</a>
"""
        else:
            text = f"""
❌ <b>GitHub - الحساب غير موجود</b>

Username: <code>{html.escape(username)}</code>

🔗 <a href="{html.escape(result['url'])}">{html.escape(result['url'])}</a>
"""
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    
    asyncio.run(get_github())


# =========================================================
# التشغيل
# =========================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        f"📞 {BOT_NAME}"
    )

    print(
        f"🚀 Version: {BOT_VERSION}"
    )

    print(
        "📱 Phone Engine: ACTIVE"
    )

    print(
        "👤 Numberbook: ACTIVE"
    )

    print(
        "🌐 Veriphone: CONNECTED"
    )

    print(
        "🕵️ Sherlock: ACTIVE"
    )

    print(
        "🎯 Sherlock Platforms: 10"
    )

    print(
        "🤖 Bot is running..."
    )

    print(
        "=" * 60
    )

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )