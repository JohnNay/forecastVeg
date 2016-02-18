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
h2o.init(min_mem_size_GB=200, max_mem_size_GB = 210)

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
# set min_mem_size_GB>=40, max_mem_size_GB >= 120. Then it works.

print "Setting all the 9999 to NA..."
# This doesnt work: data[data==9999] = NaN
# So i have to do it for every column, which are modified in place after being selected out of the frame:

# GWP has no missing data
# GWP_lag = data['GWP_lag']
# GWP_lag[GWP_lag==9999.0] = None
# data['GWP_lag'] = GWP_lag

# want to do this but it doesnt work: data['LST_lag'][data['LST_lag']==9999] = None
LST_lag = data['LST_lag']
LST_lag[LST_lag==9999] = None
data['LST_lag'] = LST_lag

NDVI_lag = data['NDVI_lag']
NDVI_lag[NDVI_lag==9999] = None
data['NDVI_lag'] = NDVI_lag

EVI_lag = data['EVI_lag']
EVI_lag[EVI_lag==9999] = None
data['EVI_lag']  = EVI_lag 

EVI = data['EVI']
EVI[EVI==9999] = None
data['EVI'] = EVI 

FPAR_lag = data['FPAR_lag']
FPAR_lag[FPAR_lag==9999] = None
data['FPAR_lag'] = FPAR_lag 

LAI_lag = data['LAI_lag']
LAI_lag[LAI_lag==9999] = None
data['LAI_lag'] = LAI_lag 

GP_lag = data['GP_lag']
GP_lag[GP_lag==9999] = None
data['GP_lag'] =GP_lag 

PSN_lag = data['PSN_lag']
PSN_lag[PSN_lag==9999] = None
data['PSN_lag'] = PSN_lag 

nino34_lag = data['nino34_lag']
nino34_lag[nino34_lag==9999] = None
data['nino34_lag'] = nino34_lag 

# h2o.remove([LST_lag, NDVI_lag, EVI_lag, EVI, PixelReliability, FPAR_lag, LAI_lag, GP_lag, PSN_lag, nino34_lag])
# del LST_lag, NDVI_lag, EVI_lag, EVI, PixelReliability, FPAR_lag, LAI_lag, GP_lag, PSN_lag, nino34_lag

h2o.export_file(frame = data, path = save_data_fp, force=True)

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
