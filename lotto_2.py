import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf

# Load and preprocess data
def load_and_preprocess_data(file_path, feature_range=(0, 1)):
    df = pd.read_csv(file_path)
    scaler = MinMaxScaler(feature_range=feature_range)
    scaled_data = scaler.fit_transform(df)
    return scaled_data, scaler

# Create dataset for LSTM
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back):
        a = dataset[i:(i+look_back)]
        dataX.append(a)
        dataY.append(dataset[i + look_back])
    return np.array(dataX), np.array(dataY)

data, scaler = load_and_preprocess_data('output.csv')

# Split the data into training and test sets
train_size = int(len(data) * 0.8)
train, test = data[0:train_size], data[train_size:len(data)]

look_back = 1
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)

# Reshape input for LSTM [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

# Define and compile the LSTM model
model = Sequential([
    LSTM(50, input_shape=(1, look_back)),
    Dense(1)
])
model.compile(optimizer='adam', loss='mean_squared_error')

# Use early stopping to halt the training when validation loss doesn't improve
early_stop = EarlyStopping(monitor='val_loss', patience=10, verbose=1)

# Train the model
model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2, callbacks=[early_stop], validation_data=(testX, testY))

# Predict the next value
last_point_scaled = data[-look_back:].reshape(1, 1, look_back)
next_point_scaled = model.predict(last_point_scaled)
next_point = scaler.inverse_transform(next_point_scaled).flatten()[0]

print(f'The predicted next value is {next_point}')
