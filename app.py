from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Endpoint para recibir datos de sensores (POST)
@app.route('/sensor-data', methods=['POST'])
def recibir_datos():
    data = request.json
    print(f"Datos recibidos: {data}")
    return jsonify({"status": "datos recibidos"}), 200

# Endpoint GET para verificar que el servidor funciona
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "El servidor está funcionando correctamente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
