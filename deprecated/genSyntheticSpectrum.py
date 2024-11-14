import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import processing as proc

# Target reference
compToRef = True                                # Turn target reference on or off
targRefData = np.loadtxt('data\\bobSF6Ar.txt')  # Provide reference data file
tsy = 10                                        # Integration time used for reference data

# Read references
refArgon = np.loadtxt('reference/refArgon.txt')
refSF6 = np.loadtxt('reference/refSF6.txt')
refH2 = np.loadtxt('reference/refH2.txt')
x0 = 150
x1 = 50
x2 = 50
tref = 5

# Set init flow rates in sccm
y0 = 10
y1 = 10
y2 = 10

def calcSyntheticSpectrum(y0, y1, y2, tsy=1):
    corrArgon = proc.backgroundCorrection(refArgon[:,0], refArgon[:,1], plot=False)
    corrSF6 = proc.backgroundCorrection(refSF6[:,0], refSF6[:,1], plot=False)
    corrH2 = proc.backgroundCorrection(refH2[:,0], refH2[:,1], plot=False)
    #return refArgon[:,1] * y0/(x0*tref) + refSF6[:,1] * y1/(x1*tref) + refH2[:,1] * y2/(x2*tref)
    return corrArgon * y0/(x0*tref) + corrSF6 * y1/(x1*tref) + corrH2 * y2/(x2*tref)


# Create subplot
if compToRef:
    fig, (ax, ax1) = plt.subplots(2, 1, height_ratios=[5, 1])
    plt.subplots_adjust(bottom=0.25)
    plt.subplot(2, 1, 1)
else:
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
spectrumTotal, = plt.plot(refArgon[:,0], calcSyntheticSpectrum(y0, y1, y2), label='Total spectrum')
spectrumAr, = plt.plot(refArgon[:,0], calcSyntheticSpectrum(y0, 0, 0), label='Ar contribution')
spectrumSF6, = plt.plot(refArgon[:,0], calcSyntheticSpectrum(0, y1, 0), label='$SF_6$ contribution')
spectrumH2, = plt.plot(refArgon[:,0], calcSyntheticSpectrum(0, 0, y2), label='$H_2$ contribution')
plt.legend()
plt.xlim([300, 875])
plt.ylim([0, None])

# TEMP REFERENCE
if compToRef:
    baseCorrected = proc.backgroundCorrection(targRefData[:,0], targRefData[:,1], plot=False)/tsy
    plt.plot(targRefData[:,0], baseCorrected, label='SF6/Ar Plasma Reference')

    plt.subplot(2, 1, 2)
    diffSpec, diffMSE = proc.calcNormDifferenceSpectrum(baseCorrected - calcSyntheticSpectrum(y0, y1, y2))
    spectrumDiff, = plt.plot(refArgon[:,0], diffSpec)
    MSEtext = plt.text((875-300)/2+300, 0, 'MSE = {:10.1f}'.format(diffMSE))
    plt.xlim([300, 875])
    plt.ylim([-1, 1])
 
# Initiate sliders for flow rates
y0slider = Slider(
    ax = plt.axes([0.2, 0.15, 0.6, 0.03]),
    label = 'Argon flow rate',
    valmin = 0.0,
    valmax = 200,
    valinit = y0,
    valstep = 1.0)
y1slider = Slider(
    ax = plt.axes([0.2, 0.1, 0.6, 0.03]),
    label = 'SF6 flow rate',
    valmin = 0.0,
    valmax = 50,
    valinit = y1,
    valstep = 1.0)
y2slider = Slider(
    ax = plt.axes([0.2, 0.05, 0.6, 0.03]),
    label = 'H2 flow rate',
    valmin = 0.0,
    valmax = 50,
    valinit = y2,
    valstep = 1.0)
exportButton = Button(plt.axes([0.85, 0.05, 0.1, 0.05]), label='Export')
 
# Create function to be called when slider value is changed
def update(val):
    y0Var = y0slider.val
    y1Var = y1slider.val
    y2Var = y2slider.val
    spectrumTotal.set_ydata(calcSyntheticSpectrum(y0Var, y1Var, y2Var))
    spectrumAr.set_ydata(calcSyntheticSpectrum(y0Var, 0, 0))
    spectrumSF6.set_ydata(calcSyntheticSpectrum(0, y1Var, 0))
    spectrumH2.set_ydata(calcSyntheticSpectrum(0, 0, y2Var))
    if compToRef:
        diffSpec, diffMSE = proc.calcNormDifferenceSpectrum(baseCorrected - calcSyntheticSpectrum(y0Var, y1Var, y2Var))
        MSEtext.set_text('MSE = {:10.1f}'.format(diffMSE))
        spectrumDiff.set_ydata(diffSpec)

def exportData(val):
    y0Var = y0slider.val
    y1Var = y1slider.val
    y2Var = y2slider.val
    outMatr = np.array([
        refArgon[:,0],
        calcSyntheticSpectrum(y0Var, 0, 0),
        calcSyntheticSpectrum(0, y1Var, 0),
        calcSyntheticSpectrum(0, 0, y2Var),
        calcSyntheticSpectrum(y0Var, y1Var, y2Var)
        ]).T
    np.savetxt('syntheticSpectrumExport.csv', outMatr, delimiter=',')
    print("Data has been exported to 'syntheticSpectrumExport.csv'.\nColumns are in order wavelength, Ar contribution, SF6 contribution, H2 contribution, Total synthetic spectrum")
 
# Call update function when slider value is changed
y0slider.on_changed(update)
y1slider.on_changed(update)
y2slider.on_changed(update)
exportButton.on_clicked(exportData)
 
plt.show()