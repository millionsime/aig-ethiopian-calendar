# Version compatibility gate (spec §15): detect incompatible Frappe/ERPNext
# and fail the install LOUDLY rather than silently corrupting dates later.
import frappe


def check_compatibility():
    v = frappe.__version__  # e.g. "16.33.0" or "v16.33.0"
    major = int(str(v).lstrip("v").split(".")[0])
    if major != 16:
        frappe.throw(
            "aig_ethiopian_calendar is built for Frappe/ERPNext v16.x "
            "(found " + str(v) + "). Refusing to install: the UI adapters "
            "must be re-validated for " + str(major) + " before use. "
            "See spec §15 (upgrade detection)."
        )


def after_install():
    check_compatibility()
    frappe.db.set_single_value(
        "System Settings", "language", frappe.db.get_single_value(
            "System Settings", "language") or "en")
    print("AIG Ethiopian Calendar installed. Feature is OFF by default -")
    print("enable with: bench --site <site> set-config aig_ethiopian_calendar 1")
