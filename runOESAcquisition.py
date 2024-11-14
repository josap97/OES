import seabreeze.spectrometers as sb
import numpy as np
import pandas as pd
import time
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib import colors
import processing as proc
import config
import matplotlib
try: import scienceplots; plt.style.use(['science', 'notebook'])
except ModuleNotFoundError: print("SciencePlots is not installed, will try to make plots without it.")
matplotlib.use('TkAgg')

# Parse arguments from the command line
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-set", help = "Set reference values, 'dark' for background, 'plasma' for an active plasma.")
parser.add_argument("-tacq", help="Take temporally resolved acquisition with software triggering. This requires a valid -set run to have been performed.")
parser.add_argument("-intens", help="Set to any value to plot intensity over time")
parser.add_argument("-setIntTime", help="Set integration time for the spectrometer in microseconds.")
parser.add_argument("-reset", help="Set to any value set the cycle index counter")
parser.add_argument("-setProc", help="Set process name to any string, used to ID files")
parser.add_argument("-track", help="Track the intensity of species during a SHORT process. Wavelengths are set in trackSpecies in config. Output will be generated when readout is stopped. Uses a lot of memory, do not use for long processes.")
args = parser.parse_args()

# Parse config
import configparser
configParse = configparser.ConfigParser()
configParse.read('_spectrometer_config.ini')
if args.setIntTime:
    if args.setIntTime.isnumeric():
        integrationTime = int(args.setIntTime)
        configParse['general']['integrationTime'] = str(integrationTime)
        print(f"Integration time was read and set to {integrationTime} in the script and config file.")
else:
    integrationTime = int(configParse['general']['integrationTime'])

bounaryOffsetStart = 5      # Set the number of initial points in the spectrum to ignore (disregard dead pixels)
setLengthInTime = False
presaveLength = 50          # Number of spectra to keep in memory
postaveLength = 50          # Number of spectra to save after dipping below the treshold before ending current acquisition
timeoutwindow = int(float(configParse['acquisitionSettings']['timeoutWindow']))
if setLengthInTime:
    presaveLength = int(np.round(presaveLength / int(configParse['general']['integrationTime'])))
    postaveLength = int(np.round(postaveLength / int(configParse['general']['integrationTime'])))

if args.reset:
    if args.reset.isnumeric():
        configParse['acquisitionSettings']['currCycle'] = str(args.reset)
    else: configParse['acquisitionSettings']['currCycle'] = str(0)
    print("Done, counter reset")

if args.setProc:
    configParse['acquisitionSettings']['procID'] = args.setProc
    print(f"Process ID set to {configParse['acquisitionSettings']['procID']} in the config file")

if args.set or args.tacq:
    spec = sb.Spectrometer.from_serial_number()
    spec.integration_time_micros(integrationTime)

if args.set:
    print("Calculating mean intensity over 50 spectra.")
    intensArr = []
    for i in range(0, 50):
        wavelengths = spec.wavelengths()[bounaryOffsetStart:]
        intensity = spec.intensities()[bounaryOffsetStart:]
        intensArr.append(np.trapz(intensity, wavelengths))
    intInt = np.mean(intensArr)
    if args.set == 'dark':
        configParse['spectrometerSettings']['dark'] = str(intInt)
        print(f'Dark spectrum intensity over 50 steps: {intInt} +/- {np.std(intensArr)}')
    elif args.set == 'plasma' or args.set == 'plas' or args.set == 'light':
        configParse['spectrometerSettings']['plasma'] = str(intInt)
        print(f'Plasma on spectrum intensity over 50 steps: {intInt} +/- {np.std(intensArr)}')

