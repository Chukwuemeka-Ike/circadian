# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_lights.ipynb.

# %% auto 0
__all__ = ['Light', 'make_pulse', 'get_pulse']

# %% ../nbs/01_lights.ipynb 3
import numpy as np
import pylab as plt
from typing import Optional
from matplotlib.pyplot import step
from fastcore.basics import patch_to
from numpy.core.fromnumeric import repeat

# %% ../nbs/01_lights.ipynb 5
class Light:
    "Helper class for creating light schedules"
    def __init__(self, 
                 light: callable, # light function that takes in a time value and returns a float, if a float is passed, then the light function is a constant set to that lux value 
                 start_time: float=0.0, # when the light function starts in hours
                 duration: float=1.0, # duration of the light function in hours
                 default_value: float=0.0 # the default value of the light function outside of its duration
                 ):
        # light type checking
        light_input_err_msg = "`light` should be a nonnegative `float`, or a callable with a single `float` parameter which returns a nonnegative `float`"
        if callable(light):
            light_fn = np.vectorize(light, otypes=[float])
            output = light_fn(0.0)
            try:
                float(output)
            except:
                # catches when the function created from light does not return values that can be cast to float
                raise ValueError(light_input_err_msg)
        else:
            try:
                light = float(light)
                light_fn = np.vectorize(lambda t: light, otypes=[float])
            except:
                # catches when the light function can't be converted to a float
                raise ValueError(light_input_err_msg)

        # start_time type checking
        start_time_err_msg = "`start_time` should be a `float`"
        try:
            start_time = float(start_time)
        except:
            # catches when start_time can't be converted to a float
            raise ValueError(start_time_err_msg)

        # duration type checking
        duration_err_msg = "`duration` should be a nonnegative `float`"
        try:
            duration = float(duration)
            if duration < 0:
                raise ValueError(duration_err_msg)
        except:
            # catches when duration can't be converted to a float
            raise ValueError(duration_err_msg)

        # default_value type checking
        default_value_err_msg = "`default_value` should be a nonnegative `float`"
        try:
            default_value = float(default_value)
            if default_value < 0:
                raise ValueError(default_value_err_msg)
        except: 
            # catches when default_value can't be converted to a float
            raise ValueError(default_value_err_msg)

        # check that the light function returns nonnegative values
        if np.any(light_fn(np.linspace(start_time, start_time + duration, 100)) < 0):
            raise ValueError(light_input_err_msg)

        # assign attributes
        self._func = light_fn
        self.duration = duration
        self.start_time = start_time
        self.default_value = default_value

# %% ../nbs/01_lights.ipynb 8
@patch_to(Light, as_prop=True)
def end_time(self: Light):
    "End time of the active portion of the light function"
    return self.start_time + self.duration

# %% ../nbs/01_lights.ipynb 10
@patch_to(Light)
def __call__(self, 
             t: np.ndarray, # time values in hours to evaluate the light function
             repeat_period: float = None # should the light function repeat after a certain period in hours
             ):
    # t type checking
    t_err_msg = "`t` should be a `float` or a 1d `numpy.ndarray` of `float`"
    try:
        t = np.array(t, dtype=float)
        if t.ndim == 0:
            try:
                t = float(t)
                t = np.array([t])
            except:
                raise ValueError(t_err_msg)
        elif t.ndim != 1:
            raise ValueError(t_err_msg)
    except:
        raise ValueError(t_err_msg)
    # repeat_period type checking
    repeat_period_err_msg = "`repeat_period` should be a nonnegative `float`"
    if repeat_period is not None:
        try:
            repeat_period = float(repeat_period)
            if repeat_period < 0:
                raise ValueError(repeat_period_err_msg)
        except:
            raise ValueError(repeat_period_err_msg)
    
    if repeat_period is not None:
        t = np.mod(t, repeat_period)
    default_result = np.zeros_like(t)
    if self.duration == 0.0:
        return default_result + self.default_value
    else:
        mask = (t >= self.start_time) & (t <= self.end_time)
        default_result[~mask] = self.default_value
        func_result  = self._func(t[mask])
        default_result[mask] += func_result
        return default_result

