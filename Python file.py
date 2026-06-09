# %% [markdown]

# # Reliabillity & Demand Dynamics in Large Scale User Traffic System



# %% [markdown]

# ## Level 0 — Data Acquisition & Infrastructure Setup



# %% [markdown]

# ### 0.1 Objective

#

# Acquire production-grade, machine-generated behavioral logs representing large-scale consumer platform traffic. The goal is to avoid preprocessed datasets and establish a realistic telemetry environment.



# %% [markdown]

# ### 0.2 Data Source

#

# Provider: Wikimedia Foundation

#

# Dataset: Hourly Wikipedia Pageview Logs

#

# URL: https://dumps.wikimedia.org/other/pageviews/2025/2025-12/

#

# Granularity: Hourly

#

# Format: .gz compressed text files

#

# Time Window: December 2025

#

# These logs represent aggregated hourly page views per project and page.



# %% [markdown]

# ### 0.3 Acquisition Method

#

# Tool: wget (CLI)

#

# Mode: Recursive download

#

# Filter: *.gz

#

# Storage: D:/wiki_pageviews/raw/

#

# Total Files: 742

#

# Total Size (compressed): ~41GB

#

# Download Time: ~6 hours



# %% [markdown]

# Command used:

#

# wget -r -np -nH --cut-dirs=4 -A "*.gz" https://dumps.wikimedia.org/other/pageviews/2025/2025-12/



# %% [markdown]

# ### 0.4 Infrastructure Constraints

#

# RAM: 16GB

#

# OS: Windows

#

# Environment: Python

#

# Disk: 20GB+ available

#

# Full-memory loading is not permitted.

# Processing must be streaming or database-backed.



# %% [markdown]

# ### 0.5 Level 0 Conclusion

#

# Raw telemetry successfully acquired.

#

# We now possess:

#

# Large-scale machine-generated behavioral logs

#

# No preprocessing applied

#

# No schema assumptions verified

#

# No metric definitions imposed

#

# Next step: structural validation before pipeline design.



# %% [markdown]

# ## Level 1 — Data Profiling & Structural Understanding

#

# We now begin executable inspection.

#

# No modeling.

# No interpretation.

# Only structural validation.



# %% [markdown]

# ### 1.1 Inspect Raw Row Structure



# %%

import gzip



file_path = "D:/wiki_pageviews/raw/pageviews-20251201-000000.gz"



with gzip.open(file_path, "rt", encoding="utf-8") as f:

    for i in range(5):

        print(f.readline().strip())



# %% [markdown]

# Purpose

#

# Validate column count

#

# Confirm delimiter

#

# Check encoding stability

#

# Detect malformed patterns



# %% [markdown]

# ### 1.2 Schema Validation



# %%

import gzip



def count_malformed_rows(file_path):

    bad_rows = 0

    with gzip.open(file_path, "rt", encoding="utf-8") as f:

        for line in f:

            if len(line.strip().split(" ")) != 4:

                bad_rows += 1

    return bad_rows



count_malformed_rows(file_path)



# %% [markdown]

# ### 1.3 Row Volume Per Hour



# %%

def count_rows(file_path):

    count = 0

    with gzip.open(file_path, "rt", encoding="utf-8") as f:

        for _ in f:

            count += 1

    return count



count_rows(file_path)



# %% [markdown]

# Run this for:

#

# Beginning of month

#

# Middle

#

# End

#

# We want variability assessment.



# %% [markdown]

# ### 1.4 Unique Project Cardinality



# %% [markdown]

# Why

#

# Project dimension scope affects filtering and partition strategy.



# %%

def count_unique_projects(file_path):

    projects = set()

    with gzip.open(file_path, "rt", encoding="utf-8") as f:

        for line in f:

            project = line.split(" ")[0]

            projects.add(project)

    return len(projects)



count_unique_projects(file_path)



# %% [markdown]

# ### 1.5 Distribution Snapshot (Streaming)



# %% [markdown]

# Why

#

# We expect heavy-tailed behavior.

# If not observed → structural misunderstanding.



# %%

def view_stats(file_path):

    max_views = 0

    min_views = float('inf')

    total = 0

    count = 0

   

    with gzip.open(file_path, "rt", encoding="utf-8") as f:

        for line in f:

            views = int(line.split(" ")[2])

            max_views = max(max_views, views)

            min_views = min(min_views, views)

            total += views

            count += 1

   

    return {

        "max": max_views,

        "min": min_views,

        "mean": total / count

    }



