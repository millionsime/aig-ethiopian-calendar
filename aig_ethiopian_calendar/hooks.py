# Frappe hooks for the AIG Ethiopian Calendar app (Phases 1-3 preview).
# Only standard, documented extension points are used - never core edits.

app_name = "aig_ethiopian_calendar"
app_title = "AIG Ethiopian Calendar"
app_publisher = "aig-tech"
app_description = (
    "Ethiopian Calendar UI and conversion layer for ERPNext/Frappe - "
    "presentation only; Gregorian stays canonical."
)
app_email = "simemillion@gmail.com"
app_license = "mit"

# Frappe/ERPNext version this app is built and tested against (spec §15).
required_min_frappe_version = "16.0.0"
required_max_frappe_version = "17.0.0"

# ----------------------------------------------------------- feature flag
# bench --site <site> set-config aig_ethiopian_calendar 1
# Absent/0 = client layer self-disables (checks frappe.boot at runtime).
boot_session = "aig_ethiopian_calendar.boot.boot_session"

# Assets: included unconditionally BUT the JS self-disables without the
# boot flag (single early return) - keeps flag flips cache-simple.
# NOTE: bump ?v= on every JS/CSS change - these are served with long cache.
app_include_css = "/assets/aig_ethiopian_calendar/css/ethiopian_calendar.css?v=3"
app_include_js = "/assets/aig_ethiopian_calendar/js/ethiopian_calendar.js?v=3"

# Jinja filter for print formats (spec §6H):
#   {{ ethiopian_date(doc.posting_date) }}
jinja_methods = {
    "ethiopian_date": "aig_ethiopian_calendar.api.formatting.jinja_ethiopian_date",
}

# after_install: version compatibility gate (spec §15)
after_install = "aig_ethiopian_calendar.install.after_install"
