import sqlite3

def get_user_data(user_id):
    conn = sqlite3.connect("database.db")
    # Intentional SQL injection for the agent to catch
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return conn.execute(query).fetchall()