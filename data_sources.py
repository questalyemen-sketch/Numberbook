# =========================================================
# Numberbook - Data Sources Engine
# =========================================================

from phone_utils import analyze_phone


# =========================================================
# 📱 Phone Engine
# =========================================================

def get_phone_source(phone, default_region="YE"):
    """
    الحصول على معلومات الرقم من محرك الهاتف المحلي.

    المصدر:
    phone_utils / phonenumbers

    لا يستخدم API خارجي.
    """

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
        "status": result.get("status"),
    }


# =========================================================
# 🔎 مدير مصادر البيانات
# =========================================================

def collect_phone_data(phone, default_region="YE"):
    """
    تجميع بيانات الرقم من جميع المصادر المتوفرة.

    حاليًا:
    - Phone Engine

    لاحقًا:
    - Numberbook
    - External Providers
    - مصادر أخرى
    """

    data = {
        "phone": phone,
        "sources": []
    }

    # -----------------------------------------------------
    # Phone Engine
    # -----------------------------------------------------

    phone_data = get_phone_source(
        phone,
        default_region=default_region
    )

    if phone_data:

        data["sources"].append(
            phone_data
        )

    return data


# =========================================================
# 🔍 البحث عن معلومة محددة
# =========================================================

def get_source_value(
    phone,
    field,
    default_region="YE"
):
    """
    الحصول على قيمة معينة من محرك المصادر.

    مثال:

    get_source_value(
        "+967771234567",
        "carrier"
    )
    """

    data = collect_phone_data(
        phone,
        default_region=default_region
    )

    for source in data["sources"]:

        value = source.get(field)

        if value:
            return {
                "value": value,
                "source": source.get("source"),
                "source_type": source.get("source_type")
            }

    return None


# =========================================================
# 🧪 اختبار المحرك
# =========================================================

if __name__ == "__main__":

    test_number = "+967771234567"

    print()
    print("=" * 60)
    print("🔎 Numberbook Data Sources Engine")
    print("=" * 60)

    result = collect_phone_data(
        test_number
    )

    if not result["sources"]:

        print("❌ لم يتم العثور على أي مصدر.")

    else:

        for source in result["sources"]:

            print()
            print(f"📡 المصدر: {source['source']}")
            print(f"📞 الرقم: {source['phone']}")
            print(f"🌍 الدولة: {source['country']}")
            print(f"📍 المنطقة: {source['region']}")
            print(f"📱 النوع: {source['type']}")
            print(f"📡 الشركة: {source['carrier']}")
            print(f"🔢 الدولي: {source['international']}")
            print(f"✅ الحالة: {source['status']}")

    print()
    print("=" * 60)