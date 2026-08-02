import unittest
from pathlib import Path
class CommandCentreAssetsTest(unittest.TestCase):
 def test_assets_and_contract_controls_exist(self):
  root=Path(__file__).resolve().parents[1];html=(root/'static/index.html').read_text();js=(root/'static/app.js').read_text()
  for token in ('camera-grid','device-grid','announce-form','ptt','alert-list','incident-list'):self.assertIn(token,html)
  for route in ('/api/v1/command-centre','/api/v1/announce','/api/v1/talkback'):self.assertIn(route,js)
if __name__=="__main__":unittest.main()
