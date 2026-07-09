"""
================================================================================
RetailMax Enterprise Data Platform

Module:      analytics.py
Purpose:     Pandas aggregates, HR KPIs, and Matplotlib chart drawing code
             generating 15+ different PNG files.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import sqlite3
from pathlib import Path
from typing import Any

# Set non-interactive Matplotlib backend before importing pyplot
# This prevents GUI window spawning errors in CLI/automated runs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import CHARTS_DIR, CSV_DATA_PATH, DB_PATH
from constants import (
    CHART_COLOR_PALETTE,
    CHART_DPI,
    CHART_FIGSIZE_HEIGHT,
    CHART_FIGSIZE_WIDTH,
)
from exceptions import AnalyticsError
from logging_config import get_logger

# Initialize logger
logger = get_logger("analytics")


class BusinessAnalyticsEngine:
    """Performs Pandas business intelligence analysis and generates Matplotlib charts."""

    def __init__(self, db_path: Path = DB_PATH, csv_path: Path = CSV_DATA_PATH) -> None:
        self.db_path = db_path
        self.csv_path = csv_path
        self.charts_dir = CHARTS_DIR
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def load_cleaned_dataframe(self) -> pd.DataFrame:
        """Loads employee data from SQLite database, falling back to CSV.

        Cleans dataset by checking duplicates and filling null records.

        Returns:
            pd.DataFrame: Cleaned Pandas DataFrame.

        Raises:
            AnalyticsError: If loading fails.
        """
        logger.info("Loading dataset for Pandas analytics...")
        df: pd.DataFrame | None = None

        # 1. Attempt database load
        if self.db_path.exists():
            try:
                conn = sqlite3.connect(str(self.db_path))
                df = pd.read_sql_query("SELECT * FROM employees;", conn)
                conn.close()
                # Standardize SQLite snake_case columns to CSV PascalCase
                rename_map = {
                    "employee_id": "EmployeeID",
                    "name": "Name",
                    "department": "Department",
                    "designation": "Designation",
                    "salary": "Salary",
                    "joining_date": "JoiningDate",
                    "performance_score": "PerformanceScore",
                }
                df = df.rename(columns=rename_map)
                logger.info(f"Loaded {len(df)} rows from SQLite Database.")
            except Exception as e:
                logger.warning(f"Failed to read from SQLite database: {e}. Falling back to CSV.")

        # 2. Attempt CSV fallback load
        if df is None or df.empty:
            if self.csv_path.exists():
                try:
                    df = pd.read_csv(self.csv_path)
                    logger.info(f"Loaded {len(df)} rows from CSV flat file.")
                except Exception as e:
                    raise AnalyticsError(f"Failed to load fallback CSV: {e}")
            else:
                raise AnalyticsError("No database or CSV data source found to run analytics.")

        try:
            # Drop duplicates on primary identifier
            initial_len = len(df)
            df = df.drop_duplicates(subset=["EmployeeID"], keep="first")
            if len(df) < initial_len:
                logger.warning(
                    f"Removed {initial_len - len(df)} duplicate EmployeeID rows during loading."
                )

            # Clean null/empty columns
            df["Salary"] = pd.to_numeric(df["Salary"], errors="coerce")
            df["PerformanceScore"] = pd.to_numeric(df["PerformanceScore"], errors="coerce")

            # Fill missing salaries with median, scores with 3 (Average)
            median_salary = df["Salary"].median()
            df["Salary"] = df["Salary"].fillna(median_salary)
            df["PerformanceScore"] = df["PerformanceScore"].fillna(3).astype(int)

            # Ensure JoiningDate is datetime
            df["JoiningDate"] = pd.to_datetime(df["JoiningDate"], errors="coerce")
            df["JoiningDate"] = df["JoiningDate"].fillna(pd.Timestamp("2024-01-01"))

            # Calculate derived column 'TenureYears' (relative to current date: July 9, 2026)
            current_date = pd.Timestamp("2026-07-09")
            df["TenureYears"] = (current_date - df["JoiningDate"]).dt.days / 365.25

            logger.info("DataFrame cleaning and feature engineering complete.")
            return df
        except Exception as e:
            raise AnalyticsError(f"Failed to clean and process DataFrame: {e}")

    def calculate_kpis(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculates 10+ core HR key performance indicators.

        Args:
            df: Cleaned employee DataFrame.

        Returns:
            Dict[str, Any]: Calculated metrics.
        """
        logger.info("Calculating HR KPIs...")
        try:
            headcount = int(len(df))
            total_salary = float(df["Salary"].sum())
            avg_salary = float(df["Salary"].mean())
            median_salary = float(df["Salary"].median())
            max_salary = float(df["Salary"].max())
            min_salary = float(df["Salary"].min())
            avg_score = float(df["PerformanceScore"].mean())
            avg_tenure = float(df["TenureYears"].mean())

            # High performers count (rating >= 4)
            high_performers = int((df["PerformanceScore"] >= 4).sum())
            high_performer_ratio = high_performers / headcount if headcount > 0 else 0.0

            # Find top 5 earners
            top_earners_df = df.nlargest(5, "Salary")
            top_earners = []
            for _, row in top_earners_df.iterrows():
                top_earners.append(
                    {
                        "EmployeeID": int(row["EmployeeID"]),
                        "Name": str(row["Name"]),
                        "Salary": float(row["Salary"]),
                        "Department": str(row["Department"]),
                    }
                )

            kpis = {
                "Headcount": headcount,
                "TotalSalaryExpense": round(total_salary, 2),
                "AverageSalary": round(avg_salary, 2),
                "MedianSalary": round(median_salary, 2),
                "MaxSalary": round(max_salary, 2),
                "MinSalary": round(min_salary, 2),
                "AveragePerformanceScore": round(avg_score, 2),
                "AverageTenureYears": round(avg_tenure, 2),
                "HighPerformersCount": high_performers,
                "HighPerformersRatio": round(high_performer_ratio * 100, 2),
                "Top5Earners": top_earners,
            }
            logger.info("KPI calculations finished.")
            return kpis
        except Exception as e:
            raise AnalyticsError(f"KPI calculation failed: {e}")

    # ==============================================================================
    # MATPLOTLIB CHART GENERATION SECTOR (16 DISTINCT CHARTS)
    # ==============================================================================

    def generate_all_charts(self, df: pd.DataFrame) -> list[str]:
        """Generates 16 distinct analytical charts and saves them to charts folder.

        Args:
            df: Cleaned employee DataFrame.

        Returns:
            List[str]: List of filenames generated.
        """
        logger.info("Beginning generation of 16 analytical charts...")
        generated_files: list[str] = []

        # Guarantee the charts folder exists before writing
        self.charts_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Chart 1: Headcount by Department (Bar)
            self._plot_bar(
                data=df["Department"].value_counts(),
                title="Employee Headcount by Department",
                xlabel="Department",
                ylabel="Headcount",
                filename="01_headcount_by_dept.png",
                color=CHART_COLOR_PALETTE[0],
            )
            generated_files.append("01_headcount_by_dept.png")

            # Chart 2: Total Salary Expense by Department (Bar)
            dept_sal = df.groupby("Department")["Salary"].sum()
            self._plot_bar(
                data=dept_sal,
                title="Total Salary Expense by Department",
                xlabel="Department",
                ylabel="Total Salary (Monthly)",
                filename="02_salary_expenses_by_dept.png",
                color=CHART_COLOR_PALETTE[1],
            )
            generated_files.append("02_salary_expenses_by_dept.png")

            # Chart 3: Average Salary by Department (Bar)
            dept_avg_sal = df.groupby("Department")["Salary"].mean()
            self._plot_bar(
                data=dept_avg_sal,
                title="Average Monthly Salary by Department",
                xlabel="Department",
                ylabel="Average Salary",
                filename="03_average_salary_by_dept.png",
                color=CHART_COLOR_PALETTE[2],
            )
            generated_files.append("03_average_salary_by_dept.png")

            # Chart 4: Salary Distribution (Histogram)
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            plt.hist(
                df["Salary"], bins=15, color=CHART_COLOR_PALETTE[3], edgecolor="black", alpha=0.7
            )
            plt.title("Distribution of Monthly Salaries")
            plt.xlabel("Salary Range")
            plt.ylabel("Number of Employees")
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "04_salary_distribution.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("04_salary_distribution.png")

            # Chart 5: Salary by Department Boxplot
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            # Group data for boxplot
            depts = df["Department"].unique()
            data_groups = [df[df["Department"] == d]["Salary"] for d in depts]
            plt.boxplot(
                data_groups,
                tick_labels=depts,
                patch_artist=True,
                boxprops={"facecolor": "#d62728", "alpha": 0.6},
            )
            plt.title("Salary Ranges and Outliers by Department")
            plt.xlabel("Department")
            plt.ylabel("Salary")
            plt.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "05_salary_by_dept_boxplot.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("05_salary_by_dept_boxplot.png")

            # Chart 6: Performance Score Distribution (Pie)
            perf_counts = df["PerformanceScore"].value_counts().sort_index()
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            labels = [f"Score {i}" for i in perf_counts.index]
            plt.pie(
                perf_counts,
                labels=labels,
                autopct="%1.1f%%",
                startangle=140,
                colors=CHART_COLOR_PALETTE,
            )
            plt.title("Share of Employees by Performance Scores")
            plt.tight_layout()
            plt.savefig(self.charts_dir / "06_performance_score_pie.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("06_performance_score_pie.png")

            # Chart 7: Performance vs Salary Correlation (Scatter)
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            plt.scatter(
                df["PerformanceScore"],
                df["Salary"],
                color=CHART_COLOR_PALETTE[4],
                alpha=0.6,
                edgecolors="black",
            )
            plt.title("Correlation between Performance Scores & Salaries")
            plt.xlabel("Performance Score (1-5)")
            plt.ylabel("Monthly Salary")
            plt.grid(linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "07_performance_vs_salary_scatter.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("07_performance_vs_salary_scatter.png")

            # Chart 8: Hiring Trends Line Chart (Cumulative Headcount)
            sorted_dates = df.sort_values("JoiningDate")
            sorted_dates["HeadcountCount"] = 1
            sorted_dates["CumulativeHeadcount"] = sorted_dates["HeadcountCount"].cumsum()
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            plt.plot(
                sorted_dates["JoiningDate"],
                sorted_dates["CumulativeHeadcount"],
                marker="o",
                color=CHART_COLOR_PALETTE[0],
                linewidth=2,
            )
            plt.title("Cumulative Headcount Growth Over Time")
            plt.xlabel("Joining Date")
            plt.ylabel("Total Headcount")
            plt.grid(linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "08_hiring_trends_line.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("08_hiring_trends_line.png")

            # Chart 9: Salary vs Tenure Scatter
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            plt.scatter(
                df["TenureYears"],
                df["Salary"],
                color=CHART_COLOR_PALETTE[1],
                alpha=0.7,
                edgecolors="black",
            )
            plt.title("Monthly Salary vs Tenure in Organization")
            plt.xlabel("Tenure (Years)")
            plt.ylabel("Monthly Salary")
            plt.grid(linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "09_salary_vs_tenure_scatter.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("09_salary_vs_tenure_scatter.png")

            # Chart 10: Department Average Performance Rating (Horizontal Bar)
            dept_perf = df.groupby("Department")["PerformanceScore"].mean().sort_values()
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            plt.barh(dept_perf.index, dept_perf, color="#9467bd", edgecolor="black", alpha=0.8)
            plt.title("Average Performance Scores by Department")
            plt.xlabel("Average Score")
            plt.ylabel("Department")
            plt.xlim(1, 5)
            plt.grid(axis="x", linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "10_dept_performance_avg.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("10_dept_performance_avg.png")

            # Chart 11: Salary by Designation (Bar)
            desig_sal = df.groupby("Designation")["Salary"].mean().sort_values(ascending=False)
            self._plot_bar(
                data=desig_sal,
                title="Average Monthly Salary by Designation",
                xlabel="Designation",
                ylabel="Average Salary",
                filename="11_salary_by_designation_bar.png",
                color=CHART_COLOR_PALETTE[2],
            )
            generated_files.append("11_salary_by_designation_bar.png")

            # Chart 12: Tenure Distribution (Histogram)
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            plt.hist(
                df["TenureYears"],
                bins=10,
                color=CHART_COLOR_PALETTE[0],
                edgecolor="black",
                alpha=0.7,
            )
            plt.title("Distribution of Employee Tenure")
            plt.xlabel("Tenure in Years")
            plt.ylabel("Number of Employees")
            plt.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "12_tenure_distribution.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("12_tenure_distribution.png")

            # Chart 13: Average Performance by Designation (Bar)
            desig_perf = df.groupby("Designation")["PerformanceScore"].mean().sort_values()
            self._plot_bar(
                data=desig_perf,
                title="Average Performance Ratings by Designation",
                xlabel="Designation",
                ylabel="Average Performance Score",
                filename="13_performance_by_designation_bar.png",
                color=CHART_COLOR_PALETTE[3],
            )
            generated_files.append("13_performance_by_designation_bar.png")

            # Chart 14: Stacked Bar - High Performers (>=4) vs Others by Dept
            df["IsHighPerformer"] = df["PerformanceScore"] >= 4
            stacked_data = (
                df.groupby(["Department", "IsHighPerformer"]).size().unstack(fill_value=0)
            )
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            # True = High Performer, False = Core
            colors = ["#cccccc", "#2ca02c"]
            stacked_data.plot(
                kind="bar", stacked=True, color=colors, edgecolor="black", ax=plt.gca()
            )
            plt.title("High Performers (Score >= 4) Distribution by Department")
            plt.xlabel("Department")
            plt.ylabel("Headcount")
            plt.legend(["Core Performer (1-3)", "High Performer (4-5)"])
            plt.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "14_high_performers_by_dept.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("14_high_performers_by_dept.png")

            # Chart 15: Salary Violin Plot by Department
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            depts_violin = df["Department"].unique()
            data_violin = [df[df["Department"] == d]["Salary"] for d in depts_violin]
            # Use matplotlib violinplot
            parts = plt.violinplot(data_violin, showmeans=True, showmedians=True)
            # Style violins
            for pc in parts["bodies"]:  # type: ignore
                pc.set_facecolor("#1f77b4")
                pc.set_edgecolor("black")
                pc.set_alpha(0.6)
            plt.xticks(range(1, len(depts_violin) + 1), depts_violin)
            plt.title("Salary Probability Density Distributions by Department")
            plt.xlabel("Department")
            plt.ylabel("Salary")
            plt.grid(axis="y", linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(self.charts_dir / "15_salary_violin_plot.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("15_salary_violin_plot.png")

            # Chart 16: Correlation Heatmap between numeric columns
            numeric_cols = ["Salary", "PerformanceScore", "TenureYears"]
            corr_matrix = df[numeric_cols].corr()
            plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
            # Simple heatmap using matplotlib imshow
            plt.imshow(corr_matrix, cmap="coolwarm", interpolation="nearest", vmin=-1, vmax=1)
            plt.colorbar(label="Pearson Correlation Coefficient")
            # Label ticks
            plt.xticks(range(len(numeric_cols)), numeric_cols)
            plt.yticks(range(len(numeric_cols)), numeric_cols)
            # Add correlation text labels inside grid
            for i in range(len(numeric_cols)):
                for j in range(len(numeric_cols)):
                    val = corr_matrix.iloc[i, j]
                    plt.text(
                        j,
                        i,
                        f"{val:.2f}",
                        ha="center",
                        va="center",
                        color="white" if abs(val) > 0.5 else "black",
                        fontweight="bold",
                    )
            plt.title("Correlation Matrix of Numeric Employee Metrics")
            plt.tight_layout()
            plt.savefig(self.charts_dir / "16_correlation_heatmap.png", dpi=CHART_DPI)
            plt.close()
            generated_files.append("16_correlation_heatmap.png")

            logger.info("Successfully generated and saved all 16 Matplotlib charts.")
            return generated_files

        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")
            # Ensure figures are closed to avoid memory leaks
            plt.close("all")
            raise AnalyticsError(f"Matplotlib chart engine failed: {e}")

    # ==============================================================================
    # CHART PLOTTING HELPERS
    # ==============================================================================

    def _plot_bar(
        self, data: pd.Series, title: str, xlabel: str, ylabel: str, filename: str, color: str
    ) -> None:
        """Helper to plot standardized 2D vertical bar charts."""
        plt.figure(figsize=(CHART_FIGSIZE_WIDTH, CHART_FIGSIZE_HEIGHT))
        plt.bar(data.index, data.values, color=color, edgecolor="black", alpha=0.8)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=15)
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(self.charts_dir / filename, dpi=CHART_DPI)
        plt.close()


# Executable entry point for testing
if __name__ == "__main__":
    try:
        engine = BusinessAnalyticsEngine()
        data_df = engine.load_cleaned_dataframe()
        kpi_metrics = engine.calculate_kpis(data_df)
        print("\n=== Business KPIs Calculated ===")
        for k, v in kpi_metrics.items():
            if k != "Top5Earners":
                print(f"{k}: {v}")
        charts = engine.generate_all_charts(data_df)
        print(f"\nGenerated {len(charts)} charts in 'charts/' directory.")
    except Exception as err:
        print("Analytics validation run failed:", err)


# ==============================================================================
# INTERVIEW NOTES & PANDAS ANALYSIS CORE MECHANICS:
#
# Q1: Explain Vectorization in Pandas vs Standard Loops.
#     Vectorization is the process of applying mathematical operations to entire
#     arrays at once rather than iterating through elements one-by-one.
#     Pandas delegates computations to pre-compiled C libraries under the hood.
#     For example: 'df["Salary"] * 12' multiplies 100,000 cells in a few microseconds,
#     while a python loop takes milliseconds and uses a lot of CPU cache memory.
#
# Q2: What is the difference between a Pandas Series and a DataFrame?
#     - Series: A 1-dimensional labeled array capable of holding any data type
#       (essentially a single column with an index).
#     - DataFrame: A 2-dimensional labeled data structure with columns of potentially
#       different types (essentially a collection of Series sharing the same index).
#
# Q3: Why do we specify 'matplotlib.use("Agg")' in backend execution?
#     By default, Matplotlib tries to open a GUI window (using Tkinter, Qt, or Wx)
#     to render charts interactively. In web servers, docker containers, or terminal
#     runner environments that lack a desktop monitor (headless server), this causes
#     the code to fail with connection display errors. "Agg" is a raster graphics
#     backend that renders charts in memory, allowing them to be saved directly
#     as PNG files without GUI displays.
# ==============================================================================
