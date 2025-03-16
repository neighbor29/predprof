from flask import Flask, render_template, jsonify
import requests
import numpy as np
from scipy.ndimage import maximum_filter

app = Flask(__name__)


API_URL = "https://olimp.miet.ru/ppo_it/api"


def get_tile():
    try:
        headers = {
            "Authorization": "Bearer YOUR_TOKEN"
        }
        response = requests.get(f"{API_URL}", headers=headers)
        response.raise_for_status()
        tile_data = response.json()['message']['data']
        print("Тайл получен:", tile_data)
        return tile_data
    except requests.RequestException as e:
        print(f"Ошибка при получении тайла: {e}")
        print(f"Статус код: {response.status_code}")
        print(f"Ответ сервера: {response.text}")
        return None


def assemble_map():
    map_data = np.zeros((256, 256), dtype=int)
    for i in range(16):
        tile = get_tile()
        if tile and len(tile) == 64 and len(tile[0]) == 64:
            x_start = (i % 4) * 64
            y_start = (i // 4) * 64
            map_data[y_start:y_start+64, x_start:x_start+64] = tile
        else:
            print(f"Тайл {i} не был загружен или имеет неверный формат.")
    print("Карта собрана:", map_data)
    return map_data


def find_peaks(map_data):
    neighborhood_size = 3
    data_max = maximum_filter(map_data, neighborhood_size)
    peaks = (map_data == data_max)
    return np.argwhere(peaks)


def place_stations(peaks, map_data):
    stations = []
    for peak in peaks:
        x, y = peak
        height = map_data[x][y]
        if height > 200:
            station_type = "Энгель" if height > 220 else "Купер"
            stations.append({"x": x, "y": y, "type": station_type})
    print("Станции размещены:", stations)
    return stations


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_map", methods=["GET"])
def get_map():
    try:
        map_data = assemble_map()
        return jsonify(map_data.tolist())
    except Exception as e:
        print(f"Ошибка при сборке карты: {e}")
        return jsonify({"error": "Не удалось собрать карту"}), 500


@app.route("/place_stations", methods=["POST"])
def place_stations_route():
    try:
        map_data = assemble_map()
        peaks = find_peaks(map_data)
        stations = place_stations(peaks, map_data)
        return jsonify(stations)
    except Exception as e:
        print(f"Ошибка при размещении станций: {e}")
        return jsonify({"error": "Не удалось разместить станции"}), 500

if __name__ == "__main__":
    app.run(port=8083, debug=True)