import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from scapy.all import *
import paho.mqtt.client as mqtt
from elasticsearch import Elasticsearch
import json
import os
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "ics/anomaly"

# Elasticsearch Configuration
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX = "ics_anomalies"

class ICSAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.feature_names = [
            'packet_size',
            'inter_arrival_time',
            'protocol_type',
            'port_number',
            'packet_count',
            'byte_count',
            'flow_duration',
            'tcp_flags',
            'tcp_window_size',
            'payload_length'
        ]
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.mqtt_client.loop_start()
        
        # Initialize Elasticsearch client
        self.es_client = Elasticsearch([{'host': ES_HOST, 'port': ES_PORT}])
        
        # Create index if not exists
        if not self.es_client.indices.exists(index=ES_INDEX):
            self.es_client.indices.create(index=ES_INDEX)
    
    def extract_features(self, packet):
        """Extract features from a network packet"""
        features = {}
        
        # Basic packet features
        features['packet_size'] = len(packet)
        features['protocol_type'] = packet.proto if 'IP' in packet else 0
        features['port_number'] = packet[TCP].dport if TCP in packet else (packet[UDP].dport if UDP in packet else 0)
        
        # TCP specific features
        if TCP in packet:
            features['tcp_flags'] = packet[TCP].flags
            features['tcp_window_size'] = packet[TCP].window
        else:
            features['tcp_flags'] = 0
            features['tcp_window_size'] = 0
        
        # Payload length
        features['payload_length'] = len(packet[Raw].load) if Raw in packet else 0
        
        return features
    
    def process_packet_batch(self, packets):
        """Process a batch of packets and extract time-based features"""
        if not packets:
            return None
            
        # Calculate time-based features
        timestamps = [float(p.time) for p in packets]
        sizes = [len(p) for p in packets]
        
        features = {
            'packet_count': len(packets),
            'byte_count': sum(sizes),
            'flow_duration': max(timestamps) - min(timestamps),
            'inter_arrival_time': np.mean(np.diff(timestamps)) if len(timestamps) > 1 else 0
        }
        
        # Add packet-level features (using the first packet as reference)
        packet_features = self.extract_features(packets[0])
        features.update(packet_features)
        
        return features
    
    def train(self, training_data):
        """Train the anomaly detection model"""
        X = pd.DataFrame(training_data)[self.feature_names]
        self.model.fit(X)
    
    def detect(self, features):
        """Detect anomalies in the current features"""
        X = pd.DataFrame([features])[self.feature_names]
        prediction = self.model.predict(X)[0]
        
        # -1 indicates anomaly, 1 indicates normal
        is_anomaly = prediction == -1
        
        # Prepare result
        result = {
            'timestamp': datetime.now().isoformat(),
            'is_anomaly': is_anomaly,
            'features': features
        }
        
        # Send to MQTT
        self.mqtt_client.publish(MQTT_TOPIC, json.dumps(result))
        
        # Store in Elasticsearch
        self.es_client.index(index=ES_INDEX, body=result)
        
        return is_anomaly
    
    def start_capture(self, interface='eth0', batch_size=100, batch_timeout=10):
        """Start capturing packets and detecting anomalies"""
        packets = []
        last_batch_time = time.time()
        
        def process_packet(packet):
            nonlocal packets, last_batch_time
            
            if IP in packet:
                packets.append(packet)
                
                current_time = time.time()
                if len(packets) >= batch_size or (current_time - last_batch_time) >= batch_timeout:
                    features = self.process_packet_batch(packets)
                    if features:
                        self.detect(features)
                    packets = []
                    last_batch_time = current_time
        
        # Start packet capture
        sniff(iface=interface, prn=process_packet, store=0)

if __name__ == "__main__":
    detector = ICSAnomalyDetector()
    
    # Example usage:
    # 1. Collect some normal traffic for training
    # 2. Train the model
    # 3. Start real-time detection
    
    # For demonstration, we'll use some dummy training data
    training_data = [
        {
            'packet_size': 100,
            'inter_arrival_time': 0.1,
            'protocol_type': 6,
            'port_number': 502,
            'packet_count': 50,
            'byte_count': 5000,
            'flow_duration': 5.0,
            'tcp_flags': 2,
            'tcp_window_size': 8192,
            'payload_length': 80
        }
        # Add more training samples here
    ]
    
    detector.train(training_data)
    detector.start_capture()
