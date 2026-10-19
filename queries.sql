-- ==============================================================================
-- SHIPTIVITAS MODULE 3: SQL QUERIES & DATA ANALYSIS
-- ==============================================================================
-- Feature Release Date: 2018-06-02 (Kanban Board Release)
-- Target Metrics: Daily Active Users (DAU) & Card Status Velocity
-- ==============================================================================


-- ==============================================================================
-- PART 1: Daily Average Active Users Before and After the Feature Change
-- ==============================================================================

-- 1A. Aggregated Comparison: Calculates the daily average active users before 
--     and after the Kanban feature launch date (2018-06-02), including total active days,
--     minimum DAU, and maximum DAU observed in each period.
WITH daily_user_counts AS (
    SELECT 
        date(login_timestamp, 'unixepoch') AS activity_date,
        COUNT(DISTINCT user_id) AS daily_active_users,
        CASE 
            WHEN date(login_timestamp, 'unixepoch') < '2018-06-02' THEN 'Before Feature (Pre-2018-06-02)'
            ELSE 'After Feature (Post-2018-06-02)'
        END AS feature_period
    FROM login_history
    GROUP BY activity_date
)
SELECT 
    feature_period,
    COUNT(activity_date) AS total_days,
    ROUND(AVG(daily_active_users), 2) AS avg_daily_active_users,
    MIN(daily_active_users) AS min_dau,
    MAX(daily_active_users) AS max_dau
FROM daily_user_counts
GROUP BY feature_period
ORDER BY feature_period DESC;


-- 1B. Side-by-Side Summary Pivot (Direct Scalar Comparison with % Growth)
SELECT 
    ROUND(AVG(CASE WHEN activity_date < '2018-06-02' THEN daily_dau END), 2) AS avg_dau_before_kanban,
    ROUND(AVG(CASE WHEN activity_date >= '2018-06-02' THEN daily_dau END), 2) AS avg_dau_after_kanban,
    ROUND(
        ((AVG(CASE WHEN activity_date >= '2018-06-02' THEN daily_dau END) - 
          AVG(CASE WHEN activity_date < '2018-06-02' THEN daily_dau END)) / 
         AVG(CASE WHEN activity_date < '2018-06-02' THEN daily_dau END)) * 100, 
        2
    ) AS pct_dau_growth
FROM (
    SELECT 
        date(login_timestamp, 'unixepoch') AS activity_date,
        COUNT(DISTINCT user_id) AS daily_dau
    FROM login_history
    GROUP BY activity_date
);


-- 1C. Daily Active Users Time Series (Mapping DAU Day-by-Day Before and After)
SELECT 
    date(login_timestamp, 'unixepoch') AS activity_date,
    COUNT(DISTINCT user_id) AS daily_active_users,
    CASE 
        WHEN date(login_timestamp, 'unixepoch') < '2018-06-02' THEN 'Before Kanban'
        ELSE 'After Kanban'
    END AS period
FROM login_history
GROUP BY activity_date
ORDER BY activity_date ASC;



-- ==============================================================================
-- PART 2: Number of Status Changes by Card Daily
-- ==============================================================================

-- 2A. Daily Status Changes by Card:
--     Calculates the number of status changes each card underwent on each individual day.
SELECT 
    date(timestamp, 'unixepoch') AS change_date,
    cardID,
    COUNT(*) AS daily_status_changes
FROM card_change_history
GROUP BY change_date, cardID
ORDER BY change_date ASC, daily_status_changes DESC;


-- 2B. Daily Aggregate Status Changes Across All Cards (Daily System Velocity):
--     Calculates total status change events and unique cards moved on each calendar day.
SELECT 
    date(timestamp, 'unixepoch') AS change_date,
    COUNT(*) AS total_status_changes,
    COUNT(DISTINCT cardID) AS unique_cards_moved
FROM card_change_history
GROUP BY change_date
ORDER BY change_date ASC;


-- 2C. Total Status Changes by Card (Cumulative Lifetime Card Velocity):
--     Calculates total status transitions per card, joined with card name and current status.
SELECT 
    c.id AS card_id,
    c.name AS card_name,
    c.status AS current_status,
    c.priority AS current_priority,
    COUNT(cch.id) AS total_status_changes
FROM card c
LEFT JOIN card_change_history cch ON c.id = cch.cardID
GROUP BY c.id, c.name, c.status, c.priority
ORDER BY total_status_changes DESC, c.id ASC;
