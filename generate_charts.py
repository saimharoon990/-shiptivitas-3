import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Set style for clean, modern look
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['font.size'] = 11

conn = sqlite3.connect('shiptivity.db')

# -------------------------------------------------------------
# 1. DAILY ACTIVE USERS (DAU) BEFORE VS AFTER KANBAN
# -------------------------------------------------------------
query_dau = """
SELECT 
    date(login_timestamp, 'unixepoch') AS activity_date,
    COUNT(DISTINCT user_id) AS dau
FROM login_history
GROUP BY activity_date
ORDER BY activity_date;
"""
df_dau = pd.read_sql_query(query_dau, conn)
df_dau['activity_date'] = pd.to_datetime(df_dau['activity_date'])
df_dau['rolling_7d'] = df_dau['dau'].rolling(window=7, min_periods=1).mean()

split_date = pd.to_datetime('2018-06-02')

df_before = df_dau[df_dau['activity_date'] < split_date]
df_after = df_dau[df_dau['activity_date'] >= split_date]

avg_before = df_before['dau'].mean()
avg_after = df_after['dau'].mean()

fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

# Background shading
ax.axvspan(df_before['activity_date'].min(), split_date, color='#fee2e2', alpha=0.35, label='Pre-Kanban Period')
ax.axvspan(split_date, df_after['activity_date'].max(), color='#dcfce7', alpha=0.35, label='Post-Kanban Period')

# Raw DAU scatter and line
ax.plot(df_dau['activity_date'], df_dau['dau'], color='#94a3b8', alpha=0.45, linewidth=1, label='Daily Active Users (Actual)')
ax.plot(df_before['activity_date'], df_before['rolling_7d'], color='#dc2626', linewidth=2.5, label='7-Day Rolling Avg (Pre-Kanban)')
ax.plot(df_after['activity_date'], df_after['rolling_7d'], color='#16a34a', linewidth=2.5, label='7-Day Rolling Avg (Post-Kanban)')

# Release line
ax.axvline(split_date, color='#2563eb', linestyle='--', linewidth=2.2, label='Kanban Board Release (2018-06-02)')

# Average horizontal reference lines
ax.hlines(avg_before, df_before['activity_date'].min(), split_date, colors='#b91c1c', linestyles=':', linewidth=2)
ax.hlines(avg_after, split_date, df_after['activity_date'].max(), colors='#15803d', linestyles=':', linewidth=2)

# Text annotations
ax.annotate(f'Pre-Release Avg: {avg_before:.2f} DAU',
            xy=(pd.to_datetime('2018-04-01'), avg_before),
            xytext=(pd.to_datetime('2018-03-01'), avg_before + 3.5),
            arrowprops=dict(facecolor='#b91c1c', shrink=0.08, width=1.5, headwidth=6),
            fontsize=11, fontweight='bold', color='#b91c1c',
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#b91c1c", lw=1.5))

ax.annotate(f'Post-Release Avg: {avg_after:.2f} DAU\n(+224.9% Increase)',
            xy=(pd.to_datetime('2018-09-15'), avg_after),
            xytext=(pd.to_datetime('2018-08-01'), avg_after + 4.5),
            arrowprops=dict(facecolor='#15803d', shrink=0.08, width=1.5, headwidth=6),
            fontsize=11, fontweight='bold', color='#15803d',
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#15803d", lw=1.5))

ax.set_title('Shiptivity: Daily Active Users (DAU) Before vs. After Kanban Release', fontsize=16, fontweight='bold', pad=18)
ax.set_xlabel('Date', fontsize=12, fontweight='bold', labelpad=10)
ax.set_ylabel('Active Users per Day', fontsize=12, fontweight='bold', labelpad=10)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.xticks(rotation=45)
ax.set_ylim(0, 26)
ax.legend(loc='upper left', frameon=True, framealpha=0.9, facecolor='white')
plt.tight_layout()
plt.savefig('dau_before_after.png', dpi=300)
plt.close()
print("Saved dau_before_after.png successfully!")

# -------------------------------------------------------------
# 2. STATUS CHANGES BY CARD
# -------------------------------------------------------------
# Query A: Daily status changes over time
query_daily_changes = """
SELECT 
    date(timestamp, 'unixepoch') AS change_date,
    COUNT(*) AS total_changes,
    COUNT(DISTINCT cardID) AS unique_cards
FROM card_change_history
GROUP BY change_date
ORDER BY change_date;
"""
df_daily_changes = pd.read_sql_query(query_daily_changes, conn)
df_daily_changes['change_date'] = pd.to_datetime(df_daily_changes['change_date'])
df_daily_changes['rolling_7d'] = df_daily_changes['total_changes'].rolling(window=7, min_periods=1).mean()

# Query B: Status changes per card
query_card_changes = """
SELECT 
    cardID,
    COUNT(*) AS total_changes,
    SUM(CASE WHEN oldStatus IS NOT NULL AND oldStatus != '' THEN 1 ELSE 0 END) AS status_transitions
FROM card_change_history
GROUP BY cardID
ORDER BY total_changes DESC;
"""
df_card_changes = pd.read_sql_query(query_card_changes, conn)

# Query C: Status transitions breakdown
query_transitions = """
SELECT 
    COALESCE(oldStatus, '(New Card)') || ' -> ' || newStatus AS transition,
    COUNT(*) AS count
FROM card_change_history
GROUP BY oldStatus, newStatus
ORDER BY count DESC;
"""
df_trans = pd.read_sql_query(query_transitions, conn)

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), dpi=300)

