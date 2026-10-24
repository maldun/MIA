"""
The hard checks (ui/REQUIREMENTS_CORE.md 12.2): programs and the outside world as evidence, not a model's opinion. Every check returns the same shape,

  {"status": "pass" | "fail" | "inconclusive" | "not_applicable", "check": name, "detail": text, "evidence": [...]}

  pass            the claim holds as far as this check can see (evidence, not proof)
  fail            the claim is wrong (a quote that is not in the source, 2 + 2 = 5, a Sunday that is a Monday)
  inconclusive    the check could not decide (a near match, a page that did not load, sources that disagree); the claim goes on to the next stage
  not_applicable  the check does not fit the data it got (a missing field, an unknown unit)

The exact checks need nothing but Python. The web checks (citation, web confirmation) are built around the search and fetch tools of web_tools.py. CheckRunner picks the
checks that apply to a claim from the library, runs the cheap ones first and combines the results with one rule (combine()): a failed check decides, passes are evidence.
"""
import ast
import calendar
import datetime
import difflib
import math
import re
import time
import unicodedata
from decimal import Decimal, InvalidOperation, localcontext
from urllib.parse import urlparse

try:
    from .schema_check import check as check_schema
    from . import web_tools
    from .sandbox import Operation
except ImportError:  # used as plain script / in tests
    from schema_check import check as check_schema
    import web_tools
    from sandbox import Operation

PASS, FAIL, INCONCLUSIVE, NOT_APPLICABLE = "pass", "fail", "inconclusive", "not_applicable"


def result(status, check, detail="", evidence=None):
    return {"status": status, "check": check, "detail": detail, "evidence": evidence if evidence is not None else []}


# --- text: quotes in sources ---------------------------------------------------------------------------------------------------

_PUNCT = {"‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'", "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
          "–": "-", "—": "-", "−": "-", "‐": "-", "‑": "-", "­": "", "​": "", "‌": "", "‍": "", "﻿": "", "…": "..."}
_ELLIPSIS = re.compile(r"\.\.\.|\[\s*\.\.\.\s*\]|\[\s*…\s*\]")


