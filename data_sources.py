# =========================================================
# Numberbook - Data Sources Engine
# =========================================================

from phone_utils import analyze_phone
from database import find_number


# =========================================================
# 📱 Phone Engine
# =========================================================

def get_phone_source(phone, default_region="YE"):
    """
    تحليل الرقم باستخدام محرك Phone Engine.

    المصدر:
    phone_utils / phonenumbers

    لا يستخدم أي API خارجي.
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
# 👤 Numberbook
# =========================================================

def get_numberbook_source(phone):
    """
    البحث عن الرقم داخل قاعدة Numberbook المحلية.

    المصدر:
    Numberbook

    لا يستخدم أي خدمة خارجية.
    """

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
            "created_at": None,
        }

    return {
        "source": "Numberbook",
        "source_type": "local",

        "found": True,

        "phone": result[0],
        "name": result[1],
        "country": result[2],
        "owner_user_id": result[3],
        "created_at": result[4],
    }


# =========================================================
# 🔎 مدير مصادر البيانات
# =========================================================

def collect_phone_data(phone, default_region="YE"):
    """
    تجميع معلومات الرقم من جميع المصادر المتوفرة.

    المصادر الحالية:

    1. Phone Engine
    2. Numberbook

    لاحقًا يمكن إضافة مصادر خارجية
    بدون تغيير النظام الأساسي.
    """

    data = {
        "phone": phone,
        "sources": []
    }

    # -----------------------------------------------------
    # 📱 Phone Engine
    # -----------------------------------------------------

    phone_source = get_phone_source(
        phone,
        default_region=default_region
    )

    if phone_source:

        data["sources"].append(
            phone_source
        )

    # -----------------------------------------------------
    # 👤 Numberbook
    # -----------------------------------------------------

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

    return data


# =========================================================
# 🔍 الحصول على مصدر معين
# =========================================================

def get_source(
    phone,
    source_name,
    default_region="YE"
):
    """
    الحصول على بيانات مصدر معين.

    مثال:

    get_source(
        "+967771234567",
        "Numberbook"
    )
    """

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
    """
    البحث عن قيمة داخل المصادر.

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

        if value is not None and value != "":

            return {
                "value": value,
                "source": source.get("source"),
                "source_type": source.get("source_type")
            }

    return None


# =========================================================
# 👤 الحصول على اسم Numberbook
# =========================================================

def get_numberbook_name(phone):
    """
    الحصول على اسم الرقم من Numberbook فقط.
    """

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

            # ---------------------------------------------
            # Phone Engine
            # ---------------------------------------------

            if source["source"] == "Phone Engine":

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

            # ---------------------------------------------
            # Numberbook
            # ---------------------------------------------

            elif source["source"] == "Numberbook":

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
                        f"🌍 الدولة: "
                        f"{source.get('country')}"
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

    print()
    print("=" * 60)