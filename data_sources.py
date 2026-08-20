# =========================================================
# Numberbook - Data Sources Engine
# =========================================================

import time

from phone_utils import analyze_phone
from database import find_number

from external_sources import verify_with_veriphone


# =========================================================
# إعدادات Cache
# =========================================================

CACHE_TTL = 24 * 60 * 60  # 24 ساعة

_veriphone_cache = {}


# =========================================================
# 📱 Phone Engine
# =========================================================

def get_phone_source(phone, default_region="YE"):

    result = analyze_phone(
        phone,
        default_region=default_region
    )

    if not result:
        return None

    return {
        "source": "Phone Engine",
        "source_type": "local",

        "phone": result.get("e164"),
        "international": result.get("international"),

        "country": result.get("country"),
        "region": result.get("region"),

        "type": result.get("type"),
        "carrier": result.get("carrier"),

        "valid": result.get("valid"),
        "possible": result.get("possible"),

        "status": (
            "رقم صالح ✅"
            if result.get("valid")
            else "رقم غير صالح ❌"
        )
    }


# =========================================================
# 👤 Numberbook
# =========================================================

def get_numberbook_source(phone):

    result = find_number(phone)

    if not result:

        return {
            "source": "Numberbook",
            "source_type": "local",

            "found": False,

            "phone": phone,
            "name": None,
            "country": None,
            "owner_user_id": None,
            "created_at": None
        }

    return {
        "source": "Numberbook",
        "source_type": "local",

        "found": True,

        "phone": result[0],
        "name": result[1],
        "country": result[2],
        "owner_user_id": result[3],
        "created_at": result[4]
    }


# =========================================================
# 🌐 Veriphone Cache
# =========================================================

def get_cached_veriphone(phone):

    cached = _veriphone_cache.get(phone)

    if not cached:
        return None

    timestamp = cached.get("_timestamp", 0)

    if time.time() - timestamp > CACHE_TTL:

        del _veriphone_cache[phone]

        return None

    return cached.get("data")


# =========================================================
# 💾 حفظ نتيجة Veriphone في Cache
# =========================================================

def set_cached_veriphone(phone, data):

    _veriphone_cache[phone] = {
        "_timestamp": time.time(),
        "data": data
    }


# =========================================================
# 🌐 Veriphone
# =========================================================

def get_veriphone_source(phone):

    # -----------------------------------------------------
    # محاولة استخدام Cache
    # -----------------------------------------------------

    cached = get_cached_veriphone(phone)

    if cached is not None:

        cached_copy = dict(cached)

        cached_copy["cached"] = True

        return cached_copy

    # -----------------------------------------------------
    # طلب API
    # -----------------------------------------------------

    result = verify_with_veriphone(phone)

    if not result:

        return {
            "source": "Veriphone",
            "source_type": "external",

            "available": False,
            "success": False,

            "error": "لم تصل استجابة من Veriphone"
        }

    # -----------------------------------------------------
    # حفظ النتيجة
    # -----------------------------------------------------

    set_cached_veriphone(
        phone,
        result
    )

    result = dict(result)

    result["cached"] = False

    return result


# =========================================================
# 🔎 مدير مصادر البيانات
# =========================================================

def collect_phone_data(
    phone,
    default_region="YE"
):
    """
    تجميع بيانات الرقم من جميع المصادر.

    المصادر:

    1. Phone Engine
    2. Numberbook
    3. Veriphone
    """

    data = {
        "phone": phone,
        "sources": []
    }

    # =====================================================
    # 📱 Phone Engine
    # =====================================================

    phone_source = get_phone_source(
        phone,
        default_region=default_region
    )

    if phone_source:

        data["sources"].append(
            phone_source
        )

    # =====================================================
    # 👤 Numberbook
    # =====================================================

    normalized_phone = None

    if phone_source:

        normalized_phone = phone_source.get(
            "phone"
        )

    if normalized_phone:

        numberbook_source = get_numberbook_source(
            normalized_phone
        )

        data["sources"].append(
            numberbook_source
        )

    # =====================================================
    # 🌐 Veriphone
    # =====================================================

    if normalized_phone:

        veriphone_source = get_veriphone_source(
            normalized_phone
        )

        data["sources"].append(
            veriphone_source
        )

    return data


