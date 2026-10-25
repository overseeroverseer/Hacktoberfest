import json
from pathlib import Path

MENU_PATH = Path(__file__).parent / "menu.json"

# Lowercase ingredient name -> allergens it contains.
# Ingredients not listed here are treated as "none listed", never as safe.
INGREDIENT_ALLERGENS = {
    "peanuts": {"peanut"},
    "peanut sauce": {"peanut"},
    "almonds": {"tree nut"},
    "cashews": {"tree nut"},
    "walnuts": {"tree nut"},
    "pine nuts": {"tree nut"},
    "pecans": {"tree nut"},
    "pistachios": {"tree nut"},
    "hazelnuts": {"tree nut"},
    "pesto": {"tree nut", "milk"},
    "peanut butter": {"peanut"},
    "soy sauce": {"soy", "wheat"},
    "tofu": {"soy"},
    "miso": {"soy"},
    "oyster sauce": {"shellfish", "soy", "wheat"},
    "wheat flour": {"wheat"},
    "wheat bun": {"wheat"},
    "wheat wrapper": {"wheat"},
    "panko": {"wheat"},
    "beer": {"wheat"},
    "bread": {"wheat"},
    "pasta": {"wheat"},
    "egg noodles": {"wheat", "egg"},
    "egg": {"egg"},
    "mayonnaise": {"egg"},
    "milk": {"milk"},
    "cheddar": {"milk"},
    "butter": {"milk"},
    "parmesan": {"milk"},
    "cream": {"milk"},
    "yogurt": {"milk"},
    "shrimp": {"shellfish"},
    "crab": {"shellfish"},
    "fish sauce": {"fish"},
    "cod": {"fish"},
    "salmon": {"fish"},
    "anchovies": {"fish"},
    "sesame oil": {"sesame"},
    "sesame seeds": {"sesame"},
    "tahini": {"sesame"},
}

ALLERGENS = sorted(set().union(*INGREDIENT_ALLERGENS.values()))

STATIONS = ["wok", "grill", "fryer", "salad bar", "steam station", "bakery"]


def load_menu(path=MENU_PATH):
    with open(path) as f:
        return json.load(f)


def save_menu(menu, path=MENU_PATH):
    with open(path, "w") as f:
        json.dump(menu, f, indent=2)


def dish_allergens(dish):
    allergens = set()
    for ingredient in dish["ingredients"]:
        allergens |= INGREDIENT_ALLERGENS.get(ingredient.lower().strip(), set())
    return allergens


def station_allergens(menu):
    """{station: {allergen: [dish names that bring it onto that station]}}"""
    result = {}
    for dish in menu:
        for station in dish["stations"]:
            by_allergen = result.setdefault(station, {})
            for allergen in dish_allergens(dish):
                by_allergen.setdefault(allergen, []).append(dish["name"])
    return result


def check(menu, allergen):
    """Split dishes into contains / cross_contact / none_listed for one allergen.

    cross_contact entries: {"dish": name, "via": [{"station": s, "from": source dish}, ...]}
    """
    stations = station_allergens(menu)
    result = {"contains": [], "cross_contact": [], "none_listed": []}
    for dish in menu:
        if allergen in dish_allergens(dish):
            result["contains"].append(dish["name"])
            continue
        via = [
            {"station": station, "from": source}
            for station in dish["stations"]
            for source in stations.get(station, {}).get(allergen, [])
        ]
        if via:
            result["cross_contact"].append({"dish": dish["name"], "via": via})
        else:
            result["none_listed"].append(dish["name"])
    return result
