import pandas as pd

# Seperate Files
useNIST = False  # Choose to use NIST data (True) or literature data (False)
sortWavelengths = []
sortSpeciesID = []
sortSpecies = []
sortIntBounds = []

# One Time Resolved Measurement File
plotAll = True                 # Set to False when bugfixing to suppress plots
plotInteractive = False         # Plot interactive version in web browser (might give issues loading in some cases)
useStaticDataSet = False         # True to use defined file, False to prompt user to select a file
energyInJoule = True            # Set to True to output radiation energies in joule, False for eV
writeEnergyToCSV = False         # Set whether to write output plasma energy to a CSV file for further analysis
spPeakAnalysis = False          # Set to True to perform scipy peak analysis
plasmaOnThreshold = 0.05        # Value for relative intensity above which the plasma is considered ON
plasmaOffThreshold = 0.05       # Value for relative intensity above which the plasma is considered to have turned OFF
referenceLine = 750.38          # Argon peak to serve as reference (actinometer) for diagnostics and normalisation
steadyStateAnalysis = True      # Set to on if the acquisition is taken for a steady state plasma. If set to off, the plasma will be considered off for all timesteps.