# %% ../nbs/01_lights.ipynb 22
@patch_to(Light)
def __add__(self, 
            light_obj: 'Light' # another light object to be added to the current light object
            ):
    start_times = [self.start_time, light_obj.start_time]
    end_times = [self.end_time, light_obj.end_time]
    default_values = [self.default_value, light_obj.default_value]
    light_functions = [self._func, light_obj._func]

    new_start_time = min(start_times)
    new_duration = max(end_times) - new_start_time
    new_default_value = sum(default_values)

    if self.duration == 0.0 and light_obj.duration != 0.0:
        new_start_time = light_obj.start_time
        new_duration = light_obj.duration
        def new_light_func(t):
            overlap_with_default = (t >= new_start_time) & (t <= new_start_time + new_duration)
            conditions = [overlap_with_default]
            values = [light_obj._func(t) + self.default_value]
            return np.piecewise(t, conditions, values)

    elif light_obj.duration == 0.0 and self.duration != 0.0:
        new_start_time = self.start_time
        new_duration = self.duration
        def new_light_func(t):
            overlap_with_default = (t >= new_start_time) & (t <= new_start_time + new_duration)
            conditions = [overlap_with_default]
            values = [self._func(t) + light_obj.default_value]
            return np.piecewise(t, conditions, values)

    elif light_obj.duration == 0.0 and self.duration == 0.0:
        new_start_time = 0.0
        new_duration = 0.0
        def new_light_func(t):
            return new_default_value

    else:
        if min(end_times) - max(start_times) <= 0:
            # light functions do not overlap
            def new_light_func(t):
                first_portion = (t >= min(start_times)) & (t <= min(end_times))
                default_zone = (t > min(end_times)) & (t < max(start_times))
                second_portion = (t >= max(start_times)) & (t <= max(end_times))
                conditions =  [first_portion, 
                            default_zone, 
                            second_portion]
                values = [light_functions[np.argmin(start_times)](t) + default_values[np.argmax(start_times)],
                        new_default_value, 
                        light_functions[np.argmax(start_times)](t) + default_values[np.argmin(start_times)]]

                return np.piecewise(t, conditions, values)
        else:
            # light functions overlap
            def new_light_func(t):
                first_no_overlap = (t >= min(start_times)) & (t < max(start_times))
                overlap = (t >= max(start_times)) & (t < min(end_times))
                second_no_overlap = (t >= min(end_times)) & (t <= max(end_times))
                conditions = [first_no_overlap, 
                            overlap, 
                            second_no_overlap]
                values = [light_functions[np.argmin(start_times)](t) + default_values[np.argmax(start_times)],
                        light_functions[0](t) + light_functions[1](t),
                        light_functions[np.argmax(start_times)](t) + default_values[np.argmin(start_times)]]

                return np.piecewise(t, conditions, values)

    return Light(new_light_func, start_time=new_start_time, duration=new_duration, default_value=new_default_value)

# %% ../nbs/01_lights.ipynb 25
@patch_to(Light)
def concatenate(self, light_obj: 'Light'):
    "Concatenate two light functions in time"
    switch_time = self.end_time
    def light_func_new(t): return np.piecewise(t, [t <= switch_time, t >= switch_time],                                       [
        self._func, lambda t: light_obj._func(t-switch_time)])

    start_time_new = min(self.start_time, light_obj.start_time)
    duration_new = light_obj.duration + self.duration
    return Light(light_func_new, start_time=start_time_new, duration=duration_new)

# %% ../nbs/01_lights.ipynb 26
@patch_to(Light)
def plot(self, 
         plot_start_time: float = None, # start time of the plot in hours
         plot_end_time: float = None, # end time of the plot in hours
         repeat_period: float = None, # period of the plot in hours
         num_samples: int=10000, # number of samples to plot
         ax=None, # matplotlib axis to plot on
         *args, # arguments to pass to matplotlib.pyplot.plot
         **kwargs # keyword arguments to pass to matplotlib.pyplot.plot
         ):
    "Plot the light function between `start_time` and `end_time` with `num_samples` samples"
    # type checking
    if plot_start_time is not None:
        if not isinstance(plot_start_time, (float, int)):
            raise ValueError(f"plot_start_time must be a float or int, got {type(plot_start_time)}")
    if plot_end_time is not None:
        if not isinstance(plot_end_time, (float, int)):
            raise ValueError(f"plot_end_time must be a float or int, got {type(plot_end_time)}")
    if repeat_period is not None:
        if not isinstance(repeat_period, (float, int)):
            raise ValueError(f"repeat_period must be a float or int, got {type(repeat_period)}")
    if ax is not None:
        if not isinstance(ax, plt.Axes):
            raise ValueError(f"ax must be a matplotlib Axes object, got {type(ax)}")
    if num_samples is not None:
        if not isinstance(num_samples, int):
            raise ValueError(f"num_samples must be an int, got {type(num_samples)}")
    
    if plot_start_time is None:
        plot_start_time = self.start_time
    if plot_end_time is None:
        plot_end_time = self.end_time
        
    t = np.linspace(plot_start_time, plot_end_time, num_samples)
    vals = self.__call__(t, repeat_period=repeat_period)
    if ax is None:
        plt.figure()
        ax = plt.gca()

    ax.plot(t, vals, *args, **kwargs)
    return ax

