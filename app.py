import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Import Person A's backend utilities
import menu as backend
import owner_ai
from assistant import answer

st.set_page_config(page_title="SafeBytes", layout="wide")

# ==========================================
# 0. DATABASE INITIALIZATION (menu.json)
# ==========================================
MENU_FILE = Path(__file__).parent / "menu.json"

# Create a sample menu.json if it doesn't exist yet
if not MENU_FILE.exists():
    sample_menu = [
        {
            "name": "Pad Thai",
            "ingredients": ["rice noodles", "shrimp", "soy sauce", "peanuts", "egg"],
            "stations": ["wok"]
        },
        {
            "name": "Satay Skewers",
            "ingredients": ["chicken", "peanuts", "sesame oil"],
            "stations": ["grill"]
        },
        {
            "name": "Veggie Fried Rice",
            "ingredients": ["rice", "egg", "carrots", "peas"],
            "stations": ["wok"]
        },
        {
            "name": "Spring Rolls",
            "ingredients": ["wheat wrapper", "cabbage", "carrots"],
            "stations": ["fryer"]
        },
        {
            "name": "Garden Salad",
            "ingredients": ["lettuce", "cucumber", "carrots"],
            "stations": ["salad bar"]
        },
        {
            "name": "Fries",
            "ingredients": ["potatoes", "salt"],
            "stations": ["fryer"]
        }
    ]
    backend.save_menu(sample_menu, MENU_FILE)

# Load the menu from the JSON file
try:
    current_menu = backend.load_menu(MENU_FILE)
except Exception as e:
    st.error(f"Error loading menu.json: {e}")
    current_menu = []

# ==========================================
# APP UI TABS
# ==========================================
st.title("SafeBytes")
st.caption("Intelligent allergen detection and cross-contamination tracking")

# on_change="rerun" makes the tabs remember the selected tab, so st.rerun() after an
# owner action (Audit, Add, Save) doesn't jump back to the Customer tab.
tab_customer, tab_owner = st.tabs(["Customer View", "Restaurant Owner View"], key="tab", on_change="rerun")

