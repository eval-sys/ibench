"""Check native login and local database readiness from any working directory."""

import subprocess
import urllib.request
from html.parser import HTMLParser


class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input":
            self.fields.add((attrs.get("name"), attrs.get("type", "text")))


with urllib.request.urlopen("http://localhost:8000/", timeout=3) as response:
    page = LoginForm()
    page.feed(response.read().decode())
if ("username", "text") not in page.fields or ("password", "password") not in page.fields:
    raise SystemExit("Native login form is unavailable")
count = subprocess.check_output(
    [
        "mariadb",
        "-h",
        "mariadb",
        "-u",
        "dolibarr",
        "-plocal-development",
        "dolibarr",
        "-N",
        "-e",
        "SELECT COUNT(*) FROM llx_user WHERE admin = 1 AND statut = 1",
    ],
    timeout=3,
    text=True,
)
if int(count.strip()) < 1:
    raise SystemExit("Native demo administrator is unavailable")
