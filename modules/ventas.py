import sqlite3
import os
from datetime import datetime
from db.database import get_connection, RAIZ_DEL_PROYECTO

# Carpeta donde se guardarán los tickets generados
TICKETS_DIR = os.path.join(RAIZ_DEL_PROYECTO, 'db/tickets')
if not os.path.exists(TICKETS_DIR):
    os.makedirs(TICKETS_DIR)


def procesar_venta(carrito):
    """
    Recibe una lista de diccionarios representando el carrito:
    [{'id': 1, 'codigo_barras': '123', 'nombre': 'Coca', 'precio': 1500, 'cantidad': 2, 'subtotal': 3000}]
    """
    if not carrito:
        return False, "El carrito está vacío."

    total_venta = sum(item['subtotal'] for item in carrito)
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Registrar la cabecera de la venta
        cursor.execute('''
            INSERT INTO ventas (total) VALUES (?)
        ''', (total_venta,))
        venta_id = cursor.lastrowid

        # 2. Registrar el detalle y descontar stock EN LA MISMA TRANSACCIÓN
        for item in carrito:
            # Insertar detalle
            cursor.execute('''
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, subtotal)
                VALUES (?, ?, ?, ?)
            ''', (venta_id, item['id'], item['cantidad'], item['subtotal']))

            # Descontar stock usando el MISMO cursor
            cursor.execute('''
                UPDATE productos 
                SET stock = stock - ? 
                WHERE id = ?
            ''', (item['cantidad'], item['id']))

        conn.commit()

        # 3. Generar el comprobante físico (archivo de texto)
        generar_ticket(venta_id, carrito, total_venta)

        return True, f"Venta #{venta_id} procesada con éxito."

    except Exception as e:
        # Si algo falla ROLLBACK
        conn.rollback()
        return False, f"Error crítico al procesar la venta: {e}"
    finally:
        conn.close()


def generar_ticket(venta_id, carrito, total):
    """Genera un archivo .txt con el formato de ticket no fiscal."""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre_archivo = f"ticket_v{venta_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    ruta_ticket = os.path.join(TICKETS_DIR, nombre_archivo)

    with open(ruta_ticket, 'w', encoding='utf-8') as f:
        f.write("========================================\n")
        f.write("      DOCUMENTO NO VÁLIDO COMO FACTURA  \n")
        f.write("               USO INTERNO              \n")
        f.write("========================================\n")
        f.write(f"Venta #: {venta_id}\n")
        f.write(f"Fecha: {fecha_actual}\n")
        f.write("----------------------------------------\n")
        f.write("CANT  DESCRIPCION         SUBTOTAL      \n")
        f.write("----------------------------------------\n")

        for item in carrito:
            linea = f"{item['cantidad']:<5} {item['nombre'][:18]:<18} ${item['subtotal']:<10.2f}\n"
            f.write(linea)

        f.write("----------------------------------------\n")
        f.write(f"TOTAL:                        ${total:.2f}\n")
        f.write("========================================\n")
        f.write("        ¡Gracias por su compra!         \n")

def obtener_historial_ventas():
    """Trae todas las ventas registradas ordenadas de la más reciente a la más antigua."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha, total FROM ventas ORDER BY id DESC")
    ventas = cursor.fetchall()
    conn.close()
    return ventas