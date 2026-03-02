import sqlite3
import os

db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Limpiar tablas que causan IntegrityError por cambio de esquema
    try:
        cur.execute("DELETE FROM embarques_embarque;")
        cur.execute("UPDATE ventas_venta SET embarque_id = NULL;")
        conn.commit()
        print("Cleanup successful.")
    except sqlite3.Error as e:
        print(f"Error during cleanup: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
