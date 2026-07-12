import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from modules.inventario import (
    buscar_producto,
    obtener_todos,
    agregar_producto,
    actualizar_precio_por_id,
    actualizar_stock_por_id,
    eliminar_producto
)
from modules.ventas import procesar_venta, obtener_historial_ventas

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Control Interno - POS")
        self.geometry("1100x650")  # Ventana más ancha para los dos paneles

        # Carrito en memoria ahora es un diccionario: {id_producto: datos_item}
        self.carrito = {}

        # Creación de pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_inventario = ttk.Frame(self.notebook)
        self.tab_caja = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_ventas, text="Punto de Venta")
        self.notebook.add(self.tab_inventario, text="Inventario / Stock")
        self.notebook.add(self.tab_caja, text="Caja / Historial")

        # Inicializar los componentes
        self.setup_tab_ventas()
        self.setup_tab_inventario()
        self.setup_tab_caja()

    # =========================================================================
    # PESTAÑA: PUNTO DE VENTA
    # =========================================================================

    def setup_tab_ventas(self):
        # --- DIVISIÓN EN DOS PANELES ---
        panel_izq = ttk.Frame(self.tab_ventas, width=450)
        panel_izq.pack(side="left", fill="y", padx=10, pady=10)

        panel_der = ttk.Frame(self.tab_ventas)
        panel_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # === PANEL IZQUIERDO: BUSCADOR Y CATÁLOGO ===
        frame_busqueda = ttk.LabelFrame(panel_izq, text=" Buscar Producto (Nombre o Código) ", padding=10)
        frame_busqueda.pack(fill="x")

        self.entry_buscador = ttk.Entry(frame_busqueda, font=("Arial", 12))
        self.entry_buscador.pack(fill="x", pady=5)
        # Filtra el catálogo en vivo
        self.entry_buscador.bind("<KeyRelease>", self.filtrar_catalogo)

        ttk.Label(frame_busqueda, text="Doble clic en un producto para agregarlo al carrito.",
                  font=("Arial", 9, "italic")).pack(anchor="w")

        # Tabla del Catálogo
        columnas_cat = ("id", "nombre", "precio", "stock")
        self.tabla_catalogo = ttk.Treeview(panel_izq, columns=columnas_cat, show="headings", height=20)
        self.tabla_catalogo.heading("id", text="ID")
        self.tabla_catalogo.heading("nombre", text="Descripción")
        self.tabla_catalogo.heading("precio", text="Precio")
        self.tabla_catalogo.heading("stock", text="Stock")

        self.tabla_catalogo.column("id", width=30, anchor="center")
        self.tabla_catalogo.column("nombre", width=200)
        self.tabla_catalogo.column("precio", width=80, anchor="center")
        self.tabla_catalogo.column("stock", width=50, anchor="center")

        self.tabla_catalogo.pack(fill="both", expand=True, pady=5)
        # Evento de doble clic para agregar al carrito
        self.tabla_catalogo.bind("<Double-1>", self.agregar_al_carrito_clic)

        # === PANEL DERECHO: CARRITO INTERACTIVO ===
        frame_carrito_title = ttk.LabelFrame(panel_der, text=" Carrito de Compras ", padding=10)
        frame_carrito_title.pack(fill="both", expand=True)

        # Para poder poner botones dentro de una lista, usamos un Canvas
        self.canvas_carrito = tk.Canvas(frame_carrito_title, highlightthickness=0)
        self.scrollbar_carrito = ttk.Scrollbar(frame_carrito_title, orient="vertical",
                                               command=self.canvas_carrito.yview)

        self.frame_items = ttk.Frame(self.canvas_carrito)
        self.frame_items.bind("<Configure>",
                              lambda e: self.canvas_carrito.configure(scrollregion=self.canvas_carrito.bbox("all")))

        self.canvas_carrito.create_window((0, 0), window=self.frame_items, anchor="nw")
        self.canvas_carrito.configure(yscrollcommand=self.scrollbar_carrito.set)

        self.canvas_carrito.pack(side="left", fill="both", expand=True)
        self.scrollbar_carrito.pack(side="right", fill="y")

        # === PANEL INFERIOR: TOTALES ===
        frame_acciones = ttk.Frame(panel_der, padding=10)
        frame_acciones.pack(fill="x", pady=10)

        self.label_total = ttk.Label(frame_acciones, text="TOTAL: $0.00", font=("Arial", 20, "bold"))
        self.label_total.pack(side="left", padx=10)

        btn_cobrar = ttk.Button(frame_acciones, text="FINALIZAR VENTA", command=self.finalizar_venta)
        btn_cobrar.pack(side="right", padx=10, ipady=10, ipadx=10)

        # Cargar productos por primera vez
        self.actualizar_catalogo()

    # --- Lógica del Buscador y Catálogo ---
    def actualizar_catalogo(self, filtro=""):
        for row in self.tabla_catalogo.get_children():
            self.tabla_catalogo.delete(row)

        productos = obtener_todos()
        filtro = filtro.lower()
        for p in productos:
            # p = (id, codigo_barras, nombre, precio, stock)
            if filtro in p[2].lower() or filtro in p[1]:  # Busca por nombre o código de barras
                self.tabla_catalogo.insert("", "end", values=(p[0], p[2], p[3], p[4]))

    def filtrar_catalogo(self, event):
        texto = self.entry_buscador.get()
        self.actualizar_catalogo(texto)

    def agregar_al_carrito_clic(self, event):
        item_seleccionado = self.tabla_catalogo.focus()
        if not item_seleccionado: return

        valores = self.tabla_catalogo.item(item_seleccionado, "values")
        p_id = int(valores[0])

        # Buscar datos completos en base de datos para sacar el código de barras
        productos = obtener_todos()
        prod_completo = next((p for p in productos if p[0] == p_id), None)

        if not prod_completo: return
        p_codigo, p_nombre, p_precio, p_stock = prod_completo[1], prod_completo[2], float(valores[2]), int(valores[3])

        if p_stock <= 0:
            messagebox.showwarning("Sin Stock", f"No queda stock de {p_nombre}.")
            return

        # Si ya está en el carrito, le sumamos 1 si hay stock
        if p_id in self.carrito:
            if self.carrito[p_id]['cantidad'] + 1 > p_stock:
                messagebox.showwarning("Límite", "No hay más unidades disponibles.")
                return
            self.carrito[p_id]['cantidad'] += 1
        else:
            # Si es nuevo, lo registramos en el diccionario
            self.carrito[p_id] = {
                'id': p_id,
                'codigo_barras': p_codigo,
                'nombre': p_nombre,
                'precio': p_precio,
                'cantidad': 1,
                'stock_maximo': p_stock
            }

        self.renderizar_carrito()

    # --- Lógica del Carrito Interactivo ---
    def modificar_cantidad(self, p_id, delta):
        if p_id not in self.carrito: return

        nueva_cantidad = self.carrito[p_id]['cantidad'] + delta
        stock_max = self.carrito[p_id]['stock_maximo']

        if nueva_cantidad > stock_max:
            messagebox.showwarning("Límite", "Stock máximo alcanzado.")
            return

        # Si la cantidad baja a 0 (o menos), se elimina directamente del carrito
        if nueva_cantidad <= 0:
            del self.carrito[p_id]
        else:
            self.carrito[p_id]['cantidad'] = nueva_cantidad

        self.renderizar_carrito()

    def renderizar_carrito(self):
        # 1. Limpiar visualmente el frame del carrito completo
        for widget in self.frame_items.winfo_children():
            widget.destroy()

        total = 0

        # 2. Dibujar Cabeceras si hay algo en el carrito
        if self.carrito:
            ttk.Label(self.frame_items, text="Producto", width=30, font=("Arial", 10, "bold")).grid(row=0, column=0,
                                                                                                    padx=5, pady=5,
                                                                                                    sticky="w")
            ttk.Label(self.frame_items, text="Precio", width=10, font=("Arial", 10, "bold")).grid(row=0, column=1,
                                                                                                  padx=5, pady=5)
            ttk.Label(self.frame_items, text="Cantidad", width=15, font=("Arial", 10, "bold"), anchor="center").grid(
                row=0, column=2, padx=5, pady=5)
            ttk.Label(self.frame_items, text="Subtotal", width=10, font=("Arial", 10, "bold")).grid(row=0, column=3,
                                                                                                    padx=5, pady=5)

        # 3. Dibujar cada fila interactiva
        row_idx = 1
        for p_id, data in self.carrito.items():
            subtotal = data['cantidad'] * data['precio']
            total += subtotal

            ttk.Label(self.frame_items, text=data['nombre'], width=30).grid(row=row_idx, column=0, padx=5, pady=5,
                                                                            sticky="w")
            ttk.Label(self.frame_items, text=f"${data['precio']:.2f}", width=10).grid(row=row_idx, column=1, padx=5,
                                                                                      pady=5)

            # El contenedor de los botones [-] Cantidad [+]
            frame_cant = ttk.Frame(self.frame_items)
            frame_cant.grid(row=row_idx, column=2, padx=5, pady=5)

            btn_menos = ttk.Button(frame_cant, text="-", width=3,
                                   command=lambda id=p_id: self.modificar_cantidad(id, -1))
            btn_menos.pack(side="left")

            lbl_cant = ttk.Label(frame_cant, text=str(data['cantidad']), width=4, anchor="center",
                                 font=("Arial", 11, "bold"))
            lbl_cant.pack(side="left", padx=5)

            btn_mas = ttk.Button(frame_cant, text="+", width=3, command=lambda id=p_id: self.modificar_cantidad(id, 1))
            btn_mas.pack(side="left")

            ttk.Label(self.frame_items, text=f"${subtotal:.2f}", width=10).grid(row=row_idx, column=3, padx=5, pady=5)

            row_idx += 1

        # 4. Actualizar el texto del Total
        self.label_total.config(text=f"TOTAL: ${total:.2f}")

    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "No hay productos en el carrito.")
            return

        # Adaptamos nuestro diccionario a la lista que espera el backend en ventas.py
        lista_carrito = []
        for p_id, data in self.carrito.items():
            data_copy = data.copy()
            data_copy['subtotal'] = data_copy['cantidad'] * data_copy['precio']
            lista_carrito.append(data_copy)

        exito, mensaje = procesar_venta(lista_carrito)
        if exito:
            messagebox.showinfo("Venta Exitosa", f"{mensaje}\n\nTicket generado correctamente.")
            self.carrito.clear()  # Vaciamos el diccionario
            self.renderizar_carrito()
            self.actualizar_vista_inventario()
            self.actualizar_catalogo(self.entry_buscador.get())  # Refresca el stock visible
            self.actualizar_vista_caja()
        else:
            messagebox.showerror("Error", mensaje)

    # =========================================================================
    # PESTAÑA 2: GESTIÓN DE INVENTARIO
    # =========================================================================
    def setup_tab_inventario(self):
        # Formulario
        frame_form = ttk.LabelFrame(self.tab_inventario, text=" Registrar / Editar Producto ", padding=10)
        frame_form.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Label(frame_form, text="Código de Barras:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_inv_codigo = ttk.Entry(frame_form)
        self.entry_inv_codigo.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Nombre/Descripción:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_inv_nombre = ttk.Entry(frame_form)
        self.entry_inv_nombre.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Precio ($):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_inv_precio = ttk.Entry(frame_form)
        self.entry_inv_precio.grid(row=2, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Stock Inicial:").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_inv_stock = ttk.Entry(frame_form)
        self.entry_inv_stock.grid(row=3, column=1, pady=5, padx=5)

        btn_guardar = ttk.Button(frame_form, text="Guardar Producto", command=self.guardar_nuevo_producto)
        btn_guardar.grid(row=4, column=0, columnspan=2, pady=15, ipady=3)

        # Tabla Inventario
        frame_lista_inv = ttk.Frame(self.tab_inventario, padding=10)
        frame_lista_inv.pack(side="right", fill="both", expand=True)

        columnas = ("id", "codigo", "nombre", "precio", "stock")
        self.tabla_inventario = ttk.Treeview(frame_lista_inv, columns=columnas, show="headings")
        self.tabla_inventario.heading("id", text="ID")
        self.tabla_inventario.heading("codigo", text="Código")
        self.tabla_inventario.heading("nombre", text="Descripción")
        self.tabla_inventario.heading("precio", text="Precio")
        self.tabla_inventario.heading("stock", text="Stock")

        self.tabla_inventario.column("id", width=40, anchor="center")
        self.tabla_inventario.column("stock", width=60, anchor="center")
        self.tabla_inventario.pack(fill="both", expand=True)

        # Crear menú contextual para click derecho
        self.menu_contextual = tk.Menu(self, tearoff=0)
        self.menu_contextual.add_command(label="Editar precio", command=self.context_editar_precio)
        self.menu_contextual.add_command(label="Editar stock", command=self.context_editar_stock)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Eliminar producto", command=self.context_eliminar_producto)

        # Asociar evento de click derecho a la tabla
        self.tabla_inventario.bind("<Button-3>", self.mostrar_menu_contextual)

        self.actualizar_vista_inventario()

    def guardar_nuevo_producto(self):
        codigo = self.entry_inv_codigo.get().strip()
        nombre = self.entry_inv_nombre.get().strip()
        precio_str = self.entry_inv_precio.get().strip()
        stock_str = self.entry_inv_stock.get().strip()

        if not (codigo and nombre and precio_str and stock_str):
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios.")
            return

        try:
            precio = float(precio_str)
            stock = int(stock_str)
        except ValueError:
            messagebox.showerror("Error", "Precio y Stock deben ser numéricos.")
            return

        exito, msj = agregar_producto(codigo, nombre, precio, stock)
        if exito:
            messagebox.showinfo("Éxito", msj)
            self.entry_inv_codigo.delete(0, tk.END)
            self.entry_inv_nombre.delete(0, tk.END)
            self.entry_inv_precio.delete(0, tk.END)
            self.entry_inv_stock.delete(0, tk.END)

            # Actualizamos ambas vistas
            self.actualizar_vista_inventario()
            self.actualizar_catalogo(self.entry_buscador.get())
        else:
            messagebox.showerror("Error", msj)

    def actualizar_vista_inventario(self):
        for row in self.tabla_inventario.get_children():
            self.tabla_inventario.delete(row)

        productos = obtener_todos()
        for p in productos:
            self.tabla_inventario.insert("", "end", values=(p[0], p[1], p[2], f"${p[3]:.2f}", p[4]))

    # =========================================================================
    # FUNCIONES DEL MENÚ CONTEXTUAL (CLICK DERECHO EN INVENTARIO)
    # =========================================================================
    def mostrar_menu_contextual(self, event):
        # Identificar la fila exacta sobre la que se hizo click derecho
        item = self.tabla_inventario.identify_row(event.y)
        if item:
            # Seleccionar esa fila visualmente
            self.tabla_inventario.selection_set(item)
            # Mostrar el menú flotante en las coordenadas del mouse
            self.menu_contextual.tk_popup(event.x_root, event.y_root)

    def context_editar_precio(self):
        item_seleccionado = self.tabla_inventario.selection()
        if not item_seleccionado: return

        valores = self.tabla_inventario.item(item_seleccionado[0], "values")
        p_id, nombre, precio_actual = int(valores[0]), valores[2], valores[3].replace('$', '')

        # Mostrar ventana emergente para ingresar el nuevo valor
        nuevo_precio_str = simpledialog.askstring("Editar Precio", f"Nuevo precio para {nombre}:",
                                                  initialvalue=precio_actual)

        if nuevo_precio_str is not None:  # Si el usuario no canceló
            try:
                nuevo_precio = float(nuevo_precio_str)
                exito, msj = actualizar_precio_por_id(p_id, nuevo_precio)
                if exito:
                    self.actualizar_vista_inventario()
                    self.actualizar_catalogo(self.entry_buscador.get())
                    messagebox.showinfo("Éxito", msj)
                else:
                    messagebox.showerror("Error", msj)
            except ValueError:
                messagebox.showerror("Error", "El precio debe ser un número (puedes usar punto para decimales).")

    def context_editar_stock(self):
        item_seleccionado = self.tabla_inventario.selection()
        if not item_seleccionado: return

        valores = self.tabla_inventario.item(item_seleccionado[0], "values")
        p_id, nombre, stock_actual = int(valores[0]), valores[2], valores[4]

        nuevo_stock_str = simpledialog.askstring("Editar Stock", f"Nuevo stock total para {nombre}:",
                                                 initialvalue=stock_actual)

        if nuevo_stock_str is not None:
            try:
                nuevo_stock = int(nuevo_stock_str)
                exito, msj = actualizar_stock_por_id(p_id, nuevo_stock)
                if exito:
                    self.actualizar_vista_inventario()
                    self.actualizar_catalogo(self.entry_buscador.get())

                    # Si el producto estaba en el carrito, le actualizamos el stock máximo
                    if p_id in self.carrito:
                        self.carrito[p_id]['stock_maximo'] = nuevo_stock
                        # Si el nuevo stock es menor a la cantidad ya en carrito, ajustamos
                        if self.carrito[p_id]['cantidad'] > nuevo_stock:
                            self.carrito[p_id]['cantidad'] = nuevo_stock
                        if self.carrito[p_id]['cantidad'] <= 0:
                            del self.carrito[p_id]
                        self.renderizar_carrito()

                    messagebox.showinfo("Éxito", msj)
                else:
                    messagebox.showerror("Error", msj)
            except ValueError:
                messagebox.showerror("Error", "El stock debe ser un número entero.")

    def context_eliminar_producto(self):
        item_seleccionado = self.tabla_inventario.selection()
        if not item_seleccionado: return

        valores = self.tabla_inventario.item(item_seleccionado[0], "values")
        p_id, nombre = int(valores[0]), valores[2]

        confirmacion = messagebox.askyesno("Confirmar Eliminación",
                                           f"¿Estás completamente seguro de eliminar '{nombre}'?\n\nEsta acción no se puede deshacer.")

        if confirmacion:
            exito, msj = eliminar_producto(p_id)
            if exito:
                self.actualizar_vista_inventario()
                self.actualizar_catalogo(self.entry_buscador.get())

                # Detalle de seguridad: Si el producto a eliminar justo estaba en el carrito actual, lo sacamos
                if p_id in self.carrito:
                    del self.carrito[p_id]
                    self.renderizar_carrito()

                messagebox.showinfo("Éxito", msj)
            else:
                messagebox.showerror("Error", msj)

    # =========================================================================
    # PESTAÑA 3: CAJA E HISTORIAL DE VENTAS
    # =========================================================================
    def setup_tab_caja(self):
        # Panel superior con el resumen de plata
        frame_resumen = ttk.Frame(self.tab_caja, padding=10)
        frame_resumen.pack(fill="x")

        self.label_recaudacion = ttk.Label(frame_resumen, text="Recaudación: $0.00", font=("Arial", 16, "bold"))
        self.label_recaudacion.pack(side="left")

        btn_refrescar = ttk.Button(frame_resumen, text="Refrescar Historial", command=self.actualizar_vista_caja)
        btn_refrescar.pack(side="right", ipady=5, ipadx=5)

        # Panel inferior con la tabla de ventas
        frame_tabla = ttk.Frame(self.tab_caja, padding=10)
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("id", "fecha", "total")
        self.tabla_caja = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tabla_caja.heading("id", text="Nº Venta")
        self.tabla_caja.heading("fecha", text="Fecha y Hora")
        self.tabla_caja.heading("total", text="Total Venta")

        self.tabla_caja.column("id", width=80, anchor="center")
        self.tabla_caja.column("fecha", width=200, anchor="center")
        self.tabla_caja.column("total", width=120, anchor="center")
        self.tabla_caja.pack(fill="both", expand=True, side="left")

        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_caja.yview)
        self.tabla_caja.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Cargar los datos la primera vez que abre
        self.actualizar_vista_caja()

    def actualizar_vista_caja(self):
        # Limpiar tabla
        for row in self.tabla_caja.get_children():
            self.tabla_caja.delete(row)

        ventas = obtener_historial_ventas()
        total_recaudado = 0

        # Llenar tabla y sumar la plata
        for v in ventas:
            # v = (id, fecha, total)
            self.tabla_caja.insert("", "end", values=(v[0], v[1], f"${v[2]:.2f}"))
            total_recaudado += v[2]

        self.label_recaudacion.config(text=f"Recaudación Histórica: ${total_recaudado:.2f}")