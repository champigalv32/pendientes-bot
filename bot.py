import os
import json
import base64
import logging
import tempfile
from datetime import datetime
import base64 as b64lib

import anthropic
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from google.oauth2.service_account import Credentials

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config desde variables de entorno ────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDENTIALS = json.loads(b64lib.b64decode(os.environ["GOOGLE_CREDENTIALS"]).decode())

# ── Clientes ──────────────────────────────────────────────────────────────────
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1


def setup_sheet():
    """Crea encabezados si la hoja está vacía."""
    if not sheet.row_values(1):
        sheet.append_row(["#", "Pendiente", "Fecha", "Estado"])
        sheet.format("A1:D1", {"textFormat": {"bold": True}})


def add_pending(item: str) -> int:
    """Agrega un ítem a la hoja y retorna el número."""
    all_rows = sheet.get_all_values()
    next_num = len(all_rows)  # fila 1 = encabezado, así que len = próximo número
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    sheet.append_row([next_num, item, date_str, "Pendiente"])
    return next_num


def process_audio(file_path: str) -> str | None:
    """
    Manda el audio a Claude para que transcriba Y extraiga el ítem en un solo paso.
    Retorna el ítem limpio, o None si no detecta intención de agregar algo.
    """
    with open(file_path, "rb") as f:
        audio_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "audio/ogg",
                            "data": audio_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribí este audio en español. "
                            "Luego extraé SOLO el ítem que el usuario quiere agregar a su lista de pendientes, "
                            "sin palabras como 'agregar', 'añadir', 'pendiente', etc. "
                            "Si el mensaje no tiene intención de agregar algo a una lista, respondé exactamente: NO_ITEM. "
                            "Respondé SOLO con el ítem o NO_ITEM, sin explicaciones ni texto extra."
                        ),
                    },
                ],
            }
        ],
    )

    result = response.content[0].text.strip()
    logger.info(f"Claude respondió: {result}")
    return None if result == "NO_ITEM" else result


def extract_item_from_text(text: str) -> str | None:
    """Extrae el ítem pendiente de un mensaje de texto."""
    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extraé SOLO el ítem que el usuario quiere agregar a su lista de pendientes "
                    f"del siguiente texto, sin palabras como 'agregar', 'añadir', etc. "
                    f"Si no hay intención de agregar algo, respondé exactamente: NO_ITEM. "
                    f"Respondé SOLO con el ítem o NO_ITEM.\n\nTexto: {text}"
                ),
            }
        ],
    )
    result = response.content[0].text.strip()
    return None if result == "NO_ITEM" else result


# ── Handlers ──────────────────────────────────────────────────────────────────
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de voz."""
    message = update.message
    await message.reply_text("🎙️ Procesando audio...")

    voice = message.voice or message.audio
    tg_file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = tmp.name

    await tg_file.download_to_drive(tmp_path)

    try:
        item = process_audio(tmp_path)

        if item is None:
            await message.reply_text(
                '🤔 No entendí qué querés agregar. Intentá decir algo como: *"agregar llamar al médico"*',
                parse_mode="Markdown",
            )
            return

        row_num = add_pending(item)
        await message.reply_text(
            f"✅ Agregado #{row_num}: *{item}*",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply_text("❌ Ocurrió un error. Intentá de nuevo.")

    finally:
        os.unlink(tmp_path)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de texto."""
    text = update.message.text
    item = extract_item_from_text(text)

    if item is None:
        await update.message.reply_text(
            "Mandame un audio o escribí qué querés agregar.\nEjemplo: *agregar comprar pan*",
            parse_mode="Markdown",
        )
        return

    row_num = add_pending(item)
    await update.message.reply_text(
        f"✅ Agregado #{row_num}: *{item}*",
        parse_mode="Markdown",
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    setup_sheet()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot iniciado")
    app.run_polling()


if __name__ == "__main__":
    main()
