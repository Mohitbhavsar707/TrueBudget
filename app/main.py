import streamlit as st
import pandas as pd
import plotly.express as px

from db import (
    init_db,
    add_income, delete_income, list_income,
    add_expense, delete_expense, list_expenses,
    upsert_profile, get_profile
)
from budget import (
    summarize_income, summarize_fixed_expenses,
    compute_savings_target, allocate_variable_budget, warnings
)
from llm import ollama_available, generate_advice, DEFAULT_MODEL


st.set_page_config(page_title="TrueBudget MVP", layout="wide")


def money(x: float) -> str:
    return f"${x:,.2f}"


init_db()

st.title("TrueBudget (MVP) — Free Tools Only")
st.caption("Streamlit + SQLite + Ollama (local LLM)")

# Sidebar: Profile / Goals
with st.sidebar:
    st.header("Profile & Goals")

    prof = get_profile() or {
        "location": "",
        "savings_goal_type": "amount",
        "savings_goal_value": 300.0,
        "focus_categories": "Groceries, Social",
    }

    location = st.text_input("Location (optional)", value=prof.get("location") or "")

    savings_goal_type = st.selectbox(
        "Savings goal type",
        options=["amount", "percent"],
        index=0 if prof.get("savings_goal_type") == "amount" else 1,
        help="Amount = $ per month. Percent = % of monthly income."
    )

    savings_goal_value = st.number_input(
        "Savings goal value",
        min_value=0.0,
        value=float(prof.get("savings_goal_value") or 0.0),
        step=25.0 if savings_goal_type == "amount" else 1.0,
    )

    focus_categories = st.text_input(
        "Focus categories (comma-separated)",
        value=prof.get("focus_categories") or "",
        help="Example: Groceries, Social, Food Out"
    )

    if st.button("Save profile"):
        upsert_profile(location, savings_goal_type, float(savings_goal_value), focus_categories)
        st.success("Saved!")

    st.divider()
    st.subheader("Local LLM (Ollama)")
    st.write("Status:", "✅ running" if ollama_available() else "❌ not detected")
    model = st.text_input("Model name", value=DEFAULT_MODEL)
    st.caption("If Ollama isn't detected, open the Ollama app and run: `ollama pull llama3.1:8b`")


# Main: Inputs 
tab1, tab2, tab3 = st.tabs(["1) Inputs", "2) Dashboard", "3) Advice"])


with tab1:
    left, right = st.columns(2)

    with left:
        st.subheader("Income sources")

        with st.form("income_form", clear_on_submit=True):
            name = st.text_input("Income name", placeholder="Job, Side gig, Freelance")
            amount = st.number_input("Amount", min_value=0.0, value=0.0, step=50.0)
            frequency = st.selectbox("Frequency", ["weekly", "biweekly", "monthly"])
            submitted = st.form_submit_button("Add income")
            if submitted:
                if not name.strip():
                    st.error("Please enter a name.")
                elif amount <= 0:
                    st.error("Amount must be > 0.")
                else:
                    add_income(name.strip(), float(amount), frequency)
                    st.success("Added!")

        incomes = list_income()
        if incomes:
            df = pd.DataFrame(incomes)[["id", "name", "amount", "frequency", "created_at"]]
            st.dataframe(df, use_container_width=True, hide_index=True)

            delete_id = st.number_input("Delete income by id", min_value=0, value=0, step=1)
            if st.button("Delete income"):
                if delete_id > 0:
                    delete_income(int(delete_id))
                    st.success("Deleted. (Refreshes automatically)")
        else:
            st.info("No income sources yet.")

    with right:
        st.subheader("Fixed expenses (bills, rent, etc.)")

        categories = ["Rent", "Bills", "Insurance", "Debt", "Subscriptions", "Other Fixed"]

        with st.form("expense_form", clear_on_submit=True):
            ename = st.text_input("Expense name", placeholder="Rent, Phone bill, Internet")
            eamount = st.number_input("Amount ", min_value=0.0, value=0.0, step=25.0)
            efreq = st.selectbox("Frequency ", ["weekly", "biweekly", "monthly"])
            ecat = st.selectbox("Category", categories)
            esub = st.form_submit_button("Add expense")
            if esub:
                if not ename.strip():
                    st.error("Please enter a name.")
                elif eamount <= 0:
                    st.error("Amount must be > 0.")
                else:
                    add_expense(ename.strip(), float(eamount), efreq, ecat)
                    st.success("Added!")

        expenses = list_expenses()
        if expenses:
            df2 = pd.DataFrame(expenses)[["id", "name", "amount", "frequency", "category", "created_at"]]
            st.dataframe(df2, use_container_width=True, hide_index=True)

            del_eid = st.number_input("Delete expense by id", min_value=0, value=0, step=1)
            if st.button("Delete expense"):
                if del_eid > 0:
                    delete_expense(int(del_eid))
                    st.success("Deleted. (Refreshes automatically)")
        else:
            st.info("No fixed expenses yet.")


