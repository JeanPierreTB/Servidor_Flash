import csv
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Ruta al archivo donde se almacenarán los datos
DATA_FILE = 'sensor_data.csv'

# Comprobar si el archivo CSV ya existe
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Escribir el encabezado del archivo CSV
        writer.writerow(['id', 'acc_X', 'acc_Y', 'acc_Z', 'temperatura', 'frecuencia'])

@app.route('/sensor-data', methods=['POST'])
def recibir_datos():
    try:
        data = request.json

        # Contar las filas existentes para generar un nuevo ID
        with open(DATA_FILE, mode='r') as file:
            reader = csv.reader(file)
            num_rows = sum(1 for row in reader)

        # Crear un nuevo registro
        new_data = [
            num_rows,  # ID
            data.get('acc_X'),
            data.get('acc_Y'),
            data.get('acc_Z'),
            data.get('temperatura'),
            data.get('frecuencia')
        ]

        # Escribir el nuevo registro en el archivo CSV
        with open(DATA_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(new_data)

        return jsonify({"status": "datos recibidos y almacenados"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sensor-data', methods=['GET'])
def obtener_datos():
    try:
        # Leer los datos del archivo CSV
        data_list = []
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_list.append(row)

        return jsonify(data_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

