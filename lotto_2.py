import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from tensorflow.python.keras.callbacks import EarlyStopping
import tensorflow as tf

# Load and preprocess data
def load_and_preprocess_data(file_path, feature_range=(0, 1)):
    # Load the dataset
    df = pd.read_csv(file_path)
    
    # Convert Year, Month, Day to a single datetime column and extract useful features
    df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
    df['Month'] = df['Date'].dt.month
    df['Day_of_Week'] = df['Date'].dt.dayofweek
    df.drop(['Year', 'Month', 'Day', 'Date'], axis=1, inplace=True)
    
    # One-hot encode the Month and Day_of_Week
    ohe = OneHotEncoder(sparse=False)
    features = df[['Month', 'Day_of_Week']]
    encoded_features = ohe.fit_transform(features)
    
    # Concatenate the one-hot encoded features with the lotto numbers
    numbers = df.drop(['Month', 'Day_of_Week'], axis=1)
    scaled_numbers = MinMaxScaler(feature_range=feature_range).fit_transform(numbers)
    combined_data = np.hstack((encoded_features, scaled_numbers))
    
    return combined_data, ohe, scaler

# Assuming the rest of the functions and model training code remain the same...

# Load your dataset
data, ohe, scaler = load_and_preprocess_data('lotto_results.csv')

# Note: Make sure to adjust the input shape in the LSTM model to match the new data shape
input_shape = (1, data.shape[1] - 1)  # Subtract 1 because the target variable is not part of the input

# Define and compile the LSTM model with the adjusted input shape
model = Sequential([
    LSTM(50, input_shape=input_shape),
    Dense(1)  # Assuming you are predicting a single number or a transformed representation of the lotto numbers
])
model.compile(optimizer='adam', loss='mean_squared_error')

# Continue with the rest of your model training and prediction code...

# Split the data into training and test sets
train_size = int(len(data) * 0.8)
train, test = data[0:train_size, :], data[train_size:len(data), :]

# Create dataset for LSTM
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back):
        a = dataset[i:(i+look_back), :-1]  # Exclude the last column for X
        dataX.append(a)
        dataY.append(dataset[i + look_back, -1])  # Last column is Y
    return np.array(dataX), np.array(dataY)

look_back = 1
trainX, trainY = create_dataset(train, look_back)
testX, testY = create_dataset(test, look_back)

# Reshape input for LSTM [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

# Use early stopping to halt the training when validation loss doesn't improve
early_stop = EarlyStopping(monitor='val_loss', patience=10, verbose=1)

# Train the model
history = model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2, callbacks=[early_stop], validation_data=(testX, testY))

# Predict the next value(s)
last_point_scaled = data[-look_back:, :-1].reshape(1, 1, -1)  # Reshape the last point for prediction
next_point_scaled = model.predict(last_point_scaled)

# If predicting multiple values, you'll need to adjust this part
# Here's an example for a single value prediction
next_point = scaler.inverse_transform(next_point_scaled.reshape(-1, 1)).flatten()[0]

print(f'The predicted next value is {next_point}')