# Dashboard 
with tab2:
    st.subheader("Monthly Dashboard")

    incomes = list_income()
    expenses = list_expenses()
    prof = get_profile()

    monthly_income = summarize_income(incomes)
    fixed_total, fixed_by_cat = summarize_fixed_expenses(expenses)

    goal_type = prof["savings_goal_type"] if prof else "amount"
    goal_value = float(prof["savings_goal_value"]) if prof else 0.0
        # Original computed savings target from profile
    base_savings_target = compute_savings_target(monthly_income, goal_type, goal_value)

    st.markdown("### What-if controls")
    whatif = st.slider(
        "Try a different savings target (temporary)",
        min_value=0,
        max_value=int(max(0, monthly_income)),
        value=int(round(base_savings_target)),
        step=25,
        help="This does not change your saved profile. It just lets you see how the plan changes."
    )

    savings_target = float(whatif)
    discretionary = round(monthly_income - fixed_total - savings_target, 2)

    discretionary = round(discretionary, 2)

    focus_list = []
    if prof and prof.get("focus_categories"):
        focus_list = [x.strip() for x in prof["focus_categories"].split(",") if x.strip()]

    variable_alloc = allocate_variable_budget(max(discretionary, 0.0), focus_list)
    warn = warnings(monthly_income, fixed_total, savings_target)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly Income", money(monthly_income))
    c2.metric("Fixed Expenses", money(fixed_total))
    c3.metric("Savings Target", money(savings_target))
    c4.metric("Discretionary Left", money(discretionary))

    if warn:
        st.warning("\n".join([f"- {w}" for w in warn]))

    st.divider()
    colA, colB = st.columns(2)

    with colA:
        st.write("**Fixed expenses by category (monthly)**")
        if fixed_by_cat:
            st.dataframe(
                pd.DataFrame([{"category": k, "monthly": v} for k, v in fixed_by_cat.items()]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No fixed expenses yet.")

    with colB:
        st.write("**Suggested variable spending targets (monthly)**")
        st.dataframe(
            pd.DataFrame([{"category": k, "target": v} for k, v in variable_alloc.items()]),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.markdown("### Visual breakdown (actually useful)")

    #  Budget health metrics 
    def pct(n, d):
        return 0.0 if d <= 0 else (n / d) * 100.0

    rent_monthly = fixed_by_cat.get("Rent", 0.0)
    rent_pct = pct(rent_monthly, monthly_income)
    fixed_pct = pct(fixed_total, monthly_income)
    savings_pct = pct(savings_target, monthly_income)

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Rent % of income", f"{rent_pct:.0f}%")
    h2.metric("Fixed % of income", f"{fixed_pct:.0f}%")
    h3.metric("Savings % of income", f"{savings_pct:.0f}%")
    h4.metric("Leftover (buffer)", money(discretionary))

    # quick interpretation
    if monthly_income > 0:
        if discretionary < 0:
            st.error("Your plan is not feasible: fixed + savings is higher than income.")
        elif fixed_pct > 60:
            st.warning("Fixed costs are very high. You’ll have limited flexibility month-to-month.")
        elif rent_pct > 40:
            st.warning("Rent is a large share of income. Consider ways to reduce housing pressure if possible.")
        else:
            st.success("Budget looks feasible. Next step: track actual spending vs targets.")

    #  Chart 1: Donut chart for overall split 
    overall_df = pd.DataFrame([
        {"Bucket": "Fixed", "Amount": fixed_total},
        {"Bucket": "Savings", "Amount": savings_target},
        {"Bucket": "Discretionary", "Amount": max(discretionary, 0.0)},
    ])

    fig1 = px.pie(
        overall_df,
        names="Bucket",
        values="Amount",
        hole=0.5,
        title="Where your monthly money goes (Fixed vs Savings vs Discretionary)"
    )
    st.plotly_chart(fig1, use_container_width=True)

    #  Chart 2: Fixed expenses by category (if present) 
    if fixed_by_cat:
        fixed_cat_df = (
            pd.DataFrame([{"Category": k, "Monthly": v} for k, v in fixed_by_cat.items()])
            .sort_values("Monthly", ascending=False)
        )
        fig2 = px.bar(
            fixed_cat_df,
            x="Category",
            y="Monthly",
            title="Fixed expenses by category (monthly)"
        )
        st.plotly_chart(fig2, use_container_width=True)

    #  Chart 3: Variable targets sorted (the “spending plan”) 
    var_df = (
        pd.DataFrame([{"Category": k, "Target": v} for k, v in variable_alloc.items()])
        .sort_values("Target", ascending=False)
    )
    fig3 = px.bar(
        var_df,
        x="Category",
        y="Target",
        title="Suggested variable spending targets (monthly)"
    )
    st.plotly_chart(fig3, use_container_width=True)
        

#  Advice 
with tab3:
    st.subheader("Advice (LLM-powered, local & free)")

    incomes = list_income()
    expenses = list_expenses()
    prof = get_profile() or {}

    monthly_income = summarize_income(incomes)
    fixed_total, fixed_by_cat = summarize_fixed_expenses(expenses)

    goal_type = prof.get("savings_goal_type", "amount")
    goal_value = float(prof.get("savings_goal_value", 0.0))
    savings_target = compute_savings_target(monthly_income, goal_type, goal_value)

    discretionary = round(monthly_income - fixed_total - savings_target, 2)

    focus_list = []
    if prof.get("focus_categories"):
        focus_list = [x.strip() for x in prof["focus_categories"].split(",") if x.strip()]

    variable_alloc = allocate_variable_budget(max(discretionary, 0.0), focus_list)
    warn = warnings(monthly_income, fixed_total, savings_target)

    payload = {
        "location": prof.get("location", ""),
        "monthly_income": monthly_income,
        "fixed_expenses_total": fixed_total,
        "fixed_expenses_by_category": fixed_by_cat,
        "savings_goal_type": goal_type,
        "savings_goal_value": goal_value,
        "savings_target_monthly": savings_target,
        "discretionary_left": discretionary,
        "focus_categories": focus_list,
        "suggested_variable_targets": variable_alloc,
        "warnings": warn,
        "note": "The app computed all numbers. Use these numbers exactly.",
    }

    st.write("Click the button to generate advice from your local LLM (Ollama).")

    if st.button("Generate advice"):
        if not ollama_available():
            st.error("Ollama not detected. Open the Ollama app, then try again.")
            st.code("ollama pull llama3.1:8b\nollama run llama3.1:8b", language="bash")
        else:
            with st.spinner("Thinking..."):
                try:
                    advice = generate_advice(payload, model=model.strip() or DEFAULT_MODEL)
                    cleaned = (
                        advice.replace("\u200b", "")   # zero-width space
                            .replace("\u200c", "")   # zero-width non-joiner
                            .replace("\u200d", "")   # zero-width joiner
                            .replace("\ufeff", "")   # BOM / zero-width no-break space
                    )

                    st.markdown(cleaned)
                except Exception as e:
                    st.error("Failed to generate advice.")
                    st.code(str(e))
                    st.info("Make sure your model name is correct and Ollama is running.")
