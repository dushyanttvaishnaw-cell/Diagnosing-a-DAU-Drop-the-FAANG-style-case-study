-- ============================================================
-- Metric Drop Investigation — SQL Queries
-- Database: data/metrics.db
-- Table: daily_sessions
-- ============================================================

-- STEP 1: Confirm the drop — overall daily DAU
SELECT date, SUM(successful_sessions) AS dau
FROM daily_sessions
GROUP BY date
ORDER BY date;

-- STEP 2: Pre/post comparison by platform
SELECT
    platform,
    ROUND(AVG(CASE WHEN date >= '2025-08-01' AND date < '2025-08-15' THEN successful_sessions END), 0) AS pre_avg_dau,
    ROUND(AVG(CASE WHEN date >= '2025-08-15' AND date < '2025-08-29' THEN successful_sessions END), 0) AS post_avg_dau
FROM (
    SELECT date, platform, SUM(successful_sessions) AS successful_sessions
    FROM daily_sessions GROUP BY date, platform
)
GROUP BY platform;

-- STEP 4: iOS login failure rate by app version (post-period)
SELECT
    app_version,
    SUM(successful_sessions) AS total_successful,
    SUM(failed_login_sessions) AS total_failed,
    ROUND(100.0 * SUM(failed_login_sessions) /
          (SUM(successful_sessions) + SUM(failed_login_sessions)), 1) AS failure_rate_pct
FROM daily_sessions
WHERE platform = 'iOS' AND date >= '2025-08-15'
GROUP BY app_version;

-- STEP 6: Failure rate by country, for the buggy version only — confound check
SELECT
    country,
    SUM(failed_login_sessions) AS failed,
    SUM(successful_sessions) AS successful,
    ROUND(100.0 * SUM(failed_login_sessions) /
          (SUM(failed_login_sessions) + SUM(successful_sessions)), 1) AS failure_rate_pct
FROM daily_sessions
WHERE platform = 'iOS' AND app_version = '4.2' AND date >= '2025-08-15'
GROUP BY country;
