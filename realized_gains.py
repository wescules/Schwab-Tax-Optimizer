import pandas as pd
import re
import numpy as np
import argparse

# Load your CSV
df = pd.read_csv("realized_gains.csv")
df_futures = pd.read_csv('schwab_transactions.csv')
parser = argparse.ArgumentParser(description="Schwab Tax Optimizer")
parser.add_argument(
    "-m", "--months",
    type=int,
    default=None,
    help="Filter transactions by number of months (ex: 6)",
    required=True
)
args = parser.parse_args()

# Clean numeric columns (remove $ and % signs, commas, etc.)
def clean_currency(x):
    if pd.isnull(x):
        return 0.0
    return float(str(x).replace('$', '').replace(',', '').replace('%', '').strip())
# Function to extract the first date from the string


def extract_date(date_str):
    match = re.search(r'\d{2}/\d{2}/\d{4}', str(date_str))
    if match:
        return pd.to_datetime(match.group(), format='%m/%d/%Y')
    return pd.NaT  # Not a Time (missing datetime)


def calculate_tax(income, brackets):
    tax = 0.0
    for lower, upper, rate in brackets:
        if income > lower:
            taxable = min(income, upper) - lower
            tax += taxable * rate
        else:
            break
    return tax


def capital_gains_tax_calculator(ordinary_income, short_term_gains, long_term_gains, filing_status="single"):
    # 2024 Federal Income Tax Brackets
    income_brackets = {
        "single": [
            (0, 11000, 0.10),
            (11000, 44725, 0.12),
            (44725, 95375, 0.22),
            (95375, 182100, 0.24),
            (182100, 231250, 0.32),
            (231250, 578125, 0.35),
            (578125, float('inf'), 0.37)
        ],
    }

    # 2024 LTCG Brackets
    ltcg_brackets = {
        "single": [
            (0, 44625, 0.0),
            (44625, 492300, 0.15),
            (492300, float('inf'), 0.20)
        ],
    }

    filing_income_brackets = income_brackets[filing_status]
    filing_ltcg_brackets = ltcg_brackets[filing_status]

    # Step 1: Calculate ordinary income tax (including short-term gains)
    total_ordinary_income = ordinary_income + short_term_gains
    income_tax = calculate_tax(total_ordinary_income, filing_income_brackets)

    # Step 2: Calculate LTCG tax (stacked on top of ordinary income)
    remaining_ltcg = long_term_gains
    ltcg_tax = 0.0

    for lower, upper, rate in filing_ltcg_brackets:
        # Adjust bracket range to start above ordinary income
        start = max(lower, total_ordinary_income)
        if upper <= total_ordinary_income:
            continue  # This bracket is already filled by ordinary income

        bracket_range = upper - start
        taxable_amount = min(bracket_range, remaining_ltcg)

        if taxable_amount > 0:
            ltcg_tax += taxable_amount * rate
            remaining_ltcg -= taxable_amount

        if remaining_ltcg <= 0:
            break

    total_tax = income_tax + ltcg_tax

    return {
        "Ordinary Income Tax": income_tax,
        "LTCG Tax": ltcg_tax,
        "Total Tax": total_tax
    }


