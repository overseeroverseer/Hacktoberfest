# Purdue's 2026 Hacktoberfest

## SafeBytes

Dining out should not be an interrogation. SafeBytes provides a solution: Real-time allergen awareness and cross-contamination alerts for peace of mind at the table.

## Our Story
Dining out with friends should be about conversation and good food. However, for our friend group, it typically starts with the same questions:
*"Does anything in our order contain peanuts? Does the fryer use this type of oil?"*

Watching our friend navigate severe allergies showed us that dining out is loaded with anxiety. Waitstaff can be uninformed, menus lack allergen warnings, and hidden cross-contamination risks turn what should be a positive experience into one filled with paranoia.

This inspired us to build **SafeBytes** to eliminate the questions. By bridging transparent restaurant menu data with proactive consumer warnings, we ensure nobody at the table has to wonder what is in their next bite.

### What It Does
---

#### 1. For Restaurants (Data Ingestion & Tagging)
- **AI Menu Import:** Paste the menu text or upload a photo of it. The AI proposes ingredients and kitchen stations for every dish ("tempura" → fryer, "stir-fried" → wok), and the owner reviews and approves before anything is saved.
- **"Did You Forget Something?" Audit:** The AI compares each dish with what it usually contains and flags allergens the owner didn't list ("Pad Thai is usually topped with peanuts. Add it?").
- **Automatic Allergen Tagging:** Ingredients are mapped to the FDA Top 9 allergens, and dishes that share a station are tracked for cross-contact.

#### 2. For Diners (Proactive Alerts)
- **Allergen Filter:** Pick an allergen and every dish is sorted into *contains*, *shared station*, or *none listed*.
- **AI Chat Assistant:** Ask in your own words, in any language ("is the fried rice ok for my nut allergy?"), and get an answer about just the dishes you asked about.

## How the AI Stays Honest

Allergy answers can't be guessed, so the AI never decides whether a dish contains an allergen. Plain code does.

1. **AI understands the question:** which allergens, which dishes, which language. Anything not on the allowed lists is dropped.
2. **Code decides:** `check()` looks up every ingredient and every shared station in the menu data. No AI is involved.
3. **AI words the answer** from those facts only, following the rules in `skills/allergen-safety/SKILL.md`.
4. **A safety guard checks the wording.** If the reply says "safe", "nut-free", or "free of", or skips a dish the customer asked about, it is thrown away and a plain, correct answer is shown instead. Every answer ends with *"Please confirm with staff."*

On the owner side the AI only *suggests*. Nothing is saved until the owner approves it, stations must come from the known list, and an audit that fails says so instead of showing "nothing missing".

## Installation and Local Setup

Follow these steps to set up and run SafeBytes locally on your machine.