# =========================================================
# 🔍 الحصول على مصدر محدد
# =========================================================

def get_source(
    phone,
    source_name,
    default_region="YE"
):

    data = collect_phone_data(
        phone,
        default_region=default_region
    )

    for source in data["sources"]:

        if source.get("source") == source_name:

            return source

    return None


# =========================================================
# 🔍 الحصول على قيمة من المصادر
# =========================================================

def get_source_value(
    phone,
    field,
    default_region="YE"
):

    data = collect_phone_data(
        phone,
        default_region=default_region
    )

    for source in data["sources"]:

        value = source.get(field)

        if value is not None and value != "":

            return {
                "value": value,
                "source": source.get("source"),
                "source_type": source.get(
                    "source_type"
                )
            }

    return None


# =========================================================
# 👤 اسم Numberbook
# =========================================================

def get_numberbook_name(phone):

    source = get_source(
        phone,
        "Numberbook"
    )

    if not source:
        return None

    if not source.get("found"):
        return None

    return source.get("name")


# =========================================================
# 🧪 اختبار المحرك
# =========================================================

if __name__ == "__main__":

    test_number = "+967771234567"

    print()
    print("=" * 65)
    print("🔎 Numberbook Data Sources Engine")
    print("=" * 65)

    result = collect_phone_data(
        test_number
    )

    sources = result.get("sources", [])

    if not sources:

        print("❌ لم يتم العثور على مصادر.")

    else:

        for source in sources:

            print()
            print(
                f"📡 المصدر: "
                f"{source.get('source')}"
            )

            # -------------------------------------------------
            # Phone Engine
            # -------------------------------------------------

            if source.get("source") == "Phone Engine":

                print(
                    f"📞 الرقم: "
                    f"{source.get('phone')}"
                )

                print(
                    f"🌍 الدولة: "
                    f"{source.get('country')}"
                )

                print(
                    f"📍 المنطقة: "
                    f"{source.get('region')}"
                )

                print(
                    f"📱 النوع: "
                    f"{source.get('type')}"
                )

                print(
                    f"📡 الشركة: "
                    f"{source.get('carrier')}"
                )

                print(
                    f"🔢 الدولي: "
                    f"{source.get('international')}"
                )

                print(
                    f"✅ الحالة: "
                    f"{source.get('status')}"
                )

            # -------------------------------------------------
            # Numberbook
            # -------------------------------------------------

            elif source.get("source") == "Numberbook":

                print(
                    f"📞 الرقم: "
                    f"{source.get('phone')}"
                )

                if source.get("found"):

                    print(
                        f"👤 الاسم: "
                        f"{source.get('name')}"
                    )

                    print(
                        "✅ الحالة: موجود في Numberbook"
                    )

                else:

                    print(
                        "👤 الاسم: غير مسجل"
                    )

                    print(
                        "❌ الحالة: غير موجود في Numberbook"
                    )

            # -------------------------------------------------
            # Veriphone
            # -------------------------------------------------

            elif source.get("source") == "Veriphone":

                if source.get("success"):

                    print(
                        "✅ اتصال Veriphone ناجح"
                    )

                    print(
                        f"📞 الرقم: "
                        f"{source.get('e164')}"
                    )

                    print(
                        f"🌍 الدولة: "
                        f"{source.get('country')}"
                    )

                    print(
                        f"📱 النوع: "
                        f"{source.get('type')}"
                    )

                    print(
                        f"📡 الشركة: "
                        f"{source.get('carrier')}"
                    )

                    print(
                        f"🔢 الدولي: "
                        f"{source.get('international')}"
                    )

                    print(
                        f"✅ صالح: "
                        f"{source.get('valid')}"
                    )

                    if source.get("cached"):

                        print(
                            "💾 النتيجة: من Cache"
                        )

                    else:

                        print(
                            "🌐 النتيجة: طلب API جديد"
                        )

                else:

                    print(
                        "❌ Veriphone غير متاح"
                    )

                    print(
                        f"⚠️ السبب: "
                        f"{source.get('error')}"
                    )

    print()
    print("=" * 65)