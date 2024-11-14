import numpy as np
import scipy as sp
import pandas as pd
import csv
import config
from pybaselines import Baseline, utils
import matplotlib.pyplot as plt

def procRaw(filePath: str):
    delStart = ">>>>>Begin Processed Spectral Data<<<<<"
    delEnd = ">>>>>End Processed Spectral Data<<<<<"
    f = open(filePath, "r")
    reading = False
    dataArr = []

    for line in f:
        line = line.strip()
        if(reading):
            if(line == delEnd):
                reading = False
            else:
                dataArr.append(line)
        elif(line == delStart):
            reading = True
    outWavelength = []
    outData = []
    for l in dataArr:
            data = l.split()
            outWavelength.append(float(data[0]))
            outData.append(float(data[1]))
    return outWavelength, outData


def getInfo(wavelength: list, intensity: list):
    area = np.trapz(intensity, dx=(wavelength[50]-wavelength[49]))

    sortWavelengths = config.sortWavelengths
    sortSpecies = config.sortSpecies
    
    sortOut = []
    for j in range(0, len(sortWavelengths)):
        for i in range(1, len(wavelength)-1):
            if wavelength[i-1] < sortWavelengths[j] and wavelength[i+1] >= sortWavelengths[j]:
                sortOut.append(intensity[i])
    
    peakIDs = findPeaks(wavelength, intensity)
    return area, sortSpecies, sortWavelengths, sortOut, peakIDs[0], peakIDs[1]

def getPeakIndices(wavelenths: list):
    sortWavelengths = config.sortWavelengths
    sortIndex = []
    sortSpec = []
    for j in range(0, len(sortWavelengths)):
        for i in range(0, len(wavelenths)-1):
            if wavelenths[i-1] < sortWavelengths[j] and wavelenths[i+1] > sortWavelengths[j]:
                sortIndex.append(i)
                sortSpec.append(config.sortSpecies[j])
    return sortIndex, sortSpec

def normaliseCSV(folder: str):
    dataFile = pd.read_csv(folder + "/output.csv")
    outputnp = dataFile.to_numpy()
    for i in range(outputnp.shape[1]):
        outputnp[:,i] = (outputnp[:,i]*1-min(outputnp[:,i]))/(max(outputnp[:,i])-min(outputnp[:,i]))
    df = pd.DataFrame(outputnp)
    df.to_csv(folder + "/outputNorm.csv")

def findPeaks(wavelength: list, intensity: list):
    peaks, _ = sp.signal.find_peaks(intensity, width=5)
    peakLocations = []
    peakIntensities = []
    for p in peaks:
        peakLocations.append(wavelength[p])
        peakIntensities.append(intensity[p])
    return peakLocations, peakIntensities

def findLambdaIndex(wavelenths: list, targetWavelength: float):
    """Find the index of a given wavelength in an array of wavelengths"""
    targetIndex = 0
    for i in range(0, len(wavelenths)):
        if wavelenths[i-1] < targetWavelength < wavelenths[i+1]:
            d1 = np.abs(wavelenths[i-1] - targetWavelength)
            d2 = np.abs(wavelenths[i] - targetWavelength)
            d3 = np.abs(wavelenths[i+1] - targetWavelength)
            if d1 == min(d1,d2,d3): targetIndex = i-1
            elif d2 == min(d1,d2,d3): targetIndex = i
            elif d3 == min(d1,d2,d3): targetIndex = i+1
            else: print('Wavelength search error')
    return targetIndex

def normaliseIntensity(intensity: list, Nindex: int):
    return np.divide(intensity, intensity[Nindex])

