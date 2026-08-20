# =========================================================
# Numberbook - External Sources
# Veriphone API
# =========================================================

import os
import requests


# =========================================================
# إعدادات Veriphone
# =========================================================

VERIPHONE_API_URL = "https://api.veriphone.io/v3/verify"

VERIPHONE_API_KEY = os.getenv("VERIPHONE_API_KEY")

# مهلة الاتصال
VERIPHONE_TIMEOUT = 10


# =========================================================
# التحقق من توفر الخدمة
# =========================================================

def veriphone_available():
    """
    التحقق من وجود مفتاح Veriphone.
    """

    return bool(
        VERIPHONE_API_KEY
        and VERIPHONE_API_KEY.strip()
    )


# =========================================================
# البحث في Veriphone
# =========================================================

def verify_with_veriphone(phone):
    """
    التحقق من رقم الهاتف باستخدام Veriphone.

    نستخدم Static Lookup فقط لأنه يستهلك:
    1 credit لكل طلب.

    لا نستخدم mode=current
    لأنه يستهلك 10 credits.
    """

    if not veriphone_available():

        return {
            "source": "Veriphone",
            "source_type": "external",
            "available": False,
            "success": False,
            "error": "VERIPHONE_API_KEY غير موجود"
        }

    try:

        response = requests.get(
            VERIPHONE_API_URL,
            params={
                "phone": phone
            },
            headers={
                "Authorization": (
                    f"Bearer {VERIPHONE_API_KEY}"
                )
            },
            timeout=VERIPHONE_TIMEOUT
        )

    except requests.Timeout:

        return {
            "source": "Veriphone",
            "source_type": "external",
            "available": True,
            "success": False,
            "error": "انتهت مهلة الاتصال"
        }

    except requests.RequestException as error:

        return {
            "source": "Veriphone",
            "source_type": "external",
            "success": False,
            "available": True,
            "error": str(error)
        }

    # =====================================================
    # تحليل استجابة API
    # =====================================================

    try:

        data = response.json()

    except ValueError:

        return {
            "source": "Veriphone",
            "source_type": "external",
            "available": True,
            "success": False,
            "error": "استجابة غير صالحة من Veriphone"
        }

    # =====================================================
    # أخطاء API
    # =====================================================

    if response.status_code != 200:

        return {
            "source": "Veriphone",
            "source_type": "external",
            "available": True,
            "success": False,

            "status_code": response.status_code,

            "error": data.get(
                "message",
                "حدث خطأ في Veriphone"
            )
        }

    # =====================================================
    # نجاح
    # =====================================================

    if data.get("status") != "success":

        return {
            "source": "Veriphone",
            "source_type": "external",
            "available": True,
            "success": False,

            "error": data.get(
                "message",
                "لم تنجح عملية التحقق"
            )
        }

    return {
        "source": "Veriphone",
        "source_type": "external",

        "available": True,
        "success": True,

        # الرقم
        "phone": data.get("phone"),
        "e164": data.get("e164"),

        # التحقق
        "valid": data.get("phone_valid"),

        # النوع
        "type": data.get("phone_type"),

        # الدولة
        "country": data.get("country"),
        "country_code": data.get("country_code"),
        "country_prefix": data.get("country_prefix"),

        # المنطقة
        "region": data.get("phone_region"),

        # الشركة
        "carrier": data.get("carrier"),

        # الصيغ
        "international": data.get(
            "international_number"
        ),

        "local": data.get(
            "local_number"
        ),

        # المنطقة الزمنية
        "timezone": data.get("timezone"),

        # هل الرقم جغرافي؟
        "geographical": data.get(
            "geographical"
        ),

        # وضع البحث
        "mode": data.get(
            "mode",
            "static"
        )
    }


# =========================================================
# اختبار الرصيد
# =========================================================

def get_veriphone_credits():
    """
    الحصول على معلومات الرصيد والاستخدام.

    هذا الطلب لا يستخدم للتحقق من الرقم.
    """

    if not veriphone_available():

        return None

    credits_url = (
        "https://api.veriphone.io/v3/credits"
    )

    try:

        response = requests.get(
            credits_url,
            headers={
                "Authorization": (
                    f"Bearer {VERIPHONE_API_KEY}"
                )
            },
            timeout=VERIPHONE_TIMEOUT
        )

        if response.status_code != 200:

            return None

        return response.json()

    except requests.RequestException:

        return None


# =========================================================
# اختبار الملف
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🌐 Numberbook - Veriphone External Source")
    print("=" * 60)

    # -----------------------------------------------------
    # فحص المفتاح
    # -----------------------------------------------------

    if not veriphone_available():

        print()
        print("⚠️ Veriphone API غير مفعلة.")
        print()
        print("أضف المتغير:")
        print("VERIPHONE_API_KEY")
        print()
        print("ثم أعد الاختبار.")

    else:

        print()
        print("🔑 API Key: موجود")
        print("🌐 Mode: static")
        print("💳 Cost: 1 credit / lookup")

        # -------------------------------------------------
        # الرقم التجريبي
        # -------------------------------------------------

        test_number = "+967771234567"

        print()
        print(f"📞 الرقم: {test_number}")
        print()
        print("🔎 جاري الاتصال بـ Veriphone...")

        result = verify_with_veriphone(
            test_number
        )

        print()

        if result.get("success"):

            print("✅ نجح الاتصال بـ Veriphone")
            print()
            print(
                f"📞 الرقم: "
                f"{result.get('e164')}"
            )

            print(
                f"🌍 الدولة: "
                f"{result.get('country')}"
            )

            print(
                f"📱 النوع: "
                f"{result.get('type')}"
            )

            print(
                f"📡 الشركة: "
                f"{result.get('carrier')}"
            )

            print(
                f"🔢 الدولي: "
                f"{result.get('international')}"
            )

            print(
                f"✅ صالح: "
                f"{result.get('valid')}"
            )

            print(
                f"📚 المصدر: "
                f"{result.get('source')}"
            )

        else:

            print("❌ فشل الاتصال بـ Veriphone")

            print(
                f"⚠️ السبب: "
                f"{result.get('error')}"
            )

    print()
    print("=" * 60)