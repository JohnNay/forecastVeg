# Fetch command line arguments
import sys
my_args = sys.argv
print "Running script:", sys.argv[0]
my_args = sys.argv[1:]
print "Arguments passed to script:", my_args
load_data_fp = my_args[0]
save_data_fp = my_args[1]

#######################################################################
print "Initializing h2o..."
import h2o
h2o.init(min_mem_size_GB=200, max_mem_size_GB =210)

#######################################################################
print "Importing data..."
data = h2o.import_frame(path = load_data_fp)

#######################################################################
## summarize data
data.describe()
data.dim()
data.head()

#######################################################################
print "Making 'time_period' and 'landuse' a factor..."
data['time_period'] = data['time_period'].asfactor()
data['time_period'].isfactor()
data['landuse'] = data['landuse'].asfactor()
print data.levels(col='landuse')

#######################################################################
print "Dropping all time period 1 because they have no lagged predictors..."
ind = data["timeID"] != 1
data = data[ind] # Gett ERRORS here that the Java heap does not have enough memory, unless you 
# set min_mem_size_GB=40, max_mem_size_GB = 120. Then it works.

print "Setting all the 9999 to NA..."

B1_lag = data['B1_lag']
B1_lag[B1_lag==9999] = None
data['B1_lag'] = B1_lag

B2_lag = data['B2_lag']
B2_lag[B2_lag==9999] = None
data['B2_lag'] = B2_lag

B3_lag = data['B3_lag']
B3_lag[B3_lag==9999] = None
data['B3_lag'] = B3_lag

B4_lag = data['B4_lag']
B4_lag[B4_lag==9999] = None
data['B4_lag'] = B4_lag

B5_lag = data['B5_lag']
B5_lag[B5_lag==9999] = None
data['B5_lag'] = B5_lag

B6_lag = data['B6_lag']
B6_lag[B6_lag==9999] = None
data['B6_lag'] = B6_lag

B7_lag = data['B7_lag']
B7_lag[B7_lag==9999] = None
data['B7_lag'] = B7_lag

EVI_lag = data['EVI_lag']
EVI_lag[EVI_lag==9999] = None
data['EVI_lag']  = EVI_lag 

EVI = data['EVI']
EVI[EVI==9999] = None
data['EVI'] = EVI 

nino34_lag = data['nino34_lag']
nino34_lag[nino34_lag==9999] = None
data['nino34_lag'] = nino34_lag

h2o.export_file(frame = data, path = save_data_fp, force=True)

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
