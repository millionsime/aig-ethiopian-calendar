/* AIG Ethiopian Calendar - UI layer v1 (Phase-3 preview: display hints).
 * Scope: under every rendered Date field input, show the Ethiopian date as
 * a read-only hint. The input itself stays Gregorian-canonical - this layer
 * NEVER touches field values (input, save, submit all untouched).
 *
 * Safety (spec 16/25):
 *  - Runs only when frappe.boot.aig_ethiopian_calendar is truthy.
 *  - One debounced, scoped observer over form render containers only.
 *  - Every conversion error is contained; hints just go quiet on failure.
 *  - No monkey patching: frappe datetime methods, Date object, and field
 *    values are untouched.
 */
(function () {
	"use strict";

	if (!frappe || !frappe.boot || !frappe.boot.aig_ethiopian_calendar) {
		return; // feature flag off: load nothing (fail-safe)
	}

	// ---- engine mirror (JS twin of calendar/ethiopian.py; same anchor) ----
	var ANCHOR_ORDINAL = null; // ordinal of 2026-09-11 GC
	var ETH_MONTHS = ["Meskerem", "Tikimt", "Hidar", "Tahsas", "Tir",
		"Yekatit", "Megabit", "Miazia", "Ginbot", "Sene", "Hamle",
		"Nehase", "Pagumen"];

	function isGLeap(y) {
		return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
	}
	function gDaysInMonth(y, m) {
		var len = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];
		if (m === 2 && isGLeap(y)) len = 29;
		return len;
	}
	function gOrdinal(y, m, d) { // days since 0001-01-01 (proleptic, RFC-like)
		var n = 365 * (y - 1) + Math.floor((y - 1) / 4)
			- Math.floor((y - 1) / 100) + Math.floor((y - 1) / 400);
		for (var i = 1; i < m; i++) n += gDaysInMonth(y, i);
		return n + d;
	}
	function isELeap(y) { return ((y % 4) + 4) % 4 === 3; }

	function ecToOrdinal(y, m, d) {
		var n = 365 * (y - 2019);
		var step = y > 2019 ? 1 : -1;
		for (var yy = 2019; yy !== y; yy += step) {
			if (isELeap(step > 0 ? yy : yy - 1)) n += step;
		}
		return n + (m - 1) * 30 + (d - 1) - 0; // N=0 at anchor below
	}
	// ordinal of anchor 2026-09-11:
	ANCHOR_ORDINAL = gOrdinal(2026, 9, 11);
	function ecDateToG(y, m, d) {
		var n = ecToOrdinal(y, m, d) + ANCHOR_ORDINAL;
		return n;
	}
	function gToEc(y, m, d) {
		var n = gOrdinal(y, m, d) - ANCHOR_ORDINAL;
		var year = 2019;
		if (n >= 0) {
			while (true) {
				var len = 365 + (isELeap(year) ? 1 : 0);
				if (n < len) break;
				n -= len; year++;
			}
		} else {
			while (true) {
				year--;
				n += 365 + (isELeap(year) ? 1 : 0);
				if (n >= 0) break;
			}
		}
		var month = Math.floor(n / 30) + 1;
		var day = (n % 30) + 1;
		if (month > 13) { month = 13; day = n - 360 + 1; }
		return [year, month, day];
	}

	function parseISO(s) {
		var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s || "");
		if (!m) return null;
		var y = +m[1], mo = +m[2], d = +m[3];
		if (mo < 1 || mo > 12 || d < 1 || d > gDaysInMonth(y, mo)) return null;
		return [y, mo, d];
	}

	function formatEc(y, mo, d) {
		var name = ETH_MONTHS[mo - 1] || ("M" + mo);
		return d + " " + name + " " + y + " EC";
	}

	// expose for tests / other layers (namespaced, read-only)
	window.AIGEthiopianCalendar = {
		gregorianToEthiopian: function (iso) {
			var p = parseISO(iso);
			if (!p) return null;
			var r = gToEc(p[0], p[1], p[2]);
			return { year: r[0], month: r[1], day: r[2], text: formatEc(r[0], r[1], r[2]) };
		},
		ethiopianToGregorianISO: function (y, m, d) {
			if (m < 1 || m > 13) return null;
			var max = m === 13 ? (isELeap(y) ? 6 : 5) : 30;
			if (d < 1 || d > max) return null;
			var n = ecToOrdinal(y, m, d) + ANCHOR_ORDINAL;
			// inverse of gOrdinal: walk back
			var yy = Math.floor(n / 366) + 1, ord;
			for (; yy < n + 4000; yy++) {
				ord = gOrdinal(yy, 1, 1);
				if (ord > n) break;
			}
			yy--;
			ord = n - gOrdinal(yy, 1, 1) + 1;
			var mm = 1;
			while (ord > gDaysInMonth(yy, mm)) { ord -= gDaysInMonth(yy, mm); mm++; }
			return yy + "-" + ("0" + mm).slice(-2) + "-" + ("0" + ord).slice(-2);
		}
	};

	// ---------------------------- DOM layer ----------------------------
	var HINT_CLASS = "aig-eth-date-hint";
	var DATE_FIELDTYPES = ["Date"];
	var scheduled = null;

	function debounce(fn, ms) {
		return function () {
			clearTimeout(scheduled);
			scheduled = setTimeout(fn, ms);
		};
	}

	function scan() {
		try {
			// the wrapper holds BOTH render modes: an <input> when editable,
			// a .control-value div when the form is in read/preview mode
			document.querySelectorAll(
				".frappe-control[data-fieldtype='Date'] .control-input-wrapper")
				.forEach(attachHint);
		} catch (e) { /* fail-safe: hints are cosmetic only */ }
	}

	// Frappe renders dates in the user's date_format (e.g. dd-mm-yyyy);
	// normalise to ISO YYYY-MM-DD before converting.
	function toISO(v) {
		v = (v || "").trim();
		if (!v) return null;
		if (/^\d{4}-\d{2}-\d{2}/.test(v)) return v.slice(0, 10);
		try {
			var s = frappe.datetime.user_to_str(v);
			return /^\d{4}-\d{2}-\d{2}/.test(s) ? s : null;
		} catch (e) {
			return null;
		}
	}

	function attachHint(wrapper) {
		var input = wrapper.querySelector("input[type='text']");
		var staticVal = wrapper.querySelector(".control-value");
		var raw = input ? input.value : (staticVal ? staticVal.textContent : "");
		var hint = wrapper.querySelector(":scope > ." + HINT_CLASS);
		if (!hint) {
			hint = document.createElement("div");
			hint.className = HINT_CLASS;
			wrapper.appendChild(hint);
		}
		var iso = toISO(raw);
		if (!iso) { hint.textContent = ""; hint.classList.remove("aig-eth-hint-err"); return; }
		var ec = window.AIGEthiopianCalendar.gregorianToEthiopian(iso);
		hint.textContent = ec ? ec.text : "";
		hint.classList.toggle("aig-eth-hint-err", !ec);
	}

	var observer = new MutationObserver(debounce(scan, 120));
	var obsRoot = document.getElementById("body") || document.body;
	if (obsRoot) {
		observer.observe(obsRoot, { childList: true, subtree: true });
	}
	// forms often re-render after boot; catch that moment too
	if (frappe.router && frappe.router.on) {
		try { frappe.router.on("change", debounce(scan, 120)); } catch (e) { /* optional */ }
	}
	function onPossibleDateEvent(ev) {
		var t = ev.target;
		if (!t || t.nodeType !== 1) return;
		if (t.tagName === "INPUT" || t.classList.contains("control-value")) {
			var wrap = t.closest(".control-input-wrapper");
			if (wrap && wrap.closest(".frappe-control[data-fieldtype='Date']")) {
				attachHint(wrap);
			}
		}
	}
	document.addEventListener("change", onPossibleDateEvent, true);
	document.addEventListener("input", onPossibleDateEvent, true);
	scan();
})();
