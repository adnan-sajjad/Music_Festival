"""
====================================================================
MUSIC FESTIVAL DATA ANALYSIS PROJECT
====================================
Project Title : Music Festival Revenue & Artist Performance Analysis
Tools Used    : Python (pandas, matplotlib, seaborn)
Author        : Adnan Sajjad Makrani

This script is the Python counterpart to music_case_study.sql.
It performs the same cleaning logic in pandas, then runs the EDA /
business / advanced analysis, and saves chart images for the README
and the portfolio site.

Run from the repo root:
    python python/analysis.py
====================================================================
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
os.makedirs(IMG_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

FESTIVAL_FILE = os.path.join(DATA_DIR, "musicfestival.csv")
ARTIST_FILE = os.path.join(DATA_DIR, "Artist_Popularity_Data.csv")


# =================================================================
# STEP 1 : LOAD DATA
# =================================================================
def load_data():
    festival = pd.read_csv(FESTIVAL_FILE)
    artist = pd.read_csv(ARTIST_FILE)
    return festival, artist


# =================================================================
# STEP 2 : CLEAN COLUMN NAMES (snake_case, no special characters)
# =================================================================
def clean_column_names(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s*\(.*?\)", "", regex=True)   # drop "(Rs)", "(millions)" etc.
        .str.replace(r"[^0-9a-zA-Z]+", "_", regex=True)
        .str.strip("_")
    )
    return df


# =================================================================
# STEP 3 : DATE STANDARDIZATION
# Source data mixes dd/mm/yyyy and dd-mm-yyyy formats.
# =================================================================
def standardize_dates(df):
    def parse_date(value):
        value = str(value)
        sep = "/" if "/" in value else "-"
        return pd.to_datetime(value, format=f"%d{sep}%m{sep}%Y", errors="coerce")

    df["date"] = df["date"].apply(parse_date)
    return df


# =================================================================
# STEP 4 : MISSING VALUE HANDLING
# =================================================================
def handle_missing_values(df):
    # Tour name: blank -> "Unknown Tour"
    df["tour_name"] = df["tour_name"].fillna("Unknown Tour").replace("", "Unknown Tour")

    # Ticket price / attendance: impute with column mean, rounded like the SQL version
    df["ticket_price"] = df["ticket_price"].fillna(round(df["ticket_price"].mean(), 2))
    df["total_attendance"] = df["total_attendance"].fillna(round(df["total_attendance"].mean()))
    df["total_attendance"] = df["total_attendance"].astype(int)

    return df


# =================================================================
# STEP 5 : DATA TYPE CONVERSION
# =================================================================
def convert_types(df):
    numeric_cols = [
        "ticket_price",
        "total_attendance",
        "merchandise_sales",
        "sponsorship_revenue",
        "total_revenue",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# =================================================================
# STEP 6 : DUPLICATE DETECTION
# Same key used in the SQL script: festival, city, date, headliner.
# =================================================================
def find_duplicates(df):
    key_cols = ["festival_name", "city", "date", "headlining_artist"]
    dupes = df[df.duplicated(subset=key_cols, keep="first")]
    return dupes


# =================================================================
# STEP 7 : ARTIST TABLE CLEANUP
# =================================================================
def clean_artist_table(artist_df, festival_df):
    artist_df = clean_column_names(artist_df)

    # Fill Bryan Adams' missing average attendance using festival data,
    # mirroring the JOIN + UPDATE done in SQL.
    mask = artist_df["artist_name"] == "Bryan Adams"
    if artist_df.loc[mask, "average_attendance_per_city"].isnull().any():
        avg_attendance = round(
            festival_df.loc[
                festival_df["headlining_artist"] == "Bryan Adams", "total_attendance"
            ].mean()
        )
        artist_df.loc[mask, "average_attendance_per_city"] = avg_attendance

    if "tour_impact" in artist_df.columns:
        artist_df["tour_impact"] = artist_df["tour_impact"].str.strip()

    return artist_df


# =================================================================
# FULL CLEANING PIPELINE
# =================================================================
def clean_festival_data(df):
    df = clean_column_names(df)
    df = standardize_dates(df)
    df = handle_missing_values(df)
    df = convert_types(df)
    return df


# =================================================================
# EDA / BUSINESS QUESTIONS (mirrors Q1-Q14 in the SQL file)
# =================================================================
def run_eda(df):
    print("\n" + "=" * 60)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 60)

    print(f"Q1  Total Revenue Generated      : Rs {df['total_revenue'].sum():,.0f}")
    print(f"Q2  Total Festival Attendance     : {df['total_attendance'].sum():,.0f}")
    print(f"Q3  Average Ticket Price          : Rs {df['ticket_price'].mean():,.2f}")
    print(f"Q4  Unique Festivals              : {df['festival_name'].nunique()}")

    top_festivals = (
        df.groupby("festival_name")["total_revenue"].sum().sort_values(ascending=False).head(10)
    )
    print("\nQ5  Top 10 Revenue Generating Festivals:")
    print(top_festivals.to_string())

    city_revenue = df.groupby("city")["total_revenue"].sum().sort_values(ascending=False)
    print("\nQ6  Revenue Performance by City:")
    print(city_revenue.to_string())

    artist_revenue = (
        df.groupby("headlining_artist")["total_revenue"].sum().sort_values(ascending=False)
    )
    print("\nQ7  Top Artists by Revenue Generated:")
    print(artist_revenue.to_string())

    artist_attendance = (
        df.groupby("headlining_artist")["total_attendance"].sum().sort_values(ascending=False)
    )
    print("\nQ8  Top Artists by Audience Attendance:")
    print(artist_attendance.to_string())

    artist_ticket_price = (
        df.groupby("headlining_artist")["ticket_price"].mean().round(2).sort_values(ascending=False)
    )
    print("\nQ9  Artists with Highest Average Ticket Price:")
    print(artist_ticket_price.to_string())

    # Q11 Revenue contribution %
    revenue_by_festival = df.groupby("festival_name")["total_revenue"].sum()
    contribution_pct = (revenue_by_festival / revenue_by_festival.sum() * 100).round(2)
    contribution_pct = contribution_pct.sort_values(ascending=False)
    print("\nQ11 Revenue Contribution Percentage (Top 5):")
    print(contribution_pct.head(5).to_string())

    # Q12 / Q13 Monthly revenue trend + MoM growth
    monthly_revenue = (
        df.dropna(subset=["date"])
        .assign(month=lambda x: x["date"].dt.to_period("M").astype(str))
        .groupby("month")["total_revenue"]
        .sum()
        .sort_index()
    )
    growth_pct = monthly_revenue.pct_change().round(4) * 100
    print("\nQ12/Q13 Monthly Revenue & MoM Growth %:")
    print(pd.DataFrame({"revenue": monthly_revenue, "growth_pct": growth_pct}).to_string())

    # Q14 Top revenue festival per city
    top_per_city = (
        df.groupby(["city", "festival_name"])["total_revenue"]
        .sum()
        .reset_index()
        .sort_values("total_revenue", ascending=False)
        .drop_duplicates(subset="city")
        .sort_values("city")
    )
    print("\nQ14 Top Revenue Festival in Each City:")
    print(top_per_city.to_string(index=False))

    return {
        "top_festivals": top_festivals,
        "city_revenue": city_revenue,
        "artist_revenue": artist_revenue,
        "artist_attendance": artist_attendance,
        "monthly_revenue": monthly_revenue,
    }


def run_artist_eda(artist_df):
    print("\n" + "=" * 60)
    print("ARTIST PERFORMANCE ANALYSIS")
    print("=" * 60)

    streaming = artist_df[["artist_name", "genre", "streaming_plays"]].sort_values(
        "streaming_plays", ascending=False
    )
    print("\nTop Artists by Streaming Popularity:")
    print(streaming.to_string(index=False))

    genre_count = artist_df.groupby("genre").size().sort_values(ascending=False)
    print("\nGenre Popularity:")
    print(genre_count.to_string())

    return {"streaming": streaming, "genre_count": genre_count}


# =================================================================
# VISUALIZATIONS
# =================================================================
def make_charts(results, artist_results):
    # 1. Top 10 festivals by revenue
    plt.figure()
    results["top_festivals"].sort_values().plot(kind="barh", color="#4C72B0")
    plt.title("Top 10 Festivals by Total Revenue")
    plt.xlabel("Total Revenue (Rs)")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "top_10_festivals_revenue.png"), dpi=150)
    plt.close()

    # 2. Revenue by city
    plt.figure()
    results["city_revenue"].plot(kind="bar", color="#55A868")
    plt.title("Total Revenue by City")
    plt.ylabel("Total Revenue (Rs)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "revenue_by_city.png"), dpi=150)
    plt.close()

    # 3. Top artists by revenue
    plt.figure()
    results["artist_revenue"].head(10).sort_values().plot(kind="barh", color="#C44E52")
    plt.title("Top 10 Artists by Revenue")
    plt.xlabel("Total Revenue (Rs)")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "top_artists_revenue.png"), dpi=150)
    plt.close()

    # 4. Monthly revenue trend
    plt.figure()
    results["monthly_revenue"].plot(kind="line", marker="o", color="#8172B2")
    plt.title("Monthly Revenue Trend")
    plt.ylabel("Total Revenue (Rs)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "monthly_revenue_trend.png"), dpi=150)
    plt.close()

    # 5. Genre popularity
    plt.figure()
    artist_results["genre_count"].plot(kind="bar", color="#CCB974")
    plt.title("Artist Count by Genre")
    plt.ylabel("Number of Artists")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(IMG_DIR, "genre_popularity.png"), dpi=150)
    plt.close()

    print(f"\nSaved 5 chart images to: {IMG_DIR}")


# =================================================================
# MAIN
# =================================================================
def main():
    festival_raw, artist_raw = load_data()

    festival = clean_festival_data(festival_raw.copy())
    artist = clean_artist_table(artist_raw.copy(), festival)

    dupes = find_duplicates(festival)
    print(f"Duplicate records found: {len(dupes)}")

    results = run_eda(festival)
    artist_results = run_artist_eda(artist)

    make_charts(results, artist_results)

    # Save cleaned datasets for reuse (e.g. by Power BI or downstream notebooks)
    cleaned_dir = os.path.join(DATA_DIR, "cleaned")
    os.makedirs(cleaned_dir, exist_ok=True)
    festival.to_csv(os.path.join(cleaned_dir, "music_festival_clean.csv"), index=False)
    artist.to_csv(os.path.join(cleaned_dir, "artist_popularity_clean.csv"), index=False)
    print(f"\nCleaned data saved to: {cleaned_dir}")


if __name__ == "__main__":
    main()
