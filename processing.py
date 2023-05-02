import numpy as np
import scipy as sp
import pandas as pd
import csv
import config

def procRaw(filePath):
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


def getInfo(wavelength, intensity):
        area = np.trapz(intensity, dx=(wavelength[50]-wavelength[49]))

        sortWavelengths = config.sortWavelengths
        sortSpecies = config.sortSpecies
        
        sortOut = []
        for j in range(0, len(sortWavelengths)):
                for i in range(1, len(wavelength)):
                        if wavelength[i-1] < sortWavelengths[j] and wavelength[i] >= sortWavelengths[j]:
                                sortOut.append(intensity[i])
        
        peakIDs = findPeaks(wavelength, intensity)
        return area, sortSpecies, sortWavelengths, sortOut, peakIDs[0], peakIDs[1]

def normaliseCSV(folder):
        dataFile = pd.read_csv(folder + "/output.csv")
        outputnp = dataFile.to_numpy()
        for i in range(outputnp.shape[1]):
                outputnp[:,i] = outputnp[:,i]*1/max(outputnp[:,i])
        df = pd.DataFrame(outputnp)
        df.to_csv(folder + "/outputNorm.csv")

def findPeaks(wavelength, intensity):
        peaks, _ = sp.signal.find_peaks(intensity, width=5)
        peakLocations = []
        peakIntensities = []
        for p in peaks:
                peakLocations.append(wavelength[p])
                peakIntensities.append(intensity[p])
        return peakLocations, peakIntensities