view_stats(file_path)



# %% [markdown]

# #### Conclusion of level 1:

# Structural profiling of December 2025 Wikimedia hourly logs reveals:

#

# Stable 4-field schema

#

# No malformed rows detected

#

# High hourly volume (~6.9M rows/hour)

#

# 1,845 distinct project identifiers

#

# Strong heavy-tailed view distribution (mean ≈ 2.93, max ≈ 115k)



# %% [markdown]

# ## Level 2 — Ingestion Architecture & Canonical Aggregation Layer



# %% [markdown]

# ### 2.1 Objective

#

# Transform 41GB of raw hourly log files into a structured, queryable, and scalable analytical base without:

#

# Loading full month into memory

#

# Decompressing everything blindly

#

# Losing reproducibility

#

# Destroying raw data



# %% [markdown]

# ### 2.2 Design Principles

#

# From Level 1 findings:

#

# ~6.9M rows per hour,

# ~742 hours,

# Heavy-tailed distribution,

# 1,845 project codes,

# 4-field stable schema

#

# This dictates:

#

# Stream processing required

#

# Early aggregation mandatory

#

# Raw logs remain immutable

#

# SQL-backed analytical engine preferred

#

# We will use:

#

# DuckDB (embedded analytical SQL engine)

#

# Reason:

# Reads compressed files directly,

# Columnar execution,

# Handles billions of rows via streaming,

# No server setup



# %% [markdown]

# ### 2.3 Target Architecture



# %% [markdown]

# We define 3 layers:

#

# raw/           → untouched .gz logs

#

# warehouse/     → structured DuckDB database

#

# analytics/     → derived analytical tables

#

# We are now building the warehouse layer.



# %% [markdown]

# ### 2.4 Installation (One-Time)



# %%

# !pip install duckdb



# %% [markdown]

# ### 2.5 Create Local Analytical Database



# %%

import duckdb

con = duckdb.connect("D:/wiki_pageviews/warehouse/wiki_traffic.duckdb")





# %% [markdown]

# This creates a persistent analytical database.

#

# Not temporary.

# Reproducible.

# Professional.



# %% [markdown]

# ### 2.6 Register Raw Logs (No Full Load)

# DuckDB can read .gz files directly.

#

# We define a virtual table over all December logs:



# %%

con.execute("""

CREATE OR REPLACE VIEW raw_pageviews AS

SELECT *

FROM read_csv(

    'D:/wiki_pageviews/raw/*.gz',

    delim=' ',

    header=False,

    columns={

        'project': 'VARCHAR',

        'page_title': 'VARCHAR',

        'views': 'BIGINT',

        'bytes': 'BIGINT'

    },

    quote='',

    escape='',

    ignore_errors=true,

    compression='gzip'

);

""")



# %% [markdown]

# Important:

#

# No data copied yet,

# No decompression to disk,

# Lazy reading,

# Schema explicitly defined



# %% [markdown]

# Why Explicit Column Types?

#

# Because:

#

# Auto-inference can fail at scale,

# Explicit types = deterministic pipeline,

# BIGINT prevents overflow risk,

# We design for billions, not thousands.

#

# Why ignore_errors = true? Because in billion scale data, one malformed row can cause serious issues in execution.



# %% [markdown]

# ### 2.7 First Controlled Aggregation (Critical)



# %% [markdown]

# We do NOT materialize raw data.

#

# We immediately aggregate to reduce dimensionality.



# %%

con.execute("""

CREATE TABLE hourly_project_traffic AS

SELECT

    project,

    SUM(views) AS total_views,

    SUM(bytes) AS total_bytes

FROM raw_pageviews

GROUP BY project;

""")



# %% [markdown]

# ### 2.8 Why We Aggregate Early

#

# Because raw logs are:

#

# Event-level,

# Extremely granular,

# High cardinality,

#

# Aggregated metrics:

# Reduce storage,

# Enable fast querying,

# Preserve analytical meaning,

# Mirror warehouse design

#



# %% [markdown]

# ### 2.9 Validate Aggregation Integrity



# %%

con.execute("""

SELECT COUNT(*) FROM hourly_project_traffic;

""").fetchall()



# %% [markdown]

# ### 2.10 Performance Notes

#

# This query may take time.

# That is fine.

# Do not interrupt.



