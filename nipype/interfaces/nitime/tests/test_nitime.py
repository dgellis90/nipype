# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

import numpy as np

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            with_setup, TraitError, skipif)

from nipype.testing import example_data

import nipype.interfaces.nitime as nitime 

import nitime.analysis as nta
import nitime.timeseries as ts

from matplotlib.mlab import csv2rec

def test_read_csv():
    """Test that reading the data from csv file gives you back a reasonable
    time-series object """

    CA = nitime.CoherenceAnalyzer()
    CA.inputs.TR = 1.89 # bogus value just to pass traits test
    CA.inputs.in_file = example_data('fmri_timeseries_nolabels.csv')
    yield assert_raises,ValueError,CA._read_csv 

    CA.inputs.in_file = example_data('fmri_timeseries.csv')
    data,roi_names = CA._read_csv()
    yield assert_equal, data[0][0],10125.9
    yield assert_equal, roi_names[0],'WM' 

def test_coherence_analysis():
    """Test that the coherence analyzer works """

    #This is the nipype interface analysis:
    CA = nitime.CoherenceAnalyzer()
    CA.inputs.TR = 1.89
    CA.inputs.in_file = example_data('fmri_timeseries.csv')
    tmp_png = tempfile.mkstemp(suffix='.png')[1] 
    CA.inputs.output_figure_file = tmp_png
    tmp_csv = tempfile.mkstemp(suffix='.csv')[1] 
    CA.inputs.output_csv_file = tmp_csv

    o = CA.run()
    yield assert_equal,o.outputs.coherence_array.shape,(31,31)

    #This is the nitime analysis:
    TR=1.89
    data_rec = csv2rec(example_data('fmri_timeseries.csv'))
    roi_names= np.array(data_rec.dtype.names)
    n_samples = data_rec.shape[0]
    data = np.zeros((len(roi_names),n_samples))

    for n_idx, roi in enumerate(roi_names):
       data[n_idx] = data_rec[roi]

    T = ts.TimeSeries(data,sampling_interval=TR)

    yield assert_equal,CA._csv2ts().data,T.data

    T.metadata['roi'] = roi_names 
    C = nta.CoherenceAnalyzer(T,method=dict(this_method='welch',
                                            NFFT=CA.inputs.NFFT,
                                            n_overlap=CA.inputs.n_overlap))

    freq_idx = np.where((C.frequencies>CA.inputs.frequency_range[0]) *
                        (C.frequencies<CA.inputs.frequency_range[1]))[0]

    #Extract the coherence and average across these frequency bands: 
    coh = np.mean(C.coherence[:,:,freq_idx],-1) #Averaging on the last dimension 

    yield assert_equal,o.outputs.coherence_array,coh

    
