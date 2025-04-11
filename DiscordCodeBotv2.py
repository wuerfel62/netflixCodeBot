import imaplib
import email
from email.parser import BytesParser
import requests
from bs4 import BeautifulSoup
import re
import discord
from discord.ext import commands, tasks
import os
import time
import logging
from dotenv import load_dotenv

# --- Konfiguration (aus .env-Datei) ---
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SUBJECT_FILTER = os.getenv("SUBJECT_FILTER")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))

# --- Logging einrichten ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logging.info(f'Bot angemeldet als {bot.user.name} ({bot.user.id})')
    check_email.start()


@tasks.loop(seconds=POLL_INTERVAL)
async def check_email():
    """Überprüft das E-Mail-Postfach und sendet den Code an Discord."""
    try:
        # --- E-Mail-Zugriff ---
        logging.info("Verbinde mit IMAP-Server...")
        with imaplib.IMAP4_SSL(IMAP_SERVER) as mail:
            mail.utf8_enabled = True  # UTF-8 aktivieren!
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select("INBOX")
            logging.info(f"Suche nach E-Mails mit Betreff: {SUBJECT_FILTER}")

            status, messages = mail.search(None, f'(UNSEEN SUBJECT "{SUBJECT_FILTER}")')

            if status == "OK":
                message_ids = messages[0].split()
                logging.info(f"Gefundene Nachrichten-IDs: {message_ids}")
                for message_id in message_ids:
                    status, data = mail.fetch(message_id, "(RFC822)")
                    if status == "OK":
                        raw_email = data[0][1]
                        msg = BytesParser().parsebytes(raw_email)
                        body, html_body = extract_email_content(msg)
                        link = extract_link(body, html_body)

                        if link:
                            code = extract_code_from_page(link)
                            if code:
                                await send_code_to_discord(code)
                            else:
                                logging.warning(f"Kein Code gefunden auf Seite: {link}")
                                await send_error_to_discord("Kein Code auf Seite gefunden")
                        else:
                            logging.warning("Kein Link in E-Mail gefunden.")
                            await send_error_to_discord("Kein Link in E-Mail gefunden.")
            else:
                logging.error(f"Fehler bei der E-Mail-Suche: {status}")
                await send_error_to_discord(f"Fehler bei der E-Mail-Suche: {status}")

    except Exception as e:
        logging.exception(f"Fehler in check_email: {e}")



def extract_email_content(msg):
    """Extrahiert den Text- und HTML-Inhalt einer E-Mail."""
    body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(errors='replace')
            elif content_type == "text/html" and "attachment" not in content_disposition:
                html_body = part.get_payload(decode=True).decode(errors='replace')
    else:
        body = msg.get_payload(decode=True).decode(errors='replace')
    return body, html_body


def extract_link(body, html_body):
    """Extrahiert den *spezifischen* Netflix-Verifizierungslink."""
    link = ""

    # 1. Versuche zuerst die Regex-Methode (primär)
    link_pattern = r'(https://www\.netflix\.com/account/travel/verify\?nftoken=[^\s]+)'
    match = re.search(link_pattern, body)  # Suche im Klartext
    if match:
        link = match.group(1)
        return link  # Gib den Link sofort zurück, wenn gefunden

    # 1.1 Wenn kein Link im body gefunden wurde und es ein html_body gibt, suche dort
    if not link and html_body:
        match = re.search(link_pattern, html_body) # Suche im HTML
        if match:
          link = match.group(1)
          return link

    # 2. Fallback auf BeautifulSoup, wenn die Regex *nichts* findet
    if html_body:
        soup = BeautifulSoup(html_body, 'html.parser')
        #link_tag = soup.find('a', href=True) #<div data-uia="travel-verification-otp" class="challenge-code">0680</div>
        link_tag = soup.find('div', {'data-uia': 'travel-verification-otp', 'class': 'challenge-code'})
        if link_tag:
            otp_code = link_tag.text.strip()
            print(f"The OTP code is: {otp_code}")
        else:
            print("OTP code element not found.")

    return otp_code


def extract_code_from_page(link):
    """Extrahiert den Verifizierungscode von der Webseite."""
    try:
        response = requests.get(link)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- HIER: Code-Extraktion anpassen ---
        code_element = soup.find('div', class_='challenge-code')  # Beispiel

        logging.info(code_element)

        if code_element:
            code = code_element.text.strip()
            return code
        else:
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Seite: {e}")
        return None
    except Exception as e:
        logging.exception(f"Fehler bei Extraktion des Codes von {link}: {e}")
        return None


async def send_code_to_discord(code):
    """Sendet den Verifizierungscode an den Discord-Kanal."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        try:
            await channel.send(f"Der Verifizierungscode lautet: {code}")
            logging.info(f"Code gesendet an Discord-Kanal {DISCORD_CHANNEL_ID}")
        except discord.Forbidden:
            logging.error(f"Bot hat keine Berechtigung, Nachrichten in Kanal {DISCORD_CHANNEL_ID} zu senden.")
        except Exception as e:
            logging.exception(f"Fehler beim senden der Nachricht an Discord: {e}")
    else:
        logging.error(f"Kanal mit ID {DISCORD_CHANNEL_ID} nicht gefunden.")

async def send_error_to_discord(error):
    """Sendet den Verifizierungscode an den Discord-Kanal."""
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        try:
            await channel.send(f"Der Fehler ist: {error}")
            logging.info(f"Error gesendet an Discord-Kanal {DISCORD_CHANNEL_ID}")
        except discord.Forbidden:
            logging.error(f"Bot hat keine Berechtigung, Nachrichten in Kanal {DISCORD_CHANNEL_ID} zu senden.")
        except Exception as e:
            logging.exception(f"Fehler beim senden der Nachricht an Discord: {e}")
    else:
        logging.error(f"Kanal mit ID {DISCORD_CHANNEL_ID} nicht gefunden.")


# --- Bot starten ---
if __name__ == "__main__":
    if not all([DISCORD_BOT_TOKEN, IMAP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD, SUBJECT_FILTER, str(DISCORD_CHANNEL_ID)]):
        logging.error(
            "Fehlende Umgebungsvariablen! Stelle sicher, dass DISCORD_BOT_TOKEN, IMAP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD, SUBJECT_FILTER und DISCORD_CHANNEL_ID in der .env-Datei gesetzt sind.")
    else:
        bot.run(DISCORD_BOT_TOKEN)