# %% [markdown]

# ## Level 3 — Canonical Metric Construction (Measurement Layer)



# %% [markdown]

# ### 3.1 Objective

#

# Construct stable, reproducible platform-level metrics derived from raw telemetry.

#

# We are transforming: Aggregated traffic counts

#

# into

#

# Analytical signals suitable for reliability & volatility assessment.

#

# Metrics must be:

# Deterministic,

# Reproducible,

# Efficiently queryable,

# Architecturally clean



# %% [markdown]

# ### 3.2 Metric Philosophy

#

# From Level 1:

#

# Heavy-tailed distribution:

# 1,845 project codes,

# ~6.9M rows/hour,

# Extreme skew.

#

# Therefore, naive totals are insufficient.

# We build three metric categories:

#

# Volume Metrics,

# Concentration Metrics,

# Structural Breadth Metrics,

# Each supports reliability analysis later.



# %% [markdown]

# ### 3.3 Volume Metrics (Global Demand)



# %%

con.execute("""

CREATE TABLE monthly_global_metrics AS

SELECT

    SUM(total_views) AS total_views,

    SUM(total_bytes) AS total_bytes

FROM hourly_project_traffic;

""")



# %%

con.execute("SELECT * FROM monthly_global_metrics;").fetchall()



# %% [markdown]

# Purpose:

#

# Establish total scale

#

# Validate aggregation correctness



# %% [markdown]

# ### 3.4 Project-Level Distribution Snapshot

#

# We need ranking structure.



# %%

con.execute("""

CREATE TABLE project_distribution AS

SELECT

    project,

    total_views,

    total_bytes,

    total_views * 1.0 /

        SUM(total_views) OVER () AS view_share

FROM hourly_project_traffic

ORDER BY total_views DESC;

""")



# %% [markdown]

# This creates:

#

# Absolute volume

#

# Relative share (critical)

#

# Ordered distribution



# %% [markdown]

# ### 3.5 Concentration Metrics

#

# Heavy-tailed data implies dominance by few projects.

#

# We compute Top-N dominance.



# %%

con.execute("""

CREATE TABLE concentration_metrics AS

SELECT

    SUM(CASE WHEN rn <= 10 THEN total_views ELSE 0 END) * 1.0 /

        SUM(total_views) AS top_10_share,

    SUM(CASE WHEN rn <= 50 THEN total_views ELSE 0 END) * 1.0 /

        SUM(total_views) AS top_50_share

FROM (

    SELECT

        total_views,

        ROW_NUMBER() OVER (ORDER BY total_views DESC) AS rn

    FROM hourly_project_traffic

) t;

""")



# %% [markdown]

# Why:

#

# Quantifies dominance

#

# Indicates aggregation fragility

#

# Detects metric instability risk

#

# ### 3.6 Structural Breadth Metrics

#

# We evaluate long-tail depth.



# %%

con.execute("""

CREATE TABLE structural_breadth AS

SELECT

    COUNT(*) AS total_projects,

    SUM(CASE WHEN total_views < 1000 THEN 1 ELSE 0 END) AS low_volume_projects,

    SUM(CASE WHEN total_views < 100 THEN 1 ELSE 0 END) AS micro_projects

FROM hourly_project_traffic;

""")



# %% [markdown]

# Why:

#

# Measures ecosystem breadth

#

# Indicates sensitivity to filtering

#

# Assesses fragmentation

#

# ### 3.7 Validate Outputs

#

# Retrieve:



# %%

con.execute("SELECT * FROM concentration_metrics;").fetchall()

con.execute("SELECT * FROM structural_breadth;").fetchall()



# %% [markdown]

# Record:

# Top 10 share

# Top 50 share

# Percent micro projects

#

#

#



# %% [markdown]

# ### Short Analytical Interpretation of level 2 and 3

#

# Massive scale: ~15B monthly views

#

# High but manageable project diversity (2127)

#

# Long-tail exists, but not extreme at project-level

#

# Bytes metric unusable

#

# Data structurally coherent



# %% [markdown]

# ## Extra Review Addition (export tables)



# %%

# Perquet files for analytical review

con.execute("""

COPY project_volatility

TO 'D:/wiki_pageviews/analytics/project_volatility.parquet'

(FORMAT PARQUET);

""")



# %%

con.execute("""

COPY monthly_global_metrics

TO 'D:/wiki_pageviews/analytics/monthly_global_metrics.parquet'

(FORMAT PARQUET);

""")



