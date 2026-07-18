import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from modules.inventario import (
    buscar_producto, obtener_todos, agregar_producto,
    actualizar_precio_por_id, actualizar_stock_por_id, eliminar_producto, obtener_categorias
)
from modules.ventas import procesar_venta, obtener_historial_ventas


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Control Interno - POS")
        self.geometry("1150x650")

        self.carrito = {}

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_ventas = ttk.Frame(self.notebook)
        self.tab_inventario = ttk.Frame(self.notebook)
        self.tab_caja = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_ventas, text="Punto de Venta")
        self.notebook.add(self.tab_inventario, text="Inventario / Stock")
        self.notebook.add(self.tab_caja, text="Caja / Historial")

        self.setup_tab_ventas()
        self.setup_tab_inventario()
        self.setup_tab_caja()

    # =========================================================================
    # PESTAÑA 1: PUNTO DE VENTA
    # =========================================================================
    def setup_tab_ventas(self):
        panel_izq = ttk.Frame(self.tab_ventas, width=500)
        panel_izq.pack(side="left", fill="y", padx=10, pady=10)

        panel_der = ttk.Frame(self.tab_ventas)
        panel_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        frame_busqueda = ttk.LabelFrame(panel_izq, text=" Buscar Producto (Nombre, Código o Categoría) ", padding=10)
        frame_busqueda.pack(fill="x")

        self.entry_buscador = ttk.Entry(frame_busqueda, font=("Arial", 12))
        self.entry_buscador.pack(fill="x", pady=5)
        self.entry_buscador.bind("<KeyRelease>", self.filtrar_catalogo)
        # TRUCO DE TECLADO: Si apreta flecha abajo, el foco salta a la tabla
        self.entry_buscador.bind("<Down>", lambda e: self.tabla_catalogo.focus_set())

        ttk.Label(frame_busqueda, text="Selecciona con Flechas y presiona ENTER para agregar.",
                  font=("Arial", 9, "italic")).pack(anchor="w")

        # Tabla del Catálogo
        columnas_cat = ("id", "nombre", "categoria", "precio", "stock")
        self.tabla_catalogo = ttk.Treeview(panel_izq, columns=columnas_cat, show="headings", height=20)
        self.tabla_catalogo.heading("id", text="ID")
        self.tabla_catalogo.heading("nombre", text="Nombre")
        self.tabla_catalogo.heading("categoria", text="Categoría")
        self.tabla_catalogo.heading("precio", text="Precio")
        self.tabla_catalogo.heading("stock", text="Stock")

        self.tabla_catalogo.column("id", width=30, anchor="center")
        self.tabla_catalogo.column("nombre", width=180)
        self.tabla_catalogo.column("categoria", width=100)
        self.tabla_catalogo.column("precio", width=70, anchor="center")
        self.tabla_catalogo.column("stock", width=50, anchor="center")

        # FORZAR COLORES: Cambiamos el color de la letra (foreground) para mayor compatibilidad en Win7
        self.tabla_catalogo.tag_configure("agotado", background="#ffcccc", foreground="#990000")
        self.tabla_catalogo.tag_configure("bajo_stock", background="#ffffcc", foreground="#cc8800")

        self.tabla_catalogo.pack(fill="both", expand=True, pady=5)

        # AGREGAR AL CARRITO TANTO CON DOBLE CLIC COMO CON ENTER
        self.tabla_catalogo.bind("<Double-1>", self.agregar_al_carrito_clic)
        self.tabla_catalogo.bind("<Return>", self.agregar_al_carrito_clic)

        # Panel Derecho (Carrito)
        frame_carrito_title = ttk.LabelFrame(panel_der, text=" Carrito de Compras ", padding=10)
        frame_carrito_title.pack(fill="both", expand=True)

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

        frame_acciones = ttk.Frame(panel_der, padding=10)
        frame_acciones.pack(fill="x", pady=10)

        self.label_total = ttk.Label(frame_acciones, text="TOTAL: $0.00", font=("Arial", 20, "bold"))
        self.label_total.pack(side="left", padx=10)

        btn_cobrar = ttk.Button(frame_acciones, text="FINALIZAR VENTA", command=self.finalizar_venta)
        btn_cobrar.pack(side="right", padx=10, ipady=10, ipadx=10)

        self.actualizar_catalogo()

    def actualizar_catalogo(self, filtro=""):
        for row in self.tabla_catalogo.get_children():
            self.tabla_catalogo.delete(row)

        productos = obtener_todos()
        filtro = filtro.lower()
        for p in productos:
            coincide = filtro in p[2].lower() or filtro in p[1].lower() or (p[3] and filtro in p[3].lower())

            if coincide:
                stock_actual = p[5]
                if stock_actual == 0:
                    tag = "agotado"
                elif 1 <= stock_actual <= 7:
                    tag = "bajo_stock"
                else:
                    tag = "normal"

                self.tabla_catalogo.insert("", "end", values=(p[0], p[2], p[3], f"${p[4]:.2f}", p[5]), tags=(tag,))

        # TRUCO DE TECLADO: Si la tabla tiene elementos, pre-seleccionamos el primero automáticamente
        hijos = self.tabla_catalogo.get_children()
        if hijos:
            self.tabla_catalogo.selection_set(hijos[0])

    def filtrar_catalogo(self, event):
        # Ignoramos si presiona Enter o flechas para no interferir con la navegación
        if event.keysym in ['Return', 'Down', 'Up']: return
        self.actualizar_catalogo(self.entry_buscador.get())

    def agregar_al_carrito_clic(self, event=None):
        item_seleccionado = self.tabla_catalogo.focus()
        if not item_seleccionado:
            seleccion = self.tabla_catalogo.selection()
            if seleccion:
                item_seleccionado = seleccion[0]
            else:
                return

        valores = self.tabla_catalogo.item(item_seleccionado, "values")
        p_id = int(valores[0])

        productos = obtener_todos()
        prod_completo = next((p for p in productos if p[0] == p_id), None)
        if not prod_completo: return

        p_codigo, p_nombre, p_precio, p_stock = prod_completo[1], prod_completo[2], float(prod_completo[4]), int(
            prod_completo[5])

        if p_stock <= 0:
            messagebox.showwarning("Sin Stock", f"No queda stock de {p_nombre}.")
            self.entry_buscador.focus_set()
            return

        # POPUP: Preguntar la cantidad exacta al usuario
        cantidad_ingresada = simpledialog.askinteger(
            "Cantidad",
            f"¿Cuántas unidades de {p_nombre} vas a vender?\n(Stock disponible: {p_stock})",
            minvalue=1,
            maxvalue=p_stock,
            initialvalue=1
        )

        if cantidad_ingresada is None:  # Si el usuario presiona Cancelar o Escape
            self.entry_buscador.focus_set()
            return

        # Sumamos al carrito
        if p_id in self.carrito:
            if self.carrito[p_id]['cantidad'] + cantidad_ingresada > p_stock:
                messagebox.showwarning("Límite", f"No hay stock suficiente para sumar {cantidad_ingresada} más.")
                self.entry_buscador.focus_set()
                return
            self.carrito[p_id]['cantidad'] += cantidad_ingresada
        else:
            self.carrito[p_id] = {
                'id': p_id, 'codigo_barras': p_codigo, 'nombre': p_nombre,
                'precio': p_precio, 'cantidad': cantidad_ingresada, 'stock_maximo': p_stock
            }

        self.renderizar_carrito()

        # Limpiar buscador y devolver el cursor ahí para el siguiente producto
        self.entry_buscador.delete(0, tk.END)
        self.actualizar_catalogo()
        self.entry_buscador.focus_set()

    # --- Lógica del Carrito Interactivo ---
    def modificar_cantidad(self, p_id, delta):
        if p_id not in self.carrito: return
        nueva_cantidad = self.carrito[p_id]['cantidad'] + delta
        stock_max = self.carrito[p_id]['stock_maximo']

        if nueva_cantidad > stock_max:
            messagebox.showwarning("Límite", "Stock máximo alcanzado.")
            return

        if nueva_cantidad <= 0:
            del self.carrito[p_id]
        else:
            self.carrito[p_id]['cantidad'] = nueva_cantidad
        self.renderizar_carrito()

    def eliminar_del_carrito(self, p_id):
        if p_id in self.carrito:
            del self.carrito[p_id]
            self.renderizar_carrito()

    def renderizar_carrito(self):
        for widget in self.frame_items.winfo_children():
            widget.destroy()

        total = 0
        if self.carrito:
            ttk.Label(self.frame_items, text="Producto", width=25, font=("Arial", 10, "bold")).grid(row=0, column=0,
                                                                                                    padx=5, pady=5,
                                                                                                    sticky="w")
            ttk.Label(self.frame_items, text="Precio", width=8, font=("Arial", 10, "bold")).grid(row=0, column=1,
                                                                                                 padx=5, pady=5)
            ttk.Label(self.frame_items, text="Cantidad", width=15, font=("Arial", 10, "bold"), anchor="center").grid(
                row=0, column=2, padx=5, pady=5)
            ttk.Label(self.frame_items, text="Subtotal", width=8, font=("Arial", 10, "bold")).grid(row=0, column=3,
                                                                                                   padx=5, pady=5)

        row_idx = 1
        for p_id, data in self.carrito.items():
            subtotal = data['cantidad'] * data['precio']
            total += subtotal

            ttk.Label(self.frame_items, text=data['nombre'], width=25).grid(row=row_idx, column=0, padx=5, pady=5,
                                                                            sticky="w")
            ttk.Label(self.frame_items, text=f"${data['precio']:.2f}", width=8).grid(row=row_idx, column=1, padx=5,
                                                                                     pady=5)

            # CONTENEDOR DE CANTIDAD: Botones [-] [Valor] [+]
            frame_cant = ttk.Frame(self.frame_items)
            frame_cant.grid(row=row_idx, column=2, padx=5, pady=5)

            ttk.Button(frame_cant, text="-", width=2, command=lambda id=p_id: self.modificar_cantidad(id, -1)).pack(
                side="left")
            ttk.Label(frame_cant, text=str(data['cantidad']), width=4, anchor="center",
                      font=("Arial", 11, "bold")).pack(side="left", padx=2)
            ttk.Button(frame_cant, text="+", width=2, command=lambda id=p_id: self.modificar_cantidad(id, 1)).pack(
                side="left")

            ttk.Label(self.frame_items, text=f"${subtotal:.2f}", width=8).grid(row=row_idx, column=3, padx=5, pady=5)

            # BOTÓN X PARA ELIMINAR LA FILA
            ttk.Button(self.frame_items, text="X", width=2, command=lambda id=p_id: self.eliminar_del_carrito(id)).grid(
                row=row_idx, column=4, padx=5, pady=5)

            row_idx += 1

        self.label_total.config(text=f"TOTAL: ${total:.2f}")

    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "No hay productos en el carrito.")
            return

        lista_carrito = []
        for p_id, data in self.carrito.items():
            data_copy = data.copy()
            data_copy['subtotal'] = data_copy['cantidad'] * data_copy['precio']
            lista_carrito.append(data_copy)

        exito, mensaje = procesar_venta(lista_carrito)
        if exito:
            messagebox.showinfo("Venta Exitosa", f"{mensaje}\n\nTicket generado correctamente.")
            self.carrito.clear()
            self.renderizar_carrito()
            self.actualizar_vista_inventario()
            self.actualizar_catalogo(self.entry_buscador.get())
            self.actualizar_vista_caja()
            self.entry_buscador.focus_set()
        else:
            messagebox.showerror("Error", mensaje)

    # =========================================================================
    # PESTAÑA 2: GESTIÓN DE INVENTARIO
    # =========================================================================
    def setup_tab_inventario(self):
        frame_form = ttk.LabelFrame(self.tab_inventario, text=" Registrar / Editar Producto ", padding=10)
        frame_form.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Label(frame_form, text="Cód. de Barras (Opcional):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_inv_codigo = ttk.Entry(frame_form)
        self.entry_inv_codigo.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Nombre/Descripción:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_inv_nombre = ttk.Entry(frame_form)
        self.entry_inv_nombre.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Categoría:").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_inv_categoria = ttk.Combobox(frame_form)
        self.entry_inv_categoria.grid(row=2, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Precio ($):").grid(row=3, column=0, sticky="w", pady=5)
        self.entry_inv_precio = ttk.Entry(frame_form)
        self.entry_inv_precio.grid(row=3, column=1, pady=5, padx=5)

        ttk.Label(frame_form, text="Stock Inicial:").grid(row=4, column=0, sticky="w", pady=5)
        self.entry_inv_stock = ttk.Entry(frame_form)
        self.entry_inv_stock.grid(row=4, column=1, pady=5, padx=5)

        btn_guardar = ttk.Button(frame_form, text="Guardar Producto (Enter)", command=self.guardar_nuevo_producto)
        btn_guardar.grid(row=5, column=0, columnspan=2, pady=15, ipady=3)

        for widget in (self.entry_inv_codigo, self.entry_inv_nombre, self.entry_inv_categoria, self.entry_inv_precio,
                       self.entry_inv_stock):
            widget.bind("<Return>", self.guardar_nuevo_producto)

        frame_lista_inv = ttk.Frame(self.tab_inventario, padding=10)
        frame_lista_inv.pack(side="right", fill="both", expand=True)

        columnas = ("id", "codigo", "nombre", "categoria", "precio", "stock")
        self.tabla_inventario = ttk.Treeview(frame_lista_inv, columns=columnas, show="headings")
        self.tabla_inventario.heading("id", text="ID")
        self.tabla_inventario.heading("codigo", text="Código")
        self.tabla_inventario.heading("nombre", text="Descripción")
        self.tabla_inventario.heading("categoria", text="Categoría")
        self.tabla_inventario.heading("precio", text="Precio")
        self.tabla_inventario.heading("stock", text="Stock")

        self.tabla_inventario.column("id", width=40, anchor="center")
        self.tabla_inventario.column("stock", width=60, anchor="center")

        # SE FUERZAN COLORES
        self.tabla_inventario.tag_configure("agotado", background="#ffcccc", foreground="#990000")
        self.tabla_inventario.tag_configure("bajo_stock", background="#ffffcc", foreground="#cc8800")

        self.tabla_inventario.pack(fill="both", expand=True)

        self.menu_contextual = tk.Menu(self, tearoff=0)
        self.menu_contextual.add_command(label="Editar precio", command=self.context_editar_precio)
        self.menu_contextual.add_command(label="Editar stock", command=self.context_editar_stock)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Eliminar producto", command=self.context_eliminar_producto)

        self.tabla_inventario.bind("<Button-3>", self.mostrar_menu_contextual)

        self.actualizar_vista_inventario()

    def guardar_nuevo_producto(self, event=None):
        codigo = self.entry_inv_codigo.get().strip()
        nombre = self.entry_inv_nombre.get().strip()
        categoria = self.entry_inv_categoria.get().strip().capitalize()
        precio_str = self.entry_inv_precio.get().strip()
        stock_str = self.entry_inv_stock.get().strip()

        if not (nombre and precio_str and stock_str):
            messagebox.showwarning("Campos vacíos", "El Nombre, Precio y Stock son obligatorios.")
            return

        try:
            precio = float(precio_str)
            stock = int(stock_str)
        except ValueError:
            messagebox.showerror("Error", "Precio y Stock deben ser numéricos.")
            return

        exito, msj = agregar_producto(codigo, nombre, categoria, precio, stock)
        if exito:
            self.entry_inv_codigo.delete(0, tk.END)
            self.entry_inv_nombre.delete(0, tk.END)
            self.entry_inv_categoria.set('')
            self.entry_inv_precio.delete(0, tk.END)
            self.entry_inv_stock.delete(0, tk.END)

            self.actualizar_vista_inventario()
            self.actualizar_catalogo(self.entry_buscador.get())
            self.entry_inv_codigo.focus_set()
        else:
            messagebox.showerror("Error", msj)

    def actualizar_vista_inventario(self):
        for row in self.tabla_inventario.get_children():
            self.tabla_inventario.delete(row)

        productos = obtener_todos()
        for p in productos:
            stock_actual = p[5]
            if stock_actual == 0:
                tag = "agotado"
            elif 1 <= stock_actual <= 7:
                tag = "bajo_stock"
            else:
                tag = "normal"
            self.tabla_inventario.insert("", "end", values=(p[0], p[1], p[2], p[3], f"${p[4]:.2f}", p[5]), tags=(tag,))

        self.entry_inv_categoria['values'] = obtener_categorias()

    def mostrar_menu_contextual(self, event):
        item = self.tabla_inventario.identify_row(event.y)
        if item:
            self.tabla_inventario.selection_set(item)
            self.menu_contextual.tk_popup(event.x_root, event.y_root)

    def context_editar_precio(self):
        item_seleccionado = self.tabla_inventario.selection()
        if not item_seleccionado: return

        valores = self.tabla_inventario.item(item_seleccionado[0], "values")
        p_id, nombre, precio_actual = int(valores[0]), valores[2], valores[4].replace('$', '')

        nuevo_precio_str = simpledialog.askstring("Editar Precio", f"Nuevo precio para {nombre}:",
                                                  initialvalue=precio_actual)

        if nuevo_precio_str is not None:
            try:
                nuevo_precio = float(nuevo_precio_str)
                exito, msj = actualizar_precio_por_id(p_id, nuevo_precio)
                if exito:
                    self.actualizar_vista_inventario()
                    self.actualizar_catalogo(self.entry_buscador.get())
                else:
                    messagebox.showerror("Error", msj)
            except ValueError:
                messagebox.showerror("Error", "El precio debe ser un número válido.")

    def context_editar_stock(self):
        item_seleccionado = self.tabla_inventario.selection()
        if not item_seleccionado: return

        valores = self.tabla_inventario.item(item_seleccionado[0], "values")
        p_id, nombre, stock_actual = int(valores[0]), valores[2], valores[5]

        nuevo_stock_str = simpledialog.askstring("Editar Stock", f"Nuevo stock para {nombre}:",
                                                 initialvalue=stock_actual)

        if nuevo_stock_str is not None:
            try:
                nuevo_stock = int(nuevo_stock_str)
                exito, msj = actualizar_stock_por_id(p_id, nuevo_stock)
                if exito:
                    self.actualizar_vista_inventario()
                    self.actualizar_catalogo(self.entry_buscador.get())

                    if p_id in self.carrito:
                        self.carrito[p_id]['stock_maximo'] = nuevo_stock
                        if self.carrito[p_id]['cantidad'] > nuevo_stock:
                            self.carrito[p_id]['cantidad'] = nuevo_stock
                        if self.carrito[p_id]['cantidad'] <= 0:
                            del self.carrito[p_id]
                        self.renderizar_carrito()
                else:
                    messagebox.showerror("Error", msj)
            except ValueError:
                messagebox.showerror("Error", "El stock debe ser entero.")

    def context_eliminar_producto(self):
        item_seleccionado = self.tabla_inventario.selection()
        if not item_seleccionado: return

        valores = self.tabla_inventario.item(item_seleccionado[0], "values")
        p_id, nombre = int(valores[0]), valores[2]

        if messagebox.askyesno("Confirmar", f"¿Eliminar '{nombre}'?"):
            exito, msj = eliminar_producto(p_id)
            if exito:
                self.actualizar_vista_inventario()
                self.actualizar_catalogo(self.entry_buscador.get())

                if p_id in self.carrito:
                    del self.carrito[p_id]
                    self.renderizar_carrito()
            else:
                messagebox.showerror("Error", msj)

    # =========================================================================
    # PESTAÑA 3: CAJA E HISTORIAL DE VENTAS
    # =========================================================================
    def setup_tab_caja(self):
        # FRAME DE FILTROS
        frame_filtros = ttk.LabelFrame(self.tab_caja, text=" Filtros del Día ", padding=10)
        frame_filtros.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_filtros, text="Inicio Jornada (HH:MM):").pack(side="left", padx=5)
        self.entry_hora_ini = ttk.Entry(frame_filtros, width=8)
        self.entry_hora_ini.pack(side="left", padx=5)

        ttk.Label(frame_filtros, text="Fin Jornada (HH:MM):").pack(side="left", padx=15)
        self.entry_hora_fin = ttk.Entry(frame_filtros, width=8)
        self.entry_hora_fin.pack(side="left", padx=5)

        btn_filtrar = ttk.Button(frame_filtros, text="Aplicar Filtros", command=self.actualizar_vista_caja)
        btn_filtrar.pack(side="left", padx=20)

        # ---
        frame_resumen = ttk.Frame(self.tab_caja, padding=10)
        frame_resumen.pack(fill="x")

        self.label_recaudacion = ttk.Label(frame_resumen, text="Recaudación: $0.00", font=("Arial", 16, "bold"))
        self.label_recaudacion.pack(side="left")

        btn_refrescar = ttk.Button(frame_resumen, text="Refrescar Historial", command=self.actualizar_vista_caja)
        btn_refrescar.pack(side="right", ipady=5, ipadx=5)

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

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla_caja.yview)
        self.tabla_caja.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.actualizar_vista_caja()

    def actualizar_vista_caja(self):
        for row in self.tabla_caja.get_children():
            self.tabla_caja.delete(row)

        ventas = obtener_historial_ventas()
        total_recaudado = 0

        # OBTENEMOS LOS FILTROS
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        hora_ini = self.entry_hora_ini.get().strip()
        hora_fin = self.entry_hora_fin.get().strip()

        for v in ventas:
            fecha_venta = v[1]  # Ej: "2023-10-25 14:30:00"

            # FILTRAMOS SOLO LO DE HOY
            if fecha_venta.startswith(hoy_str):
                hora_venta = fecha_venta[11:16]  # Extrae "HH:MM"

                # SI HAY FILTRO DE JORNADA CARGADO, VERIFICAMOS QUE ESTÉ EN EL RANGO
                if hora_ini and hora_fin:
                    if not (hora_ini <= hora_venta <= hora_fin):
                        continue  # Lo saltea si no entra en la jornada

                self.tabla_caja.insert("", "end", values=(v[0], v[1], f"${v[2]:.2f}"))
                total_recaudado += v[2]

        self.label_recaudacion.config(text=f"Recaudación de Hoy: ${total_recaudado:.2f}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()