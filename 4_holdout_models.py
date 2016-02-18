from __future__ import division
import pandas as pd
import numpy as np
import csv, time, sys, pickle, h2o

my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
train_data_fp = my_args[1]
training_res_fp = my_args[2]
saving_fp = my_args[3]
saving_predictions_fp = my_args[4]
saving_varimp_fp = my_args[5]
predictors = my_args[6:]

# predictors = GWP_lag LST_lag NDVI_lag FPAR_lag LAI_lag GP_lag PSN_lag nino34_lag time_period EVI_lag

print "Loading in data..."
h2o.init(min_mem_size_GB=200, max_mem_size_GB = 210)

# holdout = h2o.import_frame(path = "/data/john/srilanka/h2o_data_holdout")
# di = h2o.import_frame(path = "/data/john/srilanka/model_imputed_data")
# 
# def fit_predict_dl(params, predictors, csvfile):
#   h1, h2, h3, hdr1, hdr2, hdr3, l2, l1, rho, epsilon = params
#   time1 = time.time()
#   print "Fitting deep learning with h1, h2, h3, hdr1, hdr2, hdr3, l2, l1, rho, epsilon values of:", h1, h2, h3, hdr1, hdr2, hdr3, l2, l1, rho, epsilon
#   dl = h2o.deeplearning(x = d[predictors],
#                 y = di['EVI'],
#                 validation_x = holdout[predictors],
#                 validation_y = holdout['EVI'],
#                 hidden = [h1, h2, h3],
#                 activation = "RectifierWithDropout",
#                 hidden_dropout_ratios = [hdr1, hdr2, hdr3],
#                 l2 = l2, l1 = l1,
#                 rho = rho, epsilon = epsilon)
#   res = dl.mse(valid=True)
#   print "Deep learning MSE:", res
#   timing = time.time() - time1
#   datetime = time.strftime("%c")
#   tosave = [res, timing, datetime]
#   with open(csvfile, "a") as output:
#     writer = csv.writer(output, lineterminator='\n')
#     writer.writerow(tosave)
#   return(h2o.as_list(dl.predict(holdout[predictors])))

holdout = h2o.import_frame(path = load_data_fp)
print "Making 'time_period' and 'landuse' a factor..."
holdout['time_period'] = holdout['time_period'].asfactor()
assert holdout['time_period'].isfactor()
print holdout.levels(col='time_period')
holdout['landuse'] = holdout['landuse'].asfactor()
assert holdout['landuse'].isfactor()
print holdout.levels(col='landuse')
holdout.describe()

d = h2o.import_frame(path = train_data_fp)
print "Making 'time_period' and 'landuse' a factor..."
d['time_period'] = d['time_period'].asfactor()
assert d['time_period'].isfactor()
print d.levels(col='time_period')
d['landuse'] = d['landuse'].asfactor()
assert d['landuse'].isfactor()
print d.levels(col='landuse')
d.describe()

