import numpy as np
import pandas as pd
import scipy as sp
import matplotlib.pyplot as plt
import tkinter as tk
import config
import processing as proc
import csv
from tkinter.filedialog import askopenfilename
tk.Tk().withdraw()
import matplotlib
try: import scienceplots; plt.style.use(['science', 'notebook'])
except ModuleNotFoundError: print("SciencePlots is not installed, will try to make plots without it.")
matplotlib.use('TkAgg')

import plotly.graph_objects as go
scrollThroughData = True            # Set to True to give a window to allow user to scroll through data

# Load Correct Datafiles
config.useNIST = False # Choose to use NIST data (True) or literature data (False)
proc.getPeakIDs()
if config.useStaticDataSet: dataFile = 'C:\\Users\\s160880\\OneDrive - TU Eindhoven\\Documents\\P - postMSc Project\\data\\OES\\data\\MLC_02_10.txt'
else: dataFile = askopenfilename()
print(dataFile)

# Definition of Constants
h = sp.constants.Planck
c = sp.constants.speed_of_light
Ce = sp.constants.elementary_charge
JtoEv = 1/Ce

# Reading reference data
print('Reading Reference')
ref_df = pd.read_csv('reference\\refArgon.txt', sep='\t')
ref_Arr = ref_df.to_numpy()
ref_Arr = ref_Arr.transpose()
ref_lambda = ref_Arr[0]
ref_Intens = ref_Arr[1]
ref_index = proc.findLambdaIndex(ref_lambda, config.referenceLine)
ref_nInensCalc = proc.normaliseIntensity(ref_Intens, ref_index)

# Reading datafile and definint arrays
print('Reading datafile')
OES_df = pd.read_csv(dataFile, sep='\t', header=None)
OES_npArr = OES_df.to_numpy()
OES_t = OES_npArr[0,1:]
timeArr = np.array(OES_t).astype(float)
OES_lambda = OES_npArr[1:,0]
OES_refAr = proc.findLambdaIndex(OES_lambda, config.referenceLine)
dLambda = (max(OES_lambda)-min(OES_lambda))/len(OES_lambda)
OES_Eaxis = h*c/(np.flip(OES_lambda)*10**(-9))      # Flip lambda array since high E is low lambda, this yields an incorrect integration
if not(config.energyInJoule): OES_Eaxis = OES_Eaxis * JtoEv
OES_count = np.transpose(OES_npArr[1:,1:-2])
OES_intensity = []
OES_peakIndex, OES_peakSpecies = proc.getPeakIndices(OES_lambda)
OES_refDelta = []
OES_species_intens = []

# Background Subtraction
# Assumes no plasma in first 10 spectra
print('Analysis started')
avgSpec = np.mean(OES_count[0:10], axis=0)
#OES_count = np.subtract(OES_count, avgSpec)


peakIntensitiesArr = []
peakEnergyArr = []
for tSnap in OES_count:
    # Integrate spectrum
    intens = np.trapz(tSnap, OES_Eaxis)
    OES_intensity.append(intens)
    specIntens = []
    for i in range(0, len(config.sortSpecies)):
        Esec = np.flip(OES_Eaxis)[config.sortIntBounds[i][0]:config.sortIntBounds[i][1]]
        specIntens.append(np.trapz(tSnap[config.sortIntBounds[i][0]:config.sortIntBounds[i][1]], np.flip(Esec)))
        #specIntens.append(np.trapz(tSnap[config.sortIntBounds[i][0]:config.sortIntBounds[i][1]], OES_lambda[config.sortIntBounds[i][0]:config.sortIntBounds[i][1]]))
    OES_species_intens.append(specIntens)

    # Get Peak Positions and Intensities
    spectrumInfo = proc.getInfo(OES_lambda, tSnap)
    currArea = spectrumInfo[0]
    currSpecies = spectrumInfo[1]
    currWavelengths = spectrumInfo[2]
    currIntensities = spectrumInfo[3]
    currPeakLocation = spectrumInfo[4]
    peakIntensitiesArr.append(currIntensities)

    # Calculate Difference Spectra
    normSpectrum = proc.normaliseIntensity(tSnap, OES_refAr)[1:]
    OES_refDelta.append(np.subtract(normSpectrum, ref_nInensCalc[:len(normSpectrum)]))

print('Plotting started')
if scrollThroughData:
    fig = go.Figure()

