import tkinter as tk
from tkinter import ttk, messagebox
import operaciones 
import setup_db # <-- NUEVO

# Aseguramos que la base de datos y las tablas existan al abrir el programa
setup_db.inicializar_base_datos() # <-- NUEVO

def procesar_ingreso():
    placa = entry_placa.get().strip().upper()
    tipo = combo_tipo.get()
    
    if not placa:
        messagebox.showerror("Error", "Por favor, digite la placa del vehículo.")
        return
        
    try:
        # Verificar mensualidad activa
        es_mensual, vencimiento = operaciones.verificar_mensualidad_activa(placa)
        
        if es_mensual:
            messagebox.showinfo(
                "Vehículo Autorizado (MENSUALIDAD)", 
                f"El vehículo con placa {placa} tiene una MENSUALIDAD ACTIVA.\n\n"
                f"Vence el: {vencimiento}\n\n"
                "¡Puede ingresar sin generar ticket!"
            )
            entry_placa.delete(0, tk.END)
            return

        # Registrar entrada normal
        id_generado, hora_in = operaciones.registrar_ingreso(placa, tipo)
        operaciones.generar_qr_ticket(id_generado, placa)
        
        # Generar el recibo térmico en texto
        operaciones.generar_recibo_fisico(id_generado, placa, tipo, hora_in)
        
        messagebox.showinfo(
            "Ingreso Exitoso", 
            f"Ticket #{id_generado} registrado para {placa}.\n\n"
            "✅ Se generó el Código QR.\n"
            "✅ Se generó el recibo térmico para impresión."
        )
        entry_placa.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("Error del Sistema", f"Ocurrió un problema: {str(e)}")

def procesar_salida(event=None):
    """Esta función se activa al dar Enter en la caja de lectura QR"""
    codigo_leido = entry_qr.get().strip()
    
    if not codigo_leido:
        return

    # Llamamos a nuestro motor de liquidación
    resultado = operaciones.registrar_salida(codigo_leido)
    
    if "error" in resultado:
        messagebox.showerror("Error de Lectura", resultado["error"])
        # Limpiar resultados anteriores en pantalla
        lbl_res_placa.config(text="Placa: ---")
        lbl_res_tiempo.config(text="Tiempo: ---")
        lbl_res_total.config(text="TOTAL: $0", fg="black")
    else:
        # Mostrar el cobro en la pantalla en letras grandes
        lbl_res_placa.config(text=f"Placa: {resultado['placa']}")
        lbl_res_tiempo.config(text=f"Tiempo: {resultado['tiempo']}")
        lbl_res_total.config(text=f"TOTAL: {resultado['total']}", fg="green")
    
    entry_qr.delete(0, tk.END) # Limpiar para la siguiente lectura

def abrir_ventana_mensualidad():
    """Ventana para registrar o renovar una mensualidad."""
    ven_men = tk.Toplevel(ventana)
    ven_men.title("Gestión de Mensualidades")
    ven_men.geometry("400x300")
    ven_men.config(padx=20, pady=20)
    
    tk.Label(ven_men, text="REGISTRAR MENSUALIDAD", font=("Arial", 12, "bold")).pack(pady=10)
    
    tk.Label(ven_men, text="Placa del Vehículo:", font=("Arial", 10)).pack(anchor="w")
    e_placa = tk.Entry(ven_men, font=("Arial", 12), width=20)
    e_placa.pack(pady=5, fill="x")
    
    tk.Label(ven_men, text="Tipo de Vehículo:", font=("Arial", 10)).pack(anchor="w", pady=(5,0))
    c_tipo = ttk.Combobox(ven_men, values=["CARRO", "MOTO"], state="readonly", font=("Arial", 10), width=18)
    c_tipo.current(0)
    c_tipo.pack(pady=5, fill="x")
    
    def guardar_mensualidad():
        placa = e_placa.get().strip().upper()
        tipo = c_tipo.get()
        if not placa:
            messagebox.showerror("Error", "Debe digitar una placa.")
            return
            
        exito, vencimiento = operaciones.registrar_mensualidad(placa, tipo)
        if exito:
            valor = "$125,000" if tipo == "CARRO" else "$50,000"
            messagebox.showinfo("Éxito", f"Mensualidad registrada para {placa}.\nTotal cobrado: {valor}\nVálido hasta: {vencimiento}")
            ven_men.destroy()
        else:
            messagebox.showerror("Error", "No se pudo registrar la mensualidad.")

    tk.Button(ven_men, text="GUARDAR Y COBRAR MENSUALIDAD", bg="#2b6cb0", fg="white", font=("Arial", 10, "bold"), command=guardar_mensualidad).pack(pady=20, fill="x")

