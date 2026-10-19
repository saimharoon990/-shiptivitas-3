import sqlite3
import pandas as pd

conn = sqlite3.connect('shiptivity.db')

# DAU analysis
df_dau = pd.read_sql_query('''
    SELECT 
        date(login_timestamp, 'unixepoch') AS activity_date,
        COUNT(DISTINCT user_id) AS dau
    FROM login_history
    GROUP BY activity_date
    ORDER BY activity_date;
''', conn)
df_dau['period'] = df_dau['activity_date'].apply(lambda d: 'Before (pre-2018-06-02)' if d < '2018-06-02' else 'After (post-2018-06-02)')

print('=== DAU SUMMARY ===')
print(df_dau.groupby('period')['dau'].describe())

# Status change analysis
df_changes = pd.read_sql_query('''
    SELECT 
        id,
        cardID,
        oldStatus,
        newStatus,
        date(timestamp, 'unixepoch') AS change_date,
        timestamp
    FROM card_change_history
    ORDER BY timestamp;
''', conn)

print('\n=== TOTAL STATUS CHANGES ===')
print(f'Total change events: {len(df_changes)}')
print(df_changes['newStatus'].value_counts())
print('\n=== TRANSITIONS ===')
print(df_changes.groupby(['oldStatus', 'newStatus']).size())

print('\n=== CHANGES PER CARD (ALL CHANGES) ===')
card_change_counts = df_changes.groupby('cardID').size()
print(card_change_counts.describe())

print('\n=== CHANGES PER CARD (EXCLUDING INITIAL CREATION) ===')
subsequent_changes = df_changes[df_changes['oldStatus'] != ''].groupby('cardID').size()
print(subsequent_changes.describe())

print('\n=== DAILY CHANGES ===')
daily_changes = df_changes.groupby('change_date').size()
print(daily_changes.describe())
