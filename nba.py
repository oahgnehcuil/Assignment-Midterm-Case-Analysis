# -*- coding: utf-8 -*-
import cloudscraper
import pandas as pd
from io import StringIO
import time
import matplotlib.pyplot as plt

NBA_TEAMS = [
    "atlanta-hawks", "boston-celtics", "brooklyn-nets", "charlotte-hornets",
    "chicago-bulls", "cleveland-cavaliers", "dallas-mavericks", "denver-nuggets",
    "detroit-pistons", "golden-state-warriors", "houston-rockets", "indiana-pacers",
    "la-clippers", "los-angeles-lakers", "memphis-grizzlies", "miami-heat",
    "milwaukee-bucks", "minnesota-timberwolves", "new-orleans-pelicans", "new-york-knicks",
    "oklahoma-city-thunder", "orlando-magic", "philadelphia-76ers", "phoenix-suns",
    "portland-trail-blazers", "sacramento-kings", "san-antonio-spurs", "toronto-raptors",
    "utah-jazz", "washington-wizards"
]

def fetch_team_year_salary(team_slug: str, year: int, scraper) -> pd.DataFrame | None:
    url = f"https://www.spotrac.com/nba/{team_slug}/payroll/_/year/{year}/"
    print(f"Fetching {team_slug} {year}...")
    resp = scraper.get(url, timeout=20)

    if resp.status_code != 200:
        print(f"⚠️  {team_slug} {year} status={resp.status_code}")
        return None

    try:
        tables = pd.read_html(StringIO(resp.text))
    except ValueError:
        print(f"⚠️  {team_slug} {year} has no readable tables")
        return None

    if not tables:
        print(f"⚠️  {team_slug} {year} no tables found")
        return None

    # 找出包含 salary 的表格
    for t in tables:
        lower_cols = [c.lower() for c in t.columns]
        if any("salary" in c for c in lower_cols):
            t["Team"] = team_slug
            t["Year"] = year
            return t

    print(f"⚠️  {team_slug} {year} has tables but none with salary column")
    return None


def clean_salary(df):
    for col in df.columns:
        if "salary" in col.lower():
            df[col] = df[col].astype(str).str.replace(r"[\$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def main():
    years = [2021, 2022, 2023, 2024, 2025]
    scraper = cloudscraper.create_scraper()

    all_data = []
    for team in NBA_TEAMS:
        for year in years:
            try:
                df = fetch_team_year_salary(team, year, scraper)
                if df is not None:
                    df = clean_salary(df)
                    all_data.append(df)
            except Exception as e:
                print(f"❌ {team} {year} error: {e}")
            time.sleep(2.5)

    if not all_data:
        print("❌ No data fetched.")
        return

    final_df = pd.concat(all_data, ignore_index=True)
    salary_cols = [c for c in final_df.columns if "salary" in c.lower()]
    if not salary_cols:
        print("❌ No salary column found in final dataframe.")
        print("Available columns:", final_df.columns.tolist())
        return

    salary_col = salary_cols[0]
    final_df = final_df.dropna(subset=[salary_col])

    summary = final_df.groupby("Year")[salary_col].agg([
        ("Mean", "mean"),
        ("Median", "median"),
        ("Q1", lambda x: x.quantile(0.25)),
        ("Q3", lambda x: x.quantile(0.75))
    ]).reset_index()

    print("\n=== NBA Salary Summary (2021–2025) ===")
    print(summary)

    plt.figure(figsize=(10,6))
    plt.plot(summary["Year"], summary["Mean"], marker="o", label="Mean")
    plt.plot(summary["Year"], summary["Median"], marker="o", label="Median")
    plt.plot(summary["Year"], summary["Q1"], marker="o", label="Q1")
    plt.plot(summary["Year"], summary["Q3"], marker="o", label="Q3")
    plt.title("NBA Player Salary Trend (2021–2025)")
    plt.xlabel("Year")
    plt.ylabel("Salary (USD)")
    plt.legend()
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig("nba_salary_trend.png", dpi=300)
    plt.show()

    final_df.to_csv("nba_all_players_2021_2025.csv", index=False, encoding="utf-8-sig")
    summary.to_csv("nba_salary_summary_2021_2025.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
