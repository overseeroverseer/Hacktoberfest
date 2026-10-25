"""
assistant.py: answers a customer's allergy question.

Flow:
  1. AI reads the question -> which allergens, which dishes (if any), what language
  2. Plain code runs check() for each allergen          (no AI = no hallucination)
  3. Facts are narrowed to the dishes the customer asked about
  4. AI answers the question from those facts, in the customer's language
  5. Safety guard: if the wording drops an asked-about dish or says "safe", use the plain version instead

Public function:  answer(question, menu) -> str
"""
import json
import pathlib
import re

from llm import chat
from menu import ALLERGENS, check

CONFIRM_LINE = "Please confirm with staff."

# "safe" as a whole word, anything "-free" (nut-free, gluten-free), and "free of".
BANNED_PATTERN = re.compile(r"\bsafe\b|\w-free\b|\bfree of\b", re.IGNORECASE)

SKILL_PATH = pathlib.Path(__file__).parent / "skills" / "allergen-safety" / "SKILL.md"


def _load_skill():
    try:
        text = SKILL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return text.strip()


# ---------- Step 1: understand the question (AI) ----------

def extract_request(question, menu):
    """Returns (allergens, dishes, language). Both lists are filtered to what really exists."""
    names = [d["name"] for d in menu]
    system = (
        "You read a restaurant customer's message about food allergies.\n"
        f"Allowed allergen names: {', '.join(ALLERGENS)}.\n"
        "'nuts' without detail means both peanut and tree nut. 'gluten' means wheat. "
        "'dairy' means milk. 'seafood' means fish and shellfish.\n"
        f"Menu dishes: {', '.join(names)}.\n"
        'Reply with ONLY JSON: {"allergens": [...], "dishes": [...], "language": "<language>"}\n'
        "dishes are the menu dishes the customer asks about by name; empty list if they ask in general.\n"
        "language is the language the customer's message is written in, e.g. English, Spanish.\n"
        "Use only allowed names. If no allergy is mentioned, use an empty list."
    )
    raw = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": question}],
        temperature=0.0,
    )
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    data = {}
    if match:
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    allergens = [a for a in data.get("allergens", []) if a in ALLERGENS]
    by_lower = {n.lower(): n for n in names}
    dishes = [by_lower[d.lower()] for d in data.get("dishes", []) if isinstance(d, str) and d.lower() in by_lower]
    dishes += [n for n in names if n.lower() in question.lower()]   # backup if the AI missed one
    language = data.get("language") or "English"
    return list(dict.fromkeys(allergens)), list(dict.fromkeys(dishes)), language


# ---------- Step 2: decide (plain code) ----------

def run_checks(menu, allergens, dishes=None):
    """Run check() for every allergen and merge into one result (worst case wins).

    Checks run against the whole menu (cross-contact needs every dish on a station),
    then the result is narrowed to `dishes` if given.

    contains:      {dish: [allergens]}
    cross_contact: {dish: ["peanut: wok, shared with Pad Thai", ...]}
    none_listed:   [dish]
    """
    contains, cross = {}, {}
    for a in allergens:
        res = check(menu, a)
        for name in res["contains"]:
            contains.setdefault(name, []).append(a)
        for c in res["cross_contact"]:
            sources = {}
            for v in c["via"]:
                sources.setdefault(v["station"], []).append(v["from"])
            for station, from_dishes in sources.items():
                cross.setdefault(c["dish"], []).append(
                    f"{a}: {station}, shared with {' and '.join(from_dishes)}"
                )
    cross_only = {n: v for n, v in cross.items() if n not in contains}
    none_listed = [d["name"] for d in menu if d["name"] not in contains and d["name"] not in cross_only]
    if dishes:
        contains = {n: v for n, v in contains.items() if n in dishes}
        cross_only = {n: v for n, v in cross_only.items() if n in dishes}
        none_listed = [n for n in none_listed if n in dishes]
    return {"contains": contains, "cross_contact": cross_only, "none_listed": none_listed}


def plain_answer(allergens, merged):
    """Deterministic answer, empty groups left out. Always correct; used as the fallback."""
    names = " or ".join(allergens)
    lines = []
    if merged["contains"]:
        lines += [f"Contains {names}:"]
        lines += [f"- {n} ({', '.join(v)})" for n, v in merged["contains"].items()]
        lines += [""]
    if merged["cross_contact"]:
        lines += [f"No {names} in the ingredients, but cooked on a shared station (cross-contact risk):"]
        lines += [f"- {n} ({'; '.join(v)})" for n, v in merged["cross_contact"].items()]
        lines += [""]
    if merged["none_listed"]:
        lines += [f"No {names} in the listed ingredients or shared stations (not a guarantee):"]
        lines += [f"- {n}" for n in merged["none_listed"]]
        lines += [""]
    lines += [CONFIRM_LINE]
    return "\n".join(lines)


# ---------- Step 3: answer the question (AI) + safety guard ----------

def _guard_ok(reply, dishes):
    if BANNED_PATTERN.search(reply):
        return False                    # the AI promised something the menu can't
    low = reply.lower()
    if any(name.lower() not in low for name in dishes):
        return False                    # the AI skipped a dish the customer asked about
    return True


def reword(question, language, facts):
    system = (
        "You help a restaurant customer understand allergy information.\n"
        "Answer only what the customer asked, briefly and conversationally. "
        "Use ONLY the facts provided. Never move a dish to a different group. "
        "If you suggest a dish with a shared station, say which station and why. "
        "Don't quote the group labels from the facts; say it in plain words instead, e.g. "
        "'X doesn't list peanut in its ingredients, though that's not a guarantee' or "
        "'X is cooked on the same grill as Y, which contains peanut'. "
        "Never say a dish is safe or free of an allergen.\n"
        f"Write the reply in {language}. Keep dish names exactly as given, untranslated. "
        f'End with this exact English line: "{CONFIRM_LINE}"\n\n'
        + _load_skill()
    )
    user = (
        f"Customer asked: {question}\n\n"
        f"Answer in {language}, using these facts:\n{facts}"
    )
    return chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
    )


# ---------- Public entry point ----------

def answer(question, menu):
    try:
        allergens, dishes, language = extract_request(question, menu)
    except Exception:
        return ("Sorry, I couldn't process that. Please tell us your allergy "
                f"(for example 'peanut'). {CONFIRM_LINE}")

    if not allergens:
        return ("Which allergy should I check? For example: "
                f"{', '.join(ALLERGENS)}. {CONFIRM_LINE}")

    merged = run_checks(menu, allergens, dishes)
    base = plain_answer(allergens, merged)

    try:
        reply = reword(question, language, base).strip()
        reply = re.sub(r"^```\w*\n|\n?```$", "", reply).strip()   # models like to wrap in a code fence
        if _guard_ok(reply, dishes):
            if not reply.endswith(CONFIRM_LINE):
                reply += "\n\n" + CONFIRM_LINE
            return reply
    except Exception:
        pass
    return base                          # fallback: always correct, just plainer


if __name__ == "__main__":
    from menu import load_menu
    m = load_menu()
    while True:
        q = input("customer> ").strip()
        if not q:
            break
        print("\n" + answer(q, m) + "\n")
