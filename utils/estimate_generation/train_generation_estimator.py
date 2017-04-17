# This Python file uses the following encoding: utf-8
"""
PowerWatch
train_generation_estimator.py
Train a Gradient Boosted Regression Tree (GBRT) model to estimate power plant electricity generation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV

# set general parameters
search_hyperparameters = False					# perform hyperparameter search (slow)
data_filename = "US_generation_data_01.csv"

# set parameters for training estimator
params = {
	'n_estimators': 500,
	'max_depth': 6,					# grid search optimum: 6
	'learning_rate': 0.01,			# grid search optimum: 0.01
	'subsample': 0.5,
	#'loss':'ls'
}

# set parameters for the hyperparam grid search
param_grid = {'learning_rate': [0.1,0.05,0.02,0.01],
				'max_depth': [4,6],
				'min_samples_leaf': [3,5,9,17]
				}

# set columns used as independent variables
x_vars = ['Latitude','Longitude','Weighted Year.Month','Primary Fuel','Total Capacity (MW)']
y_var = ['Net Generation (MWh)']

# prepare to convert fuel type to int
fuel_types = {'Biomass':1,'Coal':2,'Gas':3,'Geothermal':4,'Hydro':5,'Nuclear':6,'Oil':7,'Other':8,'Solar':9,'Waste':10,'Wind':11}

def convert_fuel_string_to_int(s):
	return fuel_types[s]

# main

# load data
Xdf = pd.read_csv(data_filename, usecols = x_vars)
ydf = pd.read_csv(data_filename, usecols = y_var)
Xdf['Primary Fuel'] = Xdf['Primary Fuel'].apply(convert_fuel_string_to_int)
X_train, X_test, y_train, y_test = train_test_split(Xdf,ydf,test_size=0.2)
print("Data loaded: {0} training observations; {1} test observations.".format(len(X_train),len(X_test)))

# fit estimator
est = GradientBoostingRegressor()
est.set_params(**params)

# do fit or hyperparameter search
if search_hyperparameters:
	print("Searching hyperparameters...")
	ext.set_params
	gs_cv = GridSearchCV(est,param_grid,n_jobs=4,verbose=2).fit(X_train,y_train.values.ravel())
	print(gs_cv.best_params_)

else:
	y_train2 = y_train.values.ravel()			# need to reshape y vals from pandas df shape
	est.fit(X_train, y_train2)
	y_test2 = y_test.values.ravel()
	acc = est.score(X_test, y_test2)			# need to reshape y vals from pandas df shape
	#print("Test accuracy: {:4.1f}%".format(100*acc))
	print("Test score: {:4.3f}".format(acc))

	# make deviance subplot
	test_score = np.zeros((params['n_estimators'],),dtype=np.float64)

	for i,y_pred in enumerate(est.staged_predict(X_test)):
		test_score[i] = est.loss_(y_test2,y_pred)

	fig = plt.figure(figsize=(15,8))
	fig.subplots_adjust(left=0.05)
	fig.subplots_adjust(right=0.95)
	fig.subplots_adjust(wspace=0.3)

	plt.subplot(1,2,1)
	plt.title('Deviance')
	plt.plot(np.arange(params['n_estimators'])+1,est.train_score_,'b-',label='Training set deviance')
	plt.plot(np.arange(params['n_estimators'])+1,test_score,'r-',label='Test set deviance')
	plt.legend(loc='upper right')
	plt.xlabel('Boosting iterations')
	plt.ylabel('Deviance')

	# make feature importance subplot
	feature_importance = est.feature_importances_
	feature_importance = 100.0 * (feature_importance / feature_importance.max())
	sorted_idx = np.argsort(feature_importance)
	pos = np.arange(sorted_idx.shape[0]) + .5
	plt.subplot(1, 2, 2)
	plt.barh(pos, feature_importance[sorted_idx], align='center')
	feature_names = [list(Xdf)[i] for i in sorted_idx]
	plt.yticks(pos, feature_names)
	plt.xlabel('Relative Importance')
	plt.title('Variable Importance')

	# tighten layout and show
	#plt.tight_layout()
	plt.show()

