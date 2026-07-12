import sqlite3
import os

DIR_DE_ESTE_ARCHIVO = os.path.dirname(os.path.abspath(__file__))
RAIZ_DEL_PROYECTO = os.path.dirname(DIR_DE_ESTE_ARCHIVO)
DB_PATH = os.path.join(DIR_DE_ESTE_ARCHIVO, 'pos_interno.db')

def get_connection():
    """Establece y retorna la conexión a la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Crea las tablas necesarias si no existen en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    ''')

    # Tabla de Ventas (Cabecera del ticket)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL
        )
    ''')

    # Tabla de Detalles de Venta (Los items dentro del ticket)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            subtotal REAL,
            FOREIGN KEY (venta_id) REFERENCES ventas (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()