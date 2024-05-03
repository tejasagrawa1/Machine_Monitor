import os
import csv
import json
import numpy as np
import pickle

# Predict on one sample

sample_path = "Sample/" # Replcae with the path of the sample to predict
Labels = {'Normal': 0,'No_Run': 1,'Loose_Foundation': 2,'Overload': 3, 'Uneven_Base': 4}

# Load data from CSV
X_predict = []
for dir in os.listdir(sample_path):
    if not dir.startswith('.'):
        sample_dir = os.path.join(sample_path, dir)
        for k in os.listdir(sample_dir):
            if not k.startswith('.'):
                if k == 'fft.csv':
                    data_file = os.path.join(sample_dir, k)
                    print('Loading...', data_file)
                    with open(data_file, newline='') as f:
                        reader = csv.reader(f)
                        data = list(reader)[1:]  # Remove header
                        data_sensor1 = json.loads(data[0][2])
                        data_sensor2 = json.loads(data[1][2])
                        Input_set = data_sensor1['FFT_X'] + data_sensor1['FFT_Y'] + data_sensor1['FFT_Z'] + data_sensor2['FFT_X'] + data_sensor2['FFT_Y'] + data_sensor2['FFT_Z']
                        X_predict.append(Input_set)

X_predict = np.array(X_predict)

# Load the model
with open('Model_RandomForest.pkl', 'rb') as f:
    rf_model = pickle.load(f)

y_predict = rf_model.predict(X_predict)

print("Prediction:", list(Labels.keys())[list(Labels.values()).index(y_predict)])