def abrir_panel_propietario():
    """Abre una nueva ventana con las estadísticas del parqueadero."""
    panel = tk.Toplevel(ventana)
    panel.title("Panel Administrativo - Control de Ingresos")
    panel.geometry("550x550")
    panel.config(padx=15, pady=15)
    
    tk.Label(panel, text="ESTADÍSTICAS DE VENTAS", font=("Arial", 14, "bold")).pack(pady=10)
    
    # Obtener datos del motor
    ventas_hoy, ventas_mes = operaciones.obtener_estadisticas()
    
    # --- SECCIÓN 1: INGRESOS DEL DÍA ---
    frame_hoy = tk.LabelFrame(panel, text="Resumen de Hoy", font=("Arial", 11, "bold"), padx=10, pady=10)
    frame_hoy.pack(fill="x", pady=5)
    
    total_dia = 0
    if not ventas_hoy:
        tk.Label(frame_hoy, text="Aún no hay ventas registradas hoy.", font=("Arial", 10)).pack()
    else:
        for v in ventas_hoy:
            tipo, total, cantidad = v
            total_dia += total
            tk.Label(frame_hoy, text=f"• {tipo}: {cantidad} servicios cerrados -> ${total:,.0f}", font=("Arial", 11)).pack(anchor="w")
            
    tk.Label(frame_hoy, text=f"TOTAL RECAUDADO HOY: ${total_dia:,.0f}", font=("Arial", 12, "bold"), fg="#008000").pack(pady=10)
    
    # --- SECCIÓN 2: HISTÓRICO MENSUAL ---
    frame_mes = tk.LabelFrame(panel, text="Comparativo Mensual", font=("Arial", 11, "bold"), padx=10, pady=10)
    frame_mes.pack(fill="both", expand=True, pady=10)
    
    # Crear una tabla para mostrar los meses
    columnas = ("Mes", "Cant. Servicios", "Total Ingresos")
    tabla = ttk.Treeview(frame_mes, columns=columnas, show="headings", height=8)
    tabla.heading("Mes", text="Año-Mes")
    tabla.heading("Cant. Servicios", text="Cant. Servicios")
    tabla.heading("Total Ingresos", text="Total Ingresos")
    
    # Ajustar ancho de columnas
    tabla.column("Mes", width=100, anchor="center")
    tabla.column("Cant. Servicios", width=120, anchor="center")
    tabla.column("Total Ingresos", width=150, anchor="e")
    tabla.pack(fill="both", expand=True)
    
    # Insertar los datos en la tabla
    for v in ventas_mes:
        mes, total, cantidad = v
        tabla.insert("", tk.END, values=(mes, cantidad, f"${total:,.0f}"))
        
    # --- SECCIÓN 3: EXPORTACIÓN ---
    def ejecutar_exportacion():
        try:
            archivo = operaciones.exportar_excel_csv()
            messagebox.showinfo("Exportación Exitosa", f"Los datos financieros se han guardado en Excel en el archivo:\n\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar: {str(e)}")
            
    tk.Button(panel, text="📥 Exportar Base de Datos a Excel (CSV)", bg="#217346", fg="white", font=("Arial", 10, "bold"), command=ejecutar_exportacion).pack(pady=10)
# --- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ---
ventana = tk.Tk()
ventana.title("Control de Parqueadero")
ventana.geometry("500x600")
ventana.config(padx=20, pady=20)

# Título General
tk.Label(ventana, text="SISTEMA DE PARQUEADERO", font=("Arial", 16, "bold")).pack(pady=10)

# --- PANEL DE INGRESO MODIFICADO (Campos independientes para Carro y Moto) ---
frame_ingreso = tk.LabelFrame(ventana, text="1. Registrar Ingreso (Generar Ticket)", font=("Arial", 11, "bold"), padx=10, pady=10)
frame_ingreso.pack(fill="x", pady=10)

# Opción Carro
tk.Label(frame_ingreso, text="Placa Carro:", font=("Arial", 10, "bold"), fg="#1a365d").grid(row=0, column=0, pady=5, sticky="e")
entry_placa_carro = tk.Entry(frame_ingreso, font=("Arial", 12), width=12)
entry_placa_carro.grid(row=0, column=1, padx=5, pady=5)

