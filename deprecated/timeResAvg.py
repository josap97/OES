import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
import config
import processing
import csv
from tkinter.filedialog import askopenfilename
tk.Tk().withdraw()

import plotly.graph_objects as go
scrollThroughData = True            # Set to True to give a window to allow user to scroll through data

# Load Correct Datafiles
config.useNIST = False # Choose to use NIST data (True) or literature data (False)
config.getPeakIDs()
if config.useStaticDataSet: dataFile = 'C:\\Users\\s160880\\OneDrive - TU Eindhoven\\Documents\\P - postMSc Project\\data\\OES\\data\\MLC_02_10.txt'
else: dataFile = askopenfilename()
print(dataFile)

# Reading datafile and definint arrays
print('Reading datafile')
OES_df = pd.read_csv(dataFile, sep='\t')
OES_npArr = OES_df.to_numpy()
OES_t = OES_df.keys().values.tolist()
OES_t = OES_t[1:-2]
timeArr = np.array(OES_t).astype(float)
OES_lambda = OES_npArr[:,0]
OES_refAr = processing.findLambdaIndex(OES_lambda, config.referenceLine)
OES_count = np.transpose(OES_npArr[:,1:-2])

print(OES_count.shape)
plt.figure()
plt.plot(timeArr, OES_count[:,OES_refAr])
plt.xlabel('Time (ms)')
plt.ylabel('Reference Intensity')
plt.show(block=False)

inpStart = float(input('Give *starting* point for averaging in ms: '))
inpEnd = float(input('Give *end* point for averaging in ms: '))

for i in range(1, len(timeArr)-1):
    if timeArr[i-1]<inpStart<=timeArr[i]: tStart = i
    if timeArr[i-1]<inpEnd<=timeArr[i]: tEnd = i

average = np.mean(OES_count[tStart:tEnd, :], axis=0)
std = np.std(OES_count[tStart:tEnd, :], axis=0)

plt.figure()
plt.errorbar(OES_lambda, average, yerr=std)

outArr = np.array([OES_lambda, average, std, np.divide(std, average)])
np.savetxt('timeAveraged.csv', outArr.T, delimiter=',')
print("Results have been written to `timeAveraged.csv` with columns: wavelength (nm), averaged intensity (counts), spread in avg intens (counts), relative error")

plt.show()