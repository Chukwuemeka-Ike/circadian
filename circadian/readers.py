# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/05_readers.ipynb.

# %% auto 0
__all__ = ['VALID_WEREABLE_STREAMS', 'ACTIWATCH_COLUMN_RENAMING', 'WEREABLE_RESAMPLE_METHOD', 'WereableData', 'load_json',
           'load_csv', 'load_actiwatch', 'resample_df', 'combine_wereable_dataframes']

# %% ../nbs/api/05_readers.ipynb 4
import json
import numpy as np
import pandas as pd
from typing import Dict

# %% ../nbs/api/05_readers.ipynb 6
VALID_WEREABLE_STREAMS = ['steps', 'heartrate', 'wake', 'light_estimate', 'activity']

# %% ../nbs/api/05_readers.ipynb 7
@pd.api.extensions.register_dataframe_accessor("wereable")
class WereableData:
    "pd.DataFrame accessor implementing wereable-specific methods"
    def __init__(self, pandas_obj):
        self._validate_columns(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate_columns(obj):
        if 'datetime' not in obj.columns:
            if 'start' not in obj.columns and 'end' not in obj.columns:
                raise AttributeError("DataFrame must have 'datetime' column or 'start' and 'end' columns")

        if not any([col in obj.columns for col in VALID_WEREABLE_STREAMS]):
            raise AttributeError(f"DataFrame must have at least one wereable data column from: {VALID_WEREABLE_STREAMS}.")
        
    @staticmethod
    def _validate_metadata(metadata):
        if metadata:
            if not isinstance(metadata, dict):
                raise AttributeError("Metadata must be a dictionary.")
            if not any([key in metadata.keys() for key in ['data_id', 'subject_id']]):
                raise AttributeError("Metadata must have at least one of the following keys: data_id, subject_id.")
            if not all([isinstance(value, str) for value in metadata.values()]):
                raise AttributeError("Metadata values must be strings.")
    
    @staticmethod
    def rename_columns(df, 
                       inplace: bool = False
                       ):
        "Standardize column names by making them lowercase and replacing spaces with underscores"
        columns = [col.lower().replace(' ', '_') for col in df.columns]
        if inplace:
            df.columns = columns
        else:
            new_df = df.copy()
            new_df.columns = columns
            return new_df

    def is_valid(self):
        self._validate_columns(self._obj)
        self._validate_metadata(self._obj.attrs)
        return True

    def add_metadata(self,
                     metadata: Dict[str, str], # metadata containing data_id, subject_id, or other_info
                     inplace: bool = False, # whether to return a new dataframe or modify the current one
                     ):
        self._validate_metadata(metadata)
        if inplace:
            for key, value in metadata.items():
                self._obj.attrs[key] = value
        else:
            obj = self._obj.copy()
            for key, value in metadata.items():
                obj.attrs[key] = value
            return obj

# %% ../nbs/api/05_readers.ipynb 9
def load_json(filepath: str, # path to file
              metadata: Dict[str, str] = None, # metadata containing data_id, subject_id, or other_info
              ) -> Dict[str, pd.DataFrame]: # dictionary of wereable dataframes, one key:value pair per wereable data stream
    "Create a dataframe from a json containing a single or multiple streams of wereable data"
    # validate inputs
    if not isinstance(filepath, str):
        raise AttributeError("Filepath must be a string.")
    if metadata is not None:
        WereableData._validate_metadata(metadata)
    # load json
    jdict = json.load(open(filepath, 'r'))
    # check that it contains valid keys
    if not np.all([key in VALID_WEREABLE_STREAMS for key in jdict.keys()]):
        raise AttributeError("Invalid keys in JSON file. At least one key must be steps, heartrate, wake, light_estimate, or activity.")
    # create a df for each wereable stream
    df_dict = {}
    for key in jdict.keys():
        if key in VALID_WEREABLE_STREAMS:
            df_dict[key] = pd.DataFrame.from_dict(jdict[key])
        else:
            print(f"Excluded key: {key} because it's not a valid wereable stream column name.")
    for key in df_dict.keys():
        df = df_dict[key]
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        elif 'start' in df.columns and 'end' in df.columns:
            df['start'] = pd.to_datetime(df['start'], unit='s')
            df['end'] = pd.to_datetime(df['end'], unit='s')
        if metadata is not None:
            df.wereable.add_metadata(metadata, inplace=True)
        else:
            df.wereable.add_metadata({'data_id': 'unknown', 'subject_id': 'unknown'}, inplace=True)
        df_dict[key] = df
    return df_dict

# %% ../nbs/api/05_readers.ipynb 10
def load_csv(filepath: str, # full path to csv file to be loaded
             metadata: Dict[str, str] = None, # metadata containing data_id, subject_id, or other_info
             timestamp_col: str = None, # name of the column to be used as timestamp. If None, it is assumed that a `datetime` column exists
             *args, # arguments to pass to pd.read_csv
             **kwargs, # keyword arguments to pass to pd.read_csv
             ):
    "Create a dataframe from a csv containing wereable data"
    # validate inputs
    if not isinstance(filepath, str):
        raise AttributeError("Filepath must be a string.")
    if not isinstance(timestamp_col, str) and timestamp_col is not None:
        raise AttributeError("Timestamp column must be a string.")
    if metadata is not None:
        WereableData._validate_metadata(metadata)
    # load csv
    df = pd.read_csv(filepath, *args, **kwargs)
    # create datetime column
    if timestamp_col is not None:
        df['datetime'] = pd.to_datetime(df[timestamp_col], unit='s')
    if timestamp_col is None and 'datetime' not in df.columns:
        raise AttributeError("CSV file must have a column named 'datetime' or a timestamp column must be provided.")
    # add metadata
    if metadata is not None:
        df.wereable.add_metadata(metadata, inplace=True)
    else:
        df.wereable.add_metadata({'data_id': 'unknown', 'subject_id': 'unknown'}, inplace=True)
    return df

# %% ../nbs/api/05_readers.ipynb 11
ACTIWATCH_COLUMN_RENAMING = {
    'White Light': 'light_estimate',
    'Sleep/Wake': 'wake',
    'Activity': 'activity',
} 

# %% ../nbs/api/05_readers.ipynb 12
def load_actiwatch(filepath: str, # full path to csv file to be loaded
                   metadata: Dict[str, str] = None, # metadata containing data_id, subject_id, or other_info
                   *args, # arguments to pass to pd.read_csv
                   **kwargs, # keyword arguments to pass to pd.read_csv
                   ) -> pd.DataFrame: # dataframe with the wereable data
    "Create a dataframe from an actiwatch csv file"
    # validate inputs
    if not isinstance(filepath, str):
        raise AttributeError("Filepath must be a string.")
    if metadata is not None:
        WereableData._validate_metadata(metadata)
    # load csv
    df = pd.read_csv(filepath, *args, **kwargs)
    df['datetime'] = pd.to_datetime(df['Date']+" "+df['Time'])
    # drop unnecessary columns
    df.drop(columns=['Date', 'Time'], inplace=True)
    # rename columns
    df.rename(columns=ACTIWATCH_COLUMN_RENAMING, inplace=True)
    # add metadata
    if metadata is not None:
        df.wereable.add_metadata(metadata, inplace=True)
    else:
        df.wereable.add_metadata({'data_id': 'unknown', 'subject_id': 'unknown'}, inplace=True)
    return df

# %% ../nbs/api/05_readers.ipynb 14
WEREABLE_RESAMPLE_METHOD = {
    'steps': 'sum',
    'wake': 'max',
    'heartrate': 'mean',
    'light_estimate': 'mean',
    'activity': 'mean',
}

# %% ../nbs/api/05_readers.ipynb 15
def resample_df(df: pd.DataFrame, # dataframe to be resampled
                name: str, # name of the wereable data to resample (one of steps, heartrate, wake, light_estimate, or activity)
                freq: str, # frequency to resample to
                agg_method: str, # aggregation method to use when resampling
                initial_datetime: pd.Timestamp = None, # initial datetime to use when resampling. If None, the minimum datetime in the dataframe is used
                final_datetime: pd.Timestamp = None, # final datetime to use when resampling. If None, the maximum datetime in the dataframe is used
                ) -> pd.DataFrame: # resampled dataframe
    "Resample a wereable dataframe. If data is specified in intervals, returns the density of the quantity per minute."
    # validate inputs
    if not df.wereable.is_valid():
        raise AttributeError("Dataframe must be a valid wereable dataframe.")
    if not isinstance(df, pd.DataFrame):
        raise AttributeError("Dataframe must be a pandas dataframe.")
    if not isinstance(freq, str):
        raise AttributeError("Frequency must be a string.")
    if name is not None and name not in VALID_WEREABLE_STREAMS:
        raise AttributeError(f"Name must be one of: {VALID_WEREABLE_STREAMS}.")
    if name not in df.columns:
        raise AttributeError(f"Name must be one of: {df.columns}.")
    if agg_method not in ['sum', 'mean', 'max', 'min']:
        raise AttributeError("Aggregation method must be one of: sum, mean, max, min.")
    if initial_datetime is not None and not isinstance(initial_datetime, pd.Timestamp):
        raise AttributeError("Initial datetime must be a pandas timestamp.")
    if final_datetime is not None and not isinstance(final_datetime, pd.Timestamp):
        raise AttributeError("Final datetime must be a pandas timestamp.")
    # resample
    values = df[name]
    if 'start' in df.columns and 'end' in df.columns:
        # data is specified in intervals
        starts = df.start
        stops = df.end
        if initial_datetime is None:
            initial_datetime = starts.min()
        if final_datetime is None:
            final_datetime = stops.max()
        new_datetime = pd.date_range(initial_datetime, final_datetime, freq=freq)
        new_values = np.zeros(len(new_datetime))
        for idx, datetime in enumerate(new_datetime):
            next_datetime = datetime + pd.to_timedelta(freq)
            mask = (starts <= next_datetime) & (stops > datetime)
            if len(values[mask]) > 0:
                # NOTE: returns the density of the quantity per minute
                time_interval = (stops[mask] - starts[mask]).apply(lambda x: x.seconds / 60.0)
                new_values[idx] = (values[mask] / time_interval).agg(agg_method)
    else:
        # data is specified per datetime
        data_datetimes = df.datetime
        if initial_datetime is None:
            initial_datetime = data_datetimes.min()
        if final_datetime is None:
            final_datetime = data_datetimes.max()
        new_datetime = pd.date_range(initial_datetime, final_datetime, freq=freq)
        new_values = np.zeros(len(new_datetime))
        for idx, datetime in enumerate(new_datetime):
            next_datetime = datetime + pd.to_timedelta(freq)
            mask = (data_datetimes <= next_datetime) & (data_datetimes >= datetime)
            if len(values[mask]) > 0:
                new_values[idx] = values[mask].agg(agg_method)

    return pd.DataFrame({'datetime': new_datetime, name: new_values})

# %% ../nbs/api/05_readers.ipynb 17
def combine_wereable_dataframes(df_dict: Dict[str, pd.DataFrame], # dictionary of wereable dataframes 
                                metadata: Dict[str, str] = None, # metadata for the combined dataframe
                                resample_freq: str = '10min', # resampling frequency (e.g. '10min' for 10 minutes, see Pandas Offset aliases: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases)
                                ) -> pd.DataFrame: # combined wereable dataframe
    "Combine a dictionary of wereable dataframes into a single dataframe with resampling"
    df_list = []
    # find common initial and final datetimes
    initial_datetimes = []
    final_datetimes = []
    for name in df_dict.keys():
        df = df_dict[name]
        df.wereable.is_valid()
        if 'start' in df.columns:
            initial_datetimes.append(df.start.min())
            final_datetimes.append(df.end.max())
        else:
            initial_datetimes.append(df.datetime.min())
            final_datetimes.append(df.datetime.max())
    initial_datetime = min(initial_datetimes)
    final_datetime = max(final_datetimes)
    # resample each df
    for name in df_dict.keys():
        df = df_dict[name]
        new_df = resample_df(df, name, resample_freq, 
                             WEREABLE_RESAMPLE_METHOD[name],
                             initial_datetime=initial_datetime,
                             final_datetime=final_datetime)
        df_list.append(new_df)
    # merge all dfs by datetime
    df = df_list[0]
    for i in range(1, len(df_list)):
        df = df.merge(df_list[i], on='datetime', how='outer')
    # sort by datetime
    df.sort_values(by='datetime', inplace=True)
    # add metadata
    if metadata is not None:
        df.wereable.add_metadata(metadata, inplace=True)
    else:
        df.wereable.add_metadata({'data_id': 'combined_dataframe'}, inplace=True)
    return df