# %%

# Perquet files for analytical review

con.execute("""

COPY hourly_global_views

TO 'D:/wiki_pageviews/analytics/hourly_global_views.parquet'

(FORMAT PARQUET);

""")



# %%

con.execute("""

COPY concentration_metrics

TO 'D:/wiki_pageviews/analytics/concentration_metrics.parquet'

(FORMAT PARQUET);

""")



# %%

# Perquet files for analytical review

con.execute("""

COPY project_distribution

TO 'D:/wiki_pageviews/analytics/project_distribution.parquet'

(FORMAT PARQUET);

""")



# %%

con.execute("""

COPY structural_breadth

TO 'D:/wiki_pageviews/analytics/structural_breadth.parquet'

(FORMAT PARQUET);

""")



# %%

# Project Distribution CSV sample for fast human varification

con.execute("""

COPY (

    SELECT *

    FROM project_distribution

    ORDER BY total_views DESC

    LIMIT 50

)

TO 'D:/wiki_pageviews/analytics/project_distribution_sample.csv'

WITH (HEADER, DELIMITER ',');

""")



# %% [markdown]

# Data Artifacts

#

# analytics/project_volatility.parquet

#     Full table of volatility metrics across all 2,127 projects.

#

# analytics/project_distribution_sample.csv

#     Top 50 projects by traffic (human-readable preview).

#

# analytics/hourly_global_views.parquet

#     Hour-level global traffic metrics used for volatility analysis.



# %% [markdown]

# ## Level 4 — Temporal Stability & Volatility Analysis



# %% [markdown]

# How does traffic behave over time?

# This is where the project becomes intellectually serious.

#

# #### Step 1 — We Need Hour-Level Aggregation

#

# Right now, hourly_project_traffic is monthly aggregated.

# That’s insufficient for volatility.

# We need:

#

# project | hour | total_views

#

# So we rebuild canonical aggregation properly.



# %% [markdown]

# ### 4.1 Build Hourly Aggregated Table

#

# We must extract hour from filename.

#

# DuckDB can read filename using filename=true.

#

# Rebuild view properly:



# %%

con.execute("""

CREATE OR REPLACE VIEW raw_pageviews_with_file AS

SELECT *,

       filename

FROM read_csv(

    'D:/wiki_pageviews/raw/*.gz',

    delim=' ',

    header=False,

    columns={

        'project': 'VARCHAR',

        'page_title': 'VARCHAR',

        'views': 'BIGINT',

        'bytes': 'BIGINT'

    },

    quote='',

    escape='',

    compression='gzip',

    filename=true

);

""")



# %%

# Now extract hour:



con.execute("""

CREATE TABLE hourly_project_views AS

SELECT

    project,

    SUBSTR(filename, LENGTH(filename)-15, 10) AS hour_id,

    SUM(views) AS total_views

FROM raw_pageviews_with_file

GROUP BY project, hour_id;

""")



# %% [markdown]

# This gives:

#

# Project, Hour ,Views

#

# This is your temporal backbone.



# %% [markdown]

# #### Step 2 — Global Hourly Stability

#

# Now compute total views per hour:



# %%

con.execute("""

CREATE TABLE hourly_global_views AS

SELECT

    hour_id,

    SUM(total_views) AS global_views

FROM hourly_project_views

GROUP BY hour_id

ORDER BY hour_id;

""")



# %% [markdown]

# #### Step 3 — Volatility Metrics

#

# Now compute:

#

# Mean hourly views

#

# Std deviation

#

# Coefficient of variation (CV)



# %%

con.execute("""

SELECT

    AVG(global_views) AS mean_views,

    STDDEV(global_views) AS std_views,

    STDDEV(global_views) / AVG(global_views) AS coeff_variation

FROM hourly_global_views;

""").fetchall()



# %% [markdown]

# **How To Think About This**

#

# Low CV → Stable demand system

#

# High CV → Spike-driven system

#

# Extremely high CV → Aggregation fragile

#

# This becomes:

#

# Measurement reliability signal

#

# #### Step 4 — Project-Level Volatility

#

# Now evaluate volatility per project:



# %%

con.execute("""

CREATE TABLE project_volatility AS

SELECT

    project,

    AVG(total_views) AS mean_views,

    STDDEV(total_views) AS std_views,

    STDDEV(total_views) / NULLIF(AVG(total_views),0) AS cv

FROM hourly_project_views

GROUP BY project;

""")