OES_intensityNorm = (OES_intensity-min(OES_intensity))/(max(OES_intensity) - min(OES_intensity))
plasmaOnTime = 0.0
plasmaOnIndex = 0.0
plasmaOffTime = 0.0
plasmaOffIndex = 0.0
plasmaInit = False
plasmaOnArr = []
for i in range(0, len(OES_intensityNorm)):
    # print("t={0}, intens = {1}, valid={2}".format(timeArr[i], OES_intensityNorm[i], (plasmaOnTime == 0) and (OES_intensityNorm[i] >= config.plasmaOnThreshold) and i>20))
    if (plasmaOnTime == 0) and (OES_intensityNorm[i] >= config.plasmaOnThreshold) and not(plasmaInit) and i>20:
        plasmaOnTime = timeArr[i-1]; 
        plasmaOnIndex = i; 
        plasmaInit = True
    if plasmaOnTime != 0 and plasmaOffTime == 0 and OES_intensityNorm[i] <= config.plasmaOffThreshold: plasmaOffTime = timeArr[i-1]; plasmaOffIndex = i
    if OES_intensityNorm[i] > config.plasmaOnThreshold and i>50: plasmaOnArr.append(1)
    else: plasmaOnArr.append(0)
    if plasmaOnArr[i]==1 and scrollThroughData: fig.add_trace(go.Scatter(visible=False, x=OES_lambda, y=OES_count[i]))

if scrollThroughData and config.plotInteractive:
    fig.data[0].visible = True
    steps = []
    onCount = 0
    for i in range(0, len(plasmaOnArr)):
        if plasmaOnArr[i]==1:
            step = dict(method="update",args=[{"visible": [False] * len(fig.data)}, {"title": "Current spectrum for t=" + str(int(float(OES_t[i])-float(plasmaOnTime)))}],)
            step["args"][0]["visible"][onCount] = True
            steps.append(step)
            onCount = onCount + 1
    sliders = [dict(active=10,currentvalue={"prefix": "Frequency: "},pad={"t": 50},steps=steps)]
    fig.update_layout(sliders=sliders)
    fig.add_vline(x=750.38, line_width=3, line_dash='dash', line_color='red', annotation_text='ArgonII')
    fig.add_vline(x=810.36, line_width=3, line_dash='dash', line_color='red', annotation_text='ArgonI')
    fig.add_vline(x=656.28, line_width=3, line_dash='dash', line_color='red', annotation_text='Halpha')
    fig.add_vline(x=443, line_width=3, line_dash='dash', line_color='red', annotation_text='SiF')
    fig.add_vline(x=336.58, line_width=3, line_dash='dash', line_color='red', annotation_text='SiO2(110)')
    fig.add_vline(x=703.8, line_width=3, line_dash='dash', line_color='red', annotation_text='F')
    fig.add_vline(x=685.8, line_width=3, line_dash='dash', line_color='red', annotation_text='F NIST')
    fig.show()

plt.plot(OES_lambda, OES_count[int(len(OES_count)/2)])
plt.ylabel('Intensity (counts)')
plt.xlabel('Wavelength (nm)')

plt.figure()
plt.plot(OES_Eaxis, OES_count[int(len(OES_count)/2)])
plt.ylabel('Intensity (counts)')
if config.energyInJoule: plt.xlabel('Photon Energy (J)')
else: plt.xlabel('Photon Energy (eV)')

plt.figure()
tlen = len(timeArr)
intlen = len(OES_intensity)
plt.plot(timeArr[:min(tlen,intlen)], OES_intensity[:min(tlen,intlen)])
plt.axvline(x = plasmaOnTime, color = 'b', label = 'Plasma On')
plt.axvline(x = plasmaOffTime, color = 'r', label = 'Plasma Off')
if config.energyInJoule: plt.ylabel('Plasma Energy (J)')
else: plt.ylabel('Plasma Energy (eV)')
plt.xlabel('Time (us)')

# Plot Evolution of Species Intensity
plt.figure()
for peak in np.transpose(peakIntensitiesArr):
    tlen = len(timeArr)
    intlen = len(peak)
    plt.plot(timeArr[:min(tlen,intlen)], peak[:min(tlen,intlen)])
plt.axvline(x = plasmaOnTime, color = 'b', label = 'Plasma On')
plt.axvline(x = plasmaOffTime, color = 'r', label = 'Plasma Off')
plt.xlabel('Time (us)')
plt.ylabel('Line Intensity (counts)')
plt.legend(currSpecies)

plt.figure()
for peak in np.transpose(peakIntensitiesArr):
    tlen = len(timeArr)
    intlen = len(peak)
    plt.plot(timeArr[:min(tlen,intlen)], np.divide(peak, np.transpose(peakIntensitiesArr)[0])[:min(tlen,intlen)])
plt.axvline(x = plasmaOnTime, color = 'b', label = 'Plasma On')
plt.axvline(x = plasmaOffTime, color = 'r', label = 'Plasma Off')
plt.xlabel('Time (us)')
plt.ylabel('Normalised Line Intensity')
plt.legend(currSpecies)

plt.figure()
for species in np.transpose(OES_species_intens):
    tlen = len(timeArr)
    intlen = len(peak)
    plt.plot(timeArr[:min(tlen,intlen)], species[:min(tlen,intlen)])
