import pandas as pd

useNIST = False  # Choose to use NIST data (True) or literature data (False)
sortWavelengths = []
sortSpecies = []

def getPeakIDs():
        if useNIST:
                sheetName = 'OESNIST'
        else:
                sheetName = 'OESreferences'
        df = pd.read_excel('OESpeakLocations.xlsx', sheet_name=sheetName)
        for spec in df['Species']:
                sortSpecies.append(spec)
        for l in df['Wavelength']:
                sortWavelengths.append(l)
        #print(df['Species'])