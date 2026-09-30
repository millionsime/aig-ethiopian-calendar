# Boot session hook (documented frappe extension point): publish the feature
# flag to the client ONCE per session - no polling, no DOM sniffing.
import frappe


def boot_session(bootinfo):
    bootinfo.aig_ethiopian_calendar = bool(
        frappe.conf.get("aig_ethiopian_calendar"))
