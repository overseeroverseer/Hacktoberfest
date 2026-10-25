"""
owner_ai.py: AI helpers for the restaurant owner's side.

1. propose_dishes(text, image): menu text or a menu photo -> proposed dishes with
   ingredient and station tags. The owner reviews every proposal before it is saved.
2. audit_dishes(dishes): "did you forget something?" For each dish, ingredients it
   usually contains that would add an allergen the owner hasn't listed.

The AI only suggests. Plain code keeps stations to the known list, keeps audit
suggestions to ingredients in INGREDIENT_ALLERGENS (so adding one really flags the
allergen), and drops suggestions that add no new allergen.
"""
import base64
import json
import re

from llm import chat
from menu import INGREDIENT_ALLERGENS, STATIONS, dish_allergens

STATION_HINTS = (
    "wok: stir-fried, fried rice, lo mein, pad thai, kung pao. "
    "fryer: deep-fried, tempura, battered, breaded, crispy, fries, rings, spring rolls. "
    "grill: grilled, charbroiled, skewers, satay, burgers, steaks. "
    "salad bar: salads, raw cold dishes. "
    "steam station: steamed, dumplings, bao. "
    "bakery: baked goods, bread, cookies, cakes, pastries."
)


def _parse_json(raw):
    """First {...} object in the reply, or {} if there isn't a valid one."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _clean_list(values):
    """Lowercased, stripped, de-duplicated strings, order kept."""
    if not isinstance(values, list):
        return []
    out = [v.lower().strip() for v in values if isinstance(v, str) and v.strip()]
    return list(dict.fromkeys(out))


# ---------- 1. Menu ingestion ----------

def propose_dishes(text="", image=None, image_type="image/png"):
    """Returns [{"name", "ingredients", "stations"}] proposed from menu text and/or a photo.

    image is the raw bytes of a menu photo. Raises if the model can't be reached.
    """
    system = (
        "You read a restaurant menu and list every dish on it.\n"
        "For each dish give its ingredients and the kitchen stations used to cook it.\n"
        "Include the ingredients the menu lists, plus the ones the dish normally contains "
        "even if the menu doesn't say (sauces, batter, oils, garnishes).\n"
        "When an ingredient matches one of these known names, use the known name exactly: "
        f"{', '.join(sorted(INGREDIENT_ALLERGENS))}.\n"
        "Use short lowercase ingredient names, e.g. 'rice', 'chicken', 'scallion'.\n"
        f"Stations must come from this list: {', '.join(STATIONS)}.\n"
        f"Station hints: {STATION_HINTS}\n"
        'Reply with ONLY JSON: {"dishes": [{"name": "...", "ingredients": [...], "stations": [...]}]}'
    )
    prompt = "Here is the menu:\n\n" + text if text.strip() else "The menu is in this photo."
    content = prompt
    if image:
        url = f"data:{image_type};base64,{base64.b64encode(image).decode()}"
        content = [{"type": "text", "text": prompt},
                   {"type": "image_url", "image_url": {"url": url}}]
    raw = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": content}],
        temperature=0.0,
    )
    dishes = []
    for d in _parse_json(raw).get("dishes", []):
        if not isinstance(d, dict) or not isinstance(d.get("name"), str) or not d["name"].strip():
            continue
        dishes.append({
            "name": d["name"].strip(),
            "ingredients": _clean_list(d.get("ingredients")),
            "stations": [s for s in _clean_list(d.get("stations")) if s in STATIONS],
        })
    return dishes


# ---------- 2. "Did you forget something?" audit ----------

AUDIT_BATCH = 4   # small models answer "nothing missing" for everything when given a long list


def audit_dishes(dishes):
    """Returns one list per dish of {"ingredient", "allergens", "reason"} suggestions.

    Raises if the model can't be reached or its reply can't be read, so the caller can
    tell the owner the check didn't run (instead of showing "nothing missing").
    """
    results = []
    for start in range(0, len(dishes), AUDIT_BATCH):
        results += _audit_batch(dishes[start:start + AUDIT_BATCH])
    return results


def _audit_batch(dishes):
    known = "\n".join(f"- {i}: {', '.join(sorted(a))}" for i, a in sorted(INGREDIENT_ALLERGENS.items()))
    listed = "\n".join(
        f'{n}. {d["name"]}: {", ".join(d["ingredients"]) or "(none listed)"}'
        for n, d in enumerate(dishes, 1)
    )
    system = (
        "You check a restaurant's dish tags for missing allergens.\n"
        "For each dish, think about what that dish normally contains. List the known "
        "ingredients below that the dish usually or often contains but the owner didn't list.\n"
        "Only suggest ingredients from this list (ingredient: allergens it contains):\n"
        f"{known}\n"
        "Give a short reason in plain words, e.g. 'Pad Thai is usually topped with peanuts.'\n"
        "If nothing is missing for a dish, give it an empty list.\n"
        'Reply with ONLY JSON: {"dishes": [{"number": 1, "missing": [{"ingredient": "...", "reason": "..."}]}]}'
    )
    raw = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": listed}],
        temperature=0.0,
    )
    data = _parse_json(raw)
    if not isinstance(data.get("dishes"), list):
        raise ValueError("the AI's audit reply couldn't be read")
    by_number = {}
    for entry in data["dishes"]:
        if isinstance(entry, dict) and isinstance(entry.get("number"), int):
            by_number[entry["number"]] = entry.get("missing") or []

    results = []
    for n, dish in enumerate(dishes, 1):
        have = {i.lower().strip() for i in dish["ingredients"]}
        covered = dish_allergens(dish)
        suggestions = []
        for m in by_number.get(n, []):
            if not isinstance(m, dict) or not isinstance(m.get("ingredient"), str):
                continue
            ingredient = m["ingredient"].lower().strip()
            if ingredient in have or ingredient not in INGREDIENT_ALLERGENS:
                continue
            new = INGREDIENT_ALLERGENS[ingredient] - covered
            if not new:
                continue                 # adds no allergen the dish isn't already flagged for
            covered |= new
            reason = m.get("reason") if isinstance(m.get("reason"), str) else ""
            suggestions.append({"ingredient": ingredient, "allergens": sorted(new), "reason": reason.strip()})
        results.append(suggestions)
    return results


if __name__ == "__main__":
    print(audit_dishes([
        {"name": "Pad Thai", "ingredients": ["rice noodles", "shrimp", "egg"], "stations": ["wok"]},
        {"name": "Pesto Pasta", "ingredients": ["pasta", "basil", "olive oil"], "stations": ["steam station"]},
    ]))
