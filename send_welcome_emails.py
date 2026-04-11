"""
Script one-shot : envoie l'email de bienvenue à tous les membres confirmés.
Usage : python send_welcome_emails.py
"""

import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

GMAIL_USER = os.environ.get("GMAIL_USER", "contact@thepulse.ma")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Load email template
jinja_env = Environment(loader=FileSystemLoader("templates/emails"))
template = jinja_env.get_template("welcome.html")


def get_confirmed_members():
    if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, email, full_name, role FROM pulse_members WHERE is_confirmed = TRUE ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return [{"id": r[0], "email": r[1], "full_name": r[2], "role": r[3]} for r in rows]
    else:
        import sqlite3
        conn = sqlite3.connect("thepulse.db")
        cur = conn.cursor()
        cur.execute("SELECT id, email, full_name, role FROM pulse_members WHERE is_confirmed = 1 ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return [{"id": r[0], "email": r[1], "full_name": r[2], "role": r[3]} for r in rows]


def send_welcome(member):
    profile_url = f"https://www.thepulse.ma/my-profile/{member['id']}"
    html = template.render(
        name=member["full_name"].split()[0],
        role=member["role"].capitalize(),
        profile_url=profile_url,
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Bienvenue sur The Pulse — votre profil est prêt"
    msg["From"] = f"The Pulse <{GMAIL_USER}>"
    msg["To"] = member["email"]
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.sendmail(GMAIL_USER, member["email"], msg.as_string())


if __name__ == "__main__":
    members = get_confirmed_members()
    print(f"Found {len(members)} confirmed members.\n")

    ok, errors = 0, []
    for m in members:
        try:
            send_welcome(m)
            print(f"  [OK]    {m['email']}")
            ok += 1
            time.sleep(1)  # éviter spam filters
        except Exception as e:
            print(f"  [FAIL]  {m['email']} — {e}")
            errors.append(m["email"])

    print(f"\nDone: {ok} sent, {len(errors)} failed.")
    if errors:
        print("Failed:", errors)
