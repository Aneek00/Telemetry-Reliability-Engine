import logging
from src.analysis.simulation import TelemetrySimulation
from src.visualization.dashboard import DashboardGenerator

# Setup global logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def main():
    """
    Main execution pipeline for the Telemetry Reliability Engine.
    """
    logging.info("=== Starting Telemetry Reliability Engine ===")

    # Step 1: Run Statistical Backtesting & Simulation
    logging.info("\n--- Phase 1: Analytical Simulation ---")
    sim = TelemetrySimulation()
    sim.run_structural_shift_backtest()
    sim.run_anomaly_detection_backtest()

    # Step 2: Generate the Output UI
    logging.info("\n--- Phase 2: Generating Executive Dashboard ---")
    DashboardGenerator.build_dashboard()

    logging.info("\n=== Pipeline Execution Complete ===")
    logging.info("To view results, open 'reports/index.html' in your browser.")

if __name__ == "__main__":
    main()