def generate_tax_insights(metrics):
    insights = []

    # Unpack values
    short_term_gain = metrics["Short-Term Gain"]
    long_term_gain = metrics["Long-Term Gain"]
    total_gains = metrics["Total Gains"]
    total_losses = metrics["Total Losses"]
    net_gain = metrics["Net Gain"]
    disallowed_losses = metrics["Disallowed Losses"]
    ordinary_income = metrics["Ordinary Income"]
    gain_count = metrics["Gain Count"]
    loss_count = metrics["Loss Count"]

    # Capital loss deduction opportunity
    if net_gain < 0:
        if abs(net_gain) >= 3000:
            insights.append(
                "You can deduct $3,000 of your net capital loss against ordinary income this year.")
            insights.append(
                f"Carry forward the remaining ${abs(net_gain) - 3000:,.2f} in future years.")
        else:
            insights.append(
                f"You can deduct the full ${abs(net_gain):,.2f} net capital loss against your income.")

    # Wash sale awareness
    if disallowed_losses > 0:
        insights.append(
            f"You had ${disallowed_losses:,.2f} in disallowed losses due to wash sales. Avoid buying the same security within 30 days of a sale to prevent this.")

    # Gain realization strategy
    if net_gain < 0:
        insights.append(
            f"You have ${abs(net_gain):,.2f} in unrealized loss buffer. Consider realizing gains to offset them with no tax impact.")
    elif net_gain > 0:
        insights.append(
            f"You have net gains of ${net_gain:,.2f}. Consider harvesting losses to reduce your tax liability.")

    # Short-term vs long-term bias
    if short_term_gain > 0 and long_term_gain < 0:
        insights.append(
            "You're realizing more short-term gains, which are taxed at a higher rate. Try holding positions longer for favorable long-term rates.")

    # Income threshold
    if ordinary_income > 2000:
        insights.append(
            f"You’ve earned ${ordinary_income:,.2f} in interest/dividends. Consider tax-efficient ETFs or municipal bonds to reduce future taxable income.")

    # Gain/Loss ratio analysis
    gain_loss_ratio = metrics["Gain/Loss Ratio"]
    if gain_loss_ratio < 0.5:
        insights.append(
            "Your portfolio has a high loss ratio. Review your investment strategy for possible improvements.")

    return insights


def optimize_gains_under_tax_limit(short_term_gains, long_term_gains, ordinary_income, st_range, lt_range) -> dict:
    best_score = float('-inf')
    best_result = None
    min_tax = float('inf')

    for st_gain in np.arange(*st_range):
        for lt_gain in np.arange(*lt_range):
            total_tax = capital_gains_tax_calculator(
                short_term_gains=short_term_gains + st_gain,
                long_term_gains=long_term_gains + lt_gain,
                ordinary_income=ordinary_income,
                filing_status="single"
            )

            score = st_gain + lt_gain

            if total_tax['Total Tax'] <= min_tax and score > best_score:
                best_score = score
                min_tax = total_tax['Total Tax']
                best_result = {
                    'Short-Term Gain': st_gain,
                    'Long-Term Gain': lt_gain,
                    'Total Tax': total_tax,
                    'Score': score
                }

    return best_result


numeric_columns = [
    "Gain/Loss ($)",
    "Disallowed Loss",
    "Long Term Gain/Loss",
    "Short Term Gain/Loss",
    "Proceeds",
    'Cost Basis (CB)',
]

futures_numeric_columns = [
    "Price",
    "Fees & Comm",
    "Amount",
]

for col in numeric_columns:
    df[col] = df[col].apply(clean_currency)

for col in futures_numeric_columns:
    df_futures[col] = df_futures[col].apply(clean_currency)

# Calculate date 6 months ago from today
six_months_ago = pd.Timestamp.now() - pd.DateOffset(months=args.months)

# Filter for rows where 'Closed Date' is within the last 6 months
df['Closed Date'] = pd.to_datetime(
    df['Closed Date'], format="%m/%d/%Y", errors='coerce')
df_futures['Closed Date'] = df_futures['Date'].apply(extract_date)
df = df[df['Closed Date'] >= six_months_ago]
df_futures = df_futures[df_futures['Closed Date'] >= six_months_ago]


# Short-term and long-term gains
# Futures tax implications are 60/40 long/short
futures_net_gain = df_futures[df_futures['Action']
                              == 'Futures MM Sweep']["Amount"].sum()
short_term_gain = df["Short Term Gain/Loss"].sum() + futures_net_gain * 0.40
long_term_gain = df["Long Term Gain/Loss"].sum() + futures_net_gain * 0.60
fees = df_futures['Fees & Comm'].sum()
# Regular income
ordinary_income = df_futures[df_futures['Action'].isin(['Interest Adj', 'Cash Dividend',
                                                        'Qual Div Reinvest', 'Reinvest Dividend',
                                                        'Reinvest Shares', 'Pr Yr Special Div',
                                                        'Bond Interest', 'Promotional Award',
                                                        'Credit Interest', 'Interest Adj', 'Misc Credits'])]['Amount'].sum()

