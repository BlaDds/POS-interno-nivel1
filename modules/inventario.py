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

def actualizar_precio_por_id(id_producto, nuevo_precio):
    """Actualiza el precio de un producto por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE productos 
            SET precio = ? 
            WHERE id = ?
        ''', (nuevo_precio, id_producto))
        conn.commit()
        return True, "Precio actualizado con éxito."
    except Exception as e:
        return False, f"Error al actualizar el precio: {e}"
    finally:
        conn.close()

def actualizar_stock_por_id(id_producto, nuevo_stock):
    """Actualiza el stock de un producto por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE productos 
            SET stock = ? 
            WHERE id = ?
        ''', (nuevo_stock, id_producto))
        conn.commit()
        return True, "Stock actualizado con éxito."
    except Exception as e:
        return False, f"Error al actualizar el stock: {e}"
    finally:
        conn.close()

def eliminar_producto(id_producto):
    """Elimina completamente un producto de la base de datos por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM productos WHERE id = ?', (id_producto,))
        conn.commit()
        return True, "Producto eliminado con éxito."
    except Exception as e:
        return False, f"Error al eliminar el producto: {e}"
    finally:
        conn.close()