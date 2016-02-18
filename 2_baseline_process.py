# Fetch command line arguments
import sys
my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
save_data_fp = my_args[1]

import numpy as np
import pandas as pd

#######################################################################
print "Importing data..."
data = pd.read_csv(load_data_fp)
print "Data shape:", data.shape

#######################################################################
print "Dropping all time period 1 because they have no lagged predictors..."
ind = data["timeID"] != 1
data = data[ind]
print "Data shape:", data.shape

print "Setting all the 9999 to NA..."
data[data==9999] = np.nan

print "Dropping rows where the outcome, EVI, is NA..."
data = data[data['EVI'].notnull()]
print "Data shape:", data.shape

data.to_csv(save_data_fp, header=True, index=False)
