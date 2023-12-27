import pandas as pd
import numpy as np

from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from keras.callbacks import Callback
import tensorflow as tf


# Function for data loading and preprocessing
def load_and_preprocess_data(file_path, header=None, feature_range=(0, 1)):
    df = pd.read_csv(file_path, header=header)
    scaler = MinMaxScaler(feature_range=feature_range)
    scaled_data = scaler.fit_transform(df.values)
    return scaled_data, scaler

# Function to create dataset
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), :]
        dataX.append(a)
        dataY.append(dataset[i + look_back, :])
    return np.array(dataX), np.array(dataY)

# Callback class with flexible target numbers
class MyCallback(Callback):
    def __init__(self, target_numbers, tolerance=1e-2):
        super(MyCallback, self).__init__()
        self.target_numbers = target_numbers
        self.tolerance = tolerance

    def on_epoch_end(self, epoch, logs=None):
        prediction = self.model.predict(trainX)
        if np.allclose(prediction, self.target_numbers, atol=self.tolerance):
            self.model.stop_training = True

# Load and preprocess data
data, scaler = load_and_preprocess_data('output.csv')

# Split the data into training and test sets
train_size = int(len(data) * 0.8)
train, test = data[0:train_size, :], data[train_size:len(data), :]

# Reshape into X=t and Y=t+1
look_back = 1
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)

# Reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], trainX.shape[2]))
trainY = np.reshape(trainY, (trainY.shape[0], trainY.shape[1]))

# Define model parameters
input_shape = (look_back, trainX.shape[2])
target_numbers = np.array([12, 14, 30, 35, 38, 40])

# Build the model
model = Sequential()
model.add(Dense(12, activation='relu', input_shape=input_shape))
model.add(Dense(8, activation='relu'))
model.add(Dense(trainY.shape[1], activation='linear'))

# Compile the model
model.compile(loss='mse', optimizer='adam', metrics=[tf.keras.metrics.CategoricalAccuracy()])

# Train the model with the callback
model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=1, callbacks=[MyCallback(target_numbers)])

# Predict the next set of numbers
next_numbers_scaled = model.predict(np.array([data[-1]]).reshape(1, look_back, data.shape[1]))
next_numbers_scaled_2d = next_numbers_scaled.reshape(1, -1)
next_numbers = scaler.inverse_transform(next_numbers_scaled_2d).astype(int)[0]

4 11 17 22 28 34




print(f'The predicted next set of numbers is {next_numbers}')
