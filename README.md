# ICS Anomaly Detection System

This system performs anomaly detection on Industrial Control System (ICS) network traffic using machine learning. It extracts network behavior features, detects anomalies, and sends results through MQTT to Elasticsearch for visualization in Kibana.

## Features

- Real-time packet capture and analysis
- Machine learning-based anomaly detection using Isolation Forest
- 10 key network behavior features extraction:
  1. Packet Size
  2. Inter-arrival Time
  3. Protocol Type
  4. Port Number
  5. Packet Count
  6. Byte Count
  7. Flow Duration
  8. TCP Flags
  9. TCP Window Size
  10. Payload Length
- MQTT integration for real-time alerts
- Elasticsearch storage for historical analysis
- Kibana dashboards for visualization

## Setup Instructions

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the infrastructure services:
   ```bash
   docker-compose up -d
   ```

3. Access Kibana to set up visualizations:
   - Open http://localhost:5601 in your browser
   - Create an index pattern for "ics_anomalies"
   - Create dashboards to visualize:
     - Anomaly detection results over time
     - Feature distributions
     - Alert history

4. Run the anomaly detector:
   ```bash
   sudo python ics_anomaly_detector/detector.py
   ```
   Note: sudo is required for packet capture capabilities

## Architecture

- **Anomaly Detector**: Uses Isolation Forest algorithm to detect anomalies in network traffic
- **MQTT Broker**: Handles real-time message publishing of detection results
- **Elasticsearch**: Stores all detection results and feature data
- **Kibana**: Provides visualization and analysis interface

## Monitoring

1. MQTT messages can be monitored using:
   ```bash
   mosquitto_sub -t "ics/anomaly" -v
   ```

2. Elasticsearch indices can be checked using:
   ```bash
   curl http://localhost:9200/_cat/indices
   ```

3. View real-time results in Kibana at http://localhost:5601
