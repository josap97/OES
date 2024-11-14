import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tkinter import filedialog
import processing as proc
import config

config.useNIST = False # Choose to use NIST data (True) or literature data (False)
config.getPeakIDs()

folderPath = filedialog.askdirectory()
if(folderPath != ""):
    first = True
    outPutFile = open(folderPath + "/output.csv", 'w', newline='')
    writer = csv.writer(outPutFile)
    outPutFilePeaks = open(folderPath + "/outputPeaks.csv", 'w', newline='')
    writerPeaks = csv.writer(outPutFilePeaks)
    fullPeakLocations = []

    print("Folder found, results processing started")
    files = os.listdir(folderPath)
    for file in files:
        if ".txt" in file:
            processed = proc.procRaw(folderPath + "/" + file)
            wavelength = processed[0]
            intensity = processed[1]

            spectrumInfo = proc.getInfo(wavelength, intensity)
            currArea = spectrumInfo[0]
            currSpecies = spectrumInfo[1]
            currWavelengths = spectrumInfo[2]
            currIntensities = spectrumInfo[3]
            currPeakLocation = spectrumInfo[4]
            fullPeakLocations.append(currPeakLocation)
            if not(first):
                outWrite = [currArea]
                for inten in currIntensities:
                    outWrite.append(inten)
                writer.writerow(outWrite)
                writerPeaks.writerow(currPeakLocation)
            else:
                outWrite = ["Area"]
                for species in currSpecies:
                    outWrite.append(species)
                writer.writerow(outWrite)
                outWrite = [currArea]
                for inten in currIntensities:
                    outWrite.append(inten)
                writer.writerow(outWrite)
                writerPeaks.writerow(currPeakLocation)
            first = False
outPutFile.close()
outPutFilePeaks.close()
print("Spectra processing finished, results written to output.csv in original folder")

proc.normaliseCSV(folderPath)
print("Normalisation finished, results written to outputNorm.csv in original folder")

plt.hist(fullPeakLocations)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Occurrences')
plt.title('Peak Location Histogram')
plt.show()
plt.savefig('wavelengthHistogram.png')