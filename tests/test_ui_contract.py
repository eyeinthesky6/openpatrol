import unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class IdParser(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.scripts=[]
 def handle_starttag(self,tag,attrs):
  values=dict(attrs)
  if 'id' in values:self.ids.append(values['id'])
  if tag=='script' and values.get('src'):self.scripts.append(values['src'])
class UIContractTest(unittest.TestCase):
 def test_dashboard_has_unique_required_controls(self):
  parser=IdParser();parser.feed((ROOT/'static/index.html').read_text())
  self.assertEqual(len(parser.ids),len(set(parser.ids)))
  required={'camera-grid','camera-preview-grid','alert-list','incident-table','device-grid','patrol-toggle','return-dock','estop','announce-form','ptt','review-dialog','auth-form'}
  self.assertFalse(required-set(parser.ids));self.assertIn('/app.js',parser.scripts)
 def test_external_strings_are_escaped_before_html_rendering(self):
  source=(ROOT/'static/app.js').read_text()
  self.assertIn('const esc=',source)
  for value in ('esc(i.detection.title)','esc(i.detection.source)','esc(c.name)','esc(d.name)'):self.assertIn(value,source)
if __name__=='__main__':unittest.main()
