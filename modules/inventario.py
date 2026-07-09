import sqlite3
from db.database import get_connection

def agregar_producto(codigo_barras, nombre, precio, stock):
    """Inserta un nuevo producto. Evita duplicados por código de barras."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO productos (codigo_barras, nombre, precio, stock)
            VALUES (?, ?, ?, ?)
        ''', (codigo_barras, nombre, precio, stock))
        conn.commit()
        return True, "Producto agregado con éxito."
    except sqlite3.IntegrityError:
        # Esto salta si intentan cargar un código de barras que ya existe
        return False, "Error: El código de barras ya está registrado."
    except Exception as e:
        return False, f"Error en la base de datos: {e}"
    finally:
        conn.close()

def buscar_producto(codigo_barras):
    """Busca un producto exacto. Es el motor principal del escáner en el POS."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, codigo_barras, nombre, precio, stock 
        FROM productos 
        WHERE codigo_barras = ?
    ''', (codigo_barras,))
    producto = cursor.fetchone()
    conn.close()
    return producto  # Retorna una tupla con los datos, o None si no existe

def obtener_todos():
    """Trae el inventario entero. Ideal para llenar una tabla (Treeview) en la interfaz."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, codigo_barras, nombre, precio, stock FROM productos')
    productos = cursor.fetchall()
    conn.close()
    return productos

def actualizar_stock(codigo_barras, cantidad_a_descontar):
    """Resta la cantidad vendida al stock actual. Se usará al finalizar una venta."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE productos 
            SET stock = stock - ? 
            WHERE codigo_barras = ?
        ''', (cantidad_a_descontar, codigo_barras))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error actualizando stock: {e}")
        return False
    finally:
        conn.close()


# PRUEBA RÁPIDA
if __name__ == "__main__":
    exito, msj = agregar_producto("7791234567890", "Coca Cola 1.5L", 1500.0, 24)
    print("Agregar:", msj)

    prod = buscar_producto("7791234567890")
    print("Buscar:", prod)

    print("Inventario completo:", obtener_todos())