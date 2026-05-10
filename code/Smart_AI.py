import socket
import numpy as np
import time
import os
import csv
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.losses import MeanSquaredError

ESP_IP = "192.168.8.179"
PORT = 80
MODEL_FILE = "ai_model.h5"
CSV_FILE = "sensor_data.csv"

history = []
soil_threshold = 2500
ldr_threshold = 2000
mq2_threshold = 400
pump_cycles = 0

if os.path.exists(MODEL_FILE):
    model = load_model(MODEL_FILE, custom_objects={"mse": MeanSquaredError()})
else:
    model = Sequential()
    model.add(LSTM(64, input_shape=(1,7)))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(7))
    model.compile(optimizer='adam', loss=MeanSquaredError())

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "MQ2","Soil","LDR","RoomTemp","Humidity","WaterTemp","Weight",
            "Pred_Soil","Pred_RoomTemp","Pred_Humidity","Pred_WaterTemp"
        ])

def auto_calibration():
    global soil_threshold, ldr_threshold, mq2_threshold
    data = np.array(history)
    soil_threshold = int(np.mean(data[:,1]) + 200)
    ldr_threshold = int(np.mean(data[:,2]))
    mq2_threshold = int(np.mean(data[:,0]) + 100)

def predict_soil_dry_time():
    if len(history) < 10:
        return "Learning..."
    soil_vals = [x[1] for x in history[-10:]]
    trend = soil_vals[-1] - soil_vals[0]
    if trend <= 0:
        return "Stable"
    rate = trend / 10
    minutes = int((soil_threshold - soil_vals[-1]) / rate)
    if minutes < 0: minutes = 0
    return str(minutes) + " min"

def predict_tank_empty():
    global pump_cycles
    if pump_cycles < 3:
        return "Learning..."
    minutes = 30 - pump_cycles * 3
    if minutes < 5: return "CRITICAL"
    return str(minutes) + " min"

def predict_mq2(prediction):
    future_mq2 = prediction[0]
    if future_mq2 > mq2_threshold:
        return "BAD AIR WARNING"
    return "AIR NORMAL"

def save_to_csv(values, prediction):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            values[0], values[1], values[2], values[3], values[4],
            values[5], values[6], prediction[1], prediction[3],
            prediction[4], prediction[5]
        ])

def display(values, prediction, pump, light, plant_msg):
    mq2, soil, ldr, tempRoom, humidity, waterTemp, weight = values
    soil_time = predict_soil_dry_time()
    tank_time = predict_tank_empty()
    mq2_status = predict_mq2(prediction)
    print("\n==============================")
    print("\nSENSOR VALUES\n")
    print("MQ2 Gas          :", int(mq2))
    print("Soil Moisture    :", int(soil))
    print("LDR Light Level  :", int(ldr))
    print("Room Temperature :", round(tempRoom,2), "C")
    print("Humidity         :", round(humidity,2), "%")
    print("Water Temperature:", round(waterTemp,2), "C")
    print("Weight           :", round(weight,2), "g")
    print("\nAI PREDICTION\n")
    print("Next Soil Moisture     :", round(prediction[1],2))
    print("Next Room Temperature  :", round(prediction[3],2))
    print("Next Humidity          :", round(prediction[4],2))
    print("Next Water Temperature :", round(prediction[5],2))
    print("\nSMART FORECASTS\n")
    print("Soil Dry In       :", soil_time)
    print("Tank Empty In     :", tank_time)
    print("MQ2 Forecast      :", mq2_status)
    print("\nAI DECISION\n")
    print("Pump  :", pump)
    print("Light :", light)
    print("Plant :", plant_msg)
    print("\n==============================")

def decide(values, prediction):
    global pump_cycles
    mq2, soil, ldr, tempRoom, humidity, waterTemp, weight = values
    pump_cmd, light_cmd = "PUMP_OFF", "LIGHT_OFF"
    pump_text, light_text = "OFF", "OFF"
    plant_message = "Plant OK"
    if weight < 200:
        plant_message = "Please put a healthy plant"
    if weight > 200:
        if soil < soil_threshold and waterTemp < 30:
            pump_cmd, pump_text = "PUMP_ON", "ON"
            pump_cycles += 1
        elif soil > soil_threshold or waterTemp >= 30:
            pump_cmd, pump_text = "PUMP_OFF", "OFF"
        if ldr < ldr_threshold:
            light_cmd, light_text = "LIGHT_ON", "ON"
    return pump_cmd, light_cmd, pump_text, light_text, plant_message

while True:
    try:
        s = socket.socket()
        s.connect((ESP_IP, PORT))
        data = s.recv(1024).decode().strip()
        values = list(map(float, data.split(",")))
        history.append(values)
        prediction = values
        if len(history) > 20:
            X = np.array(history[:-1]).reshape((-1,1,7))
            y = np.array(history[1:])
            model.fit(X, y, epochs=1, verbose=0)
            x_pred = np.array(values).reshape((1,1,7))
            prediction = model.predict(x_pred, verbose=0)[0]
        if len(history) % 50 == 0:
            auto_calibration()
            model.save(MODEL_FILE)
        pump_cmd, light_cmd, pump_text, light_text, plant_msg = decide(values, prediction)
        display(values, prediction, pump_text, light_text, plant_msg)
        save_to_csv(values, prediction)
        s.send((pump_cmd+"\n").encode())
        s.send((light_cmd+"\n").encode())
        s.close()
        time.sleep(2)
    except Exception as e:
        print("Connection Error:", e)
        time.sleep(2)
