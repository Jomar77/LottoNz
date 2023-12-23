# Import necessary libraries
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM

# Load the data
df = pd.read_csv('output.csv', header=None)

# Ignore the even lines
df = df[df.index % 2 != 0]

# Normalize the data
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(df.values)

# Split the data into training and test sets
train_size = int(len(scaled_data) * 0.8)
train, test = scaled_data[0:train_size,:], scaled_data[train_size:len(scaled_data),:]

def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), :]
        dataX.append(a)
        dataY.append(dataset[i + look_back, :])
    return np.array(dataX), np.array(dataY)

# Reshape into X=t and Y=t+1
look_back = 1
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)

# Reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1], trainX.shape[2]))
testX = np.reshape(testX, (testX.shape[0], testX.shape[1], testX.shape[2]))
# Create and fit the LSTM network
model = Sequential()
model.add(LSTM(4, input_shape=(1, 6)))
model.add(Dense(6))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2)

# Make a prediction for the next set of numbers in the sequence
next_numbers = model.predict(np.array([[[scaled_data[-1]]]]))

# Invert the prediction to get the original scale
next_numbers = scaler.inverse_transform(next_numbers)

# Round the numbers and convert them to integers
next_numbers = [int(round(num)) for num in next_numbers[0]]

print(f'The predicted next set of numbers is {next_numbers}')
