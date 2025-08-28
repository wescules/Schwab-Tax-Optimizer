# Schwab Tax Optimizer

**Schwab Tax Optimizer** is a Python tool that helps you analyze and optimize your investment-related tax outcomes using exported CSV data from your Charles Schwab brokerage account. It calculates short-term and long-term capital gains, ordinary income, disallowed losses, and provides actionable insights to help you minimize your tax burden.

---

## What It Does

* Analyzes your **realized capital gains/losses**
* Distinguishes between **short-term** and **long-term** gains
* Categorizes **ordinary income** (e.g. dividends, interest)
* Identifies **disallowed wash sale losses**
* Provides **insights and strategies** to optimize your tax position
* Supports **scenario simulations** for tax planning

---

## Exporting Data from Schwab

You need **two CSV files** from Schwab:

1. **Realized Gains Page**

   * Navigate to: `Accounts > Realized Gain/Loss`
   * Select your desired time range (e.g., year-to-date or custom)
   * Click **Export** and download the **CSV**

2. **Transaction History Page**

   * Navigate to: `Accounts > History`
   * Select a time range that **covers all relevant transactions**
   * Click **Export** and download the **CSV**

---

## How to Use

Once you’ve exported your data:

1. Save both CSVs in the project directory.
2. Rename them to:

   * `realized_gains.csv`
   * `transaction_history.csv`
3. Run the tax optimizer:

```bash
python realized_gains.py --months 6
```

---

## 📈 Sample Output

```
---------Tax Stats---------
Short-Term Gain: $-1,649.98
Long-Term Gain: $-9,499.86
Ordinary Income: $222.34
Disallowed Losses: $257.82
Fees: $26.18


Total Gains: $13,135.62
Total Losses: $-24,285.46
Net Gain: $-11,149.84
Total Losses: $-24,285.46
Net Gain: $-11,149.84
Gain/Loss Ratio: 0.54
Number of Gain Transactions: 40
Number of Loss Transactions: 13
--------------------------------
Proceeds: $1,493,597.33 (0.495%)
Cost Basis: $1,486,238.09


---------Tax Insights---------
• You can deduct $3,000 of your net capital loss against ordinary income this year.
• Carry forward the remaining $8,149.84 in future years.
• You had $257.82 in disallowed losses due to wash sales. Avoid buying the same security within 30 days of a sale to prevent this.
• You have $11,149.84 in unrealized loss buffer. Consider realizing gains to offset them with no tax impact.

---------Optimal Tax Scenario---------
You can liquidate $1,400.00 of short term gains
You can liquidate $54,100.00 of long term gains
Total Tax: $0.00
LTCG Tax: $0.00
Ordinary Income Tax: $0.00
```

---

## Optimization Tips Provided

The script gives guidance such as:

* When to harvest tax losses or gains
* Whether you’re in a 0%, 15%, or 20% LTCG bracket
* Whether you're overpaying due to wash sale disallowed losses
* Simulation support for minimizing tax with gain/loss rebalancing


## Disclaimer

This tool is for **informational and educational purposes only**. It does not constitute financial, tax, or investment advice. Please consult a tax professional before making any decisions.
