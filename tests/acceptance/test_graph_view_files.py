"""
File checks of the graph viewer page (G-V4.VIEW Track B): TC-GA-031 (REQ-GA-014) and TC-GA-032 (REQ-GA-015) of
specs/mia/goals/G-V4.VIEW/test-spec.md, under TR-VIEW-018, 020, 021. They read the files as committed; no browser.
Run with: python tests/acceptance/test_graph_view_files.py
"""
import glob
import hashlib
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
REPO = os.path.dirname(TESTS)
sys.path.insert(0, os.path.join(TESTS, "helpers"))

from markers import mark  # noqa: E402

PAGE = os.path.join(REPO, "graph_app")
MAIN_TOKENS = os.path.join(REPO, "templates", "static", "chat", "tokens.css")

# the CSS named colours (CSS Color 4); `transparent`, `currentcolor` and `inherit` are keywords, not colours, and are allowed
NAMED = set("""aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown burlywood cadetblue chartreuse
chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen
darkorange darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue dimgray
dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred
indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon
mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue
mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred
papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna
silver skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow
yellowgreen""".split())


def strip_vars(value):
    """the value without its var(...) uses, fallbacks included (nested parentheses counted)"""
    out, i = [], 0
    while i < len(value):
        if value.startswith("var(", i):
            depth, i = 1, i + 4
            while i < len(value) and depth:
                depth += {"(": 1, ")": -1}.get(value[i], 0)
                i += 1
        else:
            out.append(value[i])
            i += 1
    return "".join(out)


def findings(css, where):
    """every style that bypasses the tokens (TR-VIEW-020): colour literals, colour functions, named colours, font families, px radius or shadow"""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found = []
    for prop, value in re.findall(r"([-\w]+)\s*:\s*([^;{}]+)", css):
        prop, rest = prop.lower(), strip_vars(value).strip()
        if re.search(r"#[0-9a-fA-F]{3,8}\b", rest) or re.search(r"\b(rgba?|hsla?)\(", rest, re.I):
            found.append("%s: colour literal in %s: %s" % (where, prop, value.strip()))
        elif any(w.lower() in NAMED for w in re.findall(r"[A-Za-z]+", rest)) and not prop.startswith("--"):
            found.append("%s: named colour in %s: %s" % (where, prop, value.strip()))
        if prop in ("font-family", "font") and rest.strip(" ,") not in ("", "inherit"):
            found.append("%s: font named in %s: %s" % (where, prop, value.strip()))
        if prop in ("border-radius", "box-shadow") and re.search(r"\d+(\.\d+)?px", rest):
            found.append("%s: px value in %s: %s" % (where, prop, value.strip()))
    return found


def page_styles():
    """(where, css) of the page's own style sheets and of the style attributes and <style> blocks of its HTML (TR-VIEW-020)"""
    out = []
    for path in sorted(glob.glob(os.path.join(PAGE, "**", "*.css"), recursive=True)):
        rel = os.path.relpath(path, PAGE)
        if rel == "tokens.css" or rel.startswith("vendor" + os.sep):
            continue
        with open(path, encoding="utf-8") as f:
            out.append((rel, f.read()))
    for path in sorted(glob.glob(os.path.join(PAGE, "*.html"))):
        with open(path, encoding="utf-8") as f:
            html = f.read()
        rel = os.path.relpath(path, PAGE)
        out += [(rel + " <style>", block) for block in re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)]
        out += [(rel + " style=", "x{%s}" % attr) for attr in re.findall(r"\sstyle\s*=\s*\"([^\"]*)\"", html, re.I)]
    return out


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class PageFiles(unittest.TestCase):

    @mark.req("REQ-GA-014")
    def test_TC_GA_031_the_main_apps_tokens_byte_for_byte(self):
        """TC-GA-031: graph_app/tokens.css has the sha256 of templates/static/chat/tokens.css, and the page loads it before its own styles.
        Example: both files hash to the same 64 hex digits; index.html links tokens.css before graph.css."""
        # Given the two token files as committed
        copy = os.path.join(PAGE, "tokens.css")
        self.assertTrue(os.path.exists(copy), "graph_app/tokens.css is missing")
        # When both are hashed and the page's HTML is read
        with open(os.path.join(PAGE, "index.html"), encoding="utf-8") as f:
            links = re.findall(r"<link[^>]+href=\"([^\"]+\.css)\"", f.read())
        # Then both have the same sha256
        self.assertEqual(sha256(copy), sha256(MAIN_TOKENS))
        # And the page loads tokens.css from its own folder before its own styles
        self.assertTrue(links and links[0] == "tokens.css", links)

    @mark.req("REQ-GA-015")
    def test_TC_GA_032_the_pages_styles_come_from_the_tokens(self):
        """TC-GA-032: no colour literal, colour function, named colour, font name or px radius/shadow outside var(--...) in the page's own styles.
        Example: `color: var(--text)` passes; `color: #fff`, `font-family: Inter` and `border-radius: 8px` are findings."""
        # Given the scan can fail: a planted literal and the three other kinds are found, var() uses and keywords are not
        planted = "a{color:#fff} b{font-family:Inter} c{border-radius:8px} d{background:rgb(1,2,3)} e{color:red}"
        self.assertEqual(len(findings(planted, "planted")), 5)
        self.assertEqual(findings("a{color:var(--text)} b{background:var(--x, #fff)} c{border-radius:var(--radius)} d{color:transparent}", "clean"), [])
        # When the page's own style sheets, <style> blocks and style attributes are scanned
        styles = page_styles()
        self.assertTrue(styles, "the page has no style sheet of its own")
        found = [f for where, css in styles for f in findings(css, where)]
        # Then nothing bypasses the tokens
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
