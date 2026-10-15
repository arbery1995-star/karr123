"""Flask-App: Formular für Suchaufträge, Double-Opt-in und Abmeldung.

    flask --app immoalert.web run
"""

import re
import secrets

from flask import Flask, abort, render_template, request

from . import config, db, mailer

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
db.init()

PROPERTY_TYPES = {"wohnung": "Eigentumswohnung", "haus": "Haus", "mehrfamilienhaus": "Mehrfamilienhaus"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOCATION_RE = re.compile(r"^[\wäöüÄÖÜß .\-/]{2,60}$")

# name: (default, min, max, required)
NUMBER_FIELDS = {
    "radius_km": (20, 5, 200, True),
    "min_cashflow": (100, -2000, 20000, True),
    "max_price": (None, 10000, 20_000_000, False),
    "min_size": (None, 10, 5000, False),
    "rent_per_sqm": (11, 3, 50, True),
    "equity": (30000, 0, 10_000_000, True),
    "interest_pct": (3.8, 0, 15, True),
    "repayment_pct": (2.0, 0, 15, True),
    "closing_pct": (10, 0, 20, True),
    "costs_pct": (15, 0, 60, True),
}


def validate(form):
    data, errors = {}, {}
    email = form.get("email", "").strip()
    if not EMAIL_RE.match(email):
        errors["email"] = "Bitte eine gültige E-Mail-Adresse angeben."
    data["email"] = email

    ptype = form.get("property_type", "")
    if ptype not in PROPERTY_TYPES:
        errors["property_type"] = "Bitte einen Immobilientyp wählen."
    data["property_type"] = ptype

    location = form.get("location", "").strip()
    if not LOCATION_RE.match(location):
        errors["location"] = "Bitte PLZ oder Ort angeben."
    data["location"] = location

    for name, (default, lo, hi, required) in NUMBER_FIELDS.items():
        raw = form.get(name, "").strip().replace(",", ".")
        if raw == "":
            if required and default is None:
                errors[name] = "Pflichtfeld."
            data[name] = default
            continue
        try:
            value = float(raw)
        except ValueError:
            errors[name] = "Bitte eine Zahl angeben."
            continue
        if not lo <= value <= hi:
            errors[name] = f"Erlaubt: {lo:g} bis {hi:g}."
        data[name] = value

    data["frequency"] = 2 if form.get("frequency") == "2" else 1
    if not form.get("consent"):
        errors["consent"] = "Bitte der Datenverarbeitung zustimmen."
    return data, errors


@app.get("/")
def index():
    return render_template("index.html", types=PROPERTY_TYPES, form={}, errors={})


@app.post("/")
def subscribe():
    data, errors = validate(request.form)
    if errors:
        return render_template("index.html", types=PROPERTY_TYPES, form=request.form, errors=errors), 400

    token = secrets.token_urlsafe(24)
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO subscriptions (email, property_type, location, radius_km, min_cashflow,
                   max_price, min_size, rent_per_sqm, equity, interest_pct, repayment_pct,
                   closing_pct, costs_pct, frequency, token)
               VALUES (:email, :property_type, :location, :radius_km, :min_cashflow, :max_price,
                   :min_size, :rent_per_sqm, :equity, :interest_pct, :repayment_pct, :closing_pct,
                   :costs_pct, :frequency, :token)""",
            {**data, "token": token},
        )
    confirm_url = f"{config.BASE_URL}/bestaetigen/{token}"
    html = mailer.render("email_confirm.html", data=data, type_label=PROPERTY_TYPES[data["property_type"]],
                         confirm_url=confirm_url)
    mailer.send(data["email"], "Bitte bestätige deinen Suchauftrag", html)
    return render_template("message.html", title="Fast geschafft!",
                           text=f"Wir haben dir eine Mail an {data['email']} geschickt. "
                                "Bitte bestätige den Link darin – danach bekommst du die Treffer.")


def _set_flag(token, column, value):
    with db.connect() as conn:
        cur = conn.execute(f"UPDATE subscriptions SET {column} = ? WHERE token = ?", (value, token))
        if cur.rowcount == 0:
            abort(404)


@app.get("/bestaetigen/<token>")
def confirm(token):
    _set_flag(token, "confirmed", 1)
    return render_template("message.html", title="Suchauftrag aktiv ✓",
                           text="Ab jetzt durchsuchen wir täglich die Portale für dich und schicken "
                                "dir neue Treffer per Mail.")


@app.get("/abmelden/<token>")
def unsubscribe(token):
    _set_flag(token, "active", 0)
    return render_template("message.html", title="Abgemeldet",
                           text="Du bekommst keine Mails mehr zu diesem Suchauftrag.")
