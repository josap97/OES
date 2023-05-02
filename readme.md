# Usage of the OES Analysis Script
## Installation
After Python has been successfully installed, install Python dependencies with the following pip command
```
pip install numpy, scipy, tk, pandas, matplotlib
```
## Modifying Tracked Species
What species are tracked in the OES data is determined by entries in the OESpeakLocations.xlsx file with the `OESNIST` sheet using species obtained from NIST (https://physics.nist.gov/PhysRefData/ASD/lines_form.html). `OESreferences` has entries for various different species from literature with a reference. Removing species that are not of interest can be done by removing a row from the spreadsheet sheet, adding species by adding a new row. All wavelengths should be given in nm, species are strings used to identify a wavelength.

# Usage
This script will analyse a set of OES data files in *.txt format in batch, it will assume that all subsequent files are subsequent exposures only separated by time. If there are differences between different runs, please run them from different folders or keep track of which entry is which file.
1. Place your files in the `data` folder
2. In the Terminal, navigate to the folder in which you saved the script
3. Run the script by `python mainAn.py`
4. Select the folder in which the to-be-analysed text files have been placed
5. Wait for the script to complete and analyse the results from the output.csv files stored in the selected folder.

## Errors
If you get the following error when running the script
```
'ReadOnlyWorksheet' object has no attribute 'defined_names'
```
please run the following command to downgrade your `openpyxl` installation as newer versions seem to cause issues when reading the `*.xlsx` file as of May 2023
```
pip install --force-reinstall -v "openpyxl==3.1.0"
```