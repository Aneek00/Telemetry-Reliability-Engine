import pandas as pd
from src.core.db import DuckDBEngine

class TelemetryMetrics:
    """
    Analytical access layer for retrieving and calculating structural
    reliability metrics from the established DuckDB warehouse.
    Uses read-only connections to prevent accidental data corruption.
    """

    @staticmethod
    def get_global_hourly_trend() -> pd.DataFrame:
        """Retrieves the macro-level hourly traffic trend."""
        query = "SELECT hour_id, global_views FROM hourly_global_views ORDER BY hour_id"
        with DuckDBEngine(read_only=True) as db:
            return db.fetch_df(query)

    @staticmethod
    def get_project_volatility() -> pd.DataFrame:
        """Retrieves the coefficient of variation (CV) for all tracked projects."""
        query = "SELECT cv FROM project_volatility WHERE cv IS NOT NULL"
        with DuckDBEngine(read_only=True) as db:
            return db.fetch_df(query)

    @staticmethod
    def get_traffic_concentration() -> pd.DataFrame:
        """
        Calculates Pareto dominance (cumulative share) of project traffic.
        Returns a ranked DataFrame ready for plotting.
        """
        query = """
            SELECT project, total_views
            FROM hourly_project_traffic
            ORDER BY total_views DESC
        """
        with DuckDBEngine(read_only=True) as db:
            df = db.fetch_df(query)

        # Compute concentration math purely in Pandas
        df['cum_views'] = df['total_views'].cumsum()
        df['cum_share'] = df['cum_views'] / df['total_views'].sum()
        df['rank'] = range(len(df))
        return df

    @staticmethod
    def get_executive_kpis() -> dict:
        """
        Calculates top-level KPI metrics for the executive dashboard.
        """
        df_hourly = TelemetryMetrics.get_global_hourly_trend()
        df_conc = TelemetryMetrics.get_traffic_concentration()

        total_views = float(df_hourly['global_views'].sum())
        avg_hourly = float(df_hourly['global_views'].mean())

        # Guard against zero-division in edge cases
        global_cv = float(df_hourly['global_views'].std() / avg_hourly) if avg_hourly > 0 else 0.0

        return {
            "total_monthly_views": total_views,
            "avg_hourly_volume": avg_hourly,
            "global_cv": global_cv,
            "total_tracked_projects": len(df_conc)
        }

if __name__ == "__main__":
    # Quick local test to verify the engine works
    print("--- Testing Metrics Extraction ---")
    kpis = TelemetryMetrics.get_executive_kpis()
    for key, value in kpis.items():
        if isinstance(value, float):
            print(f"{key}: {value:,.2f}")
        else:
            print(f"{key}: {value:,}")