if args.tacq:
    print(f"Time out window set to {timeoutwindow} points or {timeoutwindow*integrationTime/10**6} seconds.")
    intensOff = float(configParse['spectrometerSettings']['dark'])
    intensOn = float(configParse['spectrometerSettings']['plasma'])
    treshold = float(configParse['general']['threshold'])
    currCycle = float(configParse['acquisitionSettings']['currCycle'])
    tresholdValue = intensOff + (intensOn - intensOff)*treshold
    
    acqIntIntens = []
    acqTime = []
    acqIntens = []

    try:
        while True:
            intIntens = [intensOff]
            timeArr = [0]
            triggerArr = [False]
            plasmaOnTime = datetime.datetime.now()
            wavelengths = spec.wavelengths()[5:]
            saveIntens = np.zeros([presaveLength, len(wavelengths)])
            saveTime = np.zeros(presaveLength)
            saveTrigger = np.zeros(presaveLength)
            postCount = -1
            acqCount = 0
            while True:
                intens = spec.intensities()[5:]
                currIntens = np.trapz(intens, wavelengths)
                currTime = time.time()
                if currIntens >= tresholdValue or (0 <= postCount < postaveLength):
                    if not(triggerArr[-1]):
                        print("Started measuring")
                        plasmaOnTime = currTime
                        saveTime = saveTime
                    triggerArr.append(True)
                    saveIntens = np.append(saveIntens, intens[:,None].T, axis = 0)
                    saveTime = np.append(saveTime, currTime)
                    saveTrigger = np.append(saveTrigger, True)
                    acqCount = acqCount + 1
                    if acqCount > timeoutwindow:
                        print("Measurement timed out, starting next one")
                        break
                    if currIntens >= tresholdValue:
                        postCount = 0
                    else:
                        postCount = postCount + 1
                else:
                    if triggerArr[-1]:
                        acqCount = 0
                        break
                    if postCount > postaveLength: postCount = -1
                    timeArr.append(0)
                    triggerArr.append(False)
                    saveIntens[:presaveLength-1,:] = saveIntens[1:,:]
                    saveIntens[-1,:] = intens
                    saveTime[:-1] = saveTime[1:]
                    saveTime[-1] = currTime

            saveTime = np.trim_zeros(saveTime) - plasmaOnTime           # Trim zero times if left and adjust with starting time
            saveIntens = saveIntens.T[:,~(saveIntens.T == 0).all(0)].T  # Trim leading zero columns for padding if left

            outArr = np.insert(saveIntens.T, 0, wavelengths, axis=1)
            outTime = np.zeros(len(saveTime)+1)
            outTime[1:] = saveTime
            outArr = np.insert(outArr, 0, outTime, axis=0)
            configParse['acquisitionSettings']['currCycle'] = str(int(configParse['acquisitionSettings']['currCycle'])+1)
            date = datetime.datetime.today().strftime('%Y%m%d')
            folderName = 'output/'+date + '_' + configParse['acquisitionSettings']['procID']
            if not(os.path.exists(folderName)): os.mkdir(folderName)
            filename = datetime.datetime.today().strftime('%Y%m%d_%H%M') + '_' + configParse['acquisitionSettings']['procID'] + '_' + configParse['acquisitionSettings']['currCycle']
            print(f"Saving results to {filename}")
            np.savetxt(f'{folderName}/{filename}.csv', outArr, delimiter = ',', fmt = '%f')
            np.savetxt(f'{folderName}/{filename}.txt', outArr, delimiter = ' ', fmt = '%f')
            pd.DataFrame(outArr).to_csv(f'{folderName}/{filename}_pd.txt', sep = '\t', index = False, header = False)
            acqIntIntens.append(np.trapz(saveIntens.T, wavelengths, axis = 0))
            acqTime.append(saveTime)
            if args.track:
                acqIntens.append(saveIntens)
    except KeyboardInterrupt:
        plt.figure()
        for t,In in zip(acqTime,acqIntIntens):
            plt.plot(t, In)
        plt.xlabel('Time (s)')
        plt.ylabel('Integrated Intensity')
        
        meanIntens, meanIntensErr = proc.tolerant_mean(acqIntIntens)
        timeArr, timeArrErr = proc.tolerant_mean(acqTime)
        plt.figure()
        plt.plot(timeArr, meanIntens, color = 'black')
        plt.fill_between(timeArr, meanIntens - meanIntensErr, meanIntens + meanIntensErr, color = 'lightgrey')
        plt.xlabel('Time (s)')
        plt.ylabel('Mean Integrated Intensity')

        if args.track:
            species = configParse['general']['trackSpecies'].split(',')
            species = np.asarray(species, dtype=float)
            specWavelength = []
            for currSpec in species:
                specWavelength.append(proc.lambdaToID(currSpec))
            plotArr = []
            print("Plotting species for all cycles")
            for currSpec, currLambda in zip(specWavelength, species):
                plt.figure()
                plt.title(currLambda)
                for t, specIntens in zip(acqTime, acqIntens):
                    plt.plot(t, specIntens[:,currSpec])

        
        outArr = np.array([timeArr, timeArrErr, meanIntens, meanIntensErr]).T
        headers = ['Time (s)', 'Time Error (s)', 'Mean Integrated Intensity', 'SD in Mean Integrated Intensity']
        pd.DataFrame(outArr).to_csv(f'{folderName}/_timeIntensity_{configParse['acquisitionSettings']['procID']}.txt', sep = '\t', index = False, header = headers)
        pd.DataFrame(outArr).to_csv(f'{folderName}/_timeIntensity_{configParse['acquisitionSettings']['procID']}.csv', sep = ',', index = False, header = headers)

with open('_spectrometer_config.ini', 'w') as configfile:    # save
    configParse.write(configfile)

plt.show()