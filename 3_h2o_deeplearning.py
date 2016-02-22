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

evals = 45

print "Loading in data..."
h2o.init(min_mem_size_GB = 225, max_mem_size_GB = 230)
d = h2o.import_frame(path = load_data_fp)
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
train_index = h2o.import_frame(path = load_train_ind_fp)
d['train_index'] = train_index
train = d[d['train_index']]

test_index = d['train_index'] != 1
test = d[test_index]

assert test.dim()[0] + train.dim()[0] == d.dim()[0]
print "Training data has",train.ncol(),"columns and",train.nrow(),"rows, test has",test.nrow(),"rows."

print "Making data 25% smaller so this doesnt take as long by randomly keeping 75% of the rows."
r = train[0].runif() # Random UNIform numbers (0,1), one per row
train = train[ r < 0.75 ] 
print "Training data now has",train.nrow(),"rows."

h2o.remove([test_index, train_index, d])
del test_index, train_index, d

def split_fit_predict_dl(h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon):
  print "Trying h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon values of:", h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon
  dl = h2o.deeplearning(x = train[predictors],
                y = train['EVI'],
                validation_x = test[predictors],
                validation_y = test['EVI'],
                training_frame = train,
                validation_frame = test,
                weights_column = 'PixelReliability',
                hidden = [int(h1), int(h2), int(h3)],
                activation = "RectifierWithDropout",
                hidden_dropout_ratios = [hdr1, hdr2, hdr3],
                fast_mode = True,
                rho = rho, epsilon = epsilon)
  mse = dl.mse(valid=True)
  r2 = dl.r2(valid=True)
  print "Deep learning MSE:", mse
  return([mse, r2])

def start_save(csvfile, initialize = ['mse', 'r2', 'h1', 'h2', 'h3', 'hdr1', 'hdr2', 'hdr3', 'rho', 'epsilon', 'timing', 'datetime']):
  with open(csvfile, "w") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(initialize)

def objective(args):
  h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon = args
  time1 = time.time()
  try:
    mse, r2 = split_fit_predict_dl(h1, h2, h3, hdr1, hdr2, hdr3, rho, epsilon)
  except:
    print "Error in trying to fit and then predict with dl model:", sys.exc_info()[0]
    mse = None
    r2 = None
    status = STATUS_FAIL
  else:
    status = STATUS_OK
  
  timing = time.time() - time1
  datetime = time.strftime("%c")
  tosave = [mse, r2, int(h1), int(h2), int(h3), hdr1, hdr2, hdr3, rho, epsilon, timing, datetime]
  with open(saving_fp, "a") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(tosave)
  return {'loss': mse,
        'status': status,
        # other non-essential results:
        'eval_time': timing}

def run_all_dl(csvfile = saving_fp, 
                space = [hp.quniform('h1', 100, 550, 1), 
                        hp.quniform('h2', 100, 550, 1),
                        hp.quniform('h3', 100, 550, 1),
                        #hp.choice('activation', ["RectifierWithDropout", "TanhWithDropout"]),
                        hp.uniform('hdr1', 0.001, 0.3),
                        hp.uniform('hdr2', 0.001, 0.3),
                        hp.uniform('hdr3', 0.001, 0.3),
                        hp.uniform('rho', 0.9, 0.999), 
                        hp.uniform('epsilon', 1e-10, 1e-4)]):
          # maxout works well with dropout (Goodfellow et al 2013), and rectifier has worked well with image recognition (LeCun et al 1998)
          start_save(csvfile = csvfile)
          trials = Trials()
          print "Deep learning..."
          best = fmin(objective,
                      space = space,
                      algo=tpe.suggest,
                      max_evals=evals,
                      trials=trials)
          print best
          print trials.losses()
          with open('output/dlbest.pkl', 'w') as output:
            pickle.dump(best, output, -1)
          with open('output/dltrials.pkl', 'w') as output:
            pickle.dump(trials, output, -1)

run_all_dl()

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