#### Prerequisites
- Python 3.9 or higher (`python3 --version`)
- [Ollama](https://ollama.com) to run the AI model locally, **or** a Snowflake account with Cortex access

---

### 1. Clone the Repository
```bash
git clone https://github.com/overseeroverseer/Hacktoberfest.git
cd Hacktoberfest
```

---

### 2. Set Up a Virtual Environment (Recommended)
An isolated virtual environment ensures that the application dependencies do not conflict with your global Python system packages.

#### On macOS and Linux / WSL:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(If this fails with "ensurepip is not available", install `python3-venv`, or use [uv](https://docs.astral.sh/uv/): `uv venv .venv`.)*

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 4. Set Up the AI Model

**Option A: Local (Ollama, works offline)**
```bash
ollama pull gemma4:e2b
```

**Option B: Cloud (Snowflake Cortex)**: use your account host and a programmatic access token.

Then create a `.env` file in the project folder (it is git-ignored, so your token never gets committed):
```
BACKEND=ollama              # or snowflake
OLLAMA_MODEL=gemma4:e2b
SF_HOST=youraccount.snowflakecomputing.com
SF_PAT=your_token_here
SF_MODEL=claude-sonnet-4-5  # any Cortex model your account offers
```
If the chosen backend fails (Wi-Fi drops, Ollama not running), SafeBytes automatically tries the other one. Check the setup with:
```bash
python llm.py   # should print a short greeting
```

---

### 5. Run the Application
```bash
streamlit run app.py
```

The app opens in your browser at http://localhost:8501. The allergen filter and station map work even without an AI model; only the chat, menu import, and audit need one.

> If you add a new function or constant to `menu.py` while the app is running, restart Streamlit (Ctrl+C, then run it again). Auto-reload can keep the old version of the module.

## Project Files

| File | What it does |
|---|---|
| `app.py` | Streamlit app: Customer and Restaurant Owner tabs |
| `menu.py` | Ingredient → allergen dictionary, `load_menu` / `save_menu`, `check()` for contains / cross-contact / none listed |
| `menu.json` | The menu: each dish has a `name`, `ingredients`, and `stations` |
| `assistant.py` | Customer chat: AI reads the question, `check()` decides, AI words the answer, guard verifies it |
| `owner_ai.py` | Owner AI: menu import from text or photo, and the missing-allergen audit |
| `llm.py` | One `chat()` function for Ollama or Snowflake Cortex, with automatic fallback |
| `skills/allergen-safety/SKILL.md` | Rules the AI must follow when answering customers |

## Core Libraries and Frameworks Used

- **Streamlit**: The web app, tabs, forms, and chat UI.
- **Pandas**: Menu tables on the owner page.
- **Requests**: Talking to Ollama and Snowflake Cortex.
- **Gemma (via Ollama)** / **Snowflake Cortex**: The AI model behind the chat, menu import, and audit.

## Features and User Capabilities

SafeBytes bridges back-of-house kitchen workflows with front-of-house consumer ordering to make allergen transparency actionable and accessible.

---

### 1. Customer View (Diner Portal)

Designed for diners with dietary restrictions or food allergies, this interface eliminates the anxiety and guesswork of dining out.

* **Dynamic Allergen Filtering:** Patrons can select their specific allergy or dietary restriction (e.g., peanuts, shellfish, gluten) from an automated selection menu populated directly from backend records.
* **Three-Tier Safety Classification:**
  * **Safe Choices (Green):** Displays dishes with no listed allergen ingredients and zero shared equipment exposure.
  * **Caution: Shared Station (Yellow):** Identifies dishes that are recipe-safe but carry cross-contact risks due to shared cooking surfaces (e.g., fries cooked in the same oil as breaded calamari). The card explicitly states the exact station and the dish responsible for introducing the allergen hazard.
  * **Contains Allergen (Red):** Clearly flags dishes containing active ingredients linked to the chosen allergen, preventing accidental consumption.
* **Staff Confirmation Prompts:** Every categorized item includes explicit safety reminders prompting diners to confirm preparation protocols with serving staff before placing an order.
* **SafeBytes AI Chat Assistant:** An integrated, conversational assistant allows customers to ask plain-language questions about prep methods, cooking oils, and potential kitchen cross-contamination risks before ordering. Can also answer questions in different languages.

---

### 2. Restaurant Owner View (Kitchen Management Dashboard)

A lightweight back-of-house portal that gives chefs and managers control over ingredient tracking and preparation surfaces.

* **AI Menu Import:** Paste a menu or upload a photo. The AI proposes every dish with its ingredients (including hidden ones like sauces and batter) and stations. The owner edits, unticks, or approves each one, and any missing allergens the audit finds are shown as pre-ticked additions.
* **Menu Item Onboarding Form:** Add a single dish by name, ingredients, and kitchen stations (wok, grill, fryer, salad bar, steam station, bakery). After saving, the AI checks it for allergens you may have missed.
* **Missing Allergen Check:** Audit the whole menu at once. Each suggestion explains why (e.g., "Fried rice is typically seasoned with soy sauce") with **Add** and **Dismiss** buttons, and added ingredients update the customer page immediately.
* **Live Menu Database Records:** A table of every dish with its ingredients, stations, and automatically detected allergens.
* **Physical Station Cross-Contamination Map:** For each station, the allergens present and the dishes that bring them there, so kitchen staff can prevent cross-contact during rush hours.
