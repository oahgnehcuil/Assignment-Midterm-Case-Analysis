# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

# ===== Load Data =====
nba = pd.read_csv("nba_salary_summary_2021_2025.csv")
mlb = pd.read_csv("mlb_salary_summary_2021_2025.csv")

# Normalize column names
nba.columns = [c.strip().capitalize() for c in nba.columns]
mlb.columns = [c.strip().capitalize() for c in mlb.columns]

# Check structure
print("NBA sample:\n", nba.head(), "\n")
print("MLB sample:\n", mlb.head(), "\n")

# ===== Plot raw trends =====
plt.figure(figsize=(8,5))
plt.plot(nba["Year"], nba["Mean"], "o-", label="NBA Mean")
plt.plot(mlb["Year"], mlb["Mean"], "o-", label="MLB Mean")
plt.title("NBA vs MLB Mean Salary Trend (2021–2025)")
plt.xlabel("Year")
plt.ylabel("Mean Salary (USD)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()

# ===== Regression function =====
def trend_forecast(df, label):
    """Linear regression + future forecast (2026–2028)"""
    X = sm.add_constant(df["Year"])
    y = df["Mean"]
    model = sm.OLS(y, X).fit()
    print(f"\n===== {label} Regression Summary =====")
    print(model.summary())

    # Predict 3 future years
    future_years = pd.Series(range(df["Year"].max()+1, df["Year"].max()+4))
    future_X = sm.add_constant(future_years)
    preds = model.predict(future_X)

    # Plot
    plt.figure(figsize=(7,4))
    plt.plot(df["Year"], y, "o-", label="Observed Mean")
    plt.plot(future_years, preds, "r--", label="Forecast (OLS)")
    plt.title(f"{label} Salary Forecast (2021–2028)")
    plt.xlabel("Year")
    plt.ylabel("Mean Salary (USD)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()

    return pd.DataFrame({"Year": future_years, "Predicted_Mean": preds})

# ===== Fit & plot both =====
nba_forecast = trend_forecast(nba, "NBA")
mlb_forecast = trend_forecast(mlb, "MLB")

# ===== Combine result =====
combined = pd.concat([
    nba_forecast.assign(League="NBA"),
    mlb_forecast.assign(League="MLB")
])
print("\n=== Forecast Summary (2026–2028) ===\n", combined)
