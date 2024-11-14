import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import processing, config
import os, glob

dataFolder = 'data\\20241106 ASP Plasma Tests'
os.chdir(dataFolder)
if not(os.path.exists('output')):
    os.mkdir('output', exist_ok=True)

for file in glob.glob('*.txt'):
    fileID = file.split(".")[0]
    print(fileID)
    OES_df = pd.read_csv(file, sep='\t')
    OES_npArr = OES_df.to_numpy()
    OES_t = OES_df.keys().values.tolist()
    OES_t = OES_t[1:-2]
    timeArr = np.array(OES_t).astype(float)
    OES_lambda = OES_npArr[:,0]
    OES_refAr = processing.findLambdaIndex(OES_lambda, config.referenceLine)
    OES_count = np.transpose(OES_npArr[:,1:-2])

    filteredMatrix = np.array(OES_count).T
    filterArray = []
    for j, lambdaT in zip(range(len(filteredMatrix)), filteredMatrix):
        tempStep = []
        for i in lambdaT:
            if i < np.max(lambdaT)*0.8:
                tempStep.append(np.nan)
                filterArray.append(True)
            else:
                tempStep.append(i)
                filterArray.append(False)
        filteredMatrix[j,:] = tempStep

    specAvg = np.average(filteredMatrix.T, axis=0)
    specAvg = specAvg - np.average(specAvg[~np.isnan(specAvg)])
    specAvgStd = np.std(filteredMatrix.T, axis=0)
    specSum = np.sum(filteredMatrix.T, axis=0)
    specSum = specSum - np.average(specSum[~np.isnan(specSum)])

    outMatr = np.array([
        OES_lambda[~np.isnan(specAvg)],
        specAvg[~np.isnan(specAvg)],
        specAvgStd[~np.isnan(specAvg)],
        specSum[~np.isnan(specAvg)]
        ])
    #np.savetxt('output\\' + fileID + '.csv', outMatr.T, delimiter=',')
    pd.DataFrame(outMatr.T).to_csv('output\\{fileID}.csv', sep=',', index=False, header=['Wavelength (nm)', 'Average Intensity', 'SD in Average Intensity', 'Summed Intensity'])