# %% [markdown]

# ### 4.2 Global Traffic Stability

#

# We computed:

#

# Mean hourly views ≈ 20,343,470

# Std deviation ≈ 3,144,078

# Coefficient of variation ≈ 0.1545

# Interpretation (Concise)

#

# CV ≈ 0.15 → Moderate fluctuation

#

# System not spike-dominated.

# Aggregated traffic relatively stable.

# No extreme hour-level instability

#

# **Professional Statement:**

# Global demand exhibits controlled temporal variability, with hourly fluctuations within ~15% of mean volume. This suggests stable aggregate system behavior over the observed month.



# %% [markdown]

# ### 4.3 Project-Level Volatility Structure



# %%

con.execute("""

SELECT

    MIN(cv),

    MAX(cv),

    AVG(cv)

FROM project_volatility;

""").fetchall()



# %% [markdown]

# This gives:

#

# Lowest volatility project,

# Most volatile project,

# Average volatility across all 2127 projects

#

# This step answers:

#

# Is instability hidden inside subsegments?



# %% [markdown]

# Minimum CV = 0.0

#

# Maximum CV ≈ 9.50

#

# Average CV ≈ 1.04

#

# What This Means

#

# 1️⃣ Min CV = 0.0

# Some projects have constant traffic across hours.

# Likely extremely low-volume or flat-behavior segments.

#

# 2️⃣ Max CV ≈ 9.5

# This is extremely volatile.

# Std dev is ~9.5× mean.

# These projects are spike-driven.

#

# 3️⃣ Average CV ≈ 1.04

# This is critical.

#

# At project level:

#

# Typical project is highly unstable.

#

# Std dev roughly equal to mean.

#

# Many projects experience significant hour-level variability.



# %% [markdown]

# ### 4.4 Cross-Sectional Stability Question

#

# Once you provide those 3 numbers, we will evaluate:

#

# Are large projects stable and small ones unstable?

#

# Is volatility inversely related to size?

#

# Does the long tail distort interpretation?

#

# This connects to reliability analysis.

#



# %% [markdown]

# Step 1 — Build Size vs Volatility Table

#

# We have:

#

# hourly_project_traffic → total_views

#

# project_volatility → CV

#

# Combine them.



# %%

df = con.execute("""

SELECT

    p.project,

    p.total_views,

    v.cv

FROM hourly_project_traffic p

JOIN project_volatility v USING(project)

""").fetchdf()



# %% [markdown]

# Step 2 — Correlation Test

#

# We measure correlation between size and volatility.



# %%

df[['total_views','cv']].corr()



# %% [markdown]

# **Negative correlation → bigger projects more stable**



# %% [markdown]

# Step 3 — Group Stability by Size

#

# Segment projects into size tiers.



# %%

df['size_bucket'] = pd.qcut(df['total_views'], 5, labels=[

    'Very Small','Small','Medium','Large','Very Large'

])



df.groupby('size_bucket')['cv'].mean()



# %% [markdown]

# #### Level 4.4 — Cross-Sectional Stability Interpretation

# Interpretation (Short, Honest)

# 1) Relationship Exists but Is Weak

#

# Correlation ≈ −0.05 → very weak inverse relationship.

#

# Size explains very little of volatility variation.

#

# 2) Very Large Projects Are Clearly More Stable

#

# Very Large CV = 0.73 (lowest group).

#

# This confirms the stable “core demand” hypothesis.

#

# 3) Mid-Tier Projects Are Not Fully Stable

#

# Large bucket CV ≈ 1.13, slightly higher than Medium.

#

# Some large projects still experience spike-driven traffic.

#

# 4) Long Tail Still the Most Volatile

#

# Very Small CV ≈ 1.28, highest volatility.

#

# Instability concentrated in low-traffic segments.

# #### Level 4.4 Conclusion (Short Professional Form)

#

# Cross-sectional analysis shows that volatility decreases only modestly with project size (correlation ≈ −0.05). While the largest projects exhibit significantly lower volatility, mid-tier segments remain moderately unstable. Overall system stability therefore arises primarily from the dominance of large, stable projects rather than a universal size-volatility relationship.



# %% [markdown]

#

# ### 4.5 Level 4 Conclusion

#

# Global traffic appears stable.

#

