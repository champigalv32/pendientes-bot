# Bot de Telegram para Lista de Pendientes

## Qué hace
Mandás un audio a Telegram diciendo "agregar llamar al médico" → el bot lo transcribe → lo agrega a tu Google Sheet → te confirma.

---

## Paso 1 — Crear el bot en Telegram

1. Abrí Telegram y buscá **@BotFather**
2. Mandá `/newbot`
3. Elegí un nombre (ej: "Mis Pendientes")
4. Elegí un username que termine en `bot` (ej: `mis_pendientes_bot`)
5. BotFather te va a dar un **token** que se ve así:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. Guardá ese token, lo vas a necesitar después

---

## Paso 2 — Obtener API Key de Anthropic (Claude)

1. Entrá a [console.anthropic.com](https://console.anthropic.com)
2. Andá a **API Keys** → **Create Key**
3. Copiá la key (empieza con `sk-ant-...`)

---

## Paso 3 — Configurar Google Sheets

1. Entrá a [Google Cloud Console](https://console.cloud.google.com)
2. Creá un proyecto nuevo (ej: "bot-pendientes")
3. Activá la **Google Sheets API**:
   - Buscá "Google Sheets API" → Enable
4. Activá la **Google Drive API**:
   - Buscá "Google Drive API" → Enable
5. Creá credenciales:
   - Andá a **Credentials** → **Create Credentials** → **Service Account**
   - Nombre: `bot-pendientes`
   - Rol: **Editor**
   - Descargá el archivo JSON de credenciales
6. Creá una Google Sheet nueva en tu cuenta
7. Copiá la URL de la Sheet, que tiene esta forma:
   ```
   https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
   ```
   Guardá el **ID** (la parte entre `/d/` y `/edit`)
8. Abrí la Sheet y compartila con el email del Service Account
   (está dentro del JSON, campo `client_email`, termina en `@...gserviceaccount.com`)
   → Compartir como **Editor**

---

## Paso 4 — Deploy en Railway

1. Creá cuenta en [railway.app](https://railway.app) (podés entrar con GitHub)
2. Creá un repo en GitHub con los archivos del bot (te los paso en el siguiente paso)
3. En Railway: **New Project** → **Deploy from GitHub repo** → elegí el repo
4. En **Variables** del proyecto, agregá:
   ```
   TELEGRAM_TOKEN=tu_token_de_botfather
   ANTHROPIC_API_KEY=tu_sk-ant-...
   GOOGLE_SHEET_ID=el_id_de_tu_sheet
   GOOGLE_CREDENTIALS={"type":"service_account",...}  ← el contenido del JSON en una sola línea
   ```
5. Railway va a deployar automáticamente y el bot va a quedar corriendo 24/7

---

## Cómo usar el bot

Una vez que está corriendo, simplemente mandás un audio a tu bot en Telegram diciendo cosas como:
- *"Agregar comprar leche"*
- *"Añadir llamar al banco mañana"*
- *"Pendiente: enviar el informe"*

El bot responde confirmando qué agregó, y lo podés ver en tu Google Sheet al instante.