plt.axvline(x = plasmaOnTime, color = 'b', label = 'Plasma On')
plt.axvline(x = plasmaOffTime, color = 'r', label = 'Plasma Off')
plt.xlabel('Process time (s)')
plt.ylabel('Integrated Intensity (counts)')
plt.legend(currSpecies)

# Difference Spectra
plt.figure()
diffArr = np.subtract(OES_intensity[:-1],OES_intensity[1:])
for i in range(0, len(plasmaOnArr)-1):
    if plasmaOnArr[i]==1 and (np.abs(diffArr[i])>max(diffArr)*0.05):
        diffCount = OES_count[i]-OES_count[i-1]
        plt.plot(OES_lambda, diffCount, label = int(float(OES_t[i]) - float(plasmaOnTime)))
plt.ylabel('$\\Delta I$ Change in Intensity (counts)')
plt.xlabel('Wavelength (nm)')
plt.legend()

# Ar Normalised Difference Spectra
plt.figure()
for i in range(0, len(plasmaOnArr)-1):
    if plasmaOnArr[i]==1 and (np.abs(diffArr[i])>max(diffArr)*0.05):
        plt.plot(OES_lambda[1:], OES_refDelta[i], label = int(float(OES_t[i]) - float(plasmaOnTime)))
plt.ylabel('$\\Delta I$ Normalised to Ar (counts)')
plt.xlabel('Wavelength (nm)')
plt.legend()

print('Writing to output files')
if config.spPeakAnalysis:
    sortMatrix = proc.peakAnalysis(OES_lambda, OES_count[plasmaOnIndex+10], OES_peakIndex, OES_peakSpecies, dLambda)
    matrixHeaderSpec = sortMatrix[0]
    matrixHeaderLambda = sortMatrix[1]
    wtrWidth = csv.writer(open ('output\\OES_widthTime.csv', 'w'), delimiter=',', lineterminator='\n')
    wtrPromi = csv.writer(open ('output\\OES_promiTime.csv', 'w'), delimiter=',', lineterminator='\n')
    wtrTimeNorm = csv.writer(open ('output\\OES_timeNorm.csv', 'w'), delimiter=',', lineterminator='\n')
    dataHeaders = np.concatenate((['time'], matrixHeaderSpec), axis = None)
    dataHeadersLam = np.concatenate((['lambda'], matrixHeaderLambda), axis = None)
    wtrWidth.writerow(dataHeaders)
    wtrWidth.writerow(dataHeadersLam)
    wtrPromi.writerow(dataHeaders)
    wtrPromi.writerow(dataHeadersLam)
    wtrTimeNorm.writerow(np.insert(OES_lambda, 0, 0).tolist())
    for k in range(plasmaOnIndex, plasmaOffIndex):
        # Analyse Peaks and Plot
        currentSpectrum = OES_count[k]
        widthMatrix = proc.peakAnalysis(OES_lambda, OES_count[k], OES_peakIndex, OES_peakSpecies, dLambda)
        if len(widthMatrix[0]) == len(matrixHeaderSpec):
            if np.array_equal(widthMatrix[0], matrixHeaderSpec):
                wtrWidth.writerow(np.insert(widthMatrix[3], 0, float(OES_t[k])-float(plasmaOnTime)).tolist())
                wtrPromi.writerow(np.insert(widthMatrix[2], 0, float(OES_t[k])-float(plasmaOnTime)).tolist())
                wtrTimeNorm.writerow(np.insert(OES_refDelta[k], 0, float(OES_t[k])-float(plasmaOnTime)).tolist())

print("Maximum total plasma energy: {0} J or {1} eV".format(max(OES_intensity)-min(OES_intensity), (max(OES_intensity)-min(OES_intensity))*JtoEv))

deltaTimeArr = np.subtract(timeArr, float(plasmaOnTime))
if config.writeEnergyToCSV:
    wtr = csv.writer(open ('output\\OES_integrated_data.csv', 'w'), delimiter=',', lineterminator='\n')
    dataHeaders = np.concatenate((['time', 'Plasma Energy (J)', 'Plasma Energy (eV)', 'Plasma On'], currSpecies), axis = None)
    wtr.writerow (dataHeaders)
    for x in range(0, len(deltaTimeArr)):
        if plasmaOnArr[min(x+20, len(deltaTimeArr)-1)]==1 or plasmaOnArr[max(x-20,0)]==1 or config.steadyStateAnalysis:
            #wtr.writerow(np.concatenate(([OES_t[x], OES_intensity[x], OES_intensity[x]*JtoEv, plasmaOnArr[x]], peakIntensitiesArr[x]), axis=None))
            wtr.writerow(np.concatenate(([deltaTimeArr[x], OES_intensity[x], OES_intensity[x]*JtoEv, plasmaOnArr[x]], OES_species_intens[x]), axis=None))
    import os
    os.system("start EXCEL.exe output\\OES_integrated_data.csv")

if config.plotAll: plt.show()
print('Done')