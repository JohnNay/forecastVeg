import sys, time

logfile = None

def log(category, message, console = True):
    global logfile

    categories = ['INFO','WARNING','ERROR','SUCCESS']
    cat_len = max(map(len,categories))
    

    logtext = '%*s %s\n' % (-(cat_len + 1),category+':',message)

    if console:    
        sys.stderr.write(logtext)
    if logfile:
        logfile.write(logtext)

def init_logfile(filename):
    global logfile

    logfile = open(filename,'a')
    logfile.write("""\
*******************************************************
    Initializing Log File: %s
*******************************************************
    
    """ % time.ctime())

def check_logfile():
    global logfile
    
    if logfile:
        return logfile.name
    else:
        return None

def close_logfile():
    global logfile
    
    if logfile:
        logfile.close()
        logfile = None

