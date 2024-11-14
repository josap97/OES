# Usage of the OES Analysis Script
## Installation
After Python has been successfully installed, install Python dependencies with the following pip command
```
pip install numpy, scipy, pandas, matplotlib, pybaselines, seabreeze, SciencePlots
```
## Modifying Tracked Species
What species are tracked in the OES data is determined by entries in the OESpeakLocations.xlsx file with the `OESNIST` sheet using species obtained from NIST (https://physics.nist.gov/PhysRefData/ASD/lines_form.html). `OESreferences` has entries for various different species from literature with a reference. Removing species that are not of interest can be done by removing a row from the spreadsheet sheet, adding species by adding a new row. All wavelengths should be given in nm, species are strings used to identify a wavelength.

# Time Resolved Measurements
## Running a Time Resolves Acquisition for Multiple Cycles
When running a process with multiple plasma cycles, it may be interesting to systematically run OES on every plasma sub-cycle. `runOESAcquisition.py` allows this to be done through the command line. The script is run as follows
`python runOESAcquisition.py -tag value`
1. `-reset 0` resets the counter index to 0 or any other value.
2. `-setProc process_name` set the name of the process to be run, this is used in the output file names.
3. `-setIntTime 5000` set the integration time in microseconds which can be 5 ms or 5000 us and up. This must be set before taking reference me
4. `-set dark` take the average intensity of 50 measurements of a background to set as a baseline. This is saved automatically.
5. `-set plasma` take the average intensity of 50 measurements of a plasma which is used to define the trigger treshold. This is saved automatically.
6. `-tacq 1` start an acquisition. It triggers and saves automatically and prints to console when a measurement is started and ended.
    * `-track 1` can be added to `-tacq` to track a list the intensity of a list of wavelengths defined in the `_spectrometer_config.ini` file in `trackspecies`.
7. When ending a set of measurements, make sure the terminal is highlighted and press `ctrl+c`.
    * Two plots will open to show the integrated intensity for every pulse and for a tolerant average of all pulses.
    * If `track` is used, a plot will open for every tracked wavelength.

### Behind the Scenes
When the script is started, the script will continuously poll the spectrometer for spectra until it is stopped using `ctrl+c`. Two null vectors are defined as $\bar{S}=[0,0,...,0]$ and $\bar{t}=[0,0,...,0]$. Every time the spectrometer is polled, the first spectrum in $\bar{S}$ is discarded and all other spectra are shifted left. A new spectrum $\bar{s}_i(\lambda)$ is measured and saved to the last position in $\bar{S}$. A total intensity is calculated as
$$I_i=\int \bar{s}(\lambda)d\lambda$$.
If this intensity satisfies
$$I_i \geq (I_{plasma}-I_{dark})\cdot \text{treshold}$$
where $I_{plasma}$ is set using `-set plasma` and $I_{dark}$ using `-set dark`, a treshold is defined in `_spectrometer_config.ini`. If the intensity is sufficiently high, the script starts measuring and includes a number of points defined in the `presaveLength` variable before reaching the trigger. When the intensity falls below the treshold value, the measurment will continue for `postaveLength` number of points. After this window has ended, the results will be saved to a file and the script starts listening for a new cycle. If a new sub-cycle starts before the `postaveLength` window ends, it will be considered as one acquisition.
When an acquisition is triggered, a window of a length defined in `timeoutwindow` is started. Whenever an acquisition is started, the length of the window is output to the terminal in the number of points and seconds. This is the maximum length of an acquisition after which the current acquisition is ended and script listens to a the next trigger.

## Averaging of High Accuracy Acquisition
Running the `outputAverages.py` script will take all *.txt files in the folder referenced in `dataFolder` and average the data per wavelength. It filters datapoints lower than 80 % of the maximum intensity measured for that wavelength in order to filter times where the plasma is off. After averaging, a *.csv file with the same name will be saved in the newly created `output` folder which contains the wavelength, average intensity, SD in average, and summed intensity.

## High Accuracy Acquisition Analysis
`timeResolvedAnalysis.py` can be used to analyse both High Accuracy Acquisition files and output files created in a `runOESAcquisition.py` run. This script will prompt for a *.txt file and derive various quantities. The outputs are as follows:
* A csv file will open which gives intensities for the tracked lines as a function of plasma on time (this time must be validated manually).
* If `plotInteractive` is set to `True` in `config.py`, an interactive plot will open in a browser to browse through all timesteps. All specified lines are annotated.
* If `plotAll` is set to `True`, a number of matplotlib plots will open showing
    * A sample spectrum at timestep 160
    * A sample spectrum at timestep 160 as function of photon energy
    * Integrated spectrum showing plasma intensity as function of derived plasma on time with the derived on and off times annotated with vertical lines.
    * Tracked species intensity as function of derived plasma on time with the derived on and off times annotated with vertical lines.
    * Tracked species intensity normalised against actinometer as function of derived plasma on time with the derived on and off times annotated with vertical lines.
    * Integrated tracked species intensity as function of derived plasma on time with the derived on and off times annotated with vertical lines.
    * Difference spectrum with respect to previous timestep for timesteps with the greatest difference.
    * Difference spectra normalised to argon line.

# Other Files
* `processing.py` contains functions used by other scripts
* `config.py` contains configuration settings used in analysis files

# Errors
If you get the following error when running the script
```
'ReadOnlyWorksheet' object has no attribute 'defined_names'
```
please run the following command to downgrade your `openpyxl` installation as newer versions seem to cause issues when reading the `*.xlsx` file as of May 2023
```
pip install --force-reinstall -v "openpyxl==3.1.0"
```

# Deprecated Scripts
## Usage For Full Analysis
This script will analyse a set of OES data files in *.txt format in batch, it will assume that all subsequent files are subsequent exposures only separated by time. If there are differences between different runs, please run them from different folders or keep track of which entry is which file.
1. Place your files in the `data` folder
2. In the Terminal, navigate to the folder in which you saved the script
3. Run the script by `python mainAn.py`
4. Select the folder in which the to-be-analysed text files have been placed
5. Wait for the script to complete and analyse the results from the output.csv files stored in the selected folder.

## Averaging of Steady-State Measurements
Measurements taken with the High Speed Acquisition option in SpetraSuite are written to a single txt file. Run `python timeResAvg.py` to average over such a measurement. You will be prompted to select your data file which will start processing. Next, you will see an intensity trace for the Argon 750 nm line. Use this trace to indicate the timestamps in ms indicating the start and end of steadystate plasma. Input the start time, press enter, input the end time, press enter. The results will be processed and the average intensities and standard deviations are written to a new csv file.