from pathlib import Path
from dataclasses import dataclass

@dataclass
class ProjectConfig:
    """
    Centralized configuration for the Telemetry Reliability Engine.
    Handles dynamic path resolution across different environments.
    """
    # Base Path Resolution (Resolves to the root of the repository)
    # Since this file is in src/core/, we go up two levels to hit the root.
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Data Directories
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DIR: Path = DATA_DIR / "raw"
    WAREHOUSE_DIR: Path = DATA_DIR / "warehouse"
    ANALYTICS_DIR: Path = DATA_DIR / "analytics"

    # Output Directories
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Specific File Targets
    DB_PATH: Path = WAREHOUSE_DIR / "wiki_traffic.duckdb"
    RAW_PATTERN: str = str(RAW_DIR / "*.gz")
    DASHBOARD_PATH: Path = REPORTS_DIR / "index.html"

    def __post_init__(self):
        """
        Safety check: Ensure output directories exist so the pipeline
        doesn't crash on fresh clones by other engineers.
        """
        for directory in [self.RAW_DIR, self.WAREHOUSE_DIR, self.ANALYTICS_DIR, self.REPORTS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

# Instantiate a global configuration object to be imported across the project
config = ProjectConfig()