"""Bamah's emails, dressed like the app: a dark band with the icon, like the curtain over a stage, and a
white page under it. Email clients are picky, so it's tables and inline styles only, no scripts, no SVG,
and every colour written out. Each one gives back (subject, text, html), and the text is the same email
for mail apps that want plain text.
"""
from html import escape

C = {"bg": "#F1ECEA", "page": "#FFFFFF", "ink": "#1D1716", "body": "#3B3331", "muted": "#6F6461",
     "rule": "#E3DCD9", "sunk": "#F6F2F0", "band": "#120E0F", "band_2": "#A3918C", "accent": "#B4513F"}
UI = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
PROSE = "Literata, Georgia, 'Times New Roman', serif"
MONO = "SFMono-Regular, Menlo, Consolas, monospace"


def esc(s) -> str:
    return escape(str(s if s is not None else ""), quote=True)


def first(name) -> str:
    return (str(name or "").strip().split() or [""])[0]


def kicker(label: str) -> str:
    return (f'<p style="margin:0 0 12px;font-family:{UI};font-size:12px;font-weight:700;letter-spacing:1.5px;'
            f'text-transform:uppercase;color:{C["accent"]}">{esc(label)}</p>')


def title(html: str) -> str:
    return (f'<h1 style="font-family:{PROSE};font-size:30px;line-height:1.25;font-weight:600;color:{C["ink"]};'
            f'margin:0 0 16px">{html}</h1>')


def para(html: str, extra: str = "") -> str:
    return (f'<p style="font-family:{UI};font-size:16px;line-height:1.6;color:{C["body"]};margin:0 0 16px;{extra}">'
            f'{html}</p>')


def small(html: str) -> str:
    return para(html, f"font-size:14px;color:{C['muted']};margin-top:14px")


def button(label: str, href: str) -> str:
    return f"""<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 4px"><tr>
<td align="center" bgcolor="{C['accent']}" style="border-radius:999px;background:{C['accent']}">
<a href="{esc(href)}" style="display:inline-block;padding:13px 28px;font-family:{UI};font-size:16px;font-weight:700;color:#FFFFFF;text-decoration:none;border-radius:999px">{esc(label)}</a>
</td></tr></table>"""


RULE = f'<div style="height:1px;background:{C["rule"]};margin:28px 0 22px;line-height:1px;font-size:0">&nbsp;</div>'

# A scene the way Bamah shows one: its dark colours, a setting, then each line with what the
# character feels and doesn't say above it.
S = {"bg": "#120E0F", "card": "#1D1718", "line": "#2A2324", "line_2": "#342B2C", "ink": "#F2EAE7",
     "muted": "#B9ACA8", "faint": "#8F817D", "inner": "#231D21", "inner_ink": "#D9C1E0"}


def _line(initial: str, hue: str, name: str, mood: str, inner: str, said: str) -> str:
    return f"""<tr><td valign="top" width="34" style="width:34px;padding:0 12px 18px 0">
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" valign="middle" width="34" height="34" bgcolor="{hue}" style="width:34px;height:34px;border-radius:17px;background:{hue};font-family:{UI};font-size:14px;font-weight:700;color:#FFFFFF">{esc(initial)}</td></tr></table></td>
<td valign="top" style="padding:0 0 18px">
<div style="font-family:{UI};font-size:14px;font-weight:600;color:{S['ink']};margin:0 0 7px">{esc(name)} <span style="font-family:{PROSE};font-style:italic;font-weight:400;font-size:13px;color:{S['muted']}">{esc(mood)}</span></div>
<div style="font-family:{PROSE};font-style:italic;font-size:14px;line-height:1.5;color:{S['inner_ink']};background:{S['inner']};border-radius:10px;padding:8px 12px;margin:0 0 7px">{esc(inner)}</div>
<div style="font-family:{PROSE};font-size:16px;line-height:1.55;color:{S['ink']};background:{S['card']};border:1px solid {S['line']};border-radius:4px 16px 16px 16px;padding:10px 15px">{esc(said)}</div>
</td></tr>"""


def scene() -> str:
    return f"""{RULE}<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{S['bg']}" style="background:{S['bg']};border-radius:14px">
<tr><td style="padding:20px 20px 4px">
<div style="font-family:{PROSE};font-style:italic;font-size:14px;line-height:1.55;color:{S['muted']};padding:0 0 14px;margin:0 0 18px;border-bottom:1px dashed {S['line_2']}">The kitchen, after midnight. The letter is still on the table.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
{_line("M", "#7A5A93", "Mara", "prickly", "She's been waiting all night for him to bring it up.", "You're late.")}
{_line("B", "#3F7363", "Ben", "guarded", "He knows she found it. He decides to wait her out.", "Traffic. You know how it is.")}
</table></td></tr></table>
{small("Every reply starts with what the character feels and won't say, and every line remembers who was in the room.")}"""


