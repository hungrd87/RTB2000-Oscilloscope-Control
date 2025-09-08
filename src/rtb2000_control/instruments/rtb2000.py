"""
RTB2000 Oscilloscope Control Module
"""

from ..communication.visa_instrument import VisaInstrument
from typing import Dict, List, Tuple, Optional
import numpy as np


class RTB2000(VisaInstrument):
    """R&S RTB2000 series oscilloscope control class"""
    
    def __init__(self, resource_name: Optional[str] = None):
        """
        Initialize RTB2000 oscilloscope
        
        Args:
            resource_name: VISA resource identifier
        """
        super().__init__(resource_name)
        self.channels = [1, 2, 3, 4]  # RTB2000 has 4 channels
        
    def identify(self) -> str:
        """Get instrument identification"""
        return self.query("*IDN?")
    
    def reset(self):
        """Reset instrument to default state"""
        self.write("*RST")
        self.write("*OPC?")  # Wait for operation complete
    
    # Channel Control
    def set_channel_enable(self, channel: int, enabled: bool):
        """Enable/disable channel display"""
        state = "ON" if enabled else "OFF"
        self.write(f"CHAN{channel}:STAT {state}")
    
    def get_channel_enable(self, channel: int) -> bool:
        """Get channel enable state"""
        response = self.query(f"CHAN{channel}:STAT?")
        return response == "1"
    
    def set_vertical_scale(self, channel: int, scale: float):
        """Set vertical scale (volts/div)"""
        self.write(f"CHAN{channel}:SCAL {scale}")
    
    def get_vertical_scale(self, channel: int) -> float:
        """Get vertical scale"""
        return float(self.query(f"CHAN{channel}:SCAL?"))
    
    def set_vertical_position(self, channel: int, position: float):
        """Set vertical position (divisions)"""
        self.write(f"CHAN{channel}:POS {position}")
    
    def get_vertical_position(self, channel: int) -> float:
        """Get vertical position"""
        return float(self.query(f"CHAN{channel}:POS?"))
    
    def set_coupling(self, channel: int, coupling: str):
        """Set input coupling (DC, AC, GND)"""
        self.write(f"CHAN{channel}:COUP {coupling}")
    
    def get_coupling(self, channel: int) -> str:
        """Get input coupling"""
        return self.query(f"CHAN{channel}:COUP?")
    
    # Timebase Control
    def set_timebase_scale(self, scale: float):
        """Set horizontal timebase scale (seconds/div)"""
        self.write(f"TIM:SCAL {scale}")
    
    def get_timebase_scale(self) -> float:
        """Get timebase scale"""
        return float(self.query("TIM:SCAL?"))
    
    def set_timebase_position(self, position: float):
        """Set horizontal position (seconds)"""
        self.write(f"TIM:POS {position}")
    
    def get_timebase_position(self) -> float:
        """Get horizontal position"""
        return float(self.query("TIM:POS?"))
    
    # Trigger Control
    def set_trigger_source(self, source: str):
        """Set trigger source (CH1, CH2, CH3, CH4, EXT)"""
        self.write(f"TRIG:SOUR {source}")
    
    def get_trigger_source(self) -> str:
        """Get trigger source"""
        return self.query("TRIG:SOUR?")
    
    def set_trigger_level(self, level: float):
        """Set trigger level (volts)"""
        self.write(f"TRIG:LEV {level}")
    
    def get_trigger_level(self) -> float:
        """Get trigger level"""
        return float(self.query("TRIG:LEV?"))
    
    def set_trigger_slope(self, slope: str):
        """Set trigger slope (POS, NEG)"""
        self.write(f"TRIG:SLOP {slope}")
    
    def get_trigger_slope(self) -> str:
        """Get trigger slope"""
        return self.query("TRIG:SLOP?")
    
    # Acquisition Control
    def single_trigger(self):
        """Perform single trigger acquisition"""
        self.write("SING")
    
    def run_continuous(self):
        """Start continuous acquisition"""
        self.write("RUN")
    
    def stop_acquisition(self):
        """Stop acquisition"""
        self.write("STOP")
    
    def get_acquisition_state(self) -> str:
        """Get acquisition state"""
        return self.query("ACQ:STAT?")
    
    # Data Acquisition
    def get_waveform_data(self, channel: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get waveform data from specified channel
        
        Args:
            channel: Channel number (1-4)
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (time_data, voltage_data)
        """
        # Set data format
        self.write("FORM:DATA REAL")
        self.write("FORM:BORD LSB")
        
        # Select channel for data transfer
        self.write(f"DAT:SOUR CHAN{channel}")
        
        # Get waveform preamble for scaling
        preamble = self.query("DAT:PRE?").split(',')
        y_increment = float(preamble[7])
        y_origin = float(preamble[8])
        y_reference = float(preamble[9])
        x_increment = float(preamble[4])
        x_origin = float(preamble[5])
        
        # Get raw waveform data
        raw_data = self.query_binary_values("DAT:WAV?", datatype='f')
        
        # Convert to voltage
        voltage_data = np.array(raw_data) * y_increment + y_origin
        
        # Generate time axis
        time_data = np.arange(len(voltage_data)) * x_increment + x_origin
        
        return time_data, voltage_data
    
    # Measurement Functions
    def measure_frequency(self, channel: int) -> float:
        """Measure frequency on channel"""
        return float(self.query(f"MEAS:FREQ? CHAN{channel}"))
    
    def measure_amplitude(self, channel: int) -> float:
        """Measure peak-to-peak amplitude"""
        return float(self.query(f"MEAS:APP? CHAN{channel}"))
    
    def measure_mean(self, channel: int) -> float:
        """Measure DC/mean level"""
        return float(self.query(f"MEAS:MEAN? CHAN{channel}"))
    
    def measure_rms(self, channel: int) -> float:
        """Measure RMS value"""
        return float(self.query(f"MEAS:RMS? CHAN{channel}"))
    
    # Utility Functions
    def screenshot(self, filename: str = "screenshot.png"):
        """Take screenshot and save to file"""
        self.write(f"HCOP:DEV:LANG PNG")
        self.write(f"HCOP:DEST 'MMEM'")
        self.write(f"HCOP:ITEM:WIND HARD")
        self.write(f"MMEM:NAME '{filename}'")
        self.write("HCOP:IMM")
        
    def get_channel_info(self, channel: int) -> Dict:
        """Get comprehensive channel information"""
        return {
            'enabled': self.get_channel_enable(channel),
            'scale': self.get_vertical_scale(channel),
            'position': self.get_vertical_position(channel),
            'coupling': self.get_coupling(channel)
        }
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        return {
            'identification': self.identify(),
            'timebase_scale': self.get_timebase_scale(),
            'timebase_position': self.get_timebase_position(),
            'trigger_source': self.get_trigger_source(),
            'trigger_level': self.get_trigger_level(),
            'trigger_slope': self.get_trigger_slope(),
            'acquisition_state': self.get_acquisition_state()
        }
