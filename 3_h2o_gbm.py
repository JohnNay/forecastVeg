from __future__ import division
import csv, time, sys, pickle, h2o
from hyperopt import fmin, tpe, hp, STATUS_OK, STATUS_FAIL, Trials

my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
load_train_ind_fp = my_args[1]
saving_fp = my_args[2]
predictors = my_args[3:]

# GWP_lag LST_lag NDVI_lag FPAR_lag LAI_lag GP_lag PSN_lag nino34_lag time_period EVI_lag
# if SPECTRAL B1_lag B2_lag B3_lag B4_lag B5_lag B6_lag B7_lag GWP_lag nino34_lag time_period EVI_lag

evals = 35

print "Loading in data..."
print "Not imputing missing predictor data because GBM can handle missing values."

h2o.init(min_mem_size_GB=230, max_mem_size_GB = 240)
d = h2o.import_frame(path = load_data_fp)
train_index = h2o.import_frame(path = load_train_ind_fp)
assert train_index.dim()[0] == d.dim()[0]

#######################################################################
## summarize data
d.describe()
d.head()
#######################################################################
print "Making 'time_period' and 'landuse' a factor..."
d['time_period'] = d['time_period'].asfactor()
assert d['time_period'].isfactor()
print d.levels(col='time_period')
d['landuse'] = d['landuse'].asfactor()
assert d['landuse'].isfactor()
print d.levels(col='landuse')
d.describe()

#######################################################################
d['train_index'] = train_index
train = d[d['train_index']]

test_index = d['train_index'] != 1
test = d[test_index]

print "Training data has",train.ncol(),"columns and",train.nrow(),"rows, test has",test.nrow(),"rows."
assert test.dim()[0] + train.dim()[0] == d.dim()[0]

print "Making data 25% smaller so this doesnt take as long by randomly keeping 75% of the rows."
r = train[0].runif() # Random UNIform numbers (0,1), one per row
train = train[ r < 0.75 ]
print "Training data now has",train.nrow(),"rows."

h2o.remove([test_index, d])
del test_index, d

def start_save(csvfile, initialize = ['mse', 'r2', 'ntrees', 'max_depth', 'learn_rate', 'timing', 'datetime']):
  with open(csvfile, "w") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(initialize)

def split_fit_predict_gbm(ntrees, max_depth, learn_rate):
  """ Splits up training d and score on validation set. Test:
       split_fit_predict_gbm(50, 3, 0.1) """
  print "Fitting GBM with ntrees, max_depth, learn_rate values of:", ntrees, max_depth, learn_rate
  gbm = h2o.gbm(x = train[predictors],
                y = train['EVI'],
                validation_x = test[predictors],
                validation_y = test['EVI'],
                training_frame = train,
                validation_frame = test,
                weights_column = 'PixelReliability',
                distribution = "gaussian",
                ntrees = ntrees,
                max_depth = max_depth,
                learn_rate = learn_rate)
  mse = gbm.mse(valid=True)
  r2 = gbm.r2(valid=True)
  print "GBM MSE:", mse
  return([mse, r2])

def objective(args):
  """ # Test: objective([50, 3, 0.1]) """
  ntrees, max_depth, learn_rate = args
  time1 = time.time()
  try:
    mse, r2 = split_fit_predict_gbm(ntrees, max_depth, learn_rate)
  except:
    print "Error in trying to fit and then predict with gbm model:", sys.exc_info()[0]
    mse = None
    r2 = None
    status = STATUS_FAIL
  else:
    status = STATUS_OK
  timing = time.time() - time1
  datetime = time.strftime("%c")
  tosave = [mse, r2, ntrees, max_depth, learn_rate, timing, datetime]
  with open(saving_fp, "a") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(tosave)    
  return {'loss': mse,
          'status': status,
          # other non-essential results:
          'eval_time': timing}

def run_all_gbm(csvfile = saving_fp, 
                space = [hp.quniform('ntrees', 200, 750, 1), hp.quniform('max_depth', 5, 15, 1), hp.uniform('learn_rate', 0.03, 0.35)]):
  # Search space is a stochastic argument-sampling program:
  start_save(csvfile = csvfile)
  trials = Trials()
  best = fmin(objective,
      space = space,
      algo=tpe.suggest,
      max_evals=evals,
      trials=trials)
  print best
  # from hyperopt import space_eval
  # print space_eval(space, best)
  # trials.trials # list of dictionaries representing everything about the search
  # trials.results # list of dictionaries returned by 'objective' during the search
  print trials.losses() # list of losses (float for each 'ok' trial)
  # trials.statuses() # list of status strings
  with open('output/gbmbest.pkl', 'w') as output:
    pickle.dump(best, output, -1)
  with open('output/gbmtrials.pkl', 'w') as output:
    pickle.dump(trials, output, -1)

# with open('output/gbmtrials.pkl', 'rb') as input:
#     trials = pickle.load(input)
# with open('output/gbmbest.pkl', 'rb') as input:
#   best = pickle.load(input)

run_all_gbm()

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