def shell(*, url: str, preheader: str, body: str, footer: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>Bamah</title></head>
<body style="margin:0;padding:0;background:{C['bg']}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{C['bg']}">{esc(preheader)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{C['bg']}" style="background:{C['bg']}"><tr><td align="center" style="padding:28px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px">
  <tr><td bgcolor="{C['band']}" style="background:{C['band']};border-radius:16px 16px 0 0;padding:24px 30px;border-bottom:4px solid {C['accent']}">
    <a href="{esc(url)}" style="text-decoration:none">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
      <td valign="middle" style="padding-right:14px"><img src="{esc(url)}/static/icon-192.png" width="44" height="44" alt="" style="display:block;border-radius:11px"></td>
      <td valign="middle" style="font-family:{UI};font-size:26px;font-weight:700;color:#FFFFFF;line-height:1">Bamah <span lang="he" dir="rtl" style="font-family:{PROSE};font-size:19px;font-weight:500;color:{C['band_2']}">&#1489;&#1468;&#1464;&#1502;&#1464;&#1492;</span></td>
    </tr></table></a>
  </td></tr>
  <tr><td bgcolor="{C['page']}" style="background:{C['page']};border-radius:0 0 16px 16px;padding:32px 30px 28px;border:1px solid {C['rule']};border-top:0">
    {body}
  </td></tr>
  <tr><td align="center" style="padding:18px 24px 0;font-family:{UI};font-size:12px;line-height:1.6;color:{C['muted']}">
    {footer}<br><a href="{esc(url)}" style="color:{C['muted']}">{esc(url.split('://')[-1])}</a>
  </td></tr>
</table></td></tr></table>
</body></html>"""


def code(code: str, url: str, minutes: int = 10):
    """The six digits, for signing in."""
    box = (f'<td align="center" width="44" style="width:44px;height:56px;border:2px solid {C["ink"]};border-radius:8px;'
           f'background:#FFFFFF;font-family:{MONO};font-size:28px;font-weight:700;color:{C["ink"]}">{{}}</td>'
           f'<td width="7" style="width:7px"></td>')
    digits = "".join(box.format(esc(d)) for d in code[:3]) + '<td width="14" style="width:14px"></td>' + \
        "".join(box.format(esc(d)) for d in code[3:])
    html = shell(
        url=url,
        preheader=f"{code} is your Bamah code. It works for {minutes} minutes.",
        footer="If you didn't ask for this code, you can ignore this email. Nobody gets in without it.",
        body=f"""{kicker('Sign in')}
{title('Your code')}
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:4px 0 22px"><tr>{digits}</tr></table>
{para(f"It works for {minutes} minutes. Type it into Bamah, or paste it.")}""")
    text = (f"{code[:3]} {code[3:]}\n\n"
            f"Your code for signing in to Bamah. It works for {minutes} minutes.\n"
            "If you didn't ask for it, you can ignore this email: nobody gets in without the code.\n\n"
            f"Bamah\n{url}\n")
    return f"{code} is your Bamah code", text, html


def invite(*, name: str, email: str, url: str, signature: str, stories: bool = True):
    hi = f"Hi {first(name)}," if first(name) else "Hi,"
    start = ("Everything that was in mine is in yours too, so you can carry on right where you were. "
             "From now on, what you write there is yours alone: your scenes, your characters and your models."
             if stories else
             "It starts empty, with the models already set up, and what you write there is yours alone.")
    how = (f"Sign in with <b style='color:{C['ink']}'>{esc(email)}</b>. You'll get a 6&#8209;digit code by email, so "
           "there's no password to remember. If you'd rather have one, you can set it in Settings, under People.")
    html = shell(
        url=url,
        preheader=f"{signature} made you a profile on Bamah. Sign in with this email, no password needed.".strip(),
        footer=f"You got this because {esc(signature or 'someone')} made you a profile on Bamah.",
        body=f"""{kicker("You're invited")}
{title(f"{esc(hi[:-1])}, this one's yours")}
{para(f"I made you a profile of your own on <b style='color:{C['ink']}'>Bamah</b>, the place for developing a story's characters by putting them in scenes together. {esc(start)}")}
{button('Open Bamah', url)}
{small(how)}
{scene()}
{para(f"If anything doesn't work, just reply to this email and let me know.<br>{esc(signature)}", "margin:22px 0 0")}""")
    text = f"""{hi}

I made you a profile of your own on Bamah, the place for developing a story's characters by putting them in scenes together. {start}

To sign in, go to {url} and type {email}. You'll get a 6-digit code by email, so there's no password to remember. If you'd rather have one, you can set it in Settings, under People.

If anything doesn't work, just reply to this email and let me know.

{signature}
"""
    return "Your own profile on Bamah", text, html
