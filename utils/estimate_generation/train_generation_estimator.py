# This Python file uses the following encoding: utf-8
"""
PowerWatch
train_generation_estimator.py
Train a Gradient Boosted Regression Tree (GBRT) model to estimate power plant electricity generation.
Follows method described here: https://www.datarobot.com/blog/gradient-boosted-regression-trees/ .
"""

import numpy as np
import csv
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV

# set general parameters
search_hyperparameters = False					# perform hyperparameter search (slow)
data_filename = "US_capacity_and_generation_20161006_raw.csv"
country_list = "USA - original data"

# set parameters for training estimator
params = {
	'n_estimators': 1000,
	'max_depth': 6,					# grid search optimum: 6
	'learning_rate': 0.01,			# grid search optimum: 0.01
	'subsample': 0.5,
	'loss':'huber'
}

# set parameters for the hyperparam grid search
param_grid = {
	'learning_rate': [0.1,0.05,0.02,0.01],
	'max_depth': [4,6],
	'min_samples_leaf': [3,5,9,17]
}

# prepare to convert fuel type to int
fuel_types = {	'Biomass': 		{'findex':1,'cap_factors':[],'avg_cf':0},
				'Coal':			{'findex':2,'cap_factors':[],'avg_cf':0},
				'Cogeneration':	{'findex':3,'cap_factors':[],'avg_cf':0},
				'Gas':			{'findex':4,'cap_factors':[],'avg_cf':0},
				'Geothermal':	{'findex':5,'cap_factors':[],'avg_cf':0},
				'Hydro':		{'findex':6,'cap_factors':[],'avg_cf':0},
				'Nuclear':		{'findex':7,'cap_factors':[],'avg_cf':0},
				'Oil':			{'findex':8,'cap_factors':[],'avg_cf':0},
				'Other':		{'findex':9,'cap_factors':[],'avg_cf':0},
				'Petcoke':		{'findex':10,'cap_factors':[],'avg_cf':0},
				'Solar':		{'findex':11,'cap_factors':[],'avg_cf':0},
				'Waste':		{'findex':12,'cap_factors':[],'avg_cf':0},
				'Wind':			{'findex':13,'cap_factors':[],'avg_cf':0},
				}

# main

# load data
X_data = []
y_data = []

feature_name_list = ['fuel_type','capacity_mw','commissioning_year','fuel_avg_cf']

with open(data_filename,'rU') as f:
	datareader = csv.reader(f)
	header = datareader.next()
	country = u'USA'
	for row in datareader:
		fuel = row[7]
		capacity_mw = float(row[8])
		gen_mwh = float(row[9])
		year = int(row[17])
		X_data.append([fuel,capacity_mw,year])

		# calculate capacity factor - TODO: handle clipping better
		capacity_factor = gen_mwh / (24.0 * 365 * capacity_mw)
		if capacity_factor > 1.0:
			capacity_factor = 1.0
		if capacity_factor < 0.0:
			capacity_factor = 0.0
		y_data.append(capacity_factor)

		# add to list for averaging
		fuel_types[fuel]['cap_factors'].append(capacity_factor)

print(u'Read in {0} observations.'.format(len(X_data)))

# calculate fuel-specific capacity factors
for k,v in fuel_types.iteritems():
	cf_list = v['cap_factors']
	avg_cf = 0.0 if not len(cf_list) else float(sum(cf_list)) / len(cf_list)
	fuel_types[k]['avg_cf'] = avg_cf
	print(u'Fuel: {0} has average cap. factor: {1}'.format(k,avg_cf))

# add fuel-specific capacity factors to X data
for observation in X_data:
	fuel = observation[0]
	observation.append(fuel_types[fuel]['avg_cf'])
	observation[0] = fuel_types[fuel]['findex']

# convert X_data, y_data to numpy arrays
X_data_np = np.array(X_data)
y_data_np = np.array(y_data)

# split X data into test and train
X_train, X_test, y_train, y_test = train_test_split(X_data_np,y_data_np,test_size=0.2)
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
	print("Fitting model...")
	est.fit(X_train, y_train)
	acc = est.score(X_test, y_test)			# need to reshape y vals from pandas df shape
	print("Test score: {:4.3f}".format(acc))

	# make deviance subplot
	test_score = np.zeros((params['n_estimators'],),dtype=np.float64)

	for i,y_pred in enumerate(est.staged_predict(X_test)):
		test_score[i] = est.loss_(y_test,y_pred)

	fig = plt.figure(figsize=(14,7))
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

	# display score
	ax = plt.gca()
	plt.text(0.5,0.5,"Test score: {:4.3f}".format(acc),transform=ax.transAxes,fontsize=16,color='r')
	plt.text(0.5,0.6,"Test observations: {0}".format(len(X_test)),transform=ax.transAxes,fontsize=12,color='b')	
	plt.text(0.5,0.65,"Train observations: {0}".format(len(X_train)),transform=ax.transAxes,fontsize=12,color='b')
	plt.text(0.5,0.7,"Countries: {0}".format(country_list),transform=ax.transAxes,fontsize=12,color='b')

	# make feature importance subplot
	feature_importance = est.feature_importances_
	feature_importance = 100.0 * (feature_importance / feature_importance.max())
	sorted_idx = np.argsort(feature_importance)
	pos = np.arange(sorted_idx.shape[0]) + .5
	plt.subplot(1, 2, 2)
	plt.barh(pos, feature_importance[sorted_idx], align='center')
	feature_names = [feature_name_list[i] for i in sorted_idx]
	plt.yticks(pos, feature_names)
	plt.xlabel('Relative Importance')
	plt.title('Variable Importance')

	# show
	plt.show()
