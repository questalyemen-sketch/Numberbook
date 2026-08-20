import phonenumbers

from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    geocoder,
    carrier
)


# =========================================================
# تحليل الرقم
# =========================================================

def analyze_phone(phone, default_region="YE"):
    """
    تحليل رقم الهاتف وإرجاع معلومات منظمة عنه.
    """

    if not phone:
        return None

    phone = str(phone).strip()

    # تحويل 00 إلى +
    if phone.startswith("00"):
        phone = "+" + phone[2:]

    try:

        number = phonenumbers.parse(
            phone,
            default_region
        )

    except NumberParseException:

        return None

    # التحقق الأساسي
    possible = phonenumbers.is_possible_number(number)
    valid = phonenumbers.is_valid_number(number)

    # الرقم بصيغة دولية
    international = phonenumbers.format_number(
        number,
        PhoneNumberFormat.INTERNATIONAL
    )

    # الرقم بصيغة E.164
    e164 = phonenumbers.format_number(
        number,
        PhoneNumberFormat.E164
    )

    # الدولة / المنطقة
    region = phonenumbers.region_code_for_number(number)

    country = geocoder.description_for_number(
        number,
        "ar"
    )

    if not country:
        country = geocoder.description_for_number(
            number,
            "en"
        )

    # شركة الاتصالات إن كانت متوفرة
    network = carrier.name_for_number(
        number,
        "ar"
    )

    if not network:
        network = carrier.name_for_number(
            number,
            "en"
        )

    # نوع الرقم
    number_type = phonenumbers.number_type(number)

    type_names = {
        PhoneNumberType.MOBILE: "هاتف محمول 📱",
        PhoneNumberType.FIXED_LINE: "خط ثابت ☎️",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "ثابت أو محمول",
        PhoneNumberType.VOIP: "VoIP 🌐",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.PERSONAL_NUMBER: "رقم شخصي",
        PhoneNumberType.PREMIUM_RATE: "رقم مدفوع Premium",
        PhoneNumberType.SHARED_COST: "تكلفة مشتركة",
        PhoneNumberType.TOLL_FREE: "رقم مجاني",
        PhoneNumberType.UAN: "رقم موحد",
        PhoneNumberType.UNKNOWN: "غير معروف"
    }

    type_name = type_names.get(
        number_type,
        "غير معروف"
    )

    return {
        "valid": valid,
        "possible": possible,
        "e164": e164,
        "international": international,
        "region": region or "غير معروف",
        "country": country or "غير معروف",
        "carrier": network or "غير متوفر",
        "type": type_name
    }


# =========================================================
# توحيد الرقم
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
# التحقق من الرقم
# =========================================================

def is_valid_phone(phone, default_region="YE"):

    result = analyze_phone(
        phone,
        default_region
    )

    if not result:
        return False

    return result["valid"]


# =========================================================
# الحصول على نوع الرقم
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
# الحصول على الدولة
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
# اختبار الملف مباشرة
# =========================================================

if __name__ == "__main__":

    test_number = "+967771234567"

    result = analyze_phone(test_number)

    if result:

        print("=" * 45)
        print("📞 Numberbook Phone Engine")
        print("=" * 45)

        for key, value in result.items():
            print(f"{key}: {value}")

    else:

        print("❌ تعذر تحليل الرقم.")