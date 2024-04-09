import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from tensorflow.keras.callbacks import EarlyStopping
import numpy as np

# Load and preprocess data
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path)
    # Parsing the datetime information
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'] + '-' + df['Day'].astype(str))
    df.drop(['Year', 'Month', 'Day'], axis=1, inplace=True)
    
    # For simplicity, let's focus on a single lotto number column if there are multiple
    # This example assumes a single sequence of numbers; adjust if predicting multiple numbers
    numbers = df['Numbers'].str.split(',', expand=True).astype(int)[0]  # Adjust this line to accommodate your actual data structure
    dates = df['Date']
    
    # Scaling the numbers - assuming they are in separate columns
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_numbers = scaler.fit_transform(numbers.values.reshape(-1, 1))
    
    # Preparing the date features (e.g., year, month as numerical values)
    df['Year'] = dates.dt.year
    df['Month'] = dates.dt.month
    df['Day'] = dates.dt.day
    # Here you can add more date-related features as needed
    
    # Assuming we are using only 'Year', 'Month', and 'Day' for simplicity
    scaled_dates = scaler.fit_transform(df[['Year', 'Month', 'Day']])
    
    # Combining the scaled date features and lotto numbers for model input
    combined_data = np.hstack((scaled_dates, scaled_numbers))
    
    return combined_data, scaler

# Assuming the rest of the model setup, training, and prediction code follows, with adjustments for combined_data


def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i + look_back), :-1]  # All features except the last column (target)
        dataX.append(a)
        dataY.append(dataset[i + look_back, -1])  # Target variable (last column)
    return np.array(dataX), np.array(dataY)

# Load and preprocess the dataset
data, scaler = load_and_preprocess_data('lotto_results.csv')

# Parameters
look_back = 1

# Create dataset for LSTM
train_size = int(len(data) * 0.8)
test_size = len(data) - train_size
train, test = data[0:train_size,:], data[train_size:len(data),:]
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)

# Reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], look_back, trainX.shape[2]))
testX = np.reshape(testX, (testX.shape[0], look_back, testX.shape[2]))


# Define the LSTM model
model = Sequential()
model.add(LSTM(50, input_shape=(look_back, trainX.shape[2])))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')


# Early stopping
early_stop = EarlyStopping(monitor='val_loss', patience=10)

# Train the model
history = model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2, validation_data=(testX, testY), callbacks=[early_stop])


# Making predictions
trainPredict = model.predict(trainX)
testPredict = model.predict(testX)

# Invert predictions
trainPredict = scaler.inverse_transform(trainPredict)
trainY = scaler.inverse_transform([trainY])
testPredict = scaler.inverse_transform(testPredict)
testY = scaler.inverse_transform([testY])

# Example: printing the last prediction
print(f'Last training prediction: {trainPredict[-1]}, Actual: {trainY[0][-1]}')
print(f'Last test prediction: {testPredict[-1]}, Actual: {testY[0][-1]}')
