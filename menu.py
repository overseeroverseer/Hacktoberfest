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
    "soy sauce": {"soy", "wheat"},
    "oyster sauce": {"shellfish", "soy", "wheat"},
    "wheat flour": {"wheat"},
    "wheat bun": {"wheat"},
    "wheat wrapper": {"wheat"},
    "panko": {"wheat"},
    "beer": {"wheat"},
    "egg": {"egg"},
    "milk": {"milk"},
    "cheddar": {"milk"},
    "butter": {"milk"},
    "shrimp": {"shellfish"},
    "fish sauce": {"fish"},
    "cod": {"fish"},
    "salmon": {"fish"},
    "sesame oil": {"sesame"},
    "sesame seeds": {"sesame"},
}

ALLERGENS = sorted(set().union(*INGREDIENT_ALLERGENS.values()))


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
