from __future__ import division
import numpy as np
import pandas as pd
import time, csv, sys, os
from annoy import AnnoyIndex
from sklearn.metrics import mean_squared_error

my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
saving_model = my_args[1]
saving_fp = my_args[2]
saving_predictions_fp = my_args[3]
Trees = int(my_args[4])
Neighbs = int(my_args[5]) # 30
K = int(my_args[6])

# load_data_fp = /data/john/srilanka/baseline_data.csv
# saving_model = /data/john/srilanka/baseline_model.ann
# saving_fp = output/baseline_holdout.csv
# saving_predictions_fp = /data/john/srilanka/baseline_predicted_holdout.csv
# Trees = 7, Neighbs = 30, K = 10

test = False

def baseline_train(olddata, f, trees):
  """" olddata to train with using f number of features of the data and building an index with trees number of trees """
  t = AnnoyIndex(f)  # Length of item vector that will be indexed
  if(os.path.isfile(saving_model)):
    print "Loading in a pre-made, large read-only data structure we previously made with training data to use for approximate nearest neighbors on holdout data..."
    t.load(saving_model)
  else: 
    print "Creating a large read-only data structure with training data to use for approximate nearest neighbors on holdout data..."
    for i in olddata.index:
      v = list(olddata.ix[i, ['latitude', 'longitude', 'time_period']])
      t.add_item(i, v)
    print "Building the trees..."
    t.build(trees)
    assert t.get_n_items() == olddata.shape[0]
    print "Saving the model..."
    t.save(saving_model) # Can easily be loaded into memory later.
  return(t)

# def baseline_predict(model, newdata, olddata, nbs, k):
#   print "Predicting new data..."
# #   print model.get_n_items()
# #   print  olddata.shape[0]
#   assert model.get_n_items() == olddata.shape[0]
#   pred = []
#   for i in newdata.index:
#     v = list(newdata.ix[i, ['latitude', 'longitude', 'time_period']])
#     ind = model.get_nns_by_vector(v, nbs, search_k = k) # nbs = number of neighbors
#     preds = [olddata.ix[j, 'EVI'] for j in ind] # ind = list with nbs elements
#     pred.append(np.mean(preds))
#   return(pred)

def baseline_predict(model, newdata, olddata, nbs, k):
  """ nbs is a vector with the same length as the vector of unique values of olddata['timeID'] where the it starts out high and then goes down low, e.g. to 3. nbs indicates how many neighbors from the old data to pull out. In this case, unique values of olddata['timeID'] seq from 2 to 253."""
  print "Predicting new data..."
  # print model.get_n_items()
  # print  olddata.shape[0]
  assert model.get_n_items() == olddata.shape[0]
  assert len(nbs) == len(np.unique(olddata['timeID']))
  
  times = np.unique(olddata["timeID"])
  times[0] = 3 # it was 2, make it 3, bc if its 2 `"timeID" < i` will return no rows in next line of code 
  mEVI = [np.mean(olddata.loc[olddata['timeID'] < i, 'EVI']) for i in times]
  
  pred = []
  for i in newdata.index:
    timeID = newdata.ix[i, ['timeID']]
    v = list(newdata.ix[i, ['latitude', 'longitude', 'time_period']])
    ind = model.get_nns_by_vector(v, nbs[(timeID-2)], search_k = k) # nbs = number of neighbors
    preds = [olddata.ix[j, 'EVI'] for j in ind if np.all(olddata.ix[j, ['timeID']] < timeID)] # have to do np.all to convert the Series object into a single boolean
    if len(preds) < 1:
      preds = mEVI[int(timeID-2)]
    pred.append(np.mean(preds))
  return(pred)

# for i in newdata.index[:10]:
#   v = list(newdata.ix[i, ['latitude', 'longitude', 'time_period']])
#   print v
#   ind = t.get_nns_by_vector(v, nbs, search_k = k) # nbs = number of neighbors
#   print ind
#   preds = [olddata.ix[j, 'EVI'] for j in ind] # ind = list with nbs elements    
#   print preds
#   pred.append(np.mean(preds))
#   print np.mean(preds)

def baseline_train_pred(olddata, newdata, nbs, f, trees, k):
  t = baseline_train(olddata, f, trees)
  print "Done training"
  y = baseline_predict(model = t, newdata = newdata, olddata = olddata, nbs = nbs, k=k)
  print "Done predicting"
  return(y)

def evaluate_performance(y, newdata):
  res = mean_squared_error(newdata["EVI"], y)
  print "Baseline MSE:", res
  return(res)

