from __future__ import division
import numpy as np
# Fetch command line arguments
import sys
my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
save_data_fp = my_args[1]
old_data_fp = my_args[2]

print "Data loading..."
dat = np.load(load_data_fp + 'finalMatrix.npy')

print "Column names:"
coln = open(load_data_fp + "columnNames.txt").read()
coln = coln.replace('Pixel Reliability', 'PixelReliability')
coln = coln.split()
# Variables to + '_lag'
lags = ["GWP","B1","B2","B3","B4","B5","B6","B7", "nino34"]

if (len(my_args)>3):
  print "Data loading for extra file..."
  load_extra_file = my_args[3]
  landuse = np.load(load_extra_file)
  assert dat.shape[0] == len(landuse)
  dat = np.c_[dat, landuse]
  coln.append("landuse")

print coln

print "Data shape is ", dat.shape # 15 columns by 253 observations x images that are 1927 rows and 1082 columns

print "Unique ID creation..."
meta = open(load_data_fp + "MOD13Q1.005/metadata_MOD13Q1.005.txt").read()
s = 'self.rows'
loc = meta.index(s)+len(s + ':  ')
first_blank_space = meta[loc:len(meta)].index(' ')
nrow = int(meta[loc:loc+first_blank_space])
s = 'self.columns'
loc = meta.index(s)+len(s + ':  ')
first_blank_space = meta[loc:len(meta)].index(' ')
ncol = int(meta[loc:loc+first_blank_space])
uniq_id = np.tile(range(1, nrow*ncol+1), 253)
len(np.unique(uniq_id))
assert dat.shape[0] == len(uniq_id)
dat = np.c_[dat, uniq_id]

coln.append("uniq_id")
print coln

# Time variable:
time_ind = coln.index("timeID") # col num for time
np.unique(dat[:,time_ind])
print "Head and tail of time:", dat[:100,time_ind], dat[-100:,time_ind]

print "Reshaping data so that unique ID is primary sorting variable and timeID is secondary..."
ind = np.lexsort((dat[:,time_ind], dat[:,-1]))
dat = dat[ind]

print "Adding time_period variable after we have re-ordered into time sequencing..."
# add a variable that indicates the time period of the year
# in R:
# time_period <- rep(as.factor(rep(1:23, 11)), nrow(d)/length(as.factor(rep(1:23, 11))))
# stopifnot(length(time_period) == nrow(d))
time_for_one_pixel = np.tile(range(1,24), 11)
time_period = np.tile(time_for_one_pixel, dat.shape[0]/len(time_for_one_pixel))
assert len(time_period) == dat.shape[0]
dat = np.c_[dat, time_period]
coln.append("time_period")
print "New column names:", coln

if 'SL' in coln:
  print "Using the SL indicator variable to subset out all the non-SL pixels..."
  #  1 == Sri Lanka and 0 == ocean
  np.unique(dat[:,coln.index("SL")])
  dat = dat[dat[:, coln.index("SL")]==1]
  
if 'landuse' in coln:
  print "Using the landuse indicator variable to subset out all the pixels missing landuse..."
  print "Data shape before dropping", dat.shape
  dat = dat[dat[:, coln.index("landuse")] != -9999]
  print "Data shape after dropping", dat.shape

print "Turn into pandas DataFrame for lagging and saving."
import pandas as pd
assert len(coln)==dat.shape[1]
df = pd.DataFrame(dat, columns = coln) # dat is a numpy 2d array
print "Created the pandas DataFrame."

print "Lagging predictor variables..."
df.GWP = df.GWP.shift(1) # Gridded world population 
df.B1 = df.B1.shift(1)
df.B2 = df.B2.shift(1)
df.B3 = df.B3.shift(1)
df.B4 = df.B4.shift(1)
df.B5 = df.B5.shift(1)
df.B6 = df.B6.shift(1)
df.B7 = df.B7.shift(1)
df.nino34 = df.nino34.shift(1)  # El Nino
df['EVI_lag'] = df.EVI.shift(1) # lag of outcome variable
print "Lagged all the predictor variables."
print "Data shape is ", df.shape
# In h2o, in next py script, I drop all time period 1 because they have no lagged predictors

coln = df.columns
new = [var + '_lag' if var in lags else var for var in coln]
assert len(df.columns) == len(new)
df.columns = new

# Drop NDVI column for spectral data:
df.drop('NDVI', axis=1, inplace=True)

print "Spliting into training and validation sets..."
## WE RAN THE CODE BELOW FOR INDEX DATA AND NOW LETS JUST LOAD THAT BACK IN AND USE THE SAME TRAINING COLUMN FROM THAT
# prop_train = 0.85
# grid_options = np.unique(df['autocorrelationGrid'])
# training_grids = np.random.choice(a = grid_options, size = round(len(grid_options)*prop_train), replace=False)
# testing_grids = grid_options[np.array([x not in training_grids for x in grid_options])]
# assert sum([len(training_grids), len(testing_grids)]) == len(grid_options)
# assert all([x not in training_grids for x in testing_grids])
# assert all([x not in testing_grids for x in training_grids])
# # create vector allocating every obs to training or testing:
# training = np.array([x in training_grids for x in df['autocorrelationGrid']])
# assert round(sum(training)/len(training), 2) == prop_train or round(sum(training)/len(training), 2) == prop_train + 1 or round(sum(training)/len(training), 2) == prop_train - 1
# assert len(training) == df.shape[0]
# df['training'] = training
data = pd.read_csv(old_data_fp)
df['training'] = data['training']

# Save to csv to then load into h2o:
print "Starting to save to csv format..."
df.to_csv(save_data_fp, header=True, index=False)
print "Done with saving. You can now move to step 2 of the modeling process: processing data for direct input to modeling functions."

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
