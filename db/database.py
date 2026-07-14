import sqlite3
import os
import sys

# PARA PYINSTALLER
if getattr(sys, 'frozen', False):
    # Si está corriendo como .exe
    # Busca la ruta donde está el ejecutable final
    RAIZ_DEL_PROYECTO = os.path.dirname(sys.executable)
else:
    # Si está corriendo desde el código fuente (.py):
    DIR_DE_ESTE_ARCHIVO = os.path.dirname(os.path.abspath(__file__))
    RAIZ_DEL_PROYECTO = os.path.dirname(DIR_DE_ESTE_ARCHIVO)

# Aseguramos que la base de datos se guarde ordenadamente en una carpeta 'db'
DB_DIR = os.path.join(RAIZ_DEL_PROYECTO, 'db')
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, 'pos_interno.db')

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