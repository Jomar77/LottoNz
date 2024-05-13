import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping

# Load the dataset
file_path = 'lotto_results.csv'  # Adjust as necessary
df = pd.read_csv(file_path)

# Parse the 'Year', 'Month', 'Day' into a single datetime object
df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])

# Drop the original 'Year', 'Month', 'Day' columns as they are now redundant
df.drop(['Year', 'Month', 'Day'], axis=1, inplace=True)

# Assuming you want to predict the next draw based on previous draws
# Here, you could create features based on historical draws, for simplicity, let's flatten the data
# NOTE: This is a simple transformation and might not directly predict the 'next' numbers without further feature engineering

# Flatten the dataset
data = df.drop('Date', axis=1).values  # Excluding date from features for simplicity
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

# Function to create dataset for LSTM
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back):
        a = dataset[i:(i + look_back)]
        dataX.append(a)
        dataY.append(dataset[i + look_back])
    return np.array(dataX), np.array(dataY)

# Specify the look_back window
look_back = 1
datasetX, datasetY = create_dataset(scaled_data, look_back)

# Split the data into training and test sets
train_size = int(len(datasetX) * 0.8)
trainX, testX = datasetX[:train_size], datasetX[train_size:]
trainY, testY = datasetY[:train_size], datasetY[train_size:]

# Reshape input for LSTM [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], look_back, trainX.shape[2]))
testX = np.reshape(testX, (testX.shape[0], look_back, testX.shape[2]))

# Define and compile the LSTM model
model = Sequential([
    LSTM(50, input_shape=(look_back, trainX.shape[2])),
    Dense(trainY.shape[1])
])
model.compile(optimizer='adam', loss='mean_squared_error')

# Use early stopping to halt the training when validation loss doesn't improve
early_stop = EarlyStopping(monitor='val_loss', patience=10, verbose=1)

# Train the model
model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2, callbacks=[early_stop], validation_data=(testX, testY))

# Predict the next draw (simplified approach)
last_draw_scaled = scaled_data[-1].reshape(1, 1, scaled_data.shape[1])
next_draw_scaled = model.predict(last_draw_scaled)
next_draw = scaler.inverse_transform(next_draw_scaled).flatten()

print(f'The predicted next draw numbers are: {next_draw}')
