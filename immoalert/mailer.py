import os
import re
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import config

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
)
env.filters["eur"] = lambda v: f"{v:,.0f} €".replace(",", ".") if v is not None else "–"


def render(template, **ctx):
    return env.get_template(template).render(base_url=config.BASE_URL, **ctx)


def send(to, subject, html, unsubscribe_url=None):
    msg = EmailMessage()
    msg["From"] = config.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
    msg.set_content(re.sub(r"<[^>]+>", "", html))  # Text-Fallback
    msg.add_alternative(html, subtype="html")

    if not config.SMTP_HOST:
        os.makedirs(config.OUTBOX_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        path = Path(config.OUTBOX_DIR) / f"{stamp}_{re.sub(r'[^a-z0-9]+', '_', to.lower())}.html"
        path.write_text(html, encoding="utf-8")
        print(f"[mail] SMTP_HOST nicht gesetzt – Mail an {to} gespeichert unter {path}")
        return

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as smtp:
        smtp.starttls()
        if config.SMTP_USER:
            smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
        smtp.send_message(msg)
