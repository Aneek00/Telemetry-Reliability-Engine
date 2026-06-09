import plotly.express as px
import logging
from src.core.config import config
from src.analysis.metrics import TelemetryMetrics

logging.basicConfig(level=logging.INFO, format='%(message)s')

class DashboardGenerator:
    """
    Generates an interactive HTML dashboard using Plotly for visualizations.
    Consumes pre-aggregated data from the TelemetryMetrics access layer.
    """

    @staticmethod
    def generate_figures():
        """Builds the Plotly figures for the dashboard."""
        logging.info("Fetching metric aggregations for UI...")
        df_hourly = TelemetryMetrics.get_global_hourly_trend()
        df_vol = TelemetryMetrics.get_project_volatility()
        df_conc = TelemetryMetrics.get_traffic_concentration()

        logging.info("Rendering interactive charts...")
        fig1 = px.line(df_hourly, x='hour_id', y='global_views', title="Hourly Global Traffic (Macro Trend)")
        fig1.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=400)

        fig2 = px.histogram(df_vol, x='cv', nbins=50, title="Project Volatility (Micro Instability)", labels={'cv': 'CV'})
        fig2.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)

        fig3 = px.line(df_conc, x='rank', y='cum_share', title="Traffic Concentration (Pareto Dominance)")
        fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)

        return fig1, fig2, fig3

    @staticmethod
    def build_dashboard():
        """Constructs the HTML file and writes it to the output directory."""
        kpis = TelemetryMetrics.get_executive_kpis()
        fig1, fig2, fig3 = DashboardGenerator.generate_figures()

        # HTML Template matching your design
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wikimedia Telemetry Dashboard</title>
            <style>
                body {{ font-family: 'Inter', -apple-system, sans-serif; background-color: #f3f4f6; color: #111827; margin: 0; padding: 20px; }}
                .dashboard-container {{ max-width: 1400px; margin: 0 auto; }}
                .header {{ text-align: left; padding-bottom: 20px; border-bottom: 2px solid #e5e7eb; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 5px 0 0 0; color: #6b7280; font-size: 16px; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }}
                .kpi-card {{ background: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-top: 4px solid #2563eb; }}
                .kpi-title {{ font-size: 14px; text-transform: uppercase; color: #6b7280; font-weight: 600; margin-bottom: 10px; }}
                .kpi-value {{ font-size: 28px; font-weight: bold; color: #1f2937; }}
                .main-chart {{ background: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                .split-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                .sub-chart {{ background: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <div class="header">
                    <h1>Reliability & Demand Dynamics</h1>
                    <p>Wikimedia Hourly Traffic Telemetry Analysis</p>
                </div>

                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-title">Total Monthly Views</div>
                        <div class="kpi-value">{kpis['total_monthly_views'] / 1e9:.2f}B</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Avg Hourly Volume</div>
                        <div class="kpi-value">{kpis['avg_hourly_volume'] / 1e6:.1f}M</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Global Volatility (CV)</div>
                        <div class="kpi-value">{kpis['global_cv']:.2f}</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-title">Total Tracked Projects</div>
                        <div class="kpi-value">{kpis['total_tracked_projects']:,}</div>
                    </div>
                </div>

                <div class="main-chart">
                    {fig1.to_html(full_html=False, include_plotlyjs='cdn')}
                </div>

                <div class="split-grid">
                    <div class="sub-chart">
                        {fig2.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                    <div class="sub-chart">
                        {fig3.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        output_path = config.DASHBOARD_PATH
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logging.info(f"✅ Professional Dashboard generated: {output_path}")

if __name__ == "__main__":
    DashboardGenerator.build_dashboard()