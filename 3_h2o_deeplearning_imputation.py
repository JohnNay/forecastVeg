from __future__ import division
import sys, time, csv, h2o
import pandas as pd
import numpy as np

arg = sys.argv
print "Running script:", sys.argv[0]
arg = sys.argv[1:]
print "Arguments passed to script:", arg
load_data_fp = arg[0]
saving_meanImputed_fp = arg[1]
saving_modelImputed_fp = arg[2]
saving_means_fp = arg[3]
saving_models_fp = arg[4]
predictors = arg[5:]

# GWP_lag is treated as an int variable. It has no missings, so no need to impute it. 
# But to keep this scripts code simple I impute anything with 'lag' in the var name.
to_impute = [var for var in predictors if 'lag' in var]

h2o.init(min_mem_size_GB=200, max_mem_size_GB = 225)
d = h2o.import_frame(path = load_data_fp)
#######################################################################
print "Making 'time_period' a factor..."
d['time_period'] = d['time_period'].asfactor()
assert d['time_period'].isfactor()
print d.levels(col='time_period')
d.describe()

def impute_data(method = "mean", 
                to_impute = to_impute,
                predictors = predictors):
  if method == "mean":
    print "Mean imputing missing data for predictors:", to_impute
    # find mean for each time period in data for each predictor, save them in a matrix with a col for the mean values of each predictor
    # then on holdout use this table to fill in all missing values based on the time period (row) and the variable (col) of this matrix
    
    #if using python module h2o-3.1.0.3131: grouped = data.group_by(["time_period"])
    #                         gm = [grouped.mean(predictor, na="rm").get_frame() for predictor in to_impute]
    gm = d["time_period"].unique()
    print "Finding means..."
    for predictor in to_impute:
      gm = gm.cbind(d.group_by(["time_period"], {predictor:["mean", d.names().index(predictor), "rm"]}, order_by = 0))
    gm.show()
    print "Saving the imputation means to disk..."
    h2o.download_csv(gm, filename = saving_means_fp)
    # df_py = h2o.as_list(gm)
    # Now that's stored for the holdout data, do this a faster way in java for the training data:
    for predictor in to_impute:
      d.impute(predictor, method='mean', by = ['time_period'], inplace = True)
      print "Done imputing", predictor
    print "Saving the final mean imputed data to disk..."
    h2o.export_file(frame = d, path =saving_meanImputed_fp, force=True)
  
  if method == "model":
    # sequentially impute 'newdata', not 'data', so the order of the predictor variables in the loop does not matter
    # otherwise, you would be using increasingly imputed data to make predictions as the loop progresses.
    newdata = d
    # With training data, build a model for each col and predict missing data, save the models, use them on the holdout data to predict all missing data.
    for predictor in to_impute:
      print "Building model for imputing " + predictor
      print "Subsetting the data into missing values for predictor and no missing values for predictor"
      na_ind = d[predictor].isna()
      not_na_ind = na_ind != 1.0
      to_train = d[not_na_ind]
      to_predict = d[na_ind]
      these_var = [var for var in predictors if var != predictor]
      trained = h2o.gbm(x = to_train[these_var],
                        y = to_train[[predictor]],
                        ntrees=300,
                        max_depth=6,
                        learn_rate=0.2)
      print "Saving the imputation tree model for " + predictor
      h2o.save_model(trained, dir = saving_models_fp, name = "dl_imputation_model_" + predictor)
      print "Imputing the missing " +  predictor + " data by predicting with the model..."
      predicted = trained.predict(to_predict[these_var])
      tofillin = newdata[predictor]
      assert len(predicted) == len(tofillin[na_ind])
      tofillin[na_ind] = predicted # mutate the column in place
      newdata[predictor] = tofillin
    
    print "Saving the final model-imputed data to disk..."
    h2o.export_file(frame = d, path =saving_modelImputed_fp, force=True)

def compare_frames(d1 = saving_meanImputed_fp, 
                  d2 = saving_modelImputed_fp,
                  imputed = to_impute):
  print "Comparing the resulting two matrices..."
  # Load the saved frames back in
  meanI  = h2o.import_file(path = d1)
  modelI = h2o.import_file(path = d2)
  
  meanIquantiles = h2o.as_list(meanI[imputed].quantile(prob=[0.01,0.1,0.25,0.333,0.5,0.667,0.75,0.9,0.99]))
  modelIquantiles = h2o.as_list(modelI[imputed].quantile(prob=[0.01,0.1,0.25,0.333,0.5,0.667,0.75,0.9,0.99]))
  
  meanIcolmeans = [v.mean() for v in meanI[imputed]]  
  modelIcolmeans = [v.mean() for v in modelI[imputed]]  
  
  meanIcolmedians = [v.median() for v in meanI[imputed]]  
  modelIcolmedians = [v.median() for v in modelI[imputed]]  
  
  meanIcolmin = [v.min() for v in meanI[imputed]]  
  modelIcolmin = [v.min() for v in modelI[imputed]]
  # TODO save all this in a csv file

impute_data("mean")
impute_data("model")
# compare_frames()
