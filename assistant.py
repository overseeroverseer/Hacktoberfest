"""
assistant.py: answers a customer's allergy question.

Flow:
  1. AI reads the question -> which allergens (and what language)
  2. Plain code runs check() for each allergen          (no AI = no hallucination)
  3. AI words the result in the customer's language (English skips this and uses the plain answer)
  4. Safety guard: if the wording drops a dish or says "safe", use the plain version instead

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

def extract_allergens(question):
    """Returns (list_of_allergens, language). Allergens are filtered to the allowed list."""
    system = (
        "You read a restaurant customer's message about food allergies.\n"
        f"Allowed allergen names: {', '.join(ALLERGENS)}.\n"
        "'nuts' without detail means both peanut and tree nut. 'gluten' means wheat. "
        "'dairy' means milk. 'seafood' means fish and shellfish.\n"
        'Reply with ONLY JSON: {"allergens": [...], "language": "<language>"}\n'
        "language is the language the customer's message is written in, e.g. English, Spanish.\n"
        "Use only allowed names. If no allergy is mentioned, use an empty list."
    )
    raw = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": question}],
        temperature=0.0,
    )
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return [], "English"
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return [], "English"
    found = [a for a in data.get("allergens", []) if a in ALLERGENS]
    language = data.get("language") or "English"
    return list(dict.fromkeys(found)), language   # de-duplicate, keep order


# ---------- Step 2: decide (plain code) ----------

def run_checks(menu, allergens):
    """Run check() for every allergen and merge into one result (worst case wins).

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
            for station, dishes in sources.items():
                cross.setdefault(c["dish"], []).append(
                    f"{a}: {station}, shared with {' and '.join(dishes)}"
                )
    cross_only = {n: v for n, v in cross.items() if n not in contains}
    none_listed = [d["name"] for d in menu if d["name"] not in contains and d["name"] not in cross_only]
    return {"contains": contains, "cross_contact": cross_only, "none_listed": none_listed}


def plain_answer(allergens, merged):
    """Deterministic answer in the skill's fixed format. Always correct; used as the fallback."""
    lines = [f"Allergen: {', '.join(allergens)}", "", "Contains:"]
    lines += [f"- {n} ({', '.join(v)})" for n, v in merged["contains"].items()] or ["- none"]
    lines += ["", "Shared station:"]
    lines += [f"- {n} ({'; '.join(v)})" for n, v in merged["cross_contact"].items()] or ["- none"]
    lines += ["", "None listed:"]
    lines += [f"- {n}" for n in merged["none_listed"]] or ["- none"]
    lines += [
        "",
        (f'"None listed" means no listed ingredient contains {", ".join(allergens)}. '
         "It is not a guarantee."),
        "",
        CONFIRM_LINE,
    ]
    return "\n".join(lines)


# ---------- Step 3: word it nicely (AI) + safety guard ----------

def _guard_ok(reply, merged):
    if BANNED_PATTERN.search(reply):
        return False                    # the AI promised something the menu can't
    low = reply.lower()
    must_mention = list(merged["contains"]) + list(merged["cross_contact"]) + merged["none_listed"]
    if any(name.lower() not in low for name in must_mention):
        return False                    # the AI dropped a dish
    return True


def reword(language, base):
    system = (
        "You help a restaurant customer understand allergy information.\n"
        "Use ONLY the facts provided. Do not add or remove dishes, or move them between groups. "
        "Never say a dish is safe or free of an allergen.\n"
        f"Write the reply in {language}. Keep dish names exactly as given, untranslated. "
        f'End with this exact English line: "{CONFIRM_LINE}"\n\n'
        + _load_skill()
    )
    user = (
        f"Rewrite these facts in {language}, keeping the same groups and dish names. "
        f'Translate everything except dish names and the final line "{CONFIRM_LINE}".\n\n'
        "Facts:\n" + base
    )
    return chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.3,
    )


# ---------- Public entry point ----------

def answer(question, menu):
    try:
        allergens, language = extract_allergens(question)
    except Exception:
        return ("Sorry, I couldn't process that. Please tell us your allergy "
                f"(for example 'peanut'). {CONFIRM_LINE}")

    if not allergens:
        return ("Which allergy should I check? For example: "
                f"{', '.join(ALLERGENS)}. {CONFIRM_LINE}")

    merged = run_checks(menu, allergens)
    base = plain_answer(allergens, merged)
    if language.lower() == "english":
        return base                      # already in the skill format; rewording only loses detail

    try:
        reply = reword(language, base).strip()
        reply = re.sub(r"^```\w*\n|\n?```$", "", reply).strip()   # models like to wrap in a code fence
        if _guard_ok(reply, merged):
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
