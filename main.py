import numpy as np
import pandas as pd
from copy import deepcopy
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
import sys
import joblib
import matplotlib.pyplot as plt
import pickle

from F16_AnomalyHandler import AnomalyHandler
from F1_BaseAnomalyGenerator import BaseAnomalyGenerator
from F2_BaseFeature import BaseFeature
from F3_BaseAnomalyClassifier import BaseAnomalyClassifier
from F4_SpikeAnomalyGenerator import SpikeAnomalyGenerator
from F5_SpikeFeature import SpikeFeature
from F6_SpikeClassifier import SpikeClassifier
from F7_LNAnomalyGenerator import LNAnomalyGenerator
from F8_LNFeature import LNFeature
from F9_LNClassifier import LNClassifier
from F10_PMSAnomalyGenerator import PMSAnomalyGenerator
from F11_PMSFeature import PMSFeature
from F12_PMSClassifier import PMSClassifier
from F13_PSDAnomalyGenerator import PSDAnomalyGenerator
from F14_PSDFeature import PSDFeatures
from F15_PSDClassifier import PSDClassifier
from sklearn.ensemble import RandomForestClassifier
from Segmenter import hmm_segmentation
from Constants import *
from Utils import *

join = os.path.join

# Make dataset for each given sensor
def make_dataset(sensor, anomaly_type, alpha):
    dataset = []
    y = []
    anomaly_dict = {'spike': SpikeAnomalyGenerator(), 'pms': PMSAnomalyGenerator(),
                    'psd': PSDAnomalyGenerator(), 'ln': LNAnomalyGenerator()}

    for i in range(len(sensor)):  # Each row of sensor
        if sensor[i].shape[0] <= 10:
          continue
        # Positive data
        x = sensor[i]
        y.append(0)
        dataset.append(x)

        # Negative data
        x = anomaly_dict[anomaly_type].transform(
            sensor[i], alpha)
        y.append(1)
        dataset.append(x)

    return np.array(dataset, dtype='object'), np.array(y)

#_________________________________________Setup Code________________________________________________#
# Paths
raw_data_path = join(os.getcwd(), 'WADI')
normal_data = pickle.load(open(join(raw_data_path, 'dfn_wadi_pp.pkl'), 'rb'))
anomaly_data = pickle.load(open(join(raw_data_path, 'dfa_wadi_pp.pkl'), 'rb'))
print(normal_data.shape, anomaly_data.shape)

# Save path
save_path = join(os.getcwd(), 'WADI', 'Sensors')
if not os.path.exists(save_path):
    os.mkdir(save_path)

data_path = join(os.getcwd(), 'WADI', 'Datasets')
if not os.path.exists(data_path):
    os.mkdir(data_path)

spike_path = join(os.getcwd(), 'WADI', 'Datasets', 'Spike')
if not os.path.exists(spike_path):
    os.mkdir(spike_path)

pms_path = join(os.getcwd(), 'WADI', 'Datasets', 'PMS')
if not os.path.exists(pms_path):
    os.mkdir(pms_path)

psd_path = join(os.getcwd(), 'WADI', 'Datasets', 'PSD')
if not os.path.exists(psd_path):
    os.mkdir(psd_path)

ln_path = join(os.getcwd(), 'WADI', 'Datasets', 'LN')
if not os.path.exists(ln_path):
    os.mkdir(ln_path)

classifier_path = join(os.getcwd(), 'WADI', 'Classifiers')
if not os.path.exists(classifier_path):
    os.mkdir(classifier_path)

spike_classifier_path = join(os.getcwd(), 'WADI', 'Classifiers', 'Spike')
if not os.path.exists(spike_classifier_path):
    os.mkdir(spike_classifier_path)

pms_classifier_path = join(os.getcwd(), 'WADI', 'Classifiers', 'PMS')
if not os.path.exists(pms_classifier_path):
    os.mkdir(pms_classifier_path)

psd_classifier_path = join(os.getcwd(), 'WADI', 'Classifiers', 'PSD')
if not os.path.exists(psd_classifier_path):
    os.mkdir(psd_classifier_path)

