import sqlite3
conn = sqlite3.connect(r'C:\Users\vijay\OneDrive\Desktop\movie\instance\movie_recommender.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM [{table[0]}]')
    count = cursor.fetchone()[0]
    print(f'  {table[0]}: {count} rows')
conn.close()