# Individual projects are highly volatile.

#

# Some projects are extreme spike-driven (CV > 9).

#

# Measurement reliability depends on aggregation level.

#

# Aggregated metrics may conceal subsegment instability.



# %% [markdown]

# ## Level 5 — Decision & Measurement Risk Framing



# %% [markdown]

# ### 5.1 Objective

#

# Translate Level 4 stability findings into decision-relevant implications for:

#

# Executive leadership,

# Product analytics,

# Engineering monitoring,

# Growth strategy

#

# We are not predicting.We are evaluating measurement reliability risk.

#

# ### 5.2 Structural Facts Established So Far

#

# From Levels 1–4:

#

# ~15B total monthly views.|2,127 distinct projects.|Global CV ≈ 0.15 (stable).|Average project-level CV ≈ 1.04 (high volatility).|Max project CV ≈ 9.5 (extreme instability).|Heavy-tailed distribution at page level.

#

# Bytes metric unusable.

#

# These are not opinions.These are structural properties.

#

# ### 5.3 Decision Risk Layer 1 — Aggregation Illusion Risk

# **Observation**

#

# Global metric is stable.

# Project-level metrics are highly unstable.

#

# **Risk**

#

# Leadership observing only global traffic could conclude:

# *“System demand is structurally stable.”*

#

# But underlying components:

# Experience large fluctuations.

# May contain localized collapses.

# May contain spike-driven distortions.

#

# This is a classic:

# Aggregation Masking Risk

# Macro stability does not guarantee micro reliability.

#

# ### 5.4 Decision Risk Layer 2 — Spike Dominance Risk

#

# Max CV ≈ 9.5 implies:

#

# Some projects are driven by rare, high-magnitude spikes.

#

# Risk implications:

# Short-term traffic surges may distort trend lines.

# Event-driven spikes may be misinterpreted as structural growth.

# Resource allocation decisions may react to noise.

#

# This matters for:

#

# Capacity planning,Growth analysis,KPI monitoring

#

# ### 5.5 Decision Risk Layer 3 — Long-Tail Monitoring Cost

#

# 2,127 projects.|

# Average project CV ≈ 1.04.

#

# This implies:

#

# Majority of segments are unstable.Monitoring all segments equally is inefficient.Stability is size-dependent (likely).

#

# Operational question:

#

# Should monitoring weight volatility by traffic share?

#

#

# ### 5.6 Risk Quantification Enhancement (Optional but Powerful)

#

# To elevate this to professional level, we quantify:

#

# What fraction of traffic comes from high-volatility projects?

#

# Define:

# High volatility = CV > 1

#



# %%

con.execute("""

SELECT

    SUM(total_views) * 1.0 /

    (SELECT SUM(total_views) FROM hourly_project_traffic)

FROM hourly_project_traffic

JOIN project_volatility USING(project)

WHERE cv > 1;

""").fetchall()



# %% [markdown]

# ### Level 5 — Updated Conclusion

#

# Aggregate traffic stability (CV ~0.15) is structurally supported by the fact that high-volatility segments represent only ~2.5% of total traffic. While micro-level instability exists, it does not materially distort global metrics. Decision-making based on aggregate demand is therefore reasonably reliable, though segment-level monitoring remains necessary.



# %% [markdown]

# ## Level 6 — Decision Error Simulation (Noise vs Structural Change)



# %% [markdown]

# ### 6.1 Objective

#

# Quantify how much apparent month-over-month “growth” could be explained purely by natural volatility.

#

# We are answering:

#

# If leadership sees +X% growth next month, how much of that could simply be statistical noise?

#

# This is not forecasting.

# This is noise band estimation.

#

# ### 6.2 Conceptual Framing

#

# From Level 4:

#

# Mean hourly global views ≈ 20.34M

# Std ≈ 3.14M

# CV ≈ 0.154

#

# We assume:

# Hourly views fluctuate around a stable mean.

#

# We estimate:

# What percent fluctuation is “normal”?

#

# ### 6.3 Compute 95% Noise Band (Hourly)

#

# Formula:

# Upper=μ+1.96σ  Lower=μ−1.96σ

#



# %%

mean = 20343470.12162162

std = 3144077.8587346924



upper = mean + 1.96 * std

lower = mean - 1.96 * std



upper, lower



# %% [markdown]

# ### 6.4 Convert to Percentage Noise Band



# %%