ln_classifier_path = join(os.getcwd(), 'WADI', 'Classifiers', 'LN')
if not os.path.exists(ln_classifier_path):
    os.mkdir(ln_classifier_path)

labels_array = np.array(anomaly_data['label'])
anomalous_indices = np.where(labels_array == 1)[0]

normal_data.columns = normal_data.columns.str.replace(r"\\", '', regex=True)
normal_data.columns = normal_data.columns.str.replace('WIN-25J4RO10SBFLOG_DATASUTD_WADILOG_DATA', '')
anomaly_data.columns = anomaly_data.columns.str.replace(r"\\", '', regex=True)
anomaly_data.columns = anomaly_data.columns.str.replace('WIN-25J4RO10SBFLOG_DATASUTD_WADILOG_DATA', '')


#_________________________________________Data Creation________________________________________________#

# Preprocess
normal_data, deleted_sensors = preprocess_normal(normal_data)

print('Segmenting...')
sensors = normal_data.columns
for sensor in sensors:
    if sensor in ['Row', 'Date', 'Time']:
        continue
    print('Sensor: ', sensor)
    # if file exists then skip
    if os.path.exists(join(save_path, sensor + '.npy')):
        continue
    decoded_array, segments, motifs, hmm_train = hmm_segmentation(normal_data[sensor], WINDOW_SIZE, N_STATES)
    signal = [x.to_numpy(dtype='float') for x in motifs]
    signal = np.array(signal, dtype='object')
    if len(segments) == 0:
        deleted_sensors.append(sensor)
        normal_data.drop(sensor, axis=1, inplace=True)
        continue
    np.save(join(save_path, sensor), signal)

# Make dataset for each sensor
print('Making datasets...')
sensors = normal_data.columns
for sensor in sensors:
    if sensor in ['Row', 'Date', 'Time']:
        continue
    print('Sensor: ', sensor)
    signal = np.load(join(save_path, sensor + '.npy'), allow_pickle=True)
    
    if not os.path.exists(join(spike_path, sensor + '_dataset.npy')):
        X, y = make_dataset(signal, 'spike', ALPHA_SPIKE)
        np.save(join(spike_path, sensor + '_dataset'), X)
        np.save(join(spike_path, sensor + '_y'), y)

    if not os.path.exists(join(pms_path, sensor + '_dataset.npy')):
        X, y = make_dataset(signal, 'pms', ALPHA_PMS)
        np.save(join(pms_path, sensor + '_dataset'), X)
        np.save(join(pms_path, sensor + '_y'), y)

    if not os.path.exists(join(psd_path, sensor + '_dataset.npy')):
        X, y = make_dataset(signal, 'psd', ALPHA_PSD)
        np.save(join(psd_path, sensor + '_dataset'), X)
        np.save(join(psd_path, sensor + '_y'), y)

    if not os.path.exists(join(ln_path, sensor + '_dataset.npy')):
        X, y = make_dataset(signal, 'ln', ALPHA_LN)
        np.save(join(ln_path, sensor + '_dataset'), X)
        np.save(join(ln_path, sensor + '_y'), y)

#_________________________________________Traning________________________________________________#

# Build classifiers for each sensor and train
print('Training...')
for sensor in sensors:
    if sensor in ['Row', 'Date', 'Time']:
        continue
    print('Sensor: ', sensor)
    if not os.path.exists(join(spike_classifier_path, sensor + '.pkl')):
        x = np.load(join(spike_path, sensor + '_dataset.npy'), allow_pickle=True)
        y = np.load(join(spike_path, sensor + '_y.npy'), allow_pickle=True)
        clf = SpikeClassifier()
        clf.fit(x, y)
        joblib.dump(clf, join(spike_classifier_path, sensor + '.pkl'))
        y_pred = clf.predict(x)
        print(f'Accuracy: {accuracy_score(y, y_pred):.3f}')
        print(f'Precision: {precision_score(y, y_pred):.3f}')
        print(f'Recall: {recall_score(y, y_pred):.3f}')
        print()

    