def peakAnalysis(wavelenth: list, spectrum: list, OES_peakIndex: list, OES_peakSpecies: list, dLambda:float=0.2):
    peaks, peakProperties = sp.signal.find_peaks(spectrum, prominence = 0.0)
    results_half = sp.signal.peak_widths(spectrum, peaks, rel_height = 0.5)
    widths = results_half[0]
    width_height = results_half[1]
    OES_FWHM = []
    OES_FWHM_species = []
    OES_FWHM_promi = []
    widthMatrix = []
    for i in range(0, len(peaks)):
        currDelta = np.round((widths[i]/2)/dLambda)                                                 # Calculate HWHM expressed in wavelength bins
        for j in range(0, len(OES_peakIndex)):
            if peaks[i] - currDelta < OES_peakIndex[j] < peaks[i] + currDelta:                      # Select the peaks that lay in the range between l-HWHM and l+HWHM
                if not(widths[i] in OES_FWHM) and not(OES_peakSpecies[j] in OES_FWHM_species):      # Discount double counts
                    OES_FWHM.append(widths[i] * dLambda)
                    OES_FWHM_species.append(OES_peakSpecies[j])
                    #OES_FWHM_promi.append(peakProperties["prominences"][i])
                    OES_FWHM_promi.append(spectrum[peaks[i]])                                       # Use actual peak height instead of prominence for more consistent results
                    widthMatrix.append([OES_FWHM_species[-1], wavelenth[peaks[i]], OES_FWHM_promi[-1], OES_FWHM[-1]])
    widthMatrix = np.array(widthMatrix)
    widthMatrix.sort(axis=0)
    return np.transpose(widthMatrix)

def backgroundCorrection(x: list, y: list, plot:bool = True):
    # Baseline correction reference: https://pybaselines.readthedocs.io/en/latest/introduction.html
    baselineFilter = Baseline(x_data=x)
    bkg_4, params_4 = baselineFilter.snip(y, max_half_window=40, decreasing=True, smooth_half_window=3)
    if plot:
        plt.figure()
        plt.plot(x, y, label='Raw Data')
        plt.plot(x, bkg_4, '--', label='Background Corrected Data')
        plt.legend()
        plt.show()

    return y-bkg_4

def calcNormDifferenceSpectrum(spectrum: list):
    """Calculate normalised difference spectrum"""
    peak = np.max(np.abs(spectrum))
    return (spectrum)/peak, calcMSE(spectrum)

def calcNormSpectrum(spectrum: list):
    """Calculate baseline corrected normalised spectrum"""
    base = np.percentile(spectrum, 1)
    peak = np.max(np.abs(spectrum-base))
    return (spectrum-base)/peak, calcMSE(spectrum-base)

def calcMSE(data: list):
    n = len(data)
    mseCalc = np.sum(data**2)/n
    return mseCalc

def tolerant_mean(arrs: list):
    """Calculate mean of a set of arrays of unequal lengths"""
    lens = [len(i) for i in arrs]
    arr = np.ma.empty((np.max(lens),len(arrs)))
    arr.mask = True
    for idx, l in enumerate(arrs):
        arr[:len(l),idx] = l
    return arr.mean(axis = -1), arr.std(axis=-1)

def getPeakIDs():
        if config.useNIST:
                sheetName = 'OESNIST'
        else:
                sheetName = 'OESreferences'
        df = pd.read_excel('reference\\OESpeakLocations.xlsx', sheet_name=sheetName)
        specList = df['Species']
        lambList = df['Wavelength']
        trackList = df['Track']
        intBoundStart = df['intRangeStart']
        intBoundEnd = df['intRangeEnd']
        for i in range(0, len(specList)):
            if trackList[i] == 1:
                config.sortSpecies.append(specList[i])
                config.sortWavelengths.append(lambList[i])
                config.sortSpeciesID.append(lambdaToID(lambList[i]))
                if not(config.useNIST):
                    config.sortIntBounds.append([lambdaToID(intBoundStart[i]), lambdaToID(intBoundEnd[i])]) # Outputs start and end of integration bounds as ID



def IDtoLambda(i):
    cubA = 176.66858
    cubB = 0.218
    cubC = -4.15119E-6
    cubD = -5.60485E-10
    cubDela = 1.95077E-4
    cubDelb = -3.91659E-5
    return cubD * i**3 + cubC * i**2 + i*(cubB-cubDela) + cubA - cubDelb

def lambdaToID(lam):
    poly4A = -792.32406
    poly4B = 4.38706
    poly4C = 0.000615907
    poly4D = -0.000000393728
    poly4E = 0.000000000530123
    return round(poly4A + poly4B*lam + poly4C*lam**2 + poly4D*lam**3 + poly4E*lam**4)