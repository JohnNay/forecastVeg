import agpredict as ap   
import sys
import os
import subprocess
import argparse

my_args = sys.argv
print "Running script:", sys.argv[0]
a = sys.argv[1:]
print "Arguments passed to script:", my_args
spectral = a[0]
directory = a[1]
username = a[2]
password = a[3]
tiles = a[4].split() 
today = a[5]
enddate = a[6]
referenceImage = a[7]

if spectral == '0':
    mod11 = ap.MOD11A2(directory = directory, username = username, password = password, dataset = 'MOD11A2.005', subset = '1 1 0 0 0 0 0 0 0 0 0 0',
    tiles = tiles, today = today, enddate = enddate, referenceImage = referenceImage)

    mod13 = ap.MOD13Q1(directory = directory, username = username, password = password, dataset = 'MOD13Q1.005', subset = '1 1 1 0 0 0 0 0 0 0 0 1',
    tiles = tiles, today = today, enddate = enddate, referenceImage = referenceImage)

    mod15 = ap.MOD15A2(directory = directory, username = username, password = password, dataset = 'MOD15A2.005', subset = '1 1 1 0 0 0',
    tiles = tiles, today = today, enddate = enddate, referenceImage = referenceImage)

    mod17 = ap.MOD17A2(directory = directory, username = username, password = password, dataset = 'MOD17A2.005', subset = '1 1 1 0 0 0 0 0 0 0 0 0',
    tiles = tiles, today = today, enddate = enddate, referenceImage = referenceImage)
    
    mod11.prepare()
    mod13.prepare()
    mod15.prepare()
    mod17.prepare()
    mod17.finalMatrix()
    
    
if spectral == '1':
    if not os.path.exists(directory):
        os.mkdir(directory)
    if not os.path.exists(directory + '/spectral'):
        os.mkdir(directory + '/spectral')
    mod09 = ap.MOD09A1(directory = directory + '/spectral', username = username, password = password, dataset = 'MOD09A1.005', subset = '1 1 1 1 1 1 1 0 0 0 0 1 0',
    tiles = tiles, today = today, enddate = enddate, referenceImage = referenceImage)
    
    mod09.download()
    mod09.finalMatrix()
    #mod09.prepare()
    #if os.path.isfile(directory + '/MOD13Q1.005.npy'):
        #subprocess.call(['cp', directory + 'MOD13Q1.npy', directory + 'MOD13Q1.txt', directory + '/spectral'])
    #else:
        #mod13 = ap.MOD13Q1(directory = directory + '/spectral', username = username, password = password, dataset = 'MOD13Q1.005', subset = '1 0 1 0 0 0 0 0 0 0 0 1',
        #tiles = tiles, today = today, enddate = enddate, referenceImage = referenceImage)
        #mod13.prepare()
    
    #mod09.finalMatrix()
