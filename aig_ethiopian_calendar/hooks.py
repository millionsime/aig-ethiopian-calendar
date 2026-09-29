# Frappe hooks for the AIG Ethiopian Calendar app (Phase 1 install).
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
# Single source of truth for enabling the calendar UI. Until Documented
# Settings exist (Phase 6), deployments opt in via site_config:
#   bench --site <site> set-config aig_ethiopian_calendar 1
# Absent/0 = the app loads NOTHING (fail-safe, spec §16/§17).
# The JS bundle itself double-checks boot.data sysdefaults before touching
# any field, so a stale cache can never enable the UI alone.

# Jinja filter for print formats (spec §6H):
#   {{ ethiopian_date(doc.posting_date) }}
jinja_methods = {
    "ethiopian_date": "aig_ethiopian_calendar.api.formatting.jinja_ethiopian_date",
}

# Server-side sanitization hook surface is added in Phase 4 with the filter
# integration; whitelisted API methods will live in api/ only.