upper_pct = (upper - mean) / mean

lower_pct = (mean - lower) / mean



upper_pct, lower_pct



# %% [markdown]

# This tells:

#

# Typical hourly variation in percentage terms.

#

# Expected result ≈ ±30%?

# No — check carefully.

#

# Since CV ≈ 0.15,

#

# 1.96 × 0.15 ≈ 0.29

#

# So noise band ≈ ±29%.

#

# Important nuance:

#

# This is hourly volatility, not monthly average.

#

# ### 6.5 Monthly Aggregation Effect

#

# Because there are ~742 hours:

#

# Variance of monthly mean reduces by:

#

# σ(monthly)=σ/Sqrt(742)

#   ​

#



# %%

import math



monthly_std = std / math.sqrt(742)

monthly_cv = monthly_std / mean



monthly_std, monthly_cv



# %% [markdown]

# ### 6.6 Interpretation

#

# If monthly CV ≈ 0.0055:

#

# Then natural month-level fluctuation ≈ ±1% (roughly 2× CV).

#

# Meaning:

#

# If leadership sees +3% growth:

#

# That likely exceeds noise band.Could represent structural change.

#

# If they see +0.5%:

#

# Probably statistical fluctuation.This is professional decision conditioning.

#

# ### 6.7 Level 6 Conclusion

#

# Hourly system volatility is moderate (~15%),

# but aggregation across 742 hours dramatically reduces month-level noise to <1%.

#

# Therefore:

# Month-over-month shifts exceeding ~1–2% are unlikely to be explained purely by random hourly fluctuation.

# Aggregate demand is statistically stable at monthly resolution.

#



# %% [markdown]

# ## Level 7 — Multi-Stakeholder Translation



# %% [markdown]

# ### 7.1 Executive (CEO / CIO)

#

# ~15B monthly views.

#

# Global demand stable (CV ~15% hourly).

#

# Monthly noise band <1%.

#

# Growth above 2% likely structural.

#

# Monitoring should track persistent deviation, not hourly spikes.

#

# Key message:

# Aggregate metrics are reliable at monthly level.

#

# ### 7.2 Product Analytics

#

# Segment volatility high (avg CV ~1).

#

# Long-tail instability exists.

#

# Aggregate smooths instability.

#

# Growth signals must be validated per segment.

#

# Consider volatility-weighted metrics.

#

# ### 7.3 Engineering / Infrastructure

#

# System-wide traffic stable.

#

# Localized spikes exist (CV up to 9).

#

# Capacity planning safe at macro scale.

#

# Burst handling required for specific segments.

#

# ### 7.4 Growth / Strategy

#

# Do not react to short-lived spikes.

#

# Validate persistence before scaling investment.

#

# 2% monthly movement is meaningful.

#

# Sub-1% movement likely noise.



# %% [markdown]

# ## Level 8 — Production Monitoring & Alert Architecture

# ### 8.1 Objective

#

# Design a monitoring system that operationalizes insights from Levels 1–6.

#

# We are answering: If this were a live platform, how would we detect instability, structural shifts, and anomalies?

#

# ### 8.2 Monitoring Philosophy

#

# From earlier findings:

# Hourly volatility exists (CV ~0.15)|

# Monthly volatility very low (<1%)

#

# Micro-segments unstable|

# Macro stable

#

# Therefore, monitoring must be:

#

# Multi-resolution|

# Volatility-aware|

# Aggregation-aware|

# Not naive threshold-based.

#

# ### 8.3 Monitoring Layers

# Layer 1 — Global Stability Monitor

#

# Metric:

#

# hourly_global_views

#

# Monitor:

#

# Rolling mean (24-hour window)

#

# Rolling std

#

# Z-score = (current - rolling_mean) / rolling_std

#

# Alert rule:

#

# |Z| > 3 → anomaly candidate

#

# Persistent |Z| > 2 over 6+ hours → structural drift

#

# This respects known volatility.

#

# Layer 2 — Segment-Level Risk Monitor

#

# For each project:

#

# Monitor:

#

# Rolling CV

#

# Traffic share change

#

# Relative volatility shift

#

# Alert conditions:

#

# CV increase > 50% baseline

#

# Traffic share jump > 2σ

#

# This captures spike-driven anomalies.

#

# Layer 3 — Structural Change Monitor (Monthly)

#

# Metric:

#

# Month-level mean

#

# Compare MoM delta

