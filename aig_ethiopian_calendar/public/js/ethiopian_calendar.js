/* AIG Ethiopian Calendar - UI layer v2 (Phase 2: date picker + hints).
 * Two clearly separated parts:
 *
 *   PART 1 - pure engine. No window/frappe/DOM at module scope. Exports via
 *   module.exports (node) and window.AIGEthiopianCalendar (browser), so the
 *   exact same file is what the mirror test runs under node.
 *
 *   PART 2 - flag-gated, fail-safe browser UI: read-only Ethiopian hints
 *   (v1 behaviour) plus the Phase 2 picker (EC month grid popover; writes
 *   Gregorian through the field's normal change event - values stay
 *   Gregorian-canonical, Frappe machinery untouched).
 *
 * Safety (spec 14/16/25): runs only when frappe.boot.aig_ethiopian_calendar
 * is truthy; one debounced scoped observer; every conversion/DOM error is
 * contained; no monkey patching of frappe datetime, Date, or field values.
 */
(function (root, factory) {
	"use strict";
	if (typeof module === "object" && module.exports) {
		module.exports = factory(); // node (mirror test)
	} else {
		root.AIGEthiopianCalendar = factory(); // browser global
	}
})(typeof self !== "undefined" ? self : this, function () {
	"use strict";

	// ======================================================================
	// PART 1 - ENGINE (pure, node-safe)
	// ======================================================================

	var MONTH_NAMES = ["Meskerem", "Tikimt", "Hidar", "Tahsas", "Tir",
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
	// days since 0001-01-01 (proleptic Gregorian ordinal, RFC 3339 style)
	function gOrdinal(y, m, d) {
		var n = 365 * (y - 1) + Math.floor((y - 1) / 4)
			- Math.floor((y - 1) / 100) + Math.floor((y - 1) / 400);
		for (var i = 1; i < m; i++) n += gDaysInMonth(y, i);
		return n + d;
	}
	function isELeap(y) { return ((y % 4) + 4) % 4 === 3; }
	function eDaysInMonth(y, m) { return m === 13 ? (isELeap(y) ? 6 : 5) : 30; }

	// day number N=0 at 1 Meskerem 2019 EC (2026-09-11 GC)
	var ANCHOR_ORDINAL = gOrdinal(2026, 9, 11);

	function eToDayNumber(y, m, d) {
		var n = 365 * (y - 2019);
		var step = y > 2019 ? 1 : -1;
		for (var yy = 2019; yy !== y; yy += step) {
			if (isELeap(step > 0 ? yy : yy - 1)) n += step;
		}
		return n + (m - 1) * 30 + (d - 1);
	}
	function eFromDayNumber(n) {
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

	function gToEc(y, m, d) { return eFromDayNumber(gOrdinal(y, m, d) - ANCHOR_ORDINAL); }
	function eToGc(y, m, d) { return gFromOrdinal(eToDayNumber(y, m, d) + ANCHOR_ORDINAL); }

	// inverse of gOrdinal: day number -> (y, m, d)
	function gFromOrdinal(n) {
		var y = Math.floor(n / 366.2425) + 1;
		while (gOrdinal(y, 1, 1) <= n) y++;
		y--;
		var ord = n - gOrdinal(y, 1, 1) + 1;
		var m = 1;
		while (ord > gDaysInMonth(y, m)) { ord -= gDaysInMonth(y, m); m++; }
		return [y, m, ord];
	}

	function pad2(n) { return (n < 10 ? "0" : "") + n; }

	function formatEc(y, m, d) {
		return d + " " + (MONTH_NAMES[m - 1] || ("M" + m)) + " " + y + " EC";
	}

	// ---------------------------- public engine API ---------------------
	var Engine = {
		MONTH_NAMES: MONTH_NAMES,
		isEthiopianLeap: isELeap,
		ethiopianDaysInMonth: eDaysInMonth,
		gregorianToEthiopian: function (iso) {
			var p = parseISO(iso);
			if (!p) return null;
			var r = gToEc(p[0], p[1], p[2]);
			return { year: r[0], month: r[1], day: r[2], text: formatEc(r[0], r[1], r[2]) };
		},
		ethiopianToGregorianISO: function (y, m, d) {
			if (m < 1 || m > 13 || y < 1 || d < 1) return null;
			if (d > eDaysInMonth(y, m)) return null;
			var g = eToGc(y, m, d);
			return g[0] + "-" + pad2(g[1]) + "-" + pad2(g[2]);
		},
		// month grid helper for the picker: returns {firstWeekday, days, monthName}
		monthGrid: function (year, month) {
			if (month < 1 || month > 13) return null;
			var days = eDaysInMonth(year, month);
			var gc = eToGc(year, month, 1);
			// weekday with getDay convention (0=Sunday..6=Saturday):
			// proleptic 0001-01-01 is a Monday and has ordinal 1, so
			// ordinal % 7 maps 1->Mon .. 6->Sat, 0->Sun. Exactly getDay().
			var weekday = ((gOrdinal(gc[0], gc[1], gc[2]) % 7) + 7) % 7;
			return { firstWeekday: weekday, days: days, monthName: MONTH_NAMES[month - 1], year: year };
		},
		todayISO: function () {
			var now = new Date();
			return now.getFullYear() + "-" + pad2(now.getMonth() + 1) + "-" + pad2(now.getDate());
		}
	};

	function parseISO(s) {
		var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s || "");
		if (!m) return null;
		var y = +m[1], mo = +m[2], d = +m[3];
		if (mo < 1 || mo > 12 || d < 1 || d > gDaysInMonth(y, mo)) return null;
		return [y, mo, d];
	}

	// ======================================================================
	// PART 2 - BROWSER UI (hints v1 + Phase 2 picker). Browser-only: the
	// factory returns the engine under node; UI wiring happens only when a
	// DOM + frappe + boot flag are present.
	// ======================================================================

	function initUI() {
		if (typeof document === "undefined" || typeof frappe === "undefined") return;
		if (!frappe.boot || !frappe.boot.aig_ethiopian_calendar) return; // flag gate
		if (initUI._done) return;
		initUI._done = true;

		var HINT_CLASS = "aig-eth-date-hint";
		var BTN_CLASS = "aig-eth-btn";
		var POP_CLASS = "aig-eth-pop";
		var scheduled = null;

		function debounce(fn, ms) {
			return function () {
				clearTimeout(scheduled);
				scheduled = setTimeout(fn, ms);
			};
		}

		// Frappe renders dates in the user's format (dd-mm-yyyy etc.);
		// normalise to ISO first.
		function toISO(v) {
			v = (v || "").trim();
			if (!v) return null;
			if (/^\d{4}-\d{2}-\d{2}/.test(v)) return v.slice(0, 10);
			try {
				var s = frappe.datetime.user_to_str(v);
				return /^\d{4}-\d{2}-\d{2}/.test(s) ? s : null;
			} catch (e) { return null; }
		}

		function scan() {
			try {
				document.querySelectorAll(
					".frappe-control[data-fieldtype='Date'] .control-input-wrapper")
					.forEach(enhance);
			} catch (e) { /* fail-safe: cosmetic only */ }
		}

		// ---------------- per-field enhancement (hint + button) ------------
		function enhance(wrapper) {
			try {
				var ctrl = wrapper.closest(".frappe-control");
				if (!ctrl || ctrl.getAttribute("data-aig-eth") === "1") return;
				ctrl.setAttribute("data-aig-eth", "1");

				var hint = document.createElement("div");
				hint.className = HINT_CLASS;
				wrapper.appendChild(hint);

				// picker button: only for editable fields (static/read-only
				// fields get the hint alone)
				var input = wrapper.querySelector("input[type='text']");
				if (input && !input.readOnly && !input.disabled) {
					var btn = document.createElement("button");
					btn.type = "button";
					btn.className = BTN_CLASS;
					btn.title = "Pick Ethiopian date";
					btn.textContent = "ዓ.ም."; // Ethiopic abbreviation, self-explanatory
					btn.addEventListener("click", function (ev) {
						ev.preventDefault();
						ev.stopPropagation();
						togglePopover(ctrl, wrapper, input);
					});
					wrapper.appendChild(btn);
				}

				updateField(ctrl);
			} catch (e) { /* fail-safe */ }
		}

		// ---------------- hint refresh --------------------------------------
		function updateField(ctrl) {
			try {
				var wrapper = ctrl.querySelector(".control-input-wrapper");
				if (!wrapper) return;
				var hint = wrapper.querySelector("." + HINT_CLASS);
				if (!hint) return;
				var input = wrapper.querySelector("input[type='text']");
				var staticVal = wrapper.querySelector(".control-value");
				var raw = input ? input.value : (staticVal ? staticVal.textContent : "");
				var iso = toISO(raw);
				if (!iso) {
					hint.textContent = "";
					hint.classList.remove("aig-eth-hint-err");
					return;
				}
				var ec = AIG.gregorianToEthiopian(iso);
				hint.textContent = ec ? ec.text : "";
				hint.classList.toggle("aig-eth-hint-err", !ec);
			} catch (e) { /* fail-safe */ }
		}

		// ---------------- popover (the picker) ------------------------------
		var openPop = null;

		function closePopover() {
			if (openPop) {
				openPop.el.remove();
				openPop = null;
				document.removeEventListener("click", onDocClick, true);
				document.removeEventListener("keydown", onKey, true);
			}
		}
		function onDocClick(ev) {
			if (openPop && !openPop.el.contains(ev.target)
				&& !(openPop.btn && openPop.btn.contains(ev.target))) closePopover();
		}
		function onKey(ev) {
			if (ev.key === "Escape") closePopover();
		}

		function togglePopover(ctrl, wrapper, input) {
			if (openPop && openPop.ctrl === ctrl) { closePopover(); return; }
			closePopover();
			var state = currentEc(ctrl);
			openPop = buildPopover(ctrl, wrapper, input, state.year, state.month);
			positionPopover(openPop.el, wrapper);
			document.addEventListener("click", onDocClick, true);
			document.addEventListener("keydown", onKey, true);
		}

		function currentEc(ctrl) {
			var wrapper = ctrl.querySelector(".control-input-wrapper");
			var input = wrapper && wrapper.querySelector("input[type='text']");
			var iso = input ? toISO(input.value) : null;
			var ec = iso ? AIG.gregorianToEthiopian(iso) : null;
			if (ec) return { year: ec.year, month: ec.month };
			// fall back to today in EC
			var t = AIG.gregorianToEthiopian(AIG.todayISO());
			return t ? { year: t.year, month: t.month } : { year: 2019, month: 1 };
		}

		function buildPopover(ctrl, wrapper, input, year, month) {
			var el = document.createElement("div");
			el.className = POP_CLASS;
			el.innerHTML = headerHTML(year, month) + gridHTML(year, month)
				+ footerHTML(year);
			wirePopover(el, ctrl, input, year, month);
			return { el: el, ctrl: ctrl, btn: wrapper.querySelector("." + BTN_CLASS) };
		}

		function headerHTML(year, month) {
			var opts = "";
			for (var m = 1; m <= 13; m++) {
				opts += '<option value="' + m + '"'
					+ (m === month ? " selected" : "") + ">"
					+ AIG.MONTH_NAMES[m - 1] + "</option>";
			}
			return '<div class="aig-eth-head">'
				+ '<select class="aig-eth-month">' + opts + "</select>"
				+ '<input type="number" class="aig-eth-year" value="' + year
				+ '" min="1" max="9999">'
				+ "</div>";
		}

		function gridHTML(year, month) {
			var g = AIG.monthGrid(year, month);
			var html = '<div class="aig-eth-grid">';
			var wd = ["S", "M", "T", "W", "T", "F", "S"];
			for (var i = 0; i < 7; i++) html += '<span class="aig-eth-wd">' + wd[i] + "</span>";
			for (var b = 0; b < g.firstWeekday; b++) html += "<span></span>";
			for (var d = 1; d <= g.days; d++) {
				html += '<button type="button" class="aig-eth-day" data-d="' + d
					+ '">' + d + "</button>";
			}
			return html + "</div>";
		}

		function footerHTML(year) {
			return '<div class="aig-eth-foot">'
				+ '<span class="aig-eth-pag">'
				+ (AIG.isEthiopianLeap(year) ? "Pagumen 6" : "Pagumen 5")
				+ "</span>"
				+ '<button type="button" class="aig-eth-today">Today</button>'
				+ "</div>";
		}

		function wirePopover(el, ctrl, input, year, month) {
			var monthSel = el.querySelector(".aig-eth-month");
			var yearInp = el.querySelector(".aig-eth-year");

			function rerender() {
				var y = parseInt(yearInp.value, 10);
				var m = parseInt(monthSel.value, 10);
				if (!y || y < 1 || y > 9999 || !m) return;
				el.querySelector(".aig-eth-grid").outerHTML = gridHTML(y, m);
				el.querySelector(".aig-eth-pag").textContent =
					AIG.isEthiopianLeap(y) ? "Pagumen 6" : "Pagumen 5";
				wireGrid(el, ctrl, input, y, m);
			}
			monthSel.addEventListener("change", rerender);
			yearInp.addEventListener("change", rerender);

			var todayBtn = el.querySelector(".aig-eth-today");
			todayBtn.addEventListener("click", function () {
				var t = AIG.gregorianToEthiopian(AIG.todayISO());
				if (!t) return;
				monthSel.value = String(t.month);
				yearInp.value = String(t.year);
				rerender();
				var dayBtn = el.querySelector('.aig-eth-day[data-d="' + t.day + '"]');
				if (dayBtn) dayBtn.classList.add("aig-eth-day-today");
			});

			wireGrid(el, ctrl, input, year, month);
		}

		function wireGrid(el, ctrl, input, year, month) {
			el.querySelectorAll(".aig-eth-day").forEach(function (b) {
				b.addEventListener("click", function (ev) {
					ev.preventDefault();
					ev.stopPropagation();
					var d = parseInt(b.getAttribute("data-d"), 10);
					var iso = AIG.ethiopianToGregorianISO(year, month, d);
					if (!iso) return; // invalid (fail-safe: do nothing)
					// write through the field's OWN machinery: set value then
					// let frappe's change handling take over
					input.value = frappe.datetime.str_to_user(iso);
					input.dispatchEvent(new Event("change", { bubbles: true }));
					closePopover();
				});
			});
		}

		function positionPopover(el, wrapper) {
			wrapper.appendChild(el);
			var r = wrapper.getBoundingClientRect();
			el.style.top = (r.height + 2) + "px";
			el.style.left = "0";
		}

		// ---------------- events / observer ---------------------------------
		function onPossibleDateEvent(ev) {
			var t = ev.target;
			if (!t || t.nodeType !== 1) return;
			if (t.tagName === "INPUT" || t.classList.contains("control-value")) {
				var ctrl = t.closest(".frappe-control[data-fieldtype='Date']");
				if (ctrl) updateField(ctrl);
			}
		}

		var observer = new MutationObserver(debounce(scan, 120));
		observer.observe(document.body, { childList: true, subtree: true });
		document.addEventListener("change", onPossibleDateEvent, true);
		document.addEventListener("input", onPossibleDateEvent, true);
		scan();
	}

	var AIG = Engine;
	if (typeof document !== "undefined" && typeof frappe !== "undefined") {
		Engine._ui = initUI;
		// boot is usually inlined before bundles; retry on late assignment
		initUI();
		document.addEventListener("DOMContentLoaded", function () { initUI(); });
		window.addEventListener("load", function () { initUI(); });
	}

	return Engine;
});