# %% ../nbs/01_lights.ipynb 31
@patch_to(Light)
def RegularLight(lux: float=150.0, # lux intensity of the light
                 lights_on: float=8.0, # hour of the day for lights to come on
                 lights_off: float=16.0, # hour of the day for lights to go off
                 ) -> 'Light':
    "Create a light function that is on from `lights_on` to `lights_off` on a 24 hour schedule"
    # type checking
    if not isinstance(lux, (float, int)):
        raise ValueError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(lights_on, (float, int)):
        raise ValueError(f"lights_on must be a float or int, got {type(lights_on)}")
    if not isinstance(lights_off, (float, int)):
        raise ValueError(f"lights_off must be a float or int, got {type(lights_off)}")

    lights_on = np.mod(lights_on, 24.0)
    lights_off = np.mod(lights_off, 24.0)
    if lights_off > lights_on:
        end_time = lights_on + (lights_off - lights_on) 
        dark_section_before = Light(0.0, start_time=0.0, duration=lights_on)
        light_section = Light(lux, 
                        start_time=lights_on, 
                        duration=lights_off - lights_on)
        dark_section = Light(0.0, end_time, duration=24.0 - end_time)
        return dark_section_before.concatenate(light_section).concatenate(dark_section)
    else:
        first_light = Light(lux, start_time = 0.0, duration=lights_off)
        dark_section = Light(0.0, start_time=lights_off, duration=lights_on - lights_off)
        second_light = Light(lux, start_time=lights_on, duration=24.0 - lights_on)
        return  first_light.concatenate(dark_section).concatenate(second_light)

# %% ../nbs/01_lights.ipynb 35
@patch_to(Light)
def ShiftWorkLight(lux: float=150.0, # lux intensity of the light
                   days_on: int=3, # number of days on the night shift
                   days_off: int=2 # number of days off shift
                   ) -> 'Light':
    "Create a light schedule for a shift worker" 
    # type checking
    if not isinstance(lux, (float, int)):
        raise ValueError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(days_on, int):
        raise ValueError(f"days_on must be a nonnegative int, got {type(days_on)}")
    elif days_on < 0:
        raise ValueError(f"days_on must be a nonnegative int, got {days_on}")
    if not isinstance(days_off, int):
        raise ValueError(f"days_off must be a nonnegative int, got {type(days_off)}")
    elif days_off < 0:
        raise ValueError(f"days_off must be a nonnegative int, got {days_off}")
    if days_on == 0 and days_off == 0:
        raise ValueError("days_on and days_off cannot both be 0")
    
    workday = Light.RegularLight(lux=lux, lights_on=19.0, lights_off=11.0)
    offday = Light.RegularLight(lux=lux, lights_on=7.0, lights_off=23.0)
    total_schedule = [workday for _ in range(days_on-1)] + [offday for _ in range(days_off)]
    for day in total_schedule:
        workday = workday.concatenate(day)
    return workday