#

# Alert threshold:

#

# Change > 2% → investigate

#

# Change > 5% → likely structural

#

# Derived from Level 6 noise modeling.

#

# ### 8.4 Production Architecture Sketch

#

# If deployed:

#

# Raw logs → ingestion service (DuckDB / warehouse)

#

# Hourly aggregation job (scheduled)

#

# Metrics materialized

#

# Monitoring queries executed

#

# Alerts pushed to dashboard / Slack / email

#

# Compute cost: low

# Memory cost: controlled

# No full raw scans repeatedly

#

# ### 8.5 Level 8 Conclusion

#

# Monitoring design aligns with:

#

# Empirical volatility structure

#

# Aggregation smoothing effect

#

# Segment instability characteristics

#



# %% [markdown]

# ## Level 9 — Documentation Consolidation (Executive-Ready)

#

# Now we convert project into a tight, non-childish professional structure.

#

# Below is the final project outline.

#

# ### 9.1 Executive Summary

#

# This project analyzes 41GB of Wikimedia hourly traffic logs (~15B monthly views) to evaluate measurement reliability in large-scale consumer platforms. Structural profiling, volatility analysis, and decision-noise simulation reveal that while segment-level traffic is highly unstable, aggregate demand remains statistically stable with month-level noise below 1%. A monitoring architecture is proposed to distinguish structural growth from volatility-driven fluctuations.

#

# ### 9.2 Problem Framing

#

# Evaluate reliability of aggregate traffic metrics.

#

# Assess whether volatility distorts decision signals.

#

# Quantify statistical noise band.

#

# Design monitoring thresholds grounded in empirical behavior.

#

# ### 9.3 Data Understanding

#

# 742 hourly logs

#

# ~6.9M rows/hour

#

# 2,127 projects

#

# Heavy-tailed page distribution

#

# Stable 4-field schema

#

# 15B total monthly views

#

# ### 9.4 Methodology

#

# Streaming ingestion via DuckDB

#

# Early aggregation

#

# Hour-level temporal modeling

#

# CV-based volatility measurement

#

# Noise band estimation via variance reduction

#

# Risk conditioning by traffic share

#

# ### 9.5 Results

#

# Global hourly CV ≈ 0.15

#

# Project-level avg CV ≈ 1.04

#

# High-volatility segments represent ~2.5% of traffic

#

# Monthly noise band <1%

#

# Aggregate metrics statistically reliable

#

# ### 9.6 Production Notes

#

# No full-memory ingestion

#

# Explicit schema control

#

# Compression-aware parsing

#

# Multi-layer monitoring design

#

# Alert thresholds grounded in empirical volatility



# %% [markdown]

# ##  Level 10 — Visualization Layer (Implementation)

#

# All plots should use aggregated tables, never raw logs.



# %%

import matplotlib.pyplot as plt

import pandas as pd



# %% [markdown]

# ### 10.1 Hourly Global Traffic Time Series



# %%

df = con.execute("""

SELECT hour_id, global_views

FROM hourly_global_views

ORDER BY hour_id

""").fetchdf()



plt.figure(figsize=(12,5))

plt.plot(df['hour_id'], df['global_views'])

plt.title("Hourly Global Traffic")

plt.xlabel("Hour")

plt.ylabel("Views")

plt.xticks(rotation=90)

plt.tight_layout()

plt.show()



# %% [markdown]

# ### 10.2 Distribution of Project Volatility



# %%

df = con.execute("""

SELECT cv

FROM project_volatility

""").fetchdf()



plt.figure(figsize=(8,5))

plt.hist(df['cv'], bins=50)

plt.title("Distribution of Project Volatility (CV)")

plt.xlabel("Coefficient of Variation")

plt.ylabel("Number of Projects")

plt.show()



# %% [markdown]

# ### 10.4 Traffic Concentrtation Curve



# %%

df = con.execute("""

SELECT project, total_views

FROM hourly_project_traffic

ORDER BY total_views DESC

""").fetchdf()



df['cum_views'] = df['total_views'].cumsum()

df['cum_share'] = df['cum_views'] / df['total_views'].sum()



plt.figure(figsize=(8,5))

plt.plot(range(len(df)), df['cum_share'])

plt.title("Cumulative Traffic Share by Project Rank")

plt.xlabel("Project Rank")

plt.ylabel("Cumulative Share")

plt.show()

# %%