# Disallowed losses
disallowed_loss = df["Disallowed Loss"].sum()

# Total gains and losses separately
gains = df[df["Gain/Loss ($)"] > 0]["Gain/Loss ($)"].sum() + (df_futures[(df_futures['Action'].isin(
    ["Futures MM Sweep", "Expired"])) & (df_futures['Amount'] > 0)])["Amount"].sum()
losses = df[df["Gain/Loss ($)"] < 0]["Gain/Loss ($)"].sum() + (df_futures[(df_futures['Action'].isin(
    ["Futures MM Sweep", "Expired"])) & (df_futures['Amount'] < 0)])["Amount"].sum()
total_gain = gains + losses

# Gain/loss ratio
gain_loss_ratio = gains / abs(losses) if losses != 0 else float('inf')

# Gain and loss transaction counts
gain_count = (df["Gain/Loss ($)"] > 0).sum() + (df_futures[df_futures['Action'] == "Futures MM Sweep"]
                                                ['Amount'] > 0).sum() + (df_futures[df_futures['Action'] == "Expired"]['Amount'] > 0).sum()
loss_count = (df["Gain/Loss ($)"] < 0).sum() + (df_futures[df_futures['Action'] == "Futures MM Sweep"]
                                                ['Amount'] < 0).sum() + (df_futures[df_futures['Action'] == "Expired"]['Amount'] < 0).sum()

# Invested Capital: cost basis for long, proceeds for short
proceeds = df['Proceeds'].sum()
cost_basis = df['Cost Basis (CB)'].sum()
pct_change = ((proceeds - cost_basis) / cost_basis) * 100


metrics = {
    "Short-Term Gain": short_term_gain,
    "Long-Term Gain": long_term_gain,
    "Ordinary Income": ordinary_income,
    "Disallowed Losses": disallowed_loss,
    "Total Gains": gains,
    "Total Losses": losses,
    "Net Gain": total_gain,
    "Gain Count": gain_count,
    "Loss Count": loss_count,
    "Gain/Loss Ratio": gain_loss_ratio,
    "Fees": fees,
}

# Output results
print('---------Tax Stats---------')
print(f"Short-Term Gain: ${short_term_gain:,.2f}")
print(f"Long-Term Gain: ${long_term_gain:,.2f}")
print(f"Ordinary Income: ${ordinary_income:,.2f}")
print(f"Disallowed Losses: ${disallowed_loss:,.2f}")
print(f"Fees: ${fees:,.2f}\n")

print(f"Total Gains: ${gains:,.2f}")
print(f"Total Losses: ${losses:,.2f}")
print(f"Net Gain: ${total_gain:,.2f}")
print(f"Gain/Loss Ratio: {gain_loss_ratio:.2f}")
print(f"Number of Gain Transactions: {gain_count}")
print(f"Number of Loss Transactions: {loss_count}")

print("--------------------------------")
print(f"Proceeds: ${proceeds:,.2f} ({pct_change:.3f}%)")
print(f"Cost Basis: ${cost_basis:,.2f}")

insights = generate_tax_insights(metrics)
print('\n\n---------Tax Insights---------')
for tip in insights:
    print("•", tip)

result = optimize_gains_under_tax_limit(
    ordinary_income=metrics["Ordinary Income"],
    short_term_gains=metrics["Short-Term Gain"],
    long_term_gains=metrics['Long-Term Gain'],
    st_range=(0, 50000, 50),
    lt_range=(0, 100000, 50),
)
print("\n---------Optimal Tax Scenario---------")

print(f"You can liquidate ${result['Short-Term Gain']:,.2f} of short term gains")
print(f"You can liquidate ${result['Long-Term Gain']:,.2f} of long term gains")
print(f"Total Tax: ${result['Total Tax']['Total Tax']:,.2f}")
print(f"LTCG Tax: ${result['Total Tax']['LTCG Tax']:,.2f}")
print(f"Ordinary Income Tax: ${result['Total Tax']['Ordinary Income Tax']:,.2f}")