# %% ../nbs/01_lights.ipynb 38
@patch_to(Light)
def SlamShift(lux: float = 150.0, # lux intensity of the light
              shift: float=8.0, # number of hours to shift the light schedule
              before_days: int=10, #number of days before the shift occurs 
              after_days: int=10, # number of days after the shift occurs
              starting_lights_on: float=8.0 # hour of the day for lights to come on
              ) -> 'Light':
    "Create a light schedule for a shift worker under a slam shift" 
    # type checking
    if not isinstance(lux, (float, int)):
        raise ValueError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(shift, (float, int)):
        raise ValueError(f"shift must be a nonnegative float or int, got {type(shift)}")
    elif shift < 0.0:
        raise ValueError(f"shift must be a nonnegative float or int, got {shift}")
    if not isinstance(before_days, int):
        raise ValueError(f"before_days must be a nonnegative int, got {type(before_days)}")
    elif before_days < 0:
        raise ValueError(f"before_days must be a nonnegative int, got {before_days}")
    if not isinstance(after_days, int):
        raise ValueError(f"after_days must be a nonnegative int, got {type(after_days)}")
    elif after_days < 0:
        raise ValueError(f"after_days must be a nonnegative int, got {after_days}")
    if not isinstance(starting_lights_on, (float, int)):
        raise ValueError(f"starting_lights_on must be a nonnegative float or int, got {type(starting_lights_on)}")
    elif starting_lights_on < 0.0:
        raise ValueError(f"starting_lights_on must be a nonnegative float or int, got {starting_lights_on}")

    light_before = Light.RegularLight(lux=lux, 
                                        lights_on=starting_lights_on, 
                                        lights_off= np.fmod(starting_lights_on + 16.0, 24.0)
                                        )
    light_after = Light.RegularLight(lux=lux, 
                                        lights_on=np.fmod(starting_lights_on+shift, 24.0), 
                                        lights_off=np.fmod(starting_lights_on+shift+16.0, 24.0)
                                        )
    total_schedule = [light_before for _ in range(before_days-1)] + [light_after for _ in range(after_days)]
    for day in total_schedule:
        light_before = light_before.concatenate(day)
    return light_before

# %% ../nbs/01_lights.ipynb 41
@patch_to(Light)
def SocialJetlag(lux: float = 150.0, # lux intensity of the light
                 num_regular_days: int = 5, # number of days with a regular schedule
                 num_jetlag_days: int = 2, # number of days with a delayed schedule
                 hours_delayed: float = 2.0, # number of hours to delay the schedule on the jetlag days
                 regular_days_lights_on: float=7.0, # hour of the day for lights to come on
                 ) -> 'Light':
    "Create a light schedule that simulates the effects of jetlag"
    # type checking
    if not isinstance(lux, (float, int)):
        raise ValueError(f"lux must be a nonnegative float or int, got {type(lux)}")
    elif lux < 0.0:
        raise ValueError(f"lux must be a nonnegative float or int, got {lux}")
    if not isinstance(num_regular_days, int):
        raise ValueError(f"num_regular_days must be a nonnegative int, got {type(num_regular_days)}")
    elif num_regular_days < 0:
        raise ValueError(f"num_regular_days must be a nonnegative int, got {num_regular_days}")
    if not isinstance(num_jetlag_days, int):
        raise ValueError(f"num_jetlag_days must be a nonnegative int, got {type(num_jetlag_days)}")
    elif num_jetlag_days < 0:
        raise ValueError(f"num_jetlag_days must be a nonnegative int, got {num_jetlag_days}")
    if not isinstance(hours_delayed, (float, int)):
        raise ValueError(f"hours_delayed must be a nonnegative float or int, got {type(hours_delayed)}")
    elif hours_delayed < 0.0:
        raise ValueError(f"hours_delayed must be a nonnegative float or int, got {hours_delayed}")
    if not isinstance(regular_days_lights_on, (float, int)):
        raise ValueError(f"regular_days_lights_on must be a nonnegative float or int, got {type(regular_days_lights_on)}")
    elif regular_days_lights_on < 0.0:
        raise ValueError(f"regular_days_lights_on must be a nonnegative float or int, got {regular_days_lights_on}")

    jetlag_day_lights_on = (regular_days_lights_on + hours_delayed) 
    jetlag_day_lights_off = (regular_days_lights_on + 16.0 + hours_delayed) 
    regular_days = Light.RegularLight(lux=lux, lights_on=regular_days_lights_on, lights_off=regular_days_lights_on+16.0)
    jetlag_day = Light.RegularLight(lux=lux, lights_on=jetlag_day_lights_on, lights_off=jetlag_day_lights_on+16.0)
    total_schedule = [regular_days for _ in range(num_regular_days-1)] + [jetlag_day for _ in range(num_jetlag_days)]
    for day in total_schedule:
        regular_days = regular_days.concatenate(day)
        
    return regular_days

# %% ../nbs/01_lights.ipynb 44
def make_pulse(t, tstart, tend, steep: float = 30.0):
    return 0.5*np.tanh(steep*(t-tstart))-0.5*np.tanh(steep*(t-tend))

def get_pulse(t: float,
              t1: float,
              t2: float,
              repeat=False,
              Intensity: float = 150.0):

    if repeat:
        t = np.fmod(t, 24.0)
    if t < 0.0:
        t += 24.0

    light_value = Intensity*make_pulse(t, t1, t2)
    return np.abs(light_value)
