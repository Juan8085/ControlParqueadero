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

# --- ZONA DE PRUEBA ---
# Este bloque solo se ejecuta si corremos este archivo directamente
if __name__ == "__main__":
    print("--- SIMULANDO INGRESO DE VEHÍCULO ---")
    
    # Datos simulados que luego vendrán de la interfaz gráfica
    placa_prueba = "XYZ-123"
    tipo_prueba = "CARRO"
    
    # 1. Registrar en la base de datos
    id_generado, hora_ingreso = registrar_ingreso(placa_prueba, tipo_prueba)
    
    # 2. Generar el código QR físico
    generar_qr_ticket(id_generado, placa_prueba)