# ==========================================
# STEP 2 & 3: CUSTOMER PAGE + CHAT
# ==========================================
with tab_customer:
    st.subheader("Order with Confidence")

    # Extract the dynamic list of allergens from backend's dictionary
    allergen_options = backend.ALLERGENS

    # Customer selects one allergen (as per Person A's check(menu, allergen) signature)
    selected_allergen = st.selectbox(
        "Select your allergen/dietary restriction:",
        options=allergen_options,
        index=allergen_options.index("peanut") if "peanut" in allergen_options else 0
    )

    # Run Person A's actual backend logic!
    results = backend.check(current_menu, selected_allergen)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(f"### Safe Choices ({len(results['none_listed'])})")
        for dish_name in results["none_listed"]:
            st.markdown(f"**{dish_name}**")
            st.caption("Always confirm with staff before ordering.")
            st.divider()

    with col2:
        st.warning(f"### Caution: Shared Station ({len(results['cross_contact'])})")
        for entry in results["cross_contact"]:
            dish_name = entry["dish"]
            st.markdown(f"**{dish_name}**")

            # Display why there's a risk
            for risk in entry["via"]:
                st.caption(
                    f"Risk: Shares {risk['station']} station with {risk['from']} "
                    f"(which contains {selected_allergen})."
                )
            st.caption("High cross-contamination risk. Confirm with staff.")
            st.divider()

    with col3:
        st.error(f"### Contains Allergen ({len(results['contains'])})")
        for dish_name in results["contains"]:
            st.markdown(f"**{dish_name}**")
            st.caption(f"Contains active ingredients linked to '{selected_allergen}'.")
            st.divider()

    # --- STEP 3: PLUG IN PERSON A'S CHAT ---
    st.write("---")
    st.subheader("Ask SafeBytes Assistant")
    st.caption("Describe your allergies in your own words, in any language.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! Tell me about any food allergies and I'll check the menu for you."}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("e.g. My friend has a severe nut allergy"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Person A's assistant: AI reads the allergens, check() decides, guard verifies the wording
        with st.chat_message("assistant"):
            with st.spinner("Checking the menu..."):
                bot_reply = answer(prompt, current_menu)
            st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

# ==========================================
# STEP 1: RESTAURANT OWNER PAGE
# ==========================================
def save_dishes(new_dishes):
    """Add dishes to menu.json, replacing any existing dish with the same name."""
    menu_list = backend.load_menu(MENU_FILE)
    for dish in new_dishes:
        menu_list = [d for d in menu_list if d["name"].lower() != dish["name"].lower()]
        menu_list.append(dish)
    backend.save_menu(menu_list, MENU_FILE)


def add_ingredient(dish_name, ingredient):
    menu_list = backend.load_menu(MENU_FILE)
    for d in menu_list:
        if d["name"] == dish_name and ingredient not in d["ingredients"]:
            d["ingredients"].append(ingredient)
    backend.save_menu(menu_list, MENU_FILE)


def run_audit(dishes):
    """Run Person A's audit and store flat suggestions for the audit panel."""
    try:
        results = owner_ai.audit_dishes(dishes)
    except Exception as e:
        st.session_state.audit = None
        st.session_state.audit_error = f"The allergen audit couldn't run: {e}"
        return
    st.session_state.pop("audit_error", None)
    st.session_state.audit = [
        {"dish": d["name"], **s} for d, suggestions in zip(dishes, results) for s in suggestions
    ]


with tab_owner:
    st.subheader("Kitchen Station & Item Manager")

    if "flash" in st.session_state:
        kind, text = st.session_state.pop("flash")
        getattr(st, kind)(text)

    # --- AI MENU IMPORT: paste or photograph the menu, AI proposes tags, owner approves ---
    with st.expander("Import a menu with AI (paste text or upload a photo)", expanded=False):
        with st.form("import_form"):
            menu_text = st.text_area("Menu text", height=160,
                                     placeholder="Shrimp Tempura - lightly battered shrimp  9\nBeef Lo Mein - stir-fried egg noodles  14")
            menu_photo = st.file_uploader("...or a photo of the menu", type=["png", "jpg", "jpeg"])
            propose = st.form_submit_button("Propose dishes")

        if propose:
            if not menu_text.strip() and not menu_photo:
                st.error("Paste some menu text or upload a photo first.")
            else:
                with st.spinner("Reading the menu and checking for missing allergens..."):
                    try:
                        proposals = owner_ai.propose_dishes(
                            menu_text,
                            menu_photo.getvalue() if menu_photo else None,
                            menu_photo.type if menu_photo else "image/png",
                        )
                    except Exception as e:
                        proposals = None
                        st.error(f"Couldn't reach the AI: {e}")
                    if proposals == []:
                        st.warning("The AI didn't find any dishes. Try pasting the text instead.")
                    elif proposals:
                        try:
                            audits = owner_ai.audit_dishes(proposals)
                        except Exception:
                            audits = [[] for _ in proposals]
                            st.warning("The missing-allergen check couldn't run. Review ingredients carefully.")
                        st.session_state.proposals = [
                            {"dish": d, "suggestions": s} for d, s in zip(proposals, audits)
                        ]

        if st.session_state.get("proposals"):
            st.markdown("**Review the proposed dishes.** Nothing is saved until you click Save.")
            with st.form("review_form"):
                for i, p in enumerate(st.session_state.proposals):
                    d = p["dish"]
                    st.markdown(f"---\n**{i + 1}. {d['name']}**")
                    include = st.checkbox("Include", value=True, key=f"inc_{i}")
                    st.text_input("Name", value=d["name"], key=f"name_{i}")
                    st.text_input("Ingredients (comma-separated)", value=", ".join(d["ingredients"]), key=f"ing_{i}")
                    st.multiselect("Stations", options=backend.STATIONS, default=d["stations"], key=f"st_{i}")
                    for j, s in enumerate(p["suggestions"]):
                        st.checkbox(
                            f"⚠️ Add **{s['ingredient']}** ({', '.join(s['allergens'])}): {s['reason']}",
                            value=True, key=f"sug_{i}_{j}",
                        )
                col_save, col_discard = st.columns(2)
                save = col_save.form_submit_button("Save selected to menu", type="primary")
                discard = col_discard.form_submit_button("Discard all")

            if save:
                to_save = []
                for i, p in enumerate(st.session_state.proposals):
                    name = st.session_state[f"name_{i}"].strip()
                    if not st.session_state[f"inc_{i}"] or not name:
                        continue
                    ingredients = [x.strip().lower() for x in st.session_state[f"ing_{i}"].split(",") if x.strip()]
                    for j, s in enumerate(p["suggestions"]):
                        if st.session_state[f"sug_{i}_{j}"] and s["ingredient"] not in ingredients:
                            ingredients.append(s["ingredient"])
                    to_save.append({"name": name, "ingredients": ingredients,
                                    "stations": st.session_state[f"st_{i}"]})
                save_dishes(to_save)
                del st.session_state.proposals
                st.session_state.flash = ("success", f"Saved {len(to_save)} dishes to menu.json.")
                st.rerun()
            if discard:
                del st.session_state.proposals
                st.rerun()

    col_form, col_table = st.columns([1, 1.2])

    with col_form:
        st.markdown("#### Add New Menu Item")
        with st.form("add_item_form", clear_on_submit=True):
            item_name = st.text_input("Dish Name", placeholder="e.g. Chicken Satay")

            # Use raw ingredients so Person A's parser can map allergens automatically
            all_known_ingredients = sorted(list(backend.INGREDIENT_ALLERGENS.keys()))
            item_ingredients = st.multiselect(
                "Select Ingredients (Allergens mapped automatically)",
                options=all_known_ingredients
            )

            # Handle multiple kitchen stations
            item_stations = st.multiselect(
                "Kitchen Stations Used",
                options=backend.STATIONS,
                default=["wok"]
            )

            submitted = st.form_submit_button("Save Item to Database")

            if submitted:
                if item_name and item_ingredients and item_stations:
                    # Construct the dish dictionary
                    new_dish = {
                        "name": item_name,
                        "ingredients": item_ingredients,
                        "stations": item_stations
                    }

                    # Read current list, append, and save to json
                    menu_list = backend.load_menu(MENU_FILE)
                    menu_list.append(new_dish)
                    backend.save_menu(menu_list, MENU_FILE)

                    st.session_state.flash = ("success", f"Successfully added '{item_name}' to menu.json!")
                    # "Did you forget something?" check on the new dish
                    with st.spinner("Checking for allergens you might have missed..."):
                        run_audit([new_dish])
                    if st.session_state.get("audit"):
                        st.session_state.flash = (
                            "warning",
                            f"Added '{item_name}', but the AI thinks it may be missing allergens. "
                            "See Missing Allergen Check below.",
                        )
                    st.rerun()
                else:
                    st.error("Please fill in all fields (Name, Ingredients, and Stations).")

    with col_table:
        st.markdown("#### Database Records (menu.json)")
        if current_menu:
            # Map ingredients and stations into comma-separated strings for clean rendering
            table_rows = []
            for dish in current_menu:
                # Automatically run Person A's dish_allergens to show what got parsed
                detected = list(backend.dish_allergens(dish))
                table_rows.append({
                    "Dish Name": dish["name"],
                    "Ingredients": ", ".join(dish["ingredients"]),
                    "Stations": ", ".join(dish["stations"]),
                    "Detected Allergens": ", ".join(detected) if detected else "None"
                })
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Menu is currently empty.")

    # --- "DID YOU FORGET SOMETHING?" AUDIT ---
    st.write("---")
    st.markdown("#### Missing Allergen Check")
    st.caption("AI compares each dish with what it usually contains and flags allergens you may not have listed.")

    if st.button("Audit whole menu"):
        with st.spinner("Checking every dish..."):
            run_audit(current_menu)
        st.rerun()

    if "audit_error" in st.session_state:
        st.error(st.session_state.audit_error)
    if "audit_note" in st.session_state:
        st.success(st.session_state.pop("audit_note"))

    audit = st.session_state.get("audit")
    if audit:
        for i, s in enumerate(audit):
            col_text, col_add, col_dismiss = st.columns([6, 1, 1])
            col_text.warning(
                f"**{s['dish']}**: {s['reason']} Add **{s['ingredient']}** "
                f"(flags {', '.join(s['allergens'])})?"
            )
            if col_add.button("Add", key=f"audit_add_{i}"):
                add_ingredient(s["dish"], s["ingredient"])
                audit.pop(i)
                st.session_state.audit_note = (
                    f"Added {s['ingredient']} to {s['dish']}. It's now flagged for "
                    f"{', '.join(s['allergens'])} on the customer page."
                )
                st.rerun()
            if col_dismiss.button("Dismiss", key=f"audit_dismiss_{i}"):
                audit.pop(i)
                st.rerun()
    elif audit == []:
        st.info("No missing allergens suggested. The AI can miss things, so keep reviewing recipes with your kitchen.")

    st.write("---")
    st.markdown("#### Active Kitchen Cross-Contamination Map")

    # Runs Person A's station_allergens(menu)
    stations_map = backend.station_allergens(current_menu)

    if stations_map:
        # Create columns dynamically for each station in our database
        station_names = list(stations_map.keys())
        station_cols = st.columns(len(station_names))

        for idx, station in enumerate(station_names):
            with station_cols[idx]:
                st.markdown(f"Station: {station}")

                allergen_risks = stations_map[station]
                if allergen_risks:
                    for allergen, source_dishes in allergen_risks.items():
                        st.caption(f"Allergen hazard ({allergen.upper()}) introduced by:")
                        for dish in source_dishes:
                            st.markdown(f"- {dish}")
                else:
                    st.success("Clean Station (No mapped allergens)")
    else:
        st.caption("No station data mapped.")
