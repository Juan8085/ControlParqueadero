import sqlite3
import datetime
import qrcode
import os

# Asegurarnos de que exista una carpeta para guardar las imágenes de los QR
if not os.path.exists("tickets"):
    os.makedirs("tickets")

def registrar_ingreso(placa, tipo_vehiculo):
    """Guarda la entrada del vehículo en la base de datos."""
    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()
    
    # Capturar la hora exacta del sistema en este instante
    hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insertar el registro (el estado por defecto es 'ACTIVO')
    cursor.execute('''
    INSERT INTO registros (placa, tipo_vehiculo, hora_ingreso)
    VALUES (?, ?, ?)
    ''', (placa, tipo_vehiculo, hora_actual))
    
    # Obtener el número de ID (Ticket) que la base de datos acaba de crear
    ticket_id = cursor.lastrowid
    
    conexion.commit()
    conexion.close()
    
    return ticket_id, hora_actual

def generar_qr_ticket(ticket_id, placa):
    """Genera una imagen QR con la información de cobro."""
    # El lector de QR leerá este texto exactamente: "ID-PLACA" (Ej: 1-XYZ123)
    datos_qr = f"{ticket_id}-{placa}"
    
    # Configuración del diseño del QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(datos_qr)
    qr.make(fit=True)
    
    imagen = qr.make_image(fill="black", back_color="white")
    
    # Guardar la imagen en la carpeta tickets
    nombre_archivo = f"tickets/ticket_{ticket_id}_{placa}.png"
    imagen.save(nombre_archivo)
    
    print(f"✅ Ingreso exitoso: Ticket #{ticket_id} para placa {placa}.")
    print(f"📁 QR guardado en: {nombre_archivo}")
import math
import csv

import os

def generar_recibo_fisico(ticket_id, placa, tipo_vehiculo, hora_ingreso):
    """Genera un recibo vertical con texto y QR alineados al centro para tiquetera térmica."""
    
    # 1. Datos actualizados del parqueadero
    nombre_parqueadero = "PARQUEADERO LA CATEDRAL"
    direccion = "Calle 6 # 7-31"
    telefono = "3142579681"
    
    # Asegurar que la carpeta 'tickets' exista
    if not os.path.exists("tickets"):
        os.makedirs("tickets")

    ruta_qr = f"tickets/ticket_{ticket_id}_{placa}.png"
    ruta_recibo_imagen = f"tickets/recibo_impresion_{ticket_id}_{placa}.png"
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Verificar si el archivo QR existe, si no, crearlo
        if not os.path.exists(ruta_qr):
            generar_qr_ticket(ticket_id, placa)
            
        img_qr = Image.open(ruta_qr).resize((150, 150)) # QR compacto para recibo
        
        # 2. CONFIGURACIÓN VERTICAL (Formato Tira Térmica)
        # Ancho: 320 píxeles, Alto: 480 píxeles (Vertical total)
        ancho_recibo = 320
        alto_recibo = 520
        img_recibo = Image.new("RGB", (ancho_recibo, alto_recibo), "white")
        draw = ImageDraw.Draw(img_recibo)
        
        try:
            fuente = ImageFont.load_default()
        except Exception:
            fuente = None

        # Líneas de texto organizadas para formato vertical
        lineas = [
            "================================",
            f"   {nombre_parqueadero}   ",
            f"   Dir: {direccion}   ",
            f"   Tel: {telefono}   ",
            "================================",
            "TICKET DE INGRESO",
            "--------------------------------",
            f"Nro Ticket : #{ticket_id}",
            f"Placa      : {placa}",
            f"Vehículo   : {tipo_vehiculo}",
            f"Ingreso    : {hora_ingreso}",
            "--------------------------------",
            "* Conserve este ticket para su",
            "  salida. En caso de pérdida",
            "  se cobrará multa.",
            "* Tiempo de gracia: 15 min.",
            "================================",
            "     ¡GRACIAS POR SU VISITA!    ",
            "================================"
        ]

        # Escribir el texto alineado con buen margen izquierdo (ej. 15 píxeles)
        y_offset = 10
        for linea in lineas:
            draw.text((15, y_offset), linea, fill="black", font=fuente)
            y_offset += 16
            
        # 3. CENTRAR EL CÓDIGO QR EXACTAMENTE EN LA MITAD HORIZONTAL
        # (Ancho del recibo 320 - Ancho del QR 150) / 2 = 85 píxeles de margen izquierdo
        x_centrado = (ancho_recibo - 150) // 2
        img_recibo.paste(img_qr, (x_centrado, y_offset + 5))
        
        # Guardar la imagen final vertical y centrada
        ruta_absoluta = os.path.abspath(ruta_recibo_imagen)
        img_recibo.save(ruta_absoluta)
        
        print(f"🖼️ Recibo vertical unificado creado: {ruta_absoluta}")
        
        # Lanzar diálogo de impresión de Windows
        os.startfile(ruta_absoluta, "print")

    except Exception as e:
        print(f"⚠️ Error generando el recibo gráfico o lanzando impresión: {e}")

    return ruta_recibo_imagen

