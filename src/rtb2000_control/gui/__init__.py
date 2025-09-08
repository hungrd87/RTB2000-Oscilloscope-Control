"""
GUI package initialization
"""

# Import modules only, not classes to avoid premature widget creation
from . import main_window
from . import connection_widget
from . import channel_control_widget
from . import timebase_widget
from . import trigger_widget
from . import waveform_widget
from . import measurement_widget

# Expose classes for explicit import
def get_main_window():
    return main_window.MainWindow

def get_connection_widget():
    return connection_widget.ConnectionWidget

def get_channel_control_widget():
    return channel_control_widget.ChannelControlWidget

def get_timebase_widget():
    return timebase_widget.TimebaseWidget

def get_trigger_widget():
    return trigger_widget.TriggerWidget

def get_waveform_widget():
    return waveform_widget.WaveformWidget

def get_measurement_widget():
    return measurement_widget.MeasurementWidget

__all__ = [
    'main_window',
    'connection_widget', 
    'channel_control_widget',
    'timebase_widget',
    'trigger_widget',
    'waveform_widget',
    'measurement_widget'
]
