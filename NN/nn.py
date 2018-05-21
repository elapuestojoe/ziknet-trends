from pandas import read_csv, DataFrame, concat
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from keras import Sequential
from keras.layers import LSTM, Dense
from matplotlib import pyplot
from numpy import concatenate, apply_along_axis
from math import sqrt
from sklearn.metrics import mean_squared_error
from keras.models import model_from_json
from os.path import isfile
from keras.constraints import non_neg

# frame a sequence as a supervised learning problem
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = DataFrame(data)
	cols, names = list(), list()
	# input sequence (t-n, ... t-1)
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	# forecast sequence (t, t+1, ... t+n)
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	# put it all together
	agg = concat(cols, axis=1)
	agg.columns = names
	# drop rows with NaN values
	if dropnan:
		agg.dropna(inplace=True)
	return agg

def experiment(dataset, n_lag):

	# dataset[["searches"]] = dataset[["searches"]] / 100
	# dataset[["cases"]] = dataset[["cases"]] / 1000
	raw_values = dataset.values.astype('float32')

	print("Original: ", dataset.shape)
	# print(raw_values)
	# scaler = MinMaxScaler(feature_range=(0, 1))
	# scaled_values = scaler.fit_transform(raw_values)
	scaled_values = raw_values
	# print(dataset.head)
	scaled_values = series_to_supervised(scaled_values, n_lag)

	print(scaled_values)
	print("Transformed: ", scaled_values.shape)
	# print(supervisedData.head)

	# split into train and test sets
	values = scaled_values.values
	n_train_weeks = 12
	n_features = 2
	train = values[:n_train_weeks, :]
	test = values[n_train_weeks:, :]

	n_obs = n_lag * n_features
	train_X, train_y = train[:, :n_obs], train[:, -1]
	test_X, test_y = test[:, :n_obs], test[:, -1]

	# print("TEST", test_X, test_y)
	print("BEFORE 3d: ",train_X.shape, len(train_X), train_y.shape)
	# print(train_X)
	# reshape input to be 3D [samples, timesteps, features]
	train_X = train_X.reshape((train_X.shape[0], n_lag, n_features))
	test_X = test_X.reshape((test_X.shape[0], n_lag, n_features))
	print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)



	#TODO: CHECK SCALER (NOT WORKING)

	model = None
	if(isfile("model.json") and isfile("model.h5")):
	# if False:
		json_file = open("model.json", "r")
		loaded_model_json = json_file.read()
		json_file.close()
		model = model_from_json(loaded_model_json)

		#load weights
		model.load_weights("model.h5")
		model.compile(loss="mae", optimizer="adam")
		print("Loaded model from disk")
	else:

		# design network
		model = Sequential()
		model.add(LSTM(128, input_shape=(train_X.shape[1], train_X.shape[2])))
		# model.add(Dense(16, activation="relu"))
		model.add(Dense(1, activation="sigmoid", kernel_constraint=non_neg()))

		model.compile(loss='mae', optimizer='adam')
		# fit network
		history = model.fit(train_X, train_y, epochs=100, batch_size=80, validation_data=(test_X, test_y), verbose=2, shuffle=False)

		#Save model
		model_json = model.to_json()
		with open("model.json", "w") as json_file:
			json_file.write(model_json)
		#seralize weights to HDF5
		model.save_weights("model.h5")
		print("Saved model to disk")

		# plot history

		if("loss" in history.history):
			pyplot.plot(history.history['loss'], label='train')
		
		if("val_loss" in history.history):
			pyplot.plot(history.history['val_loss'], label='test')

		pyplot.legend()
		pyplot.show()

	#Make predictions
	yhat = model.predict(test_X)
	inv_yhat = test_y

	print("FSHAPE", yhat.shape, inv_yhat.shape)

	# yhat = apply_along_axis(lambda x: x*1000, 1, yhat)
	# test_y = apply_along_axis(lambda x: x*1000, 0, test_y)


	# # calculate RMSE
	rmse = sqrt(mean_squared_error(yhat, test_y))
	print('Test RMSE: %.3f' % rmse)
	print("Total", sum(test_y))
	print("len", len(test_y))
	# print("REAL",inv_y)

	x = []
	y = []
	pred = []
	for i in range(len(test_y)):
		x.append(i)


	print("REAL: ", test_y)
	print("PRED: ", yhat)

	pyplot.plot(x, yhat, label="Predicition")
	pyplot.plot(x, test_y, label="Actual Values")
	pyplot.legend()
	pyplot.show()


def run():
	dataset = read_csv('data/Weekly-Veracruz_15-11-2015_848.csv', header=0, index_col=0)

	#Parameters
	n_lag = 3

	experiment(dataset, n_lag)

run()