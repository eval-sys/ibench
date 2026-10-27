#!/usr/bin/env bash
set -euo pipefail
# install/empty_data.php provides glpi/glpi and global Computer preferences,
# but no personal preferences for this user/type. Only that missing personal
# configuration is owned by this experiment. Global defaults are never written.
# Use GLPI's authenticated native endpoint; resolve user ID and CSRF at runtime.
python3 - "${1:-cleanup}" <<'PYTHON'
import http.cookiejar, urllib.request, urllib.parse, sys
from html.parser import HTMLParser
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.inputs={}; self.user_ids=[]; self.csrf=None; self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='input' and a.get('name'):
            self.inputs[a['name']]=a.get('value','')
            if a['name']=='users_id': self.user_ids.append(a.get('value'))
        if tag=='meta' and a.get('property')=='glpi:csrf_token': self.csrf=a['content']
jar=http.cookiejar.CookieJar(); client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def request(path,data=None,csrf=None):
    req=urllib.request.Request('http://localhost:8000'+path,data=urllib.parse.urlencode(data).encode() if data else None,headers={'X-Glpi-Csrf-Token':csrf,'X-Requested-With':'XMLHttpRequest'} if csrf else {})
    
    try: return client.open(req,timeout=30).read().decode()
    except urllib.error.HTTPError as e:
        print(e.read().decode()[-5000:]); raise
p=Page(request('/'))
fields=p.inputs; fields.update(login_name='glpi',login_password='glpi',auth='local',submit='Sign in');fields.pop('login_remember',None)
request('/front/login.php',fields)
page=Page(request('/front/displaypreference.form.php?itemtype=Computer'))
p=Page(request('/ajax/common.tabs.php?'+urllib.parse.urlencode({'_glpi_tab':'DisplayPreference$2','displaytype':'Computer','in_modal':'1','_target':'/front/displaypreference.form.php','_itemtype':'DisplayPreference','id':'0'})))
uid=next(x for x in p.user_ids if int(x)>0)
if sys.argv[1] == 'setup':
    data={'itemtype':'Computer','users_id':uid,'action':'update_order','opts[]':'31','interface':'central'}
else:
    data={'itemtype':'Computer','users_id':uid,'disable':'1'}
request('/ajax/displaypreference.php', data, page.csrf)
print('Personal Computer preferences: '+sys.argv[1])
PYTHON