def start_save(csvfile, initialize = ['timing', 'datetime']):
  with open(csvfile, "w") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(initialize)

def run_all_baseline(data, csvfile = saving_fp, 
                    csvfile_vector = saving_predictions_fp,
                    f = 3, trees = 50, nbs = 5, k = 100):
  print "Pre-processing the data..."
  print "Dividing into training and testing with 'autocorrelationGrid' column..."
  prop_train = 0.80 # This is from 1_pre_process.py
  d = data[data['training']]
  assert round(d.shape[0]/data.shape[0], 2) == prop_train or round(d.shape[0]/data.shape[0], 2) == prop_train + .01 or round(d.shape[0]/data.shape[0], 2) == prop_train - .01
  hold_index = data['training'] != True
  holdout = data[hold_index]
  assert holdout.shape[0] + d.shape[0] == data.shape[0]
  del data, d # Use holdout for old and new data so deleting all the other data, just did the above to ensure we had correct holdout
  # d.reset_index([np.arange(len(d.index))], inplace = True)
  holdout.reset_index([np.arange(len(holdout.index))], inplace = True)
  print "Finished pre-processing the data."
  
  start_save(csvfile = csvfile, initialize = ['timing', 'datetime'])
  print "Running baseline..."
  time1 = time.time()
  
  # Use holdout for old and new data so we give baseline best chance possible
  y = baseline_train_pred(olddata = holdout, f = f, trees = trees, newdata = holdout, nbs = nbs, k=k)
  
  temp = {'Pred' : y, 'EVI' : holdout["EVI"], 'landuse': holdout["landuse"], 'time_period' : holdout["time_period"], 'latitude': holdout["latitude"], 'longitude' : holdout["longitude"]}
  out = pd.DataFrame(data = temp)
  out.to_csv(csvfile_vector, header=True, index=False)
  
  timing = time.time() - time1
  datetime = time.strftime("%c")
  tosave = [timing, datetime]
  with open(csvfile, "a") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(tosave)
  print "Finished baseline."

def run_all_baseline_test(data, csvfile = "output/baselinetest.csv", csvfile_vector = "output/baseline_predictedtest.csv",
                          f = 3, trees = 50, nbs = 5, k = 100):
  d = data[:1000]
  holdout = data[1001:2000]
  del data
  start_save(csvfile = csvfile, initialize = ['timing', 'datetime'])
  print "Running baseline..."
  time1 = time.time()
  
  y = baseline_train_pred(olddata = d, f = f, trees = trees, newdata = holdout, nbs = nbs, k=k)
  
  temp = {'Pred' : y, 'EVI' : holdout["EVI"], 'landuse': holdout["landuse"], 'time_period' : holdout["time_period"], 'latitude': holdout["latitude"], 'longitude' : holdout["longitude"]}
  out = pd.DataFrame(data = temp)
  out.to_csv(csvfile_vector, header=True, index=False)
  
  timing = time.time() - time1
  datetime = time.strftime("%c")
  tosave = [timing, datetime]
  with open(csvfile, "a") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(tosave)
  print "Finished baseline test."

print "Loading in data..."
if test:
  testfuncdata = pd.read_csv("/data/john/srilanka/testfuncsmalldata")
  testfuncdata.reset_index([np.arange(len(testfuncdata.index))], inplace = True)
  run_all_baseline_test(testfuncdata, f = 3, trees = Trees, 
                        nbs = np.linspace(Neighbs, 10, num=len(np.unique(testfuncdata['timeID'])), dtype = 'int'), 
                        k = K)
else:
  data = pd.read_csv(load_data_fp)
  # reset index to 0:len because annoy needs index like this.
  # data.reset_index([np.arange(len(data.index))], inplace = True)
  run_all_baseline(data, f = 3, trees = Trees, 
                  nbs = np.linspace(Neighbs, 10, num=len(np.unique(data['timeID'])), dtype = 'int'),
                  k = K)

import smtplib
GMAIL_USERNAME = "gilligan.research"
session = smtplib.SMTP('smtp.gmail.com', 587)
session.ehlo()
session.starttls()
session.login(GMAIL_USERNAME, "Bangarang")
recip = "john.j.nay@vanderbilt.edu"
headers = "\r\n".join(["from: " + GMAIL_USERNAME,
                       "subject: " + "Finished running script: " + __file__,
                       "to: " + recip,
                       "mime-version: 1.0",
                       "content-type: text/html"])

content = headers + "\r\n\r\n" + "Done running the script.\n Sent from my Python code."
session.sendmail(GMAIL_USERNAME, recip, content)
