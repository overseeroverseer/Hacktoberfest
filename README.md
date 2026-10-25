# Purdue's 2026 Hacktoberfest

## SafeBytes

Dining out should not be an interrogation. SafeBytes provides a solution: Real-time allergen awareness and cross-contamination alerts for peace of mind at the table.

## Our Story
Dining out with friends should be about conversation and good food. However, for our friend group, it typically starts with the same questions:
*"Does anything in our order contain peanuts? Does the fryer use this type of oil?"*

Watching our friend navigate severe allergies showed us that dining out is loaded with anxiety. Waitstaff can be uninformed, menus lack allergen warnings, and hidden cross-contamination risks turn what should be a positive experience into one filled with paranoia.

This inspired us to build **SafeBytes** to eliminate the questions. By bridging transparent restaurant menu data with proactive consumer warnings, we ensure nobody at the table has to wonder if their next bite is safe.

### What It Does
---

#### 1. For Restaurants (Data Ingestion & Tagging)
- **Menu Management Portal:** Kitchens input dishes as well as their potential allergens.
- **Allergen Flagging:** Uses structured dietary datasets (e.g., FDA Top 9 allergens, USDA food databases) to cross-reference common allergens.

#### 2. For Diners (Proactive Alerts)
- **Pre-Order Warning System:** Scans the selected meal, flagging common allergens before they place an order.



## Installation and Local Setup

Follow these steps to set up and run SafeBytes locally on your machine.

#### Prerequisites
Make sure you have Python 3.8 or higher installed on your system. You can check your version by running:
```bash
python3 --version  # On macOS/Linux
python --version   # On Windows
```

---

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/safebytes.git
cd safebytes
```

---

### 2. Set Up a Virtual Environment (Recommended)
An isolated virtual environment ensures that the application dependencies do not conflict with your global Python system packages.

#### On macOS and Linux / WSL:
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```
*(Once activated, you will see (venv) appear at the beginning of your terminal prompt).*

#### On Windows:
Open your terminal (PowerShell or Command Prompt) and run:

**Using PowerShell:**
```powershell
# Create the virtual environment
python -m venv venv

# Activate the environment
.\venv\Scripts\Activate.ps1
```

**Using Command Prompt (cmd):**
```cmd
# Create the virtual environment
python -m venv venv

# Activate the environment
venv\Scripts\activate
```

---

### 3. Install Dependencies
With your virtual environment activated, install the required packages using pip:
```bash
pip install pandas streamlit
```

---

### 4. Run the Application
Start the SafeBytes Streamlit application:
```bash
streamlit run app.py
```

Once launched, the application will automatically boot up and open a new tab in your default web browser (usually at http://localhost:8501).


## Core Libraries and Frameworks Used

- **Streamlit (v1.x)**: Powering our responsive, highly interactive web application. It handles our custom multipage navigation (Customer vs. Restaurant Owner), active form states, and chat UI rendering.
- **Pandas (v2.x)**: Managing back-of-house database displays, parsing structural datasets, and visualizing menu matrices efficiently.

---

### Code Environment Verification

If you are a developer looking to confirm the baseline package structure, verify that your local environment contains the two primary files in the root folder:
- **menu.py**: Handles the core backend processing, ingredient-to-allergen mapping, station-contamination matrices, and dataset search logic.
- **app.py**: Handles the Streamlit user interface, database updates, interactive components, and customer chat interface.

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
* **SafeBytes AI Chat Assistant:** An integrated, conversational assistant allows customers to ask plain-language questions about prep methods, cooking oils, and potential kitchen cross-contamination risks before ordering.

---

### 2. Restaurant Owner View (Kitchen Management Dashboard)

A lightweight back-of-house portal that gives chefs and managers control over ingredient tracking and preparation surfaces.

* **Menu Item Onboarding Form:** Kitchen operators can add new dishes by defining:
  * Dish Name.
  * Ingredients: Multi-select tagging from a normalized food database.
  * Kitchen Stations: Physical equipment and preparation areas used (e.g., wok, grill, fryer, salad bar).
* **Automated Allergen Tagging:** Ingredients entered into the system are automatically matched against our standardized allergen taxonomy, removing manual data entry overhead for staff.
* **Live Menu Database Records:** A clean, searchable data table displaying all current menu items, assigned ingredients, physical kitchen stations, and automatically computed allergen flags.
* **Physical Station Cross-Contamination Map:** A dedicated back-of-house visualization tool that breaks down each physical workstation in the kitchen:
  * Lists every dish prepared at that specific station.
  * Identifies any active allergen hazards introduced to shared equipment.
  * Visually marks stations as clean or contaminated, helping kitchen staff prevent cross-contact during rush hours.
