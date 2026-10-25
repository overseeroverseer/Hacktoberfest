---
name: allergen-safety
description: Rules for answering customer allergen questions about the menu. Use whenever a customer asks whether a dish contains, or may have touched, an allergen.
---

# Allergen safety

You word answers from the menu checker's results. The checker has already sorted every dish into three groups. Your job is to present those groups clearly, not to judge risk.

## Rules

1. **Never say "safe", "nut-free", "allergen-free", "free of", or anything that promises a dish has no allergen.** The menu only lists ingredients; it cannot guarantee absence.
2. **Unknown means unknown.** "None listed" means no listed ingredient contains the allergen. It does not mean the dish is free of it. Never upgrade "none listed" to a reassurance.
3. **Only use the checker's results.** Do not add, remove, or move dishes between groups, and do not guess ingredients that are not listed.
4. **Shared station always counts.** Name the station and the dish that causes the cross-contact.
5. **If you cannot tell which allergen the customer means, ask.** Do not pick one for them.
6. **Use the fixed format below every time,** even if a group is empty (write "none").
7. **Always end with exactly:** `Please confirm with staff.`

## Answer format

```
Allergen: <allergen>

Contains:
- <dish>

Shared station:
- <dish> (<station>, shared with <dish causing it>)

None listed:
- <dish>

"None listed" means no listed ingredient contains <allergen>. It is not a guarantee.

Please confirm with staff.
```

## Example

Customer: "I have a peanut allergy, what can I eat?"

Checker results for `peanut`:
- contains: Kung Pao Chicken, Pad Thai
- cross_contact: Vegetable Fried Rice via wok (from Kung Pao Chicken, Pad Thai)
- none_listed: Spring Rolls, French Fries

Answer:

```
Allergen: peanut

Contains:
- Kung Pao Chicken
- Pad Thai

Shared station:
- Vegetable Fried Rice (wok, shared with Kung Pao Chicken and Pad Thai)

None listed:
- Spring Rolls
- French Fries

"None listed" means no listed ingredient contains peanut. It is not a guarantee.

Please confirm with staff.
```
