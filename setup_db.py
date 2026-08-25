import sqlite3
import os

def inicializar_base_datos():
    # Nombre del archivo de la base de datos
    db_path = "parqueadero.db"
    
    # Conectarse a la base de datos (si no existe, la crea automáticamente)
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    # 1. Crear tabla de Tarifas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tarifas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo_vehiculo TEXT UNIQUE NOT NULL,
        valor_hora REAL NOT NULL,
        valor_12_horas REAL NOT NULL,
        valor_dia REAL NOT NULL,
        valor_mes REAL NOT NULL
    )
    ''')

    # 2. Crear tabla de Registros (Transacciones)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT NOT NULL,
        tipo_vehiculo TEXT NOT NULL,
        hora_ingreso DATETIME NOT NULL,
        hora_salida DATETIME,
        estado TEXT NOT NULL DEFAULT 'ACTIVO', 
        total_pagado REAL DEFAULT 0
    )
    ''')

    # 3. Insertar las tarifas iniciales basadas en tu imagen (Solo si la tabla está vacía)
    cursor.execute("SELECT COUNT(*) FROM tarifas")
    if cursor.fetchone()[0] == 0:
        tarifas_iniciales = [
            ('CARRO', 2500, 15000, 20000, 125000),
            ('MOTO', 1000, 8000, 12000, 50000)
        ]
        cursor.executemany('''
        INSERT INTO tarifas (tipo_vehiculo, valor_hora, valor_12_horas, valor_dia, valor_mes)
        VALUES (?, ?, ?, ?, ?)
        ''', tarifas_iniciales)
        print("Tarifas iniciales configuradas correctamente.")

    # Guardar cambios y cerrar la conexión
    conexion.commit()
    conexion.close()
    
    print(f"¡Base de datos '{db_path}' creada y configurada con éxito!")

if __name__ == "__main__":
    inicializar_base_datos()