def registrar_carro():
    placa = entry_placa_carro.get().strip().upper()
    if not placa:
        messagebox.showerror("Error", "Por favor, digite la placa del carro.")
        return
    ejecutar_ingreso_general(placa, "CARRO")
    entry_placa_carro.delete(0, tk.END)

btn_ingresar_carro = tk.Button(frame_ingreso, text="Entrada Carro", bg="#0052cc", fg="white", font=("Arial", 9, "bold"), command=registrar_carro)
btn_ingresar_carro.grid(row=0, column=2, padx=5, pady=5)

# Opción Moto
tk.Label(frame_ingreso, text="Placa Moto:", font=("Arial", 10, "bold"), fg="#1a365d").grid(row=1, column=0, pady=5, sticky="e")
entry_placa_moto = tk.Entry(frame_ingreso, font=("Arial", 12), width=12)
entry_placa_moto.grid(row=1, column=1, padx=5, pady=5)

def registrar_moto():
    placa = entry_placa_moto.get().strip().upper()
    if not placa:
        messagebox.showerror("Error", "Por favor, digite la placa de la moto.")
        return
    ejecutar_ingreso_general(placa, "MOTO")
    entry_placa_moto.delete(0, tk.END)

btn_ingresar_moto = tk.Button(frame_ingreso, text="Entrada Moto", bg="#2b6cb0", fg="white", font=("Arial", 9, "bold"), command=registrar_moto)
btn_ingresar_moto.grid(row=1, column=2, padx=5, pady=5)

# Función interna unificada para procesar el ingreso y el recibo térmico
def ejecutar_ingreso_general(placa, tipo):
    try:
        # Verificar mensualidad activa
        es_mensual, vencimiento = operaciones.verificar_mensualidad_activa(placa)
        
        if es_mensual:
            messagebox.showinfo(
                "Vehículo Autorizado (MENSUALIDAD)", 
                f"El vehículo con placa {placa} tiene una MENSUALIDAD ACTIVA.\n\n"
                f"Vence el: {vencimiento}\n\n"
                "¡Puede ingresar sin generar ticket!"
            )
            return

        # Registrar entrada normal y generar ticket/recibo
        id_generado, hora_in = operaciones.registrar_ingreso(placa, tipo)
        operaciones.generar_qr_ticket(id_generado, placa)
        operaciones.generar_recibo_fisico(id_generado, placa, tipo, hora_in)
        
        messagebox.showinfo(
            "Ingreso Exitoso", 
            f"Ticket #{id_generado} registrado para {tipo} ({placa}).\n\n"
            "✅ QR generado.\n"
            "✅ Recibo térmico enviado a impresión."
        )
    except Exception as e:
        messagebox.showerror("Error del Sistema", f"Ocurrió un problema: {str(e)}")

# --- PANEL DE SALIDA (LECTURA PISTOLA) ---
frame_salida = tk.LabelFrame(ventana, text="2. Registrar Salida (Lectura Pistola QR)", font=("Arial", 11, "bold"), padx=10, pady=10)
frame_salida.pack(fill="x", pady=10)

tk.Label(frame_salida, text="Ubique el cursor aquí y escanee el QR:", font=("Arial", 10)).pack(pady=5)
entry_qr = tk.Entry(frame_salida, font=("Arial", 14), justify="center")
entry_qr.pack(pady=5, fill="x")
entry_qr.bind("<Return>", procesar_salida) # El evento <Return> es la tecla Enter

# Resultados del Cobro
frame_resultados = tk.Frame(frame_salida)
frame_resultados.pack(pady=10)

lbl_res_placa = tk.Label(frame_resultados, text="Placa: ---", font=("Arial", 12))
lbl_res_placa.pack()
lbl_res_tiempo = tk.Label(frame_resultados, text="Tiempo: ---", font=("Arial", 12))
lbl_res_tiempo.pack()
lbl_res_total = tk.Label(frame_resultados, text="TOTAL: $0", font=("Arial", 18, "bold"))
lbl_res_total.pack(pady=5)


# Botones administrativos al fondo de la ventana principal
btn_mensualidad = tk.Button(ventana, text="💳 Registrar / Renovar Mensualidad", bg="#2b6cb0", fg="white", font=("Arial", 10, "bold"), command=abrir_ventana_mensualidad)
btn_mensualidad.pack(pady=5, fill="x")

btn_admin = tk.Button(ventana, text="📊 Ver Panel del Propietario", bg="#333333", fg="white", font=("Arial", 10, "bold"), command=abrir_panel_propietario)
btn_admin.pack(pady=5, fill="x")

# Iniciar la aplicación
ventana.mainloop()