def calcular_tarifa(tipo_vehiculo, tiempo_transcurrido):
    """Calcula el cobro basado en la imagen image_be7527.jpg"""
    # Convertir el tiempo a minutos para mayor precisión
    minutos_totales = tiempo_transcurrido.total_seconds() / 60
    
    # Tiempo de gracia de 15 minutos (si entra y sale rápido, no cobra)
    if minutos_totales <= 15:
        return 0
        
    horas = math.ceil(minutos_totales / 60) # Se cobra la fracción como hora completa
    dias = math.ceil(horas / 24)
    monto = 0

    if tipo_vehiculo == 'CARRO':
        if horas <= 6:  # 6h * 2500 = 15000 (Tope antes de la tarifa de 12h)
            monto = horas * 2500
        elif horas <= 12:
            monto = 15000
        elif horas <= 24:
            monto = 20000 # 1 día
        elif dias == 2:
            monto = 40000
        elif dias == 3:
            monto = 55000
        elif 4 <= dias <= 6:
            monto = 75000
        elif 7 <= dias <= 14:
            monto = 95000
        elif 15 <= dias <= 22:
            monto = 115000
        elif 23 <= dias <= 30:
            monto = 125000 # Tarifa de mes (ajustado según la imagen)
            
    elif tipo_vehiculo == 'MOTO':
        if horas <= 8: # 8h * 1000 = 8000 (Tope antes de la tarifa de 12h)
            monto = horas * 1000
        elif horas <= 12:
            monto = 8000
        elif horas <= 24:
            monto = 12000
        elif dias == 2:
            monto = 20000
        elif dias == 3:
            monto = 25000
        elif 4 <= dias <= 6:
            monto = 30000
        elif 7 <= dias <= 14:
            monto = 40000
        elif 15 <= dias <= 22:
            monto = 50000
        elif 23 <= dias <= 30:
            monto = 50000 # Mensualidad (ajustado según la imagen)

    return monto

def registrar_salida(datos_qr):
    """Simula la lectura de la pistola QR, liquida el pago y cierra el ticket."""
    try:
        # El 1 al final indica que solo debe dividir por el PRIMER guion que encuentre.
        # Así "2-XYZ-123" se divide correctamente en "2" y "XYZ-123".
        ticket_id, placa = datos_qr.split('-', 1)
    except ValueError:
        return {"error": "Código QR inválido."}

    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()

    # Buscar el registro activo en la base de datos
    cursor.execute('''
        SELECT tipo_vehiculo, hora_ingreso FROM registros 
        WHERE id = ? AND placa = ? AND estado = 'ACTIVO'
    ''', (ticket_id, placa))
    
    registro = cursor.fetchone()
    
    if not registro:
        conexion.close()
        return {"error": f"No se encontró un vehículo activo con la placa {placa}."}

    tipo_vehiculo = registro[0]
    hora_ingreso = datetime.datetime.strptime(registro[1], "%Y-%m-%d %H:%M:%S")
    
    # Simular que pasaron horas o usar la hora actual (para pruebas sumaremos horas)
    hora_actual = datetime.datetime.now()
    tiempo_transcurrido = hora_actual - hora_ingreso

    # Calcular cuánto debe pagar
    total_a_pagar = calcular_tarifa(tipo_vehiculo, tiempo_transcurrido)

    # Actualizar la base de datos cerrando el ticket
    cursor.execute('''
        UPDATE registros 
        SET hora_salida = ?, estado = 'PAGADO', total_pagado = ? 
        WHERE id = ?
    ''', (hora_actual.strftime("%Y-%m-%d %H:%M:%S"), total_a_pagar, ticket_id))
    
    conexion.commit()
    conexion.close()

    # Retornar el resumen de la operación
    horas_totales = round(tiempo_transcurrido.total_seconds() / 3600, 2)
    return {
        "placa": placa,
        "tipo": tipo_vehiculo,
        "tiempo": f"{horas_totales} horas",
        "total": f"${total_a_pagar:,.0f}"
    }

from dateutil.relativedelta import relativedelta # Necesario para sumar un mes exacto

