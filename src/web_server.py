"""
================================================================================
RetailMax Enterprise Data Platform

Module:      web_server.py
Purpose:     FastAPI Web Server & BI Dashboard for Local Execution
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import asyncio
from typing import Any

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from analytics import BusinessAnalyticsEngine

# Import first-party platform modules
from config import CHARTS_DIR
from database import DatabaseHandler
from logging_config import get_logger
from main import run_pipeline

# Initialize Logger
logger = get_logger("web_server")

app = FastAPI(
    title="RetailMax BI Platform",
    description="Corporate dashboard and API layer for the Enterprise Data Platform",
    version="6.0.0",
)

# Mount the Matplotlib charts folder to serve generated images
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# In-memory execution state lock for pipeline run
pipeline_running = False


@app.post("/api/run-pipeline")
async def trigger_pipeline(background_tasks: BackgroundTasks) -> Any:
    """Triggers the ETL pipeline asynchronously to prevent blocking the web server thread."""
    global pipeline_running
    if pipeline_running:
        return JSONResponse(
            status_code=429,
            content={"status": "error", "message": "Pipeline run is already in progress."},
        )

    pipeline_running = True

    def async_pipeline_executor() -> None:
        global pipeline_running
        logger.info("Asynchronously executing ETL pipeline from web dashboard request...")
        try:
            # Run the async pipeline loop
            asyncio.run(run_pipeline())
        except Exception as e:
            logger.error(f"Async dashboard pipeline run failed: {e}", exc_info=True)
        finally:
            pipeline_running = False
            logger.info("Async dashboard pipeline run complete.")

    background_tasks.add_task(async_pipeline_executor)
    return {"status": "success", "message": "ETL pipeline triggered successfully."}


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard() -> HTMLResponse:
    """Generates and serves a premium, glassmorphic analytics dashboard."""
    db = DatabaseHandler()
    analytics = BusinessAnalyticsEngine()

    # Load data dynamically from SQLite
    try:
        df = analytics.load_cleaned_dataframe()
        kpis = analytics.calculate_kpis(df)
        employees = db.get_all_employees()
    except Exception as e:
        logger.warning(f"Initial dashboard load encountered missing data: {e}")
        # If database is empty or doesn't exist, provide safe fallback stats
        kpis = {
            "Headcount": 0,
            "AverageSalary": 0.0,
            "MaxSalary": 0.0,
            "MinSalary": 0.0,
            "TotalSalaryExpense": 0.0,
            "HighPerformersCount": 0,
            "HighPerformersRatio": 0.0,
        }
        employees = []

    # Format numbers for dashboard view
    formatted_total_expense = f"₹{kpis['TotalSalaryExpense']:,.2f}"
    formatted_avg_salary = f"₹{kpis['AverageSalary']:,.2f}"

    # Build raw HTML response with beautiful, premium glassmorphism styling
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RetailMax Enterprise BI Platform</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-dark: #0f172a;
                --card-bg: rgba(30, 41, 59, 0.7);
                --card-border: rgba(255, 255, 255, 0.08);
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --accent-blue: #3b82f6;
                --accent-cyan: #06b6d4;
                --accent-green: #10b981;
                --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
            }}
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg-dark);
                background-image: 
                    radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
                    radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.1) 0px, transparent 50%);
                color: var(--text-main);
                min-height: 100vh;
                padding: 2rem;
                line-height: 1.5;
            }}

            header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2.5rem;
                padding-bottom: 1.5rem;
                border-bottom: 1px solid var(--card-border);
            }}

            .logo-area {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}

            .logo-icon {{
                background: var(--accent-gradient);
                width: 48px;
                height: 48px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 1.5rem;
                box-shadow: 0 4px 20px rgba(6, 182, 212, 0.3);
            }}

            .logo-text h1 {{
                font-size: 1.5rem;
                font-weight: 600;
                letter-spacing: -0.5px;
            }}

            .logo-text p {{
                font-size: 0.85rem;
                color: var(--text-muted);
            }}

            .btn-pipeline {{
                background: var(--accent-gradient);
                border: none;
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 10px;
                font-family: inherit;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                transition: all 0.2s ease;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
            }}

            .btn-pipeline:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
            }}

            .btn-pipeline:active {{
                transform: translateY(0);
            }}

            /* KPI Stats Grid */
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2.5rem;
            }}

            .kpi-card {{
                background: var(--card-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--card-border);
                border-radius: 16px;
                padding: 1.5rem;
                position: relative;
                overflow: hidden;
                transition: transform 0.3s ease;
            }}

            .kpi-card:hover {{
                transform: translateY(-3px);
                border-color: rgba(255, 255, 255, 0.15);
            }}

            .kpi-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: var(--accent-blue);
            }}

            .kpi-card.cyan::before {{ background: var(--accent-cyan); }}
            .kpi-card.green::before {{ background: var(--accent-green); }}

            .kpi-label {{
                font-size: 0.85rem;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 0.5rem;
            }}

            .kpi-value {{
                font-size: 1.75rem;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}

            /* Dashboard Layout split */
            .main-content {{
                display: grid;
                grid-template-columns: 3fr 2fr;
                gap: 2rem;
                margin-bottom: 2.5rem;
            }}

            @media(max-width: 1024px) {{
                .main-content {{
                    grid-template-columns: 1fr;
                }}
            }}

            .section-card {{
                background: var(--card-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--card-border);
                border-radius: 20px;
                padding: 2rem;
            }}

            .section-title {{
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            /* Scrollable Directory Table */
            .table-wrapper {{
                overflow-x: auto;
                max-height: 480px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                font-size: 0.9rem;
            }}

            th {{
                padding: 1rem;
                color: var(--text-muted);
                font-weight: 500;
                border-bottom: 1px solid var(--card-border);
                position: sticky;
                top: 0;
                background: #1e293b;
                z-index: 10;
            }}

            td {{
                padding: 1rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }}

            tr:hover td {{
                background: rgba(255, 255, 255, 0.02);
            }}

            .badge {{
                display: inline-block;
                padding: 0.25rem 0.5rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
                background: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
            }}

            .badge.score-high {{
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
            }}

            /* Charts Gallery */
            .chart-gallery {{
                display: flex;
                flex-direction: column;
                gap: 1.5rem;
            }}

            .chart-container {{
                background: rgba(15, 23, 42, 0.6);
                border-radius: 12px;
                padding: 0.75rem;
                border: 1px solid var(--card-border);
                text-align: center;
            }}

            .chart-container img {{
                max-width: 100%;
                border-radius: 8px;
            }}

            .chart-title {{
                font-size: 0.85rem;
                color: var(--text-muted);
                margin-top: 0.5rem;
            }}

            /* Toast Notification */
            .toast {{
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                background: #1e293b;
                border-left: 4px solid var(--accent-cyan);
                border-radius: 8px;
                padding: 1rem 1.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                z-index: 100;
                transform: translateY(150%);
                transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }}

            .toast.show {{
                transform: translateY(0);
            }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo-area">
                <div class="logo-icon">RM</div>
                <div class="logo-text">
                    <h1>RetailMax Enterprise</h1>
                    <p>Live BI & ETL Orchestration Platform</p>
                </div>
            </div>
            <div>
                <button class="btn-pipeline" onclick="triggerETL()">
                    <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2M7 9a4 4 0 110-8h10a4 4 0 110 8H7z"></path></svg>
                    Trigger Pipeline Run
                </button>
            </div>
        </header>

        <!-- KPI Grid -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Active Headcount</div>
                <div class="kpi-value">{kpis['Headcount']}</div>
            </div>
            <div class="kpi-card cyan">
                <div class="kpi-label">Avg Monthly Salary</div>
                <div class="kpi-value">{formatted_avg_salary}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Monthly Expense</div>
                <div class="kpi-value">{formatted_total_expense}</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-label">High Performers</div>
                <div class="kpi-value">{kpis['HighPerformersRatio']}%</div>
            </div>
        </section>

        <!-- Main Dashboard Split Layout -->
        <main class="main-content">
            <!-- Left Panel: Employee Directory -->
            <section class="section-card">
                <div class="section-title">
                    <span>👥 Corporate Employee Directory ({len(employees)} Persisted)</span>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Department</th>
                                <th>Designation</th>
                                <th>Monthly Salary</th>
                                <th>Rating</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{emp.employee_id}</td>
                                <td><strong>{emp.name}</strong></td>
                                <td><span class="badge">{emp.department}</span></td>
                                <td>{emp.designation}</td>
                                <td>₹{emp.salary:,.2f}</td>
                                <td><span class="badge {"score-high" if emp.performance_score >= 4 else ""}">★ {emp.performance_score}</span></td>
                            </tr>
                            ''' for emp in employees])}
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- Right Panel: BI Charts Feed -->
            <section class="section-card">
                <div class="section-title">
                    <span>📊 Dynamic Visual Analytics</span>
                </div>
                <div class="chart-gallery">
                    <div class="chart-container">
                        <img src="/charts/15_salary_violin_plot.png" alt="Violin Plot">
                        <div class="chart-title">Salary Density Distribution by Division</div>
                    </div>
                    <div class="chart-container">
                        <img src="/charts/01_headcount_by_dept.png" alt="Headcount Bar Chart">
                        <div class="chart-title">Total Headcount by Department</div>
                    </div>
                    <div class="chart-container">
                        <img src="/charts/07_performance_vs_salary_scatter.png" alt="Performance vs Salary Scatter">
                        <div class="chart-title">Bivariate Scatter: Performance vs. Salary</div>
                    </div>
                    <div class="chart-container">
                        <img src="/charts/16_correlation_heatmap.png" alt="Correlation Heatmap">
                        <div class="chart-title">Numeric Parameter Correlations</div>
                    </div>
                </div>
            </section>
        </main>

        <!-- Notification Toast -->
        <div id="toast" class="toast">ETL Data Pipeline Execution Triggered...</div>

        <script>
            function triggerETL() {{
                const toast = document.getElementById('toast');
                toast.classList.add('show');
                
                fetch('/api/run-pipeline', {{ method: 'POST' }})
                    .then(response => response.json())
                    .then(data => {{
                        toast.innerText = data.message;
                        setTimeout(() => {{
                            toast.classList.remove('show');
                            // Reload the page after 4 seconds to show new data and regenerated charts
                            setTimeout(() => window.location.reload(), 1000);
                        }}, 3000);
                    }})
                    .catch(err => {{
                        toast.innerText = "Error triggering pipeline run.";
                        setTimeout(() => toast.classList.remove('show'), 3000);
                    }});
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    # Start the server locally on port 8000
    uvicorn.run("web_server:app", host="127.0.0.1", port=8000, reload=True)
