# Calendar constants for the Ethiopian <-> Gregorian conversion layer.
# Phase 1: intentionally dependency-free (no frappe, no third-party libs).

# 13 months: 12 x 30 days + Pagumen (5 or 6 days).
ETHIOPIC_MONTH_NAMES = [
    "Meskerem", "Tikimt", "Hidar", "Tahsas", "Tir", "Yekatit",
    "Megabit", "Miazia", "Ginbot", "Sene", "Hamle", "Nehase", "Pagumen",
]

# Amharic (Ge'ez script) month names, same ordering.
ETHIOPIC_MONTH_NAMES_AMHARIC = [
    "መስከረም", "ጥቅምት", "ኅዳር", "ታኅሣሥ", "ጥር", "የካቲት",
    "መጋቢት", "ሚያዝያ", "ግንቦት", "ሰኔ", "ሐምሌ", "ነሐሴ", "ጳጉሜን",
]

# Gregorian month names for picker/formatter display.
GREGORIAN_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Weekday headers, Monday-first (picker grid convention).
WEEKDAY_HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

DAYS_IN_ETHIOPIC_MONTH = 30
PAGUMEN_INDEX = 13
PAGUMEN_DAYS_COMMON = 5
PAGUMEN_DAYS_LEAP = 6

# External ground-truth anchors (verified 2026-09-29):
#   1 Meskerem 2019 EC == 2026-09-11 GC (Enkutatash, multiple public sources)
#   1 Meskerem 2016 EC == 2023-09-12 GC (NY falls on Sep 12 iff Y % 4 == 0)
#   1 Meskerem 2000 EC == 2007-09-12 GC (Ethiopian millennium)
ANCHOR_EC = (2019, 1, 1)
ANCHOR_GC = (2026, 9, 11)
