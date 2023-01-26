Circadian
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Install

``` sh
pip install circadian
```

## How to use

Fill me in please! Don’t forget code examples:

``` python
# Example run for forger 99 vdp model

from circadian.plots import Actogram
from circadian.models import *
from circadian.lights import *

import matplotlib.pyplot as plt
import numpy as np


ts =  np.arange(0.0, 24*100, 0.1)
light_values = np.array([SlamShift(t, Intensity=150.0) for t in ts])
model = Forger99Model()
spm_model = SinglePopModel()
tpm_model = TwoPopulationModel()
initial_conditions_forger = model.initial_conditions_loop(ts, light_est=light_values, num_loops=1)
initial_conditions_spm = spm_model.initial_conditions_loop(ts, light_est=light_values, num_loops=1)
initial_conditions_tpm = tpm_model.initial_conditions_loop(ts, light_est=light_values, num_loops=1)
dlmo = model.integrate_observer(ts=ts, light_est=light_values, u0 = initial_conditions_forger)
dlmo_spm = spm_model.integrate_observer(ts=ts, light_est=light_values, u0 = initial_conditions_spm)
dlmo_tpm = tpm_model.integrate_observer(ts=ts, light_est=light_values, u0 = initial_conditions_tpm)

sol = tpm_model.integrate_model(ts=ts, light_est=light_values, state=initial_conditions_tpm)
acto = Actogram(ts, light_vals=light_values, opacity=1.0)
acto.plot_phasemarker(dlmo, color='blue', label= "DLMO Forger99")
acto.plot_phasemarker(dlmo_spm, color='darkgreen', label = "DLMO SPM" )
acto.plot_phasemarker(dlmo_tpm, color='red', label = "DLMO TPM" )
plt.title("Actogram for a Simulated Shift Worker")
plt.tight_layout()
plt.show()
```

![](index_files/figure-commonmark/cell-2-output-1.png)
