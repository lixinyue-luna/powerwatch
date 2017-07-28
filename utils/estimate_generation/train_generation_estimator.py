# This Python file uses the following encoding: utf-8
"""
PowerWatch
train_generation_estimator.py
Train a Gradient Boosted Regression Tree (GBRT) model to estimate power plant electricity 
generation.

Follows methods described on these sites: 
https://www.datarobot.com/blog/gradient-boosted-regression-trees/
http://machinelearningmastery.com/configure-gradient-boosting-algorithm/
http://machinelearningmastery.com/evaluate-gradient-boosting-models-xgboost-python/
https://medium.com/towards-data-science/train-test-split-and-cross-validation-in-python-80b61beca4b6
"""

import numpy as np
import csv
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, KFold, cross_val_score, cross_val_predict
from sklearn import metrics


def make_capacity_factor(capacity_mw,gen_mwh):
	# calculate capacity factor; TODO: handle clipping better
	capacity_factor = gen_mwh / (24.0 * 365 * capacity_mw)
	if capacity_factor > 1.0:
		capacity_factor = 1.0
	if capacity_factor < 0.0:
		capacity_factor = 0.0
	return capacity_factor

# set parameters
data_filename = "generation_data_USA.csv"
num_folds = 10						# number of cross-validation folds

params = {							# parameters for training estimator
	'n_estimators': 2000,           # AKA number of trees?
	'max_depth': 6,					# number of leaves is 2^max_depth; optimum = 6
	'learning_rate': 0.003,			# AKA shrinkage; optimum = 0.01 
	'subsample': 0.5,				# unclear: good choice is 0.5
	'loss':'huber'					# unclear: good choice is 'huber'
}

# main
countries = []						# will hold list of countries
fuel_types = []						# will hold list of fuel types
capacity_factors = {}   			# will hold plant-level cfs by country and fuel
fuel_capacity_factors = {}			# will hold average cfs by country and fuel
capacity_totals = {}				# will hold total capacity by country and fuel
capacity_totals_by_fuel = {}		# will hold total capacity by country

feature_name_list = ['country','fuel_type','capacity_mw','commissioning_year','fuel_avg_cf','cap_sh_country','cap_sh_country_fuel']

# load data
X_data = []
y_data = []

# read in data
with open(data_filename,'rU') as f:

	datareader = csv.reader(f)
	header = datareader.next()
	
	for row in datareader:

		# read in (raw) independent variables (X)

		# handle country
		country_name = row[1]
		if country_name not in countries:
			countries.append(country_name)
		country = countries.index(country_name)

		# handle fuel type
		fuel_name = row[6]
		if fuel_name not in fuel_types:
			fuel_types.append(fuel_name)
		fuel = fuel_types.index(fuel_name)

		# handle plant capacity
		capacity_mw = float(row[7])
		if country not in capacity_totals:
			capacity_totals[country] = 0
		if country not in capacity_totals_by_fuel:
			capacity_totals_by_fuel[country] = {}
		if fuel not in capacity_totals_by_fuel[country]:
			capacity_totals_by_fuel[country][fuel] = 0
		capacity_totals[country] += capacity_mw
		capacity_totals_by_fuel[country][fuel] += capacity_mw

		# handle year
		year = int(row[9])

		# add (raw) independent variable data to training set
		X_data.append([country,fuel,capacity_mw,year])   	# must match feature_name_list (fuel_av_cf added later)

		# calculate capacity factor (dependent variable) and add to training set
		capacity_factor = make_capacity_factor(capacity_mw,float(row[8])) 
		y_data.append(capacity_factor)

		# add capacity factor to list for averaging by country and fuel
		if country not in capacity_factors.keys():
			capacity_factors[country] = {}

		if fuel not in capacity_factors[country].keys():
			capacity_factors[country][fuel] = []

		capacity_factors[country][fuel].append(capacity_factor)

print(u'Read in {0} observations.'.format(len(X_data)))

# calculate fuel-specific capacity factors for each country
for country,fuel_list in capacity_factors.iteritems():
	if country not in fuel_capacity_factors.keys():
		fuel_capacity_factors[country] = {}

	for fuel,cfs in fuel_list.iteritems():
		avg_cf = 0.0 if not len(cfs) else float(sum(cfs)) / len(cfs)
		fuel_capacity_factors[country][fuel] = avg_cf
		print(u'{:6}; {:10}: av c.f.: {:1.2f}'.format(countries[country],fuel_types[fuel],avg_cf))

# add fuel-specific capacity factors to X data
for observation in X_data:
	country = observation[0]
	fuel = observation[1]
	observation.append(fuel_capacity_factors[country][fuel])

# add plant-specific share of total (country) capacity and total (country,fuel-type) capacity
for observation in X_data:
	country = observation[0]
	fuel = observation[1]
	capacity = observation[2]
	capacity_country_share = capacity / capacity_totals[country]
	observation.append(capacity_country_share)
	capacity_country_fuel_share = capacity / capacity_totals_by_fuel[country][fuel]
	observation.append(capacity_country_fuel_share)

# convert X_data, y_data to numpy arrays
X_data_np = np.array(X_data)
y_data_np = np.array(y_data)

# set up k-fold object for cross-validation
kfold = KFold(n_splits = num_folds)

# create fit estimator
est = GradientBoostingRegressor()
est.set_params(**params)

# do fit
print("Fitting model...")
est.fit(X_data_np, y_data_np)
print("...finished fit; doing cross-validation...")
results = cross_val_score(est, X_data_np, y_data_np, cv=kfold)
acc = results.mean()
dev = results.std()
print("Cross val: {:4.3f} (+/-{:4.3f})".format(acc,dev))

# make prediction plot
fig = plt.figure(figsize=(14,7))
fig.subplots_adjust(left=0.05)
fig.subplots_adjust(right=0.95)
fig.subplots_adjust(wspace=0.3)
plt.subplot(1,2,1)
plt.title('Predictions vs data')
plt.xlabel('Capacity factor (data)')
plt.ylabel('Capacity factor (model prediction)')
predictions = cross_val_predict(est, X_data_np, y_data_np, cv=kfold)
plt.scatter(y_data_np, predictions, marker='.')

# calculate r2
r2_score = metrics.r2_score(y_data_np,predictions)
print("R2: {:4.3f}".format(r2_score))

# make feature importance subplot
feature_importance = est.feature_importances_
feature_importance = feature_importance / feature_importance.sum()
sorted_idx = np.argsort(feature_importance)
pos = np.arange(sorted_idx.shape[0]) + 0.5
plt.subplot(1, 2, 2)
plt.barh(pos, feature_importance[sorted_idx], align='center')
feature_names = [feature_name_list[i] for i in sorted_idx]
plt.yticks(pos, feature_names)
plt.xlabel('Relative Importance')
plt.title('Variable Importance')

# display score
ax = plt.gca()
plt.text(0.55,0.36,"Countries: {0}".format(countries),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.32,"Total observations: {0}".format(len(X_data_np)),transform=ax.transAxes,fontsize=12,color='r')	
plt.text(0.55,0.28,"N_estimators: {0}".format(params['n_estimators']),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.24,"Max depth: {0}".format(params['max_depth']),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.20,"Num. folds: {0}".format(num_folds),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.16,"Learning rate: {0}".format(params['learning_rate']),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.12,"Sub-sample: {0}".format(params['subsample']),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.08,"Loss: {0}".format(params['loss']),transform=ax.transAxes,fontsize=12,color='r')
plt.text(0.55,0.04,"R2: {:4.3f}".format(r2_score),transform=ax.transAxes,fontsize=12,color='r')

# show
plt.show()
