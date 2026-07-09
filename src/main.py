"""
================================================================================
RetailMax Enterprise Data Platform

Module:      main.py
Purpose:     Main ETL Orchestrator Entrypoint (Synchronous & Asynchronous ETL)
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import asyncio
import sys

from analytics import BusinessAnalyticsEngine
from api_service import APIServiceClient
from async_fetcher import AsyncFeedFetcher
from data_transformer import DataTransformer
from database import DatabaseHandler
from db_migrator import DatabaseMigrator
from logging_config import get_logger
from report_generator import ExecutiveReportGenerator

# Obtain orchestrator logger
logger = get_logger("orchestrator")


async def run_pipeline() -> None:
    """Executes the end-to-end ETL corporate data pipeline flow."""
    logger.info("Initializing RetailMax Enterprise ETL Pipeline...")

    try:
        # Step 1: Migrate baseline employee CSV to SQLite Relational DB
        migrator = DatabaseMigrator()
        baseline_count, baseline_duration = migrator.migrate()
        logger.info(f"Baseline loaded: {baseline_count} employees in {baseline_duration:.4f}s.")

        # Step 2: Fetch and transform raw external API employees
        api_client = APIServiceClient()
        raw_api_payload = api_client.fetch_raw_employees()

        transformer = DataTransformer()
        api_employees = transformer.transform_raw_payload(raw_api_payload)

        # Save API employees to SQLite
        db_handler = DatabaseHandler()
        db_handler.insert_employees_batch(api_employees)
        logger.info(f"Merged {len(api_employees)} external API records to database.")

        # Step 3: Run concurrent async fetch of auxiliary payroll feeds
        fetcher = AsyncFeedFetcher()
        feed_results, feed_duration = await fetcher.fetch_all_feeds_concurrently()
        logger.info(f"Concurrently checked {len(feed_results)} feeds in {feed_duration:.4f}s.")

        # Step 4: Run Pandas business analytics engine & calculate KPIs
        analytics_engine = BusinessAnalyticsEngine()
        df = analytics_engine.load_cleaned_dataframe()
        kpis = analytics_engine.calculate_kpis(df)

        # Step 5: Render 16 business charts with Matplotlib
        chart_files = analytics_engine.generate_all_charts(df)
        logger.info(f"Generated {len(chart_files)} analytical charts in 'charts/' directory.")

        # Step 6: Export formatted reports (CEO Dashboard and Excel Worksheets)
        dept_summary = db_handler.get_department_summary()
        report_generator = ExecutiveReportGenerator()

        md_report = report_generator.generate_ceo_markdown_dashboard(kpis, dept_summary)
        xlsx_report = report_generator.generate_excel_workbook(
            db_handler.get_all_employees(), dept_summary
        )

        logger.info(f"ETL Dashboard Report ready: {md_report}")
        logger.info(f"Styled Excel Directory ready: {xlsx_report}")
        logger.info("=== ETL Data Pipeline Pipeline Executed Successfully ===")

    except Exception as e:
        logger.critical(f"Data Pipeline run crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Execute the asynchronous wrapper pipeline
    asyncio.run(run_pipeline())
