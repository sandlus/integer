# import os
# import mysql.connector
# from dotenv import load_dotenv

# load_dotenv()


# def get_db_connection():
#     try:
#         return mysql.connector.connect(
#             host=os.getenv("DB_HOST"),
#             port=int(os.getenv("DB_PORT", 3306)),
#             user=os.getenv("DB_USER"),
#             password=os.getenv("DB_PASSWORD"),
#             database=os.getenv("DB_NAME"),
#             autocommit=True
#         )
#     except mysql.connector.Error as e:
#         print(f"DB Connection Error: {e}")
#         return None


# def fetch_all(query, params=None):
#     conn = get_db_connection()
#     if not conn:
#         return []

#     cursor = None
#     try:
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute(query, params or ())
#         return cursor.fetchall()
#     except Exception as e:
#         print(f"Query Error: {e}")
#         return []
#     finally:
#         if cursor:
#             cursor.close()
#         conn.close()


# def fetch_one(query, params=None):
#     rows = fetch_all(query, params)
#     return rows[0] if rows else None 

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            autocommit=True
        )
    except mysql.connector.Error as e:
        print(f"DB Connection Error: {e}")
        return None


def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn:
        return []

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Exception as e:
        print(f"Query Error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_one(query, params=None):
    rows = fetch_all(query, params)
    return rows[0] if rows else None