def registrar_mensualidad(placa, tipo_vehiculo):
    """Registra el pago de un mes para una placa y actualiza las estadísticas."""
    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()
    
    # Determinar el valor de la mensualidad según tu tabla de tarifas
    valor_mensualidad = 125000 if tipo_vehiculo == 'CARRO' else 50000
    
    fecha_pago = datetime.datetime.now()
    fecha_vencimiento = fecha_pago + relativedelta(months=1)
    
    try:
        # Usamos REPLACE por si el cliente ya existía y está renovando
        cursor.execute('''
        INSERT OR REPLACE INTO mensualidades (placa, tipo_vehiculo, fecha_pago, fecha_vencimiento, total_pagado)
        VALUES (?, ?, ?, ?, ?)
        ''', (placa, tipo_vehiculo, fecha_pago.strftime("%Y-%m-%d"), fecha_vencimiento.strftime("%Y-%m-%d"), valor_mensualidad))
        
        # Opcional: Registrar este pago en la tabla de transacciones generales para que sume en el Excel y cuadre la caja del día
        cursor.execute('''
        INSERT INTO registros (placa, tipo_vehiculo, hora_ingreso, hora_salida, estado, total_pagado)
        VALUES (?, ?, ?, ?, 'PAGADO', ?)
        ''', (placa, f"{tipo_vehiculo} (MES)", fecha_pago.strftime("%Y-%m-%d %H:%M:%S"), fecha_pago.strftime("%Y-%m-%d %H:%M:%S"), valor_mensualidad))
        
        conexion.commit()
        resultado = True
    except Exception as e:
        print(f"Error al registrar mensualidad: {e}")
        resultado = False
    finally:
        conexion.close()
        
    return resultado, fecha_vencimiento.strftime("%Y-%m-%d")

def verificar_mensualidad_activa(placa):
    """Verifica si una placa tiene un mes pagado y vigente."""
    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()
    
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute('''
        SELECT fecha_vencimiento FROM mensualidades 
        WHERE placa = ? AND fecha_vencimiento >= ?
    ''', (placa, hoy))
    
    registro = cursor.fetchone()
    conexion.close()
    
    if registro:
        return True, registro[0] # Retorna True y la fecha de vencimiento
    return False, None

def obtener_estadisticas():
    """Consulta la base de datos para obtener las ventas de hoy y el histórico mensual."""
    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()
    
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 1. Calcular Ventas del Día Actual
    cursor.execute('''
        SELECT tipo_vehiculo, SUM(total_pagado), COUNT(id) 
        FROM registros 
        WHERE estado = 'PAGADO' AND date(hora_salida) = ? 
        GROUP BY tipo_vehiculo
    ''', (hoy,))
    ventas_hoy = cursor.fetchall()
    
    # 2. Calcular Ventas Agrupadas por Mes (Para el comparativo)
    cursor.execute('''
        SELECT strftime('%Y-%m', hora_salida) as mes, SUM(total_pagado), COUNT(id)
        FROM registros 
        WHERE estado = 'PAGADO' 
        GROUP BY mes 
        ORDER BY mes DESC
    ''')
    ventas_mes = cursor.fetchall()
    conexion.close()
    
    return ventas_hoy, ventas_mes

def exportar_excel_csv():
    """Exporta todos los registros pagados a un archivo apto para Excel."""
    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id, placa, tipo_vehiculo, hora_ingreso, hora_salida, total_pagado 
        FROM registros WHERE estado = 'PAGADO'
    ''')
    datos = cursor.fetchall()
    conexion.close()
    
    # Generar un nombre de archivo único con la fecha y hora
    nombre_archivo = f"Reporte_Parqueadero_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';') # El punto y coma facilita abrirlo en Excel en español
        writer.writerow(['ID_Ticket', 'Placa', 'Tipo', 'Fecha Ingreso', 'Fecha Salida', 'Total Cobrado'])
        writer.writerows(datos)
        
    return nombre_archivo
# --- ZONA DE PRUEBA ---
if __name__ == "__main__":
    print("--- 1. SIMULANDO INGRESO ---")
    placa_prueba = "XYZ-123"
    tipo_prueba = "CARRO"
    id_generado, hora_in = registrar_ingreso(placa_prueba, tipo_prueba)
    generar_qr_ticket(id_generado, placa_prueba)
    
    print("\n--- 2. SIMULANDO LECTURA CON PISTOLA QR (SALIDA) ---")
    conexion = sqlite3.connect("parqueadero.db")
    cursor = conexion.cursor()
    hace_10_horas = (datetime.datetime.now() - datetime.timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE registros SET hora_ingreso = ? WHERE id = ?", (hace_10_horas, id_generado))
    conexion.commit()
    conexion.close()

    codigo_leido = f"{id_generado}-{placa_prueba}"
    resultado = registrar_salida(codigo_leido)
    
    # Validación para evitar caídas si hay un error en la lectura
    if "error" in resultado:
        print(f"❌ ERROR: {resultado['error']}")
    else:
        print("\n================ TICKET DE SALIDA ================")
        print(f"Placa: {resultado['placa']}")
        print(f"Tipo: {resultado['tipo']}")
        print(f"Tiempo: {resultado['tiempo']}")
        print(f"TOTAL A PAGAR: {resultado['total']}")
        print("==================================================")