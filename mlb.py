# -*- coding: utf-8 -*-
import cloudscraper
import pandas as pd
from io import StringIO
import time
import matplotlib.pyplot as plt

MLB_TEAMS = [
    "arizona-diamondbacks", "atlanta-braves", "baltimore-orioles", "boston-red-sox",
    "chicago-cubs", "chicago-white-sox", "cincinnati-reds", "cleveland-guardians",
    "colorado-rockies", "detroit-tigers", "houston-astros", "kansas-city-royals",
    "los-angeles-angels", "los-angeles-dodgers", "miami-marlins", "milwaukee-brewers",
    "minnesota-twins", "new-york-mets", "new-york-yankees", "oakland-athletics",
    "philadelphia-phillies", "pittsburgh-pirates", "san-diego-padres", "san-francisco-giants",
    "seattle-mariners", "st-louis-cardinals", "tampa-bay-rays", "texas-rangers",
    "toronto-blue-jays", "washington-nationals"
]

def fetch_team_year_salary(team_slug: str, year: int, scraper) -> pd.DataFrame | None:
    """抓取指定球隊某年的薪資表"""
    url = f"https://www.spotrac.com/mlb/{team_slug}/payroll/_/year/{year}/"
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
    """清理薪資欄位"""
    for col in df.columns:
        if "salary" in col.lower():
            df[col] = df[col].astype(str).str.replace(r"[\$,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def main():
    years = [2021, 2022, 2023, 2024, 2025]
    scraper = cloudscraper.create_scraper()

    all_data = []
    for team in MLB_TEAMS:
        for year in years:
            try:
                df = fetch_team_year_salary(team, year, scraper)
                if df is not None:
                    df = clean_salary(df)
                    all_data.append(df)
            except Exception as e:
                print(f"❌ {team} {year} error: {e}")
            time.sleep(2.5)  # 禮貌延遲，避免被封鎖

    if not all_data:
        print("❌ No data fetched.")
        return

    # 過濾掉沒有 salary 欄位的表格
    filtered = []
    for df in all_data:
        if any("salary" in c.lower() for c in df.columns):
            filtered.append(df)
        else:
            print(f"⚠️  Skipping table without salary column: {df.columns}")

    if not filtered:
        print("❌ No valid salary tables found.")
        return

    final_df = pd.concat(filtered, ignore_index=True)
    salary_cols = [c for c in final_df.columns if "salary" in c.lower()]

    if not salary_cols:
        print("❌ No salary column found in final dataframe.")
        print("Available columns:", final_df.columns.tolist())
        return

    salary_col = salary_cols[0]
    final_df = final_df.dropna(subset=[salary_col])

    # 年度薪資統計
    summary = final_df.groupby("Year")[salary_col].agg([
        ("Mean", "mean"),
        ("Median", "median"),
        ("Q1", lambda x: x.quantile(0.25)),
        ("Q3", lambda x: x.quantile(0.75))
    ]).reset_index()

    print("\n=== MLB Salary Summary (2021–2025) ===")
    print(summary)

    plt.figure(figsize=(10,6))
    plt.plot(summary["Year"], summary["Mean"], marker="o", label="Mean")
    plt.plot(summary["Year"], summary["Median"], marker="o", label="Median")
    plt.plot(summary["Year"], summary["Q1"], marker="o", label="Q1")
    plt.plot(summary["Year"], summary["Q3"], marker="o", label="Q3")
    plt.title("MLB Player Salary Trend (2021–2025)")
    plt.xlabel("Year")
    plt.ylabel("Salary (USD)")
    plt.legend()
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig("mlb_salary_trend.png", dpi=300)
    plt.show()

    # 儲存資料
    final_df.to_csv("mlb_all_players_2021_2025.csv", index=False, encoding="utf-8-sig")
    summary.to_csv("mlb_salary_summary_2021_2025.csv", index=False, encoding="utf-8-sig")
    print("✅ Saved: mlb_all_players_2021_2025.csv, mlb_salary_summary_2021_2025.csv")

if __name__ == "__main__":
    main()
