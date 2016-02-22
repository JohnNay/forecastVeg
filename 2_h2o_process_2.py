from __future__ import division
import sys, time, csv, h2o
import numpy as np
import pandas as pd

# Fetch command line arguments
my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
save_training_data_fp = my_args[1]
save_holdout_data_fp = my_args[2]

if (len(my_args)>3):
  print "Saving the vector of training indices because you passed in an argument for a file path to save it."
  save_training_ind_fp = my_args[3]

print "Pre-processing the data..."
testing = False
prop_train = 0.80 # This is from 1_pre_process.py

h2o.init(min_mem_size_GB=200, max_mem_size_GB = 210)
data = h2o.import_frame(path = h2o.locate(load_data_fp))

data.describe()

#######################################################################
print "Setting values of the PixelReliability column to use it for the weights_column in modeling"
PixelReliability = data['PixelReliability']
PixelReliability[PixelReliability==2] = 9999 # this is snow, so set it to NA
PixelReliability[PixelReliability==0] = 2 # this is good, so give it high value: 2
PixelReliability[PixelReliability==3] = 1 # this is medium quality, so give it lower value: 1
data['PixelReliability'] = PixelReliability
print "Unique values of the PixelReliability column:", PixelReliability.unique().show()

data.describe()

print "Dropping rows where the PixelReliability is NA..."
ind = data['PixelReliability'] == 9999
ind = ind!=1.0
ind.show()
print data.dim()
data = data[ind] 
print data.dim()

print "Setting all the -9999.0 in the CA landuse to NA..."
landuse = data['landuse']
landuse[landuse==-9999] = None
landuse[landuse==9999] = None
data['landuse'] = landuse
print data.levels(col='landuse')

#######################################################################
print "Making 'time_period' 'landuse' a factor..."
data['time_period'] = data['time_period'].asfactor()
print data.levels(col='time_period')
data['landuse'] = data['landuse'].asfactor()
print data.levels(col='landuse')
data.describe()

print "Dropping rows where the outcome, EVI, is NA..."
ind = data['EVI'].isna()
ind = ind!=1.0
ind.show()
print data.dim() 
data = data[ind] 
print data.dim()

print "Dividing into training and holdout with 'autocorrelationGrid' column..."
print data.dim()
train_index = data['training']
d = data[train_index]
print d.dim()
print "Proportion of data in training data", d.dim()[0]/data.dim()[0]
assert round(d.dim()[0]/data.dim()[0], 2) == prop_train or round(d.dim()[0]/data.dim()[0], 2) == prop_train + .01 or round(d.dim()[0]/data.dim()[0], 2) == prop_train - .01
hold_index = train_index != 'True'
holdout = data[hold_index]
assert holdout.dim()[0] + d.dim()[0] == data.dim()[0]

h2o.remove([data, hold_index, train_index])
del data, hold_index, train_index

# Create training and testing sets FOR TRAINING DATA here so they are the same in both
# Only do this if user passes in the argument for the file path to save the vector of training indices
if (len(my_args)>3):
  prop_train = 0.80
  autocor = d['autocorrelationGrid']
  print "autocor", autocor.show()
  grid_options = autocor.unique()
  print "Grid options", grid_options.show()
  grid_options_l = h2o.as_list(grid_options, use_pandas=False)
  grid_options = np.squeeze(grid_options_l)
  # drop col name:
  grid_options = grid_options[1:]
  
  # convert autocor to a python list from h2o, lists are too large so have to do this in two pieces
  autocor1 = h2o.as_list(autocor[0:autocor.dim()[0]/2,:,], use_pandas=False)
  autocor2 = h2o.as_list(autocor[len(autocor1):autocor.dim()[0]+1,:,], use_pandas=False)
  autocor_l = autocor1 + autocor2
  autocor = np.squeeze(autocor_l)
  # drop col name:
  autocor = autocor[1:]
  print "autocor head:", autocor[:25]
  print "autocor length:", len(autocor)
  print "data rows:", d.dim()[0]
  
  training_grids = np.random.choice(a = grid_options, size = len(grid_options)*prop_train, replace=False)
  testing_grids = np.array(grid_options[np.array([x not in training_grids for x in grid_options])])
  assert sum([len(training_grids), len(testing_grids)]) == len(grid_options)
  assert all([x not in training_grids for x in testing_grids])
  assert all([x not in testing_grids for x in training_grids])
  # create vector allocating every obs to training or testing:
  training = np.array([x in training_grids for x in autocor])
  print "Proportion of data in training", sum(training)/len(training), "and prop_train =", prop_train
  
  while(not(round(sum(training)/len(training), 2) == prop_train or round(sum(training)/len(training), 2) == prop_train + 0.01 or round(sum(training)/len(training), 2) == prop_train - 0.01 or round(sum(training)/len(training), 2) == prop_train - 0.02 or round(sum(training)/len(training), 2) == prop_train + 0.02)):
    print "Trying to assign data to training in a way that gives us the correct proportion..."
    training_grids = np.random.choice(a = grid_options, size = round(len(grid_options)*prop_train), replace=False)
    testing_grids = np.array(grid_options[np.array([x not in training_grids for x in grid_options])])
    assert sum([len(training_grids), len(testing_grids)]) == len(grid_options)
    assert all([x not in training_grids for x in testing_grids])
    assert all([x not in testing_grids for x in training_grids])
    # create vector allocating every obs to training or testing:
    training = np.array([x in training_grids for x in autocor])
    print "Proportion of data in training", sum(training)/len(training), "and prop_train =", prop_train

  # assert round(sum(training)/len(training), 2) == prop_train or round(sum(training)/len(training), 2) == prop_train + 1 or round(sum(training)/len(training), 2) == prop_train - 1
  print "len(training):", len(training) 
  print "d.dim()[0]:", d.dim()[0]
  #assert len(training) == d.dim()[0]
  # Save to csv to then load into h2o later:
  print "Starting to save to csv format..."
  training = pd.DataFrame(training)
  training.to_csv(save_training_ind_fp, header=False, index=False)
  print "Done with saving training and testing sets for training data."

h2o.export_file(frame = d, path = save_training_data_fp, force=True)
h2o.export_file(frame = holdout, path = save_holdout_data_fp, force=True)

# Send email
email = False
if(email):
  import smtplib
  GMAIL_USERNAME = None
  GMAIL_PW = None
  RECIP = None
  SMTP_NUM = None
  session = smtplib.SMTP('smtp.gmail.com', SMTP_NUM)
  session.ehlo()
  session.starttls()
  session.login(GMAIL_USERNAME, GMAIL_PW)
  headers = "\r\n".join(["from: " + GMAIL_USERNAME,
                         "subject: " + "Finished running script: " + __file__,
                         "to: " + RECIP,
                         "mime-version: 1.0",
                         "content-type: text/html"])
  content = headers + "\r\n\r\n" + "Done running the script.\n Sent from my Python code."
  session.sendmail(GMAIL_USERNAME, RECIP, content)

