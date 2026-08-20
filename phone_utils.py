import phonenumbers

from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    geocoder,
    carrier,
)


# =========================================================
# 🇾🇪 أسماء الدول
# =========================================================

COUNTRY_NAMES = {
    "YE": "اليمن 🇾🇪",
    "SA": "السعودية 🇸🇦",
    "AE": "الإمارات 🇦🇪",
    "OM": "عُمان 🇴🇲",
    "QA": "قطر 🇶🇦",
    "KW": "الكويت 🇰🇼",
    "BH": "البحرين 🇧🇭",
    "EG": "مصر 🇪🇬",
    "JO": "الأردن 🇯🇴",
    "IQ": "العراق 🇮🇶",
    "SY": "سوريا 🇸🇾",
    "TR": "تركيا 🇹🇷",
    "GB": "المملكة المتحدة 🇬🇧",
    "US": "الولايات المتحدة 🇺🇸",
}


# =========================================================
# 📱 أنواع أرقام الهاتف
# =========================================================

TYPE_NAMES = {
    PhoneNumberType.MOBILE: "هاتف محمول 📱",
    PhoneNumberType.FIXED_LINE: "خط ثابت ☎️",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "ثابت أو محمول 📱☎️",
    PhoneNumberType.VOIP: "VoIP 🌐",
    PhoneNumberType.PAGER: "Pager",
    PhoneNumberType.PERSONAL_NUMBER: "رقم شخصي",
    PhoneNumberType.PREMIUM_RATE: "رقم مدفوع Premium",
    PhoneNumberType.SHARED_COST: "تكلفة مشتركة",
    PhoneNumberType.TOLL_FREE: "رقم مجاني",
    PhoneNumberType.UAN: "رقم موحد",
    PhoneNumberType.UNKNOWN: "غير معروف",
}


# =========================================================
# 🔢 تنسيق الرقم بشكل مقروء
# =========================================================

def format_readable(number):
    """
    تحويل الرقم إلى صيغة دولية مقروءة.
    مثال:
    +967771234567
    ↓
    +967 77 123 4567
    """

    try:
        return phonenumbers.format_number(
            number,
            PhoneNumberFormat.INTERNATIONAL
        )
    except Exception:
        return "غير متوفر"


# =========================================================
# 🔎 تحليل الرقم
# =========================================================

def analyze_phone(phone, default_region="YE"):
    """
    تحليل رقم الهاتف وإرجاع معلومات منظمة عنه.

    لا تستخدم أي API خارجي.
    تعتمد بالكامل على مكتبة phonenumbers.
    """

    if phone is None:
        return None

    phone = str(phone).strip()

    if not phone:
        return None

    # -----------------------------------------------------
    # تحويل 00XXXXXXXX إلى +XXXXXXXX
    # -----------------------------------------------------

    if phone.startswith("00"):
        phone = "+" + phone[2:]

    try:
        number = phonenumbers.parse(
            phone,
            default_region
        )

    except NumberParseException:
        return None

    except Exception:
        return None

    # -----------------------------------------------------
    # التحقق
    # -----------------------------------------------------

    possible = phonenumbers.is_possible_number(number)
    valid = phonenumbers.is_valid_number(number)

    # -----------------------------------------------------
    # E.164
    # -----------------------------------------------------

    try:
        e164 = phonenumbers.format_number(
            number,
            PhoneNumberFormat.E164
        )
    except Exception:
        e164 = "غير متوفر"

    # -----------------------------------------------------
    # الصيغة الدولية
    # -----------------------------------------------------

    international = format_readable(number)

    # -----------------------------------------------------
    # كود الدولة
    # -----------------------------------------------------

    region = phonenumbers.region_code_for_number(number)

    if not region:
        region = default_region

    # -----------------------------------------------------
    # اسم الدولة
    # -----------------------------------------------------

    country = COUNTRY_NAMES.get(region)

    if not country:
        country = geocoder.description_for_number(
            number,
            "ar"
        )

    if not country:
        country = geocoder.description_for_number(
            number,
            "en"
        )

    if not country:
        country = "غير معروف 🌍"

    # -----------------------------------------------------
    # شركة الاتصالات
    # -----------------------------------------------------

    network = carrier.name_for_number(
        number,
        "ar"
    )

    if not network:
        network = carrier.name_for_number(
            number,
            "en"
        )

    if not network:
        network = "غير متوفر"

    # -----------------------------------------------------
    # نوع الرقم
    # -----------------------------------------------------

    number_type = phonenumbers.number_type(number)

    type_name = TYPE_NAMES.get(
        number_type,
        "غير معروف"
    )

    # -----------------------------------------------------
    # حالة الرقم
    # -----------------------------------------------------

    if valid:
        status = "رقم صالح ✅"
    elif possible:
        status = "رقم محتمل ⚠️"
    else:
        status = "رقم غير صالح ❌"

    # -----------------------------------------------------
    # النتيجة النهائية
    # -----------------------------------------------------

    return {
        "valid": valid,
        "possible": possible,

        "e164": e164,
        "international": international,

        "region": region,
        "country": country,

        "carrier": network,

        "type": type_name,
        "status": status,

        # معلومات إضافية مفيدة للمراحل القادمة
        "country_code": number.country_code,
        "national_number": number.national_number,
    }


# =========================================================
# 🔢 توحيد الرقم
# =========================================================

def normalize_phone(phone, default_region="YE"):
    """
    تحويل الرقم إلى صيغة E.164.

    مثال:
    771234567
    ↓
    +967771234567
    """

    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return None

    if not result["possible"]:
        return None

    return result["e164"]


# =========================================================
# ✅ التحقق من الرقم
# =========================================================

def is_valid_phone(phone, default_region="YE"):
    """
    إرجاع True إذا كان الرقم صالحًا.
    """

    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return False

    return result["valid"]


# =========================================================
# 📱 الحصول على نوع الرقم
# =========================================================

def get_phone_type(phone, default_region="YE"):
    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return "غير معروف"

    return result["type"]


# =========================================================
# 🌍 الحصول على الدولة
# =========================================================

def get_phone_country(phone, default_region="YE"):
    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return "غير معروف"

    return result["country"]


# =========================================================
# 📡 الحصول على شركة الاتصالات
# =========================================================

def get_phone_carrier(phone, default_region="YE"):
    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return "غير متوفر"

    return result["carrier"]


# =========================================================
# 🔢 الحصول على الصيغة الدولية
# =========================================================

def get_international_phone(phone, default_region="YE"):
    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return "غير متوفر"

    return result["international"]


# =========================================================
# 🧪 اختبار الملف مباشرة
# =========================================================

if __name__ == "__main__":

    test_number = "+967771234567"

    result = analyze_phone(test_number)

    print()
    print("=" * 50)
    print("📞 Numberbook Phone Engine")
    print("=" * 50)

    if result:

        print(f"📞 الرقم: {result['e164']}")
        print(f"🌍 الدولة: {result['country']}")
        print(f"📱 نوع الرقم: {result['type']}")
        print(f"📡 شركة الاتصالات: {result['carrier']}")
        print(f"🔢 الصيغة الدولية: {result['international']}")
        print(f"✅ الحالة: {result['status']}")

        print("-" * 50)

        print(f"🌐 كود الدولة: {result['country_code']}")
        print(f"🔢 الرقم المحلي: {result['national_number']}")
        print(f"🗺️ رمز المنطقة: {result['region']}")

    else:

        print("❌ تعذر تحليل الرقم.")

    print("=" * 50)