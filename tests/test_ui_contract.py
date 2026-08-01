import unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
class IdParser(HTMLParser):
    def __init__(self): super().__init__(); self.ids=[]; self.scripts=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if "id" in values: self.ids.append(values["id"])
        if tag=="script" and values.get("src"): self.scripts.append(values["src"])
class UIContractTest(unittest.TestCase):
    def test_dashboard_has_unique_required_controls(self):
        parser=IdParser(); parser.feed((ROOT/"static"/"index.html").read_text(encoding="utf-8"))
        self.assertEqual(len(parser.ids),len(set(parser.ids)))
        required={"map","camera-preview","patrol-toggle","return-dock","estop","incident-table","diagnostics-grid","settings-form","confirm-dialog","review-dialog"}
        self.assertFalse(required-set(parser.ids)); self.assertIn("/app.js",parser.scripts)
    def test_external_strings_are_escaped_before_html_rendering(self):
        source=(ROOT/"static"/"app.js").read_text(encoding="utf-8")
        self.assertIn("const escapeHtml=",source); self.assertIn("escapeHtml(i.detection.title)",source); self.assertIn("escapeHtml(i.detection.source)",source)
if __name__=="__main__": unittest.main()
