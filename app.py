import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Import Person A's backend utilities
import menu as backend
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

tab_customer, tab_owner = st.tabs(["Customer View", "Restaurant Owner View"])

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
with tab_owner:
    st.subheader("Kitchen Station & Item Manager")

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
                options=["wok", "grill", "fryer", "salad bar", "steam station", "bakery"],
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

                    st.success(f"Successfully added '{item_name}' to menu.json!")
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
