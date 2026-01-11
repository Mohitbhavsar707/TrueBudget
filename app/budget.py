from typing import Dict, List, Tuple


FREQ_TO_MONTHLY = {
    "weekly": 52 / 12,
    "biweekly": 26 / 12,
    "monthly": 1.0,
}

DEFAULT_VARIABLE_WEIGHTS = {
    "Groceries": 0.30,
    "Food Out": 0.15,
    "Social": 0.15,
    "Transport": 0.15,
    "Misc": 0.15,
    "Investing (Extra)": 0.10,
}


def to_monthly(amount: float, frequency: str) -> float:
    if frequency not in FREQ_TO_MONTHLY:
        raise ValueError(f"Unknown frequency: {frequency}")
    return float(amount) * FREQ_TO_MONTHLY[frequency]


def summarize_income(incomes: List[dict]) -> float:
    return sum(to_monthly(i["amount"], i["frequency"]) for i in incomes)


def summarize_fixed_expenses(expenses: List[dict]) -> Tuple[float, Dict[str, float]]:
    """
    Returns:
      total_fixed, category_totals
    """
    category_totals: Dict[str, float] = {}
    total = 0.0
    for e in expenses:
        monthly = to_monthly(e["amount"], e["frequency"])
        total += monthly
        category_totals[e["category"]] = category_totals.get(e["category"], 0.0) + monthly
    return total, category_totals


def compute_savings_target(monthly_income: float, goal_type: str, goal_value: float) -> float:
    if goal_type == "amount":
        return max(0.0, float(goal_value))
    if goal_type == "percent":
        return max(0.0, monthly_income * (float(goal_value) / 100.0))
    raise ValueError("goal_type must be 'amount' or 'percent'")


def allocate_variable_budget(discretionary: float, focus_categories: List[str]) -> Dict[str, float]:
    """
    Allocate discretionary money across variable categories.
    If the user selected focus categories, slightly boost those weights.
    """
    if discretionary <= 0:
        return {k: 0.0 for k in DEFAULT_VARIABLE_WEIGHTS.keys()}

    weights = DEFAULT_VARIABLE_WEIGHTS.copy()

    # boost focus categories a bit
    boost = 0.08  # small boost per focus category
    for c in focus_categories:
        if c in weights:
            weights[c] += boost

    # renormalize
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    return {k: round(discretionary * w, 2) for k, w in weights.items()}


def warnings(monthly_income: float, fixed_total: float, savings_target: float) -> List[str]:
    w = []
    if monthly_income <= 0:
        w.append("No income entered yet. Add at least one income source.")
        return w

    fixed_pct = (fixed_total / monthly_income) * 100.0 if monthly_income else 0.0
    if fixed_pct > 60:
        w.append(f"Fixed expenses are {fixed_pct:.0f}% of income. That’s high; flexibility may be limited.")
    elif fixed_pct > 45:
        w.append(f"Fixed expenses are {fixed_pct:.0f}% of income. Watch discretionary spending carefully.")

    if fixed_total + savings_target > monthly_income:
        gap = (fixed_total + savings_target) - monthly_income
        w.append(f"Your fixed expenses + savings goal exceed income by about ${gap:.2f}/month.")

    return w
