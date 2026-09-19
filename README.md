# Smart AI Plant Monitoring & Control

An AI-assisted plant-monitoring project combining an ESP32 sensor node with a Python LSTM workflow for forecasting environmental conditions and controlling irrigation and lighting.

## Sensors & Inputs
- Soil moisture
- MQ2 gas / air-quality reading
- LDR light level
- Room temperature
- Humidity
- Water temperature
- Plant / pot weight

## AI & Automation
The Python application maintains sensor history, trains an LSTM-based prediction model, forecasts selected values, and sends pump/light commands back to the ESP32.

## Technology
ESP32, Arduino/C++, Python, TensorFlow/Keras, NumPy, Blynk, DHT11, DS18B20, HX711/load cell, MQ2, LDR, soil-moisture sensor.

## Structure
```text
Smart_AI_Plant/
├── code/
│   ├── Smart_AI.py
│   ├── SMART/SMART.ino
│   ├── ai_model.h5
│   └── sensor_data.csv
├── components/
├── results/
├── BLOCK.drawio
├── FLOW.drawio
└── Fritzing_file.fzz
```

## Security
Public firmware uses placeholder Wi-Fi and Blynk credentials. Add your own values locally and keep secrets out of Git.

## Future Improvements
- Separate configuration from source code
- Improve time-series validation
- Add MQTT instead of raw socket communication
- Add model versioning
- Add fail-safe actuator rules
- Add a full web dashboard

## Author
**Sadik Shaik**
