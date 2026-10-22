"""Writes the contact block on site/about.html (D-43).

No address appears on the site: About carries a form that posts to
Web3Forms, which forwards it to Andrew's inbox. The form's access key is
public by design (Web3Forms keys only name a destination; they cannot read
anything) and comes from the environment, by name, through envfile.get():
WEB3FORMS_ACCESS_KEY. The destination address is set at web3forms.com and
never appears here.

Without the key the block is the LinkedIn link alone, so a machine without
C:\\Users\\dasil\\.env builds a page with no dead form on it.

    python build_about.py            rewrite the block in site/about.html
    python build_about.py --check    exit 1 if the page differs from what it would write

The block sits between two markers; everything outside them is the page's
own, hand-written text (D-02), and this script never touches it. The
substitution counts its markers and refuses when there is not exactly one
pair (trap 27: a patch that matches nothing writes the shipped page and
looks like success).
"""
import html
import os
import sys

import envfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "site", "about.html")
BEGIN = "<!-- contact:begin (build_about.py writes this block; D-43) -->"
END = "<!-- contact:end -->"
LINKEDIN = "https://www.linkedin.com/in/andrewsilvestri/"


def block(key):
    li = f'<a href="{LINKEDIN}">LinkedIn</a>'
    if not key:
        return f"<p>{li}</p>"
    k = html.escape(key, quote=True)
    return f"""<h2 id="contact">Contact</h2>
<form class="contact" id="contact-form" action="https://api.web3forms.com/submit" method="POST" hidden>
<input type="hidden" name="access_key" value="{k}">
<input type="hidden" name="from_name" value="andrewsilvestri.com contact form">
<input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<label for="cf-name">Name</label>
<input id="cf-name" type="text" name="name" required maxlength="100" autocomplete="name">
<label for="cf-subject">Subject</label>
<input id="cf-subject" type="text" name="subject" required maxlength="150">
<label for="cf-message">Message</label>
<textarea id="cf-message" name="message" required rows="6" maxlength="5000"></textarea>
<button type="submit" class="btn">Send</button>
<p class="small" id="cf-status" role="status" aria-live="polite"></p>
</form>
<noscript><p>The contact form needs JavaScript. Without it, write to me on {li}.</p></noscript>
<p>Also on {li}.</p>"""


def render(page, key):
    if page.count(BEGIN) != 1 or page.count(END) != 1:
        sys.exit(f"about.html: expected one {BEGIN!r} and one {END!r}, found "
                 f"{page.count(BEGIN)} and {page.count(END)}")
    a = page.index(BEGIN) + len(BEGIN)
    b = page.index(END)
    return page[:a] + "\n" + block(key) + "\n" + page[b:]


def main():
    check = "--check" in sys.argv
    page = open(PAGE, encoding="utf-8", newline="").read()
    key = envfile.get("WEB3FORMS_ACCESS_KEY")
    out = render(page, key)
    print(f"  contact block: {'form' if key else 'LinkedIn only (WEB3FORMS_ACCESS_KEY not set)'}")
    if out == page:
        print("  about.html: unchanged")
        return 0
    if check:
        print("  about.html: DIFFERS from what build_about.py writes")
        return 1
    with open(PAGE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print("  about.html: rewritten")
    return 0


if __name__ == "__main__":
    sys.exit(main())