# Subplot 1: Daily status changes time series
ax1.bar(df_daily_changes['change_date'], df_daily_changes['total_changes'], color='#60a5fa', width=1.2, alpha=0.7, label='Daily Status Changes')
ax1.plot(df_daily_changes['change_date'], df_daily_changes['rolling_7d'], color='#1d4ed8', linewidth=2.2, label='7-Day Moving Avg')
ax1.set_title('A. Daily Status Changes Over Time', fontsize=13, fontweight='bold')
ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
ax1.set_ylabel('Status Changes per Day', fontsize=11, fontweight='bold')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax1.legend(loc='upper right')

# Subplot 2: Distribution of total status changes per card
change_dist = df_card_changes['total_changes'].value_counts().sort_index()
bars = ax2.bar(change_dist.index.astype(str), change_dist.values, color='#8b5cf6', edgecolor='#6d28d9', width=0.6)
ax2.set_title('B. Distribution of Status Changes per Card', fontsize=13, fontweight='bold')
ax2.set_xlabel('Total Changes Recorded per Card', fontsize=11, fontweight='bold')
ax2.set_ylabel('Number of Cards', fontsize=11, fontweight='bold')
for bar in bars:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, yval + 1.5, f"{int(yval)} cards", ha='center', va='bottom', fontsize=10, fontweight='bold')
ax2.set_ylim(0, max(change_dist.values) + 12)

# Subplot 3: Breakdown of status transitions
bars_t = ax3.barh(df_trans['transition'], df_trans['count'], color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1'])
ax3.set_title('C. Status Transition Types', fontsize=13, fontweight='bold')
ax3.set_xlabel('Number of Transitions', fontsize=11, fontweight='bold')
ax3.invert_yaxis()
for bar in bars_t:
    w = bar.get_width()
    ax3.text(w + 3, bar.get_y() + bar.get_height()/2, f"{int(w)} ({w/df_trans['count'].sum()*100:.1f}%)", ha='left', va='center', fontsize=10, fontweight='bold')
ax3.set_xlim(0, max(df_trans['count']) + 40)

# Subplot 4: Top 10 Most Actively Moved Cards
top10_cards = df_card_changes.head(10)
bars_top = ax4.bar([f"Card {cid}" for cid in top10_cards['cardID']], top10_cards['total_changes'], color='#ec4899', edgecolor='#be185d', width=0.6)
ax4.set_title('D. Top 10 Most Frequently Updated Cards', fontsize=13, fontweight='bold')
ax4.set_xlabel('Card Identifier', fontsize=11, fontweight='bold')
ax4.set_ylabel('Total Changes Recorded', fontsize=11, fontweight='bold')
plt.setp(ax4.get_xticklabels(), rotation=35, ha='right')
for bar in bars_top:
    yval = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{int(yval)}", ha='center', va='bottom', fontsize=10, fontweight='bold')
ax4.set_ylim(0, max(top10_cards['total_changes']) + 1)

plt.suptitle('Shiptivity: Card Status Change & Velocity Dynamics', fontsize=17, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('status_changes_by_card.png', dpi=300)
plt.close()
print("Saved status_changes_by_card.png successfully!")

conn.close()