def normalize(text, ignore_case=True):
    """text as a reader sees it: compatibility forms (ligatures, full-width letters), typographic quotes and dashes made plain, spaces squeezed"""
    text = unicodedata.normalize("NFKC", str(text))
    text = "".join(_PUNCT.get(c, c) for c in text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold() if ignore_case else text


def _for_matching(text, ignore_case=True):
    """normalised and without double quotation marks, which sources and quotations often set differently (curly, straight, guillemets, none)"""
    return re.sub(r" +", " ", normalize(text, ignore_case).replace('"', "")).strip()


def _tokens(text):
    return re.findall(r"\w+", text)


def _closest_window(quote_tokens, source_tokens):
    """the stretch of the source that is most like the quote: (ratio, tokens); only windows that share enough words are compared"""
    n = len(quote_tokens)
    if n < 4 or len(source_tokens) < 2:
        return 0.0, []
    wanted = set(quote_tokens)
    hits = [1 if t in wanted else 0 for t in source_tokens]
    prefix = [0]
    for h in hits:
        prefix.append(prefix[-1] + h)
    best, best_window = 0.0, []
    for size in sorted({n, max(1, int(n * 0.9)), int(n * 1.1) + 1}):
        for i in range(0, max(1, len(source_tokens) - size + 1)):
            if prefix[min(i + size, len(source_tokens))] - prefix[i] < 0.6 * n:
                continue
            window = source_tokens[i:i + size]
            ratio = difflib.SequenceMatcher(None, quote_tokens, window, autojunk=False).ratio()
            if ratio > best:
                best, best_window = ratio, window
    return best, best_window


def quote_in_source(quote, source, ignore_case=True, near=0.85):
    """the quote occurs in the source after normalising typography and spaces ('...' or '[...]' inside the quote skip text between the pieces).
    A near match (word order or one word differs) is inconclusive and shows the closest passage: a quotation must be exact to pass."""
    name = "quote_in_source"
    if not isinstance(quote, str) or not isinstance(source, str) or len(normalize(quote)) < 4:
        return result(NOT_APPLICABLE, name, "a quote of at least 4 characters and a source text are needed")
    wanted, text = _for_matching(quote, ignore_case), _for_matching(source, ignore_case)
    pieces = [p.strip(" .\"'") for p in _ELLIPSIS.split(wanted)]
    pieces = [p for p in pieces if p]
    position, found_pieces = 0, []
    for piece in pieces:
        at = text.find(piece, position)
        if at < 0:
            found_pieces = None
            break
        found_pieces.append({"at": at, "text": text[max(0, at - 40):at + len(piece) + 40]})
        position = at + len(piece)
    if found_pieces:
        return result(PASS, name, "the quote occurs in the source" + (" (%d pieces in order)" % len(pieces) if len(pieces) > 1 else ""), found_pieces)
    ratio, window = _closest_window(_tokens(wanted), _tokens(text))
    if ratio >= near:
        return result(INCONCLUSIVE, name, "only a near match (%.0f%% of the words in order): the quote is not exact" % (ratio * 100), [{"closest": " ".join(window)}])
    return result(FAIL, name, "the quote does not occur in the source")


# --- numbers: arithmetic and units -------------------------------------------------------------------------------------------------

DECIMAL_PRECISION = 40
_BINARY = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**"}
_CONSTANTS = {"pi": ("3.14159265358979323846264338327950288419716939937510", math.pi), "e": ("2.71828182845904523536028747135266249775724709369995", math.e)}
MAX_EXPRESSION = 200
MAX_POWER = 1000


class ExpressionError(ValueError):
    pass


def _walk(node, number, binary, unary, call, name, depth=0):
    if depth > 30:
        raise ExpressionError("the expression is nested too deeply")
    rec = lambda n: _walk(n, number, binary, unary, call, name, depth + 1)   # noqa: E731
    if isinstance(node, ast.Expression):
        return rec(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return number(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        return binary(_BINARY[type(node.op)], rec(node.left), rec(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return unary(isinstance(node.op, ast.USub), rec(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return name(node.id)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("sqrt", "abs") and len(node.args) == 1 and not node.keywords:
        return call(node.func.id, rec(node.args[0]))
    raise ExpressionError("only numbers, + - * / // % **, parentheses, pi, e, sqrt() and abs() are allowed")


def _float_op(op, a, b):
    if op == "**" and (abs(b) > MAX_POWER or (a != 0 and abs(b * math.log10(abs(a))) > 300)):
        raise ExpressionError("the power is too large")
    return {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "/": lambda: a / b, "//": lambda: a // b, "%": lambda: a % b, "**": lambda: a ** b}[op]()


def _decimal_op(op, a, b):
    if op == "**" and (abs(b) > MAX_POWER or (a != 0 and abs(b * Decimal(abs(a)).log10()) > 300)):
        raise ExpressionError("the power is too large")
    return {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "/": lambda: a / b, "//": lambda: a // b, "%": lambda: a % b, "**": lambda: a ** b}[op]()


def evaluate_two_ways(expression):
    """(float value, Decimal value) of an arithmetic expression, evaluated without eval() by two independent evaluators"""
    if not isinstance(expression, str) or not expression.strip() or len(expression) > MAX_EXPRESSION:
        raise ExpressionError("an expression of up to %d characters is needed" % MAX_EXPRESSION)
    text = expression.replace("^", "**").replace("×", "*").replace("÷", "/").replace("−", "-").replace(",", "")
    try:
        tree = ast.parse(text.strip(), mode="eval")
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        raise ExpressionError("this is not an arithmetic expression")
    if sum(1 for _ in ast.walk(tree)) > 80:
        raise ExpressionError("the expression is too long")
    try:
        as_float = _walk(tree, float, _float_op, lambda neg, v: -v if neg else v, lambda f, v: math.sqrt(v) if f == "sqrt" else abs(v), lambda n: _CONSTANTS[n][1])
        with localcontext() as context:
            context.prec = DECIMAL_PRECISION
            as_decimal = _walk(tree, lambda v: Decimal(repr(v)) if isinstance(v, float) else Decimal(v), _decimal_op, lambda neg, v: -v if neg else v,
                               lambda f, v: v.sqrt() if f == "sqrt" else abs(v), lambda n: Decimal(_CONSTANTS[n][0]))
    except (ZeroDivisionError, OverflowError, ValueError, InvalidOperation) as exc:
        raise ExpressionError("cannot be calculated (%s)" % exc.__class__.__name__)
    if isinstance(as_float, complex) or isinstance(as_decimal, complex):
        raise ExpressionError("the result is not a real number")
    return float(as_float), as_decimal


def parse_number(value):
    """a number from a number or a text such as '1,234.5', '1.234,5' or '3,5' (the last separator is the decimal mark when both occur; a comma followed by exactly three digits is a thousands mark)"""
    if isinstance(value, bool):
        raise ValueError("not a number")
    if isinstance(value, (int, float)):
        return float(value)
    return float(_clean_number(value))


def _clean_number(value):
    """the digits of a written number with a point as the decimal mark and no thousands marks (see parse_number)"""
    text = re.sub(r"[\s\u00a0'_]", "", str(value)).replace("\u2212", "-")
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", text):
        return text
    if "," in text and "." in text:
        decimal = "," if text.rfind(",") > text.rfind(".") else "."
        text = text.replace("." if decimal == "," else ",", "").replace(decimal, ".")
    elif "," in text:
        text = text.replace(",", "") if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+", text) else text.replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    float(text)                                                               # raises ValueError for anything that is not a number
    return text


def _exact(value):
    """the claimed number as an exact Decimal (floats through their shortest text)"""
    if isinstance(value, bool):
        raise ValueError("not a number")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    return Decimal(_clean_number(value))


def _decimals(value):
    """how many decimals the claimed number shows ('3.1' -> 1): the claim may be rounded to that many"""
    if isinstance(value, str):
        m = re.search(r"[.,](\d+)\s*$", value.strip())
        return len(m.group(1)) if m and not re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+", value.strip()) else 0
    return len(repr(float(value)).partition(".")[2].rstrip("0")) if isinstance(value, float) else 0


ROUNDING_CAP = 0.02          # rounding explains at most 2 percent of the real value: "5 km = 3 mi" is not a rounded 3.1


def _agrees(claimed, actual, tolerance, claimed_raw):
    """within the relative tolerance, or within the rounding the claimed number shows (half a unit of its last digit, but never more than ROUNDING_CAP of the real value).
    An exact result (a whole number) has nothing to round: the claim has to equal it within the rounding it shows and no relative tolerance applies, so 250 * 4 is not 1004."""
    half_unit = 0.5 * 10 ** -_decimals(claimed_raw)
    nearest = round(actual)
    if abs(actual - nearest) <= 1e-9 * max(1.0, abs(actual)):
        return abs(claimed - nearest) <= half_unit * 1.0000001
    return abs(claimed - actual) <= max(tolerance * abs(actual), min(half_unit * 1.0000001, ROUNDING_CAP * abs(actual)))


def arithmetic_claim(expression, value, tolerance=0.005):
    """'expression = value' holds (relative tolerance, and the rounding the claimed value shows). Evaluated twice, with floats and with 40-digit decimals; if they disagree the check is inconclusive"""
    name = "arithmetic"
    try:
        claimed = parse_number(value)
        as_float, as_decimal = evaluate_two_ways(expression)
    except ExpressionError as exc:
        return result(NOT_APPLICABLE, name, str(exc))
    except (ValueError, TypeError):
        return result(NOT_APPLICABLE, name, "the claimed value is not a number")
    decimal_float = float(as_decimal)
    if not math.isclose(as_float, decimal_float, rel_tol=1e-9, abs_tol=1e-12):
        return result(INCONCLUSIVE, name, "the two evaluations disagree (%r and %r)" % (as_float, decimal_float), [{"float": as_float, "decimal": str(as_decimal)}])
    evidence = [{"expression": expression, "result": as_float, "claimed": claimed}]
    if as_decimal == as_decimal.to_integral_value():
        # an exact whole number, also a very big one (floats cannot tell 121932631112635269 from ...270, the decimals can)
        try:
            agrees = abs(_exact(value) - as_decimal) <= Decimal(5) / Decimal(10) ** (_decimals(value) + 1)
        except (ValueError, InvalidOperation):
            agrees = False
    else:
        agrees = _agrees(claimed, as_float, tolerance, value)
    if agrees:
        return result(PASS, name, "%s = %s" % (expression, _fmt(as_float)), evidence)
    return result(FAIL, name, "%s is %s, not %s" % (expression, _fmt(as_float), value), evidence)


def _fmt(number):
    return ("%.10g" % number)


# units: dimension -> (base unit, {unit: factor to the base unit})
_UNITS = {
    "length": {"mm": 1e-3, "cm": 1e-2, "m": 1.0, "km": 1e3, "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344, "nmi": 1852.0},
    "mass": {"mg": 1e-6, "g": 1e-3, "kg": 1.0, "t": 1000.0, "oz": 0.028349523125, "lb": 0.45359237, "st": 6.35029318},
    "time": {"ms": 1e-3, "s": 1.0, "min": 60.0, "h": 3600.0, "day": 86400.0, "week": 604800.0},
    "volume": {"ml": 1e-3, "l": 1.0, "m3": 1000.0, "gal": 3.785411784, "qt": 0.946352946, "pt": 0.473176473, "floz": 0.0295735295625, "cup": 0.2365882365,
               "tbsp": 0.01478676478125, "tsp": 0.00492892159375},
    "speed": {"m/s": 1.0, "km/h": 1 / 3.6, "mph": 0.44704, "kn": 1852 / 3600, "ft/s": 0.3048},
    "area": {"cm2": 1e-4, "m2": 1.0, "km2": 1e6, "ha": 1e4, "acre": 4046.8564224, "ft2": 0.09290304, "in2": 6.4516e-4, "mi2": 2589988.110336},
    "data": {"bit": 0.125, "b": 1.0, "kb": 1e3, "mb": 1e6, "gb": 1e9, "tb": 1e12, "kib": 1024.0, "mib": 1048576.0, "gib": 1073741824.0, "tib": 1099511627776.0},
    "energy": {"j": 1.0, "kj": 1e3, "cal": 4.184, "kcal": 4184.0, "wh": 3600.0, "kwh": 3.6e6},
    "pressure": {"pa": 1.0, "hpa": 100.0, "kpa": 1e3, "bar": 1e5, "atm": 101325.0, "psi": 6894.757293168, "mmhg": 133.322387415},
}
_ALIASES = {"meter": "m", "metre": "m", "meters": "m", "metres": "m", "kilometer": "km", "kilometre": "km", "kilometers": "km", "kilometres": "km", "centimeter": "cm",
            "centimeters": "cm", "millimeter": "mm", "millimeters": "mm", "inch": "in", "inches": "in", "foot": "ft", "feet": "ft", "yard": "yd", "yards": "yd", "mile": "mi",
            "miles": "mi", "gram": "g", "grams": "g", "kilogram": "kg", "kilograms": "kg", "kilo": "kg", "tonne": "t", "tonnes": "t", "ounce": "oz", "ounces": "oz", "pound": "lb",
            "pounds": "lb", "lbs": "lb", "second": "s", "seconds": "s", "sec": "s", "minute": "min", "minutes": "min", "hour": "h", "hours": "h", "hr": "h", "days": "day",
            "weeks": "week", "liter": "l", "litre": "l", "liters": "l", "litres": "l", "milliliter": "ml", "milliliters": "ml", "gallon": "gal", "gallons": "gal", "quart": "qt",
            "pint": "pt", "cups": "cup", "kph": "km/h", "kmh": "km/h", "kmph": "km/h", "knot": "kn", "knots": "kn", "mps": "m/s", "hectare": "ha", "acres": "acre", "byte": "b",
            "bytes": "b", "kilobyte": "kb", "megabyte": "mb", "gigabyte": "gb", "terabyte": "tb", "joule": "j", "joules": "j", "calorie": "cal", "calories": "cal",
            "kilocalorie": "kcal", "pascal": "pa", "celsius": "c", "centigrade": "c", "fahrenheit": "f", "kelvin": "k", "km²": "km2", "m²": "m2", "cm²": "cm2",
            "m³": "m3", "sqft": "ft2", "sqm": "m2", "teaspoon": "tsp", "tablespoon": "tbsp"}
_TEMPERATURE = {"c": (lambda v: v + 273.15, lambda k: k - 273.15), "f": (lambda v: (v - 32) * 5 / 9 + 273.15, lambda k: (k - 273.15) * 9 / 5 + 32),
                "k": (lambda v: v, lambda k: k)}


def _unit(text):
    u = re.sub(r"[°\s]", "", str(text).lower().replace("µ", "u"))
    return _ALIASES.get(u, u)


def unit_conversion(value, from_unit, to_unit, result_value, tolerance=0.01):
    """'value from_unit = result to_unit' holds (the rounding the result shows is allowed; default relative tolerance 1%). Length, mass, time, volume (US), speed, area, data, energy, pressure, temperature"""
    name = "unit_conversion"
    try:
        amount, claimed = parse_number(value), parse_number(result_value)
    except (ValueError, TypeError):
        return result(NOT_APPLICABLE, name, "value and result must be numbers")
    a, b = _unit(from_unit), _unit(to_unit)
    if a in _TEMPERATURE and b in _TEMPERATURE:
        actual = _TEMPERATURE[b][1](_TEMPERATURE[a][0](amount))
    else:
        dimension = next((d for d, table in _UNITS.items() if a in table and b in table), None)
        if dimension is None:
            return result(NOT_APPLICABLE, name, "the units '%s' and '%s' are unknown or measure different things" % (from_unit, to_unit))
        actual = amount * _UNITS[dimension][a] / _UNITS[dimension][b]
    evidence = [{"computed": actual, "claimed": claimed}]
    if _agrees(claimed, actual, tolerance, result_value):
        return result(PASS, name, "%s %s = %s %s" % (_fmt(amount), from_unit, _fmt(actual), to_unit), evidence)
    return result(FAIL, name, "%s %s is %s %s, not %s" % (_fmt(amount), from_unit, _fmt(actual), to_unit, result_value), evidence)


# --- dates ---------------------------------------------------------------------------------------------------------------------------

_MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
_MONTHS.update({name.lower(): i for i, name in enumerate(calendar.month_abbr) if name})
_MONTHS.update({"januar": 1, "februar": 2, "märz": 3, "maerz": 3, "mai": 5, "juni": 6, "juli": 7, "oktober": 10, "dezember": 12, "sept": 9})
_WEEKDAYS = {}
for _i, (_en, _de) in enumerate(zip(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                                    ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"])):
    for _name in (_en, _en[:3], _de, _de[:2]):
        _WEEKDAYS[_name] = _i
_WEEKDAYS.update({"mon": 0, "tue": 1, "tues": 1, "wed": 2, "thu": 3, "thur": 3, "thurs": 3, "fri": 4, "sat": 5, "sun": 6, "sonnabend": 5})


def parse_date(value):
    """a date from 2024-02-29, 29.02.2024, 29/02/2024 (day first), 'February 29, 2024' or '29 February 2024'"""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = str(value).strip().rstrip(".")
    for pattern, order in ((r"(\d{4})-(\d{1,2})-(\d{1,2})", "ymd"), (r"(\d{1,2})\.(\d{1,2})\.(\d{4})", "dmy"), (r"(\d{1,2})/(\d{1,2})/(\d{4})", "dmy")):
        m = re.fullmatch(pattern, text)
        if m:
            parts = dict(zip(order, map(int, m.groups())))
            return datetime.date(parts["y"], parts["m"], parts["d"])
    m = re.fullmatch(r"([A-Za-zäÄ]+)\.? (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})", text)
    if m and m.group(1).lower() in _MONTHS:
        return datetime.date(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2)))
    m = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?\.? ([A-Za-zäÄ]+)\.? (\d{4})", text)
    if m and m.group(2).lower() in _MONTHS:
        return datetime.date(int(m.group(3)), _MONTHS[m.group(2).lower()], int(m.group(1)))
    raise ValueError("'%s' is not a date I can read" % text)


def date_claim(kind, date=None, weekday=None, start=None, end=None, days=None, birth=None, on=None, years=None, year=None, leap=None, a=None, b=None,
               relation=None, result_date=None):
    """calendar facts, with the data already in fields (reading dates from prose is the model's job, checking them is code's):
    weekday {date, weekday}; days_between {start, end, days} (end minus start); add_days {start, days, result_date}; age {birth, on, years}; leap_year {year, leap};
    order {a, b, relation: before | after | same}"""
    name = "date_claim"
    try:
        if kind == "weekday":
            actual = parse_date(date).weekday()
            claimed = _WEEKDAYS[str(weekday).strip().lower().rstrip(".")]
            names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            ok, detail = actual == claimed, "%s was a %s" % (parse_date(date).isoformat(), names[actual])
        elif kind == "days_between":
            actual = (parse_date(end) - parse_date(start)).days
            ok, detail = actual == int(days), "%s to %s are %d days" % (parse_date(start).isoformat(), parse_date(end).isoformat(), actual)
        elif kind == "add_days":
            actual = parse_date(start) + datetime.timedelta(days=int(days))
            ok, detail = actual == parse_date(result_date), "%s + %d days is %s" % (parse_date(start).isoformat(), int(days), actual.isoformat())
        elif kind == "age":
            birthday, today = parse_date(birth), parse_date(on)
            actual = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            ok, detail = actual == int(years), "born %s, on %s the age is %d" % (birthday.isoformat(), today.isoformat(), actual)
        elif kind == "leap_year":
            actual = calendar.isleap(int(year))
            ok, detail = actual == bool(leap), "%d %s a leap year" % (int(year), "is" if actual else "is not")
        elif kind == "order":
            first, second = parse_date(a), parse_date(b)
            actual = "before" if first < second else "after" if first > second else "same"
            ok, detail = actual == str(relation).strip().lower(), "%s is %s %s" % (first.isoformat(), actual, second.isoformat())
        else:
            return result(NOT_APPLICABLE, name, "unknown kind '%s' (weekday, days_between, add_days, age, leap_year, order)" % kind)
    except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
        return result(NOT_APPLICABLE, name, "the data cannot be read: %s" % exc)
    return result(PASS if ok else FAIL, name, detail + ("" if ok else ", which is not what was claimed"), [{"computed": str(actual)}])


# --- structure -------------------------------------------------------------------------------------------------------------------------

def schema_valid(value, schema):
    problems = check_schema(value, schema) if isinstance(schema, dict) else None
    if problems is None:
        return result(NOT_APPLICABLE, "schema_valid", "a schema object is needed")
    return result(FAIL if problems else PASS, "schema_valid", "; ".join(problems[:5]) if problems else "the value fits the schema", [{"problems": problems}] if problems else [])


def _moment(value):
    if isinstance(value, (datetime.datetime,)):
        return value
    text = str(value).strip()
    if re.fullmatch(r"\d{1,2}:\d{2}", text):
        hours, minutes = map(int, text.split(":"))
        return datetime.datetime(2000, 1, 1, hours, minutes)
    return datetime.datetime.fromisoformat(text)


def schedule_overlap(events, allow_touching=True):
    """no two events overlap (one may start when the other ends); events: [{name, start, end}] with ISO times or HH:MM"""
    name = "schedule_overlap"
    try:
        items = sorted(((_moment(e["start"]), _moment(e["end"]), str(e.get("name", i))) for i, e in enumerate(events)), key=lambda x: x[0])
        for start, end, label in items:
            if end <= start:
                return result(FAIL, name, "'%s' ends before it starts" % label, [{"event": label}])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return result(NOT_APPLICABLE, name, "the events cannot be read (%s)" % exc)
    clashes = []
    for (s1, e1, n1), (s2, e2, n2) in zip(items, items[1:]):
        if s2 < e1 or (not allow_touching and s2 == e1):
            clashes.append({"first": n1, "second": n2})
    if clashes:
        return result(FAIL, name, "%d overlap(s): %s" % (len(clashes), ", ".join("%s / %s" % (c["first"], c["second"]) for c in clashes)), clashes)
    return result(PASS, name, "%d events without overlap" % len(items))


# --- web checks ---------------------------------------------------------------------------------------------------------------------------

_MULTI_SUFFIX = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "org.au", "co.jp", "co.nz", "co.za", "co.in", "com.br", "com.cn", "com.mx", "com.tr", "co.kr"}
_SEARCH_PAGES = re.compile(r"^https?://([a-z0-9-]+\.)*(google|bing|duckduckgo|yahoo|ecosia|startpage|baidu|yandex)\.[a-z.]+(:\d+)?(/search\b|/?(\?|$)|/html\b)|/search\?|[?&]q=", re.I)


def registered_domain(host):
    """example.co.uk for www.news.example.co.uk (a short list of two-part suffixes; good enough to tell sources apart)"""
    labels = [l for l in str(host).lower().strip(".").split(".") if l]
    if len(labels) <= 2:
        return ".".join(labels)
    return ".".join(labels[-3:]) if ".".join(labels[-2:]) in _MULTI_SUFFIX else ".".join(labels[-2:])


def _shingles(text, size=5):
    words = _tokens(normalize(text))[:600]
    return {" ".join(words[i:i + size]) for i in range(max(1, len(words) - size + 1))}


def same_content(a, b, threshold=0.8):
    """two pages that are copies of each other (mirrors, syndicated articles) count as one source"""
    sa, sb = _shingles(a), _shingles(b)
    if not sa or not sb:
        return False
    return len(sa & sb) / min(len(sa), len(sb)) >= threshold


def make_citation_check(fetch):
    """citation_check(url, quote=None, title=None): the cited page loads, is not a search result page, and contains the quote. fetch(url) -> page dict of web_tools; raises WebError"""
    name = "citation"

    def citation_check(url, quote=None, title=None):
        if not isinstance(url, str) or not url.strip():
            return result(NOT_APPLICABLE, name, "an address is needed")
        if _SEARCH_PAGES.search(url):
            return result(FAIL, name, "this is a search results page, not a source", [{"url": url}])
        try:
            page = fetch(url)
        except web_tools.UnsafeUrl as exc:
            return result(FAIL, name, "the address cannot be a source: %s" % exc, [{"url": url}])
        except web_tools.HttpStatusError as exc:
            if exc.status in (404, 410):
                return result(FAIL, name, "the page does not exist (%d)" % exc.status, [{"url": url, "status": exc.status}])
            return result(INCONCLUSIVE, name, "the page could not be read now (%d)" % exc.status, [{"url": url, "status": exc.status}])
        except web_tools.UnsupportedContent as exc:
            return result(INCONCLUSIVE, name, str(exc), [{"url": url}])
        except web_tools.WebError as exc:
            return result(INCONCLUSIVE, name, "the page could not be loaded: %s" % exc, [{"url": url}])
        evidence = [{"url": page.get("url", url), "title": page.get("title", ""), "clipped": page.get("clipped", False), "signals": page.get("signals", [])}]
        if quote:
            outcome = quote_in_source(quote, page.get("text", ""))
            note = " (the page was clipped, the quote may be in the part that was not read)" if page.get("clipped") and outcome["status"] == FAIL else ""
            status = INCONCLUSIVE if note else outcome["status"]
            return result(status, name, "the page loads; " + outcome["detail"] + note, evidence + outcome["evidence"])
        if title:
            wanted, got = set(_tokens(normalize(title))), set(_tokens(normalize(page.get("title", ""))))
            overlap = len(wanted & got) / len(wanted) if wanted else 0.0
            if overlap < 0.3:
                return result(INCONCLUSIVE, name, "the page loads, but its title ('%s') hardly matches the cited one" % page.get("title", ""), evidence)
        return result(PASS, name, "the page loads and is a real page", evidence)

    return citation_check


_DISPUTE = re.compile(r"\b(myth|misconception|false|incorrect|debunk\w*|hoax|not true|untrue|wrong|fake|correction|retract\w*|disproved?)\b", re.I)
DEFAULT_DISCONFIRMING = ("myth", "false")


def _fact_in(fact, text):
    f, t = normalize(str(fact)), normalize(text)
    if f in t:
        return True
    digits = re.sub(r"[,\s]", "", f)                                        # 1,000 and 1000
    return bool(re.fullmatch(r"[\d.]+", digits)) and digits in re.sub(r"(?<=\d)[,\s](?=\d{3})", "", t)


DISPUTE_WINDOW = 90


def _disputed(snippet, facts, width=DISPUTE_WINDOW):
    """a correction marker (myth, false, misconception ...) within `width` characters of one of the facts in the snippet. The marker alone is not enough: a search for 'X myth'
    returns pages about myths in general, and those mention the fact in passing."""
    text = normalize(snippet)
    for fact in facts:
        needle = normalize(str(fact))
        start = text.find(needle)
        while needle and start >= 0:
            if _DISPUTE.search(text[max(0, start - width):start + len(needle) + width]):
                return True
            start = text.find(needle, start + 1)
    return False


def _around(fact, text, width=120):
    t = re.sub(r"\s+", " ", text)
    at = t.lower().find(str(fact).lower())
    return t[max(0, at - width):at + len(str(fact)) + width] if at >= 0 else ""


def make_web_confirm(search, fetch):
    """web_confirm(entities, facts=None, claim=None, ...): independent confirmation on the web. search(query, count) and fetch(url) are the tools of web_tools.
    The query is built from the key entities and numbers (never from the wording of the claim); a disconfirming query always runs; at least `min_sources` independent
    domains (no mirrors) must contain all the facts; nothing found or disagreement is `inconclusive`, never `fail`."""
    name = "web_confirm"

    def web_confirm(entities, facts=None, claim=None, language=None, max_fetches=4, min_sources=2, disconfirming=DEFAULT_DISCONFIRMING, time_range=None):
        entities = [str(e).strip() for e in (entities or []) if str(e).strip()]
        facts = [str(f).strip() for f in (facts if facts is not None else entities) if str(f).strip()]
        if not entities or not facts:
            return result(NOT_APPLICABLE, name, "key entities or numbers of the claim are needed")
        query = " ".join(entities[:6])
        calls = {"searches": 0, "fetches": 0}
        if claim and _jaccard(_tokens(normalize(query)), _tokens(normalize(claim))) > 0.8:
            return result(NOT_APPLICABLE, name, "the query would repeat the wording of the claim: give the key entities and numbers only")
        notes, sources, mirrors, signals = [], [], 0, []
        try:
            found = search(query, count=8, language=language, time_range=time_range)
            calls["searches"] += 1
        except web_tools.SearchError as exc:
            return result(INCONCLUSIVE, name, "no search backend answered: %s" % exc, [{"calls": calls}])
        seen_domains, accepted_texts = set(), []
        for item in found.get("results", []):
            if len(sources) + mirrors >= max_fetches or calls["fetches"] >= max_fetches:
                break
            domain = registered_domain(urlparse(item["url"]).hostname or "")
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            try:
                page = fetch(item["url"])
                calls["fetches"] += 1
            except web_tools.WebError as exc:
                calls["fetches"] += 1
                notes.append("%s: %s" % (domain, exc))
                continue
            text = page.get("text", "")
            if page.get("signals"):
                signals.append({"domain": domain, "signals": page["signals"]})
            if not all(_fact_in(f, text) for f in facts):
                continue
            if any(same_content(text, other) for other in accepted_texts):
                mirrors += 1
                continue
            accepted_texts.append(text)
            sources.append({"domain": domain, "url": page.get("url", item["url"]), "title": page.get("title", ""), "passage": _around(facts[0], text)})
        disputes, disconfirm_ran = [], 0
        for word in tuple(disconfirming or ()):
            try:
                other = search("%s %s" % (query, word), count=8, language=language, time_range=time_range)
                calls["searches"] += 1
                disconfirm_ran += 1
            except web_tools.SearchError as exc:
                notes.append("disconfirming search '%s' failed: %s" % (word, exc))
                continue
            for item in other.get("results", []):
                snippet = item.get("snippet", "")
                if _disputed(snippet, facts):
                    disputes.append({"url": item["url"], "snippet": item.get("snippet", "")[:300], "query": word})
        evidence = [{"sources": sources, "disputes": disputes, "mirrors_ignored": mirrors, "notes": notes, "injection_signals": signals, "calls": calls, "query": query}]
        if disputes:
            return result(INCONCLUSIVE, name, "%d independent source(s) agree, but %d result(s) look like a correction or a debunking" % (len(sources), len(disputes)), evidence)
        if len(sources) < min_sources:
            return result(INCONCLUSIVE, name, "%d of %d independent sources contain the facts%s" % (len(sources), min_sources, " (%d mirror(s) ignored)" % mirrors if mirrors else ""), evidence)
        if not disconfirm_ran:
            return result(INCONCLUSIVE, name, "%d independent sources agree, but the disconfirming search could not run" % len(sources), evidence)
        return result(PASS, name, "%d independent sources contain the facts, no sign of a correction" % len(sources), evidence)

    return web_confirm


def _jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


# --- scripts: the model writes a check, the sandbox runs it -------------------------------------------------------------------------------

def _clip(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "...[+%d characters]" % (len(text) - limit)


def make_script_check(router, broker_factory=None, web=False):
    """script_check(script, data=None, expect=None, ...): a script written for a claim runs in the sandbox (sandbox.py) and its result is the evidence. The contract of the script:
    `result = {"holds": True | False, "values": {the numbers and facts it used}, "explanation": "..."}` (see sandbox.SCRIPT_GUIDE).
    Because a script written by the model that made the claim can share its misconception (HC3), a verdict needs the values: a script that does not say what it used cannot be reviewed,
    so it stays inconclusive. The script text, its hash, the output and the backend are in the evidence. web=True: the script may use `web.get` / `web.search` through the broker
    (broker_factory() makes one per run); such a script is a strong-tier operation (podman). `tainted` says that the input comes from unchecked web or file text."""
    name = "script_web" if web else "script"

    def script_check(script, data=None, expect=None, tainted=False, origin="model", stakes="normal", timeout=None):
        if not isinstance(script, str) or not script.strip():
            return result(NOT_APPLICABLE, name, "a script is needed")
        if router is None:
            return result(INCONCLUSIVE, name, "no sandbox is configured, scripts cannot run")
        if web and broker_factory is None:
            return result(NOT_APPLICABLE, name, "web access for scripts is not configured")
        operation = Operation("web_script" if web else "compute", origin, tainted, stakes)
        broker = broker_factory() if web else None
        if broker is not None:
            with broker:
                run = router.run(script, data, operation=operation, broker=broker, timeout=timeout or 60)
        else:
            run = router.run(script, data, operation=operation, timeout=timeout or 10)
        evidence = {"script_hash": run.script_hash, "script": _clip(script, 1500), "backend": run.backend, "tier": run.tier, "degraded": run.degraded,
                    "seconds": round(run.seconds, 3), "stdout": _clip(run.stdout, 500), "result": run.result}
        if broker is not None:
            evidence["web_log"] = broker.log
        if run.status == "rejected":
            return result(INCONCLUSIVE, name, "the script was not run: %s" % "; ".join(run.problems[:3]), [dict(evidence, problems=run.problems)])
        if run.status == "unavailable":
            return result(INCONCLUSIVE, name, "no sandbox for this operation: %s" % (run.error or {}).get("message", ""), [evidence])
        if run.status != "ok":
            error = run.error or {}
            where = " (line %s)" % error["line"] if error.get("line") else ""
            message = error.get("message", run.status)
            if error.get("type") == "KeyError" and isinstance(data, dict):
                message += " (KeyError: `data` has only the keys %s)" % ", ".join(repr(k) for k in list(data)[:15])          # so that a repair knows what exists
            return result(INCONCLUSIVE, name, "the script %s: %s%s" % ({"timeout": "did not finish", "crashed": "was stopped", "error": "failed"}.get(run.status, run.status), message, where),
                          [dict(evidence, error=error)])
        report = run.result
        if isinstance(report, dict) and "holds" in report:
            holds, values = report["holds"], report.get("values")
            if not isinstance(holds, bool):
                return result(INCONCLUSIVE, name, "`holds` must be true or false", [evidence])
            if not isinstance(values, dict) or not values:
                return result(INCONCLUSIVE, name, "the script says %s but does not report the values it used, so it cannot be reviewed" % ("true" if holds else "false"), [evidence])
            detail = str(report.get("explanation") or ("the script confirms the claim" if holds else "the script refutes the claim"))
            return result(PASS if holds else FAIL, name, _clip(detail, 300), [dict(evidence, values=values)])
        if expect is not None and isinstance(report, dict) and "value" in report:
            try:
                actual, wanted = parse_number(report["value"]), parse_number(expect)
                agrees = _agrees(wanted, actual, 0.005, expect)
            except (ValueError, TypeError):
                actual, wanted = report["value"], expect
                agrees = actual == wanted
            return result(PASS if agrees else FAIL, name, "the script computed %s, the claim says %s" % (report["value"], expect), [evidence])
        return result(INCONCLUSIVE, name, "the script did not report `holds` (or `value` with an expected value)", [evidence])

    return script_check


def describe_data(data, hint=""):
    """the shape of the input of a script as text, made from the real data (names and kinds, never the values), so that the model that writes the script cannot misread it:
    '`data` is a dict with the keys: numbers (list of 4 numbers), claimed (number)'. `hint` (what the keys mean) is appended."""
    def kind(value, depth=0):
        if isinstance(value, bool):
            return "true or false"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "text"
        if value is None:
            return "null"
        if isinstance(value, dict):
            if depth >= 2 or not value:
                return "dict" if not value else "dict with %d keys" % len(value)
            return "dict with the keys: " + ", ".join("%s (%s)" % (k, kind(v, depth + 1)) for k, v in list(value.items())[:15])
        if isinstance(value, (list, tuple)):
            if not value:
                return "empty list"
            if all(isinstance(v, dict) for v in value) and depth < 2 and value[0]:
                keys = list(value[0].items())[:15]
                return "list of %d dicts, each with the keys: %s" % (len(value), ", ".join("%s (%s)" % (k, kind(v, depth + 2)) for k, v in keys))
            kinds = {kind(v, depth + 1) for v in value}
            if len(kinds) == 1:
                one = next(iter(kinds))
                return "list of %d %s" % (len(value), one + "s" if not one.startswith(("dict", "list")) and not one.endswith("s") else one)
            return "list of %d mixed values" % len(value)
        return type(value).__name__
    text = "`data` is a " + kind(data)
    return text + (". " + str(hint).strip() if str(hint).strip() else "")


def build_script_checks(router, broker_factory=None):
    """the functions of the script checks for a sandbox router (sandbox.SandboxRouter) and, for web scripts, a function that makes a broker per run"""
    return {"script_check": make_script_check(router, broker_factory, web=False), "script_check_web": make_script_check(router, broker_factory, web=True)}


# --- the registry and the runner -------------------------------------------------------------------------------------------------------------------------------

OFFLINE_FUNCTIONS = {"describe_data": describe_data, "quote_in_source": quote_in_source, "arithmetic_claim": arithmetic_claim, "unit_conversion": unit_conversion, "date_claim": date_claim,
                     "schema_valid": schema_valid, "schedule_overlap": schedule_overlap}


def build_web_checks(search, fetch):
    """the functions of the web checks for the given tools (search(query, count, language, time_range) -> dict, fetch(url) -> dict)"""
    return {"citation_check": make_citation_check(fetch), "web_confirm": make_web_confirm(search, fetch)}


def combine(results):
    """the one rule (HC1): any fail decides; passes are evidence; inconclusive or nothing applicable leaves the claim open for the next stage.
    Returns {"status": fail | pass | open | not_applicable, "verdict": contradicted | supported | open | none}"""
    applicable = [r for r in results if r["status"] != NOT_APPLICABLE]
    if not applicable:
        return {"status": "not_applicable", "verdict": "none"}
    if any(r["status"] == FAIL for r in applicable):
        return {"status": "fail", "verdict": "contradicted"}
    if all(r["status"] == PASS for r in applicable):
        return {"status": "pass", "verdict": "supported"}
    return {"status": "open", "verdict": "open"}


class CheckRunner:
    """runs the hard checks that apply to a claim: {"type": quotation | citation | numeric | unit | date | structured | schedule | fact, "text": "...", "data": {fields}}.
    The checks come from the library (nodes tagged 'check' that declare the claim type), cheapest first; a check whose required fields are missing in `data` is skipped."""

    def __init__(self, library, functions, tools=None, sandbox=None):
        """functions: callable returning {name: function} (looked up at run time); tools: callable returning the names of tools that exist; sandbox: a SandboxRouter or None
        (without a working sandbox the script checks are not offered, they are never run unprotected)"""
        self.library, self._functions, self._tools, self.sandbox = library, functions, tools or (lambda: None), sandbox

    def run(self, claim, include_web=False, fail_fast=True):
        started = time.time()
        if not isinstance(claim, dict) or not isinstance(claim.get("data", {}), dict):
            return {"status": "not_applicable", "verdict": "none", "results": [], "trace": [], "detail": "a claim needs a type and data fields"}
        data, functions = claim.get("data", {}), self._functions()
        sandboxed = self.sandbox is not None and self.sandbox.available
        chosen = self.library.select("node", tags=["check"], applies_to={"claim_types": claim.get("type", "")}, allow_web=include_web, allow_code=sandboxed,
                                     tools=self._tools(), sandbox=sandboxed)
        candidates = []
        for item in chosen["selected"]:
            entry = self.library.resolve(item["ref"], "node", allow_draft=True)
            if entry["kind"] != "code" or entry["body"]["function"] not in functions or claim.get("type", "") not in (entry.get("applies_to") or {}).get("claim_types", []):
                continue
            safety = entry.get("safety") or {}
            if safety.get("runs_code"):
                # a script that reads the web is a strong-tier operation: skip it when no backend can run it (the run itself would be refused, never weakened)
                kind = "web_script" if safety.get("reads_web") else "compute"
                if not (sandboxed and self.sandbox.available_for(Operation(kind, "model", bool(claim.get("tainted")), claim.get("stakes", "normal")))):
                    continue
            candidates.append(entry)
        candidates.sort(key=lambda e: ((e.get("cost") or {}).get("seconds", 0), e["id"]))
        results, trace = [], []
        for entry in candidates:
            schema = (entry.get("inputs") or {}).get("schema", {})
            properties = schema.get("properties", {})
            missing = [k for k in schema.get("required", []) if k not in data]
            ref = "%s@%d" % (entry["id"], entry["version"])
            if missing:
                trace.append({"ref": ref, "skipped": "missing " + ", ".join(missing)})
                continue
            kwargs = {k: v for k, v in data.items() if k in properties}
            if "claim" in properties and "claim" not in kwargs and claim.get("text"):
                kwargs["claim"] = claim["text"]
            for key in ("tainted", "stakes", "origin"):                     # what the sandbox needs to choose its wall (sandbox.Operation)
                if key in properties and key not in kwargs and key in claim:
                    kwargs[key] = claim[key]
            kwargs.update({k: spec["default"] for k, spec in (entry.get("params") or {}).items() if k not in kwargs and "default" in spec})
            began = time.time()
            try:
                outcome = functions[entry["body"]["function"]](**kwargs)
            except Exception as exc:                        # a check that breaks is inconclusive, not fatal
                outcome = result(INCONCLUSIVE, entry["id"], "the check failed: %s: %s" % (type(exc).__name__, exc))
            outcome = dict(outcome, ref=ref)
            results.append(outcome)
            trace.append({"ref": ref, "status": outcome["status"], "detail": outcome["detail"], "ms": int((time.time() - began) * 1000)})
            if fail_fast and outcome["status"] == FAIL:
                break
        return dict(combine(results), results=results, trace=trace, seconds=round(time.time() - started, 3))


# --- number check (Plan iteration 1, specs/number-gate: REQ-NUM-001 to REQ-NUM-006, IF-001) ------------------------------------------------

_SCALES = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_NOT_UNITS = {"in", "st", "b", "pt", "cup"}                     # ordinary words after a number ("40 in the room")
_PERCENT = {"%": "percent", "percent": "percent"}
_MONEY = {"$": "usd", "€": "eur", "£": "gbp", "₹": "inr", "¥": "jpy", "dollars": "usd", "euros": "eur", "usd": "usd", "eur": "eur"}
_MONEY_SYMBOLS = [k for k in _MONEY if len(k) == 1]
_BOUNDS = (("at least", "ge"), ("at most", "le"), ("more than", "gt"), ("less than", "lt"), ("fewer than", "lt"), ("over", "gt"), ("under", "lt"))
_FILLER = {"the", "a", "an", "of", "in", "on", "at", "and", "or", "is", "are", "was", "were", "has", "have", "had", "by", "for", "to", "with", "as", "about", "around",
           "approximately", "than", "more", "less", "over", "under", "least", "most", "long", "tall", "high", "that", "it", "its", "which", "from"}
_NUMBER = re.compile(r"(?<![\w.,])\d(?:[\d,. ']*\d)?")
_WORD = re.compile(r"[^\W\d_]+(?:/[^\W\d_]+)?|%")


def _dimension(word):
    """(dimension, factor to its base unit) of a unit word, or None"""
    word = word.lower()
    if word in _PERCENT:
        return "percent", 1.0
    if word in _MONEY:
        return "money:" + _MONEY[word], 1.0
    if word in _NOT_UNITS:
        return None
    unit = _unit(word)
    for dimension, table in _UNITS.items():
        if unit in table:
            return dimension, table[unit]
    return None


def _quantities(text):
    """the numbers of a text as quantities: value, scale word, unit dimension, bound, and the content words that follow (up to three)"""
    found = []
    for match in _NUMBER.finditer(text):
        try:
            value = parse_number(match.group())
        except ValueError:
            continue
        symbol = text[:match.start()].rstrip()[-1:]                                    # a currency symbol may stand between a bound and its number ("less than $ 44")
        before = text[:match.start()].rstrip().rstrip("".join(_MONEY_SYMBOLS)).rstrip()
        words = _WORD.findall(re.split(r"[.;!?]\s|\d", text[match.end():], maxsplit=1)[0])
        scale = 1.0
        if words and words[0].lower() in _SCALES:
            scale = _SCALES[words.pop(0).lower()]
        unit = _dimension(words[0]) if words else None
        if unit:
            words.pop(0)
        elif symbol in _MONEY_SYMBOLS:
            unit = ("money:" + _MONEY[symbol], 1.0)
        bound = next((code for phrase, code in _BOUNDS if before.lower().endswith(phrase)), None)
        nouns = {w.lower().rstrip("s") for w in words[:3] if w.lower() not in _FILLER}
        found.append({"value": value, "raw": match.group(), "scale": scale, "unit": unit, "bound": bound, "nouns": nouns})
    return found


def _same_quantity(claimed, seen):
    """REQ-NUM-006: the same unit dimension, or (when one side has no unit) the same noun in the three words after the number ("₹50 crore" and "18 Crore")"""
    if claimed["unit"] and seen["unit"]:
        return claimed["unit"][0] == seen["unit"][0]
    return bool(claimed["nouns"] & seen["nouns"])


def _holds(claimed, seen):
    """does the evidence value keep the claim? The evidence value is expressed in the unit and scale of the claim (REQ-NUM-001, -003, -005)"""
    unit = claimed["unit"][1] if claimed["unit"] else 1.0
    actual = seen["value"] * seen["scale"] * (seen["unit"][1] if seen["unit"] else 1.0) / (claimed["scale"] * unit)
    bound, limit = claimed["bound"], claimed["value"]
    if bound:
        return {"gt": actual > limit, "ge": actual >= limit, "lt": actual < limit, "le": actual <= limit}[bound]
    return _agrees(limit, actual, 0.01, claimed["raw"])


def _judge_quantity(claimed, seen_values):
    """pass, fail or None (nothing of the evidence decides) for one claimed quantity; a bound in the evidence ("more than 23 million") decides nothing"""
    deciding = [s for s in seen_values if _same_quantity(claimed, s) and not s["bound"]]
    if not deciding:
        return None
    return PASS if any(_holds(claimed, s) for s in deciding) else FAIL


def number_check(claim, evidence):
    """Compares the numbers of a claim with the values of the same quantity in the evidence. Status: pass, fail (the evidence states the quantity with
    another value), inconclusive (nothing of the evidence decides) or not_applicable (no evidence, or no number in the claim). The detail is at most 200 characters."""
    name = "number_check"
    if not str(evidence).strip():
        return result(NOT_APPLICABLE, name, "no evidence")
    claimed = _quantities(str(claim))
    if not claimed:
        return result(NOT_APPLICABLE, name, "the claim has no number")
    seen = _quantities(str(evidence))
    verdicts = [(c, _judge_quantity(c, seen)) for c in claimed]
    for status, text in ((FAIL, "the evidence gives another value for %s"), (PASS, "the evidence agrees with %s")):
        hit = next((c for c, v in verdicts if v == status), None)
        if hit:
            return result(status, name, (text % hit["raw"])[:200], [{"claimed": hit["raw"]}])
    return result(INCONCLUSIVE, name, "no value of the same quantity in the evidence")