def fit_predict_gbm(params, predictors, csvfile, saving_varimp_fp):
  ntrees, max_depth, learn_rate = params
  time1 = time.time()
  print "Fitting GBM with ntrees, max_depth, learn_rate values of:", ntrees, max_depth, learn_rate
  model = h2o.gbm(x = d[predictors],
                y = d['EVI'],
                training_frame = d,
                weights_column = 'PixelReliability',
                distribution = "gaussian",
                ntrees = ntrees,
                max_depth = max_depth,
                learn_rate = learn_rate)
  
  varimp = model.varimp(return_list=True) # Each entry is a 4-tuple of (variable, relative_importance, scaled_importance, percentage)
  with open(saving_varimp_fp, "a") as output:
    writer = csv.writer(output, lineterminator='\n')
    for item in varimp:
      writer.writerow(item)
  
  timing = time.time() - time1
  datetime = time.strftime("%c")
  tosave = [timing, datetime]
  with open(csvfile, "a") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(tosave)
  
  # lists are too large so have to do this in two pieces
  yh2o = model.predict(holdout[predictors])
  y1 = h2o.as_list(yh2o[0:yh2o.dim()[0]/2,:,], use_pandas=False)
  y2 = h2o.as_list(yh2o[len(y1):yh2o.dim()[0]+1,:,], use_pandas=False)
  y_l = y1 + y2
  y = np.squeeze(y_l)
  
  evi = holdout["EVI"]
  yreal1 = h2o.as_list(evi[0:evi.dim()[0]/2,:,], use_pandas=False)
  yreal2 = h2o.as_list(evi[len(yreal1):evi.dim()[0]+1,:,], use_pandas=False)
  yreal_l = yreal1 + yreal2
  yreal = np.squeeze(yreal_l)
  
  lu = holdout["landuse"]
  lu1 = h2o.as_list(lu[0:lu.dim()[0]/2,:,], use_pandas=False)
  lu2 = h2o.as_list(lu[len(lu1):lu.dim()[0]+1,:,], use_pandas=False)
  lu_l = lu1 + lu2
  landuse = np.squeeze(lu_l)
  
  tp = holdout["time_period"]
  tp1 = h2o.as_list(tp[0:tp.dim()[0]/2,:,], use_pandas=False)
  tp2 = h2o.as_list(tp[len(tp1):tp.dim()[0]+1,:,], use_pandas=False)
  tp_l = tp1 + tp2
  time_period = np.squeeze(tp_l)
  
  lat = holdout["latitude"]
  lat1 = h2o.as_list(lat[0:lat.dim()[0]/2,:,], use_pandas=False)
  lat2 = h2o.as_list(lat[len(lat1):lat.dim()[0]+1,:,], use_pandas=False)
  lat_l = lat1 + lat2
  latitude = np.squeeze(lat_l)
  
  longi = holdout["longitude"]
  longi1 = h2o.as_list(longi[0:longi.dim()[0]/2,:,], use_pandas=False)
  longi2 = h2o.as_list(longi[len(longi1):longi.dim()[0]+1,:,], use_pandas=False)
  longi_l = longi1 + longi2
  longitude = np.squeeze(longi_l)
  
  #   yreal = h2o.as_list(holdout["EVI"], use_pandas=True)
  #   landuse = h2o.as_list(holdout["landuse"], use_pandas=True)
  #   time_period = h2o.as_list(holdout["time_period"], use_pandas=True)
  #   latitude = h2o.as_list(holdout["latitude"], use_pandas=True)
  #   longitude = h2o.as_list(holdout["longitude"], use_pandas=True)
  out = pd.DataFrame({'Pred' : y, 'EVI' : yreal, 'landuse': landuse, 'time_period' : time_period, 'latitude':latitude, 'longitude' : longitude})
  #   temp = {'predicted': y, 'real': yreal}
  #   out = pd.DataFrame(data = temp)
  return(out)

def start_save(csvfile, initialize):
  with open(csvfile, "w") as output:
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(initialize)

def final_predict(best_params, predict_function,
                  csvfile, csvfile_vector, saving_varimp_fp,
                  predictors = predictors):
  print "Training d has",d.ncol(),"columns and",d.nrow(),"rows, holdout has",holdout.nrow(),"rows."
  start_save(csvfile = csvfile, initialize = ['timing', 'datetime'])
  start_save(csvfile = saving_varimp_fp, initialize = ['variable', 'relative_importance', 'scaled_importance', 'percentage'])
  out = predict_function(best_params, predictors, csvfile, saving_varimp_fp)
  out.to_csv(csvfile_vector, header=True, index=False)

gbm = pd.read_csv(training_res_fp, sep=',')
# dl = pd.read_csv("output/dlres.csv", sep=',')
# 
# final_predict(dl.ix[dl['res'].idxmin(), ['h1', 'h2', 'h3', 'hdr1', 'hdr2', 'hdr3', 'l2', 'l1', 'rho', 'epsilon']], 
#               fit_predict_dl,
#               csvfile = "output/dl_holdout.csv", 
#               csvfile_vector = "/data/john/srilanka/dl_predicted_holdout.csv")
final_predict(gbm.ix[gbm['mse'].idxmin(), ['ntrees', 'max_depth', 'learn_rate']], 
              fit_predict_gbm,
              csvfile = saving_fp, saving_varimp_fp = saving_varimp_fp,
              csvfile_vector = saving_predictions_fp)

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
