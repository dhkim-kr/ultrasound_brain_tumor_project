import os, sys
import numpy as np
from struct import unpack
import pyvisa as visa

def setup():
    global scope
    try:
        rm = visa.ResourceManager()
        scope = rm.open_resource(os.environ["VXM_VISA_RESOURCE"])
    except Exception as e:
        print("error open oscilloscope: " + str(e))
        exit()

def getData():
    global waveform
    global data_ch1

    scope.write('DATA:SOU CH2')
    scope.write('DATA:WIDTH 1')
    scope.write('DATA:ENC ASC')
    scope.write('*OPC')

    ymult = scope.query('WFMOUTPRE:YMULT?')
    yoff = scope.query('WFMOUTPRE:YOFF?')
    print(ymult, yoff)
    ymult = float(ymult)
    yoff = float(yoff)
    scope.write('DATA:START 1')
    scope.write('DATA:STOP 5000')
    scope.write('*WAI')
    scope.write('CURVE?')

    data_ch1 = scope.read_raw()
    #print(len(data_ch1))
    waveform = data_ch1[5: 5005]
    waveform = np.array(unpack('5000b', waveform))
    waveform = (waveform - yoff) * ymult
    print(yoff, ymult)
    return waveform

def print_data():
    print(waveform[4990:5000], waveform[1], data_ch1[1], len(data_ch1))

def clear():
    scope.close()

