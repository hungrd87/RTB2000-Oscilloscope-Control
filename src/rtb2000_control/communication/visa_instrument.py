"""
VISA Communication Module for RTB2000 Oscilloscope
"""

import pyvisa
import logging
from typing import Optional, Union, List


class VisaInstrument:
    """Base class for VISA instrument communication"""
    
    def __init__(self, resource_name: str = None):
        """
        Initialize VISA instrument
        
        Args:
            resource_name: VISA resource identifier (e.g., 'USB0::0x0AAD::0x0119::100001::INSTR')
        """
        self.resource_name = resource_name
        self.instrument = None
        self.resource_manager = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self, resource_name: str = None) -> bool:
        """
        Connect to the instrument
        
        Args:
            resource_name: VISA resource identifier
            
        Returns:
            bool: True if connection successful
        """
        try:
            if resource_name:
                self.resource_name = resource_name
                
            if not self.resource_name:
                raise ValueError("Resource name not specified")
                
            self.resource_manager = pyvisa.ResourceManager()
            self.instrument = self.resource_manager.open_resource(self.resource_name)
            
            # Configure communication settings
            self.instrument.timeout = 5000  # 5 second timeout
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            
            # Test connection
            idn = self.query("*IDN?")
            self.logger.info(f"Connected to: {idn}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from instrument"""
        try:
            if self.instrument:
                self.instrument.close()
            if self.resource_manager:
                self.resource_manager.close()
            self.logger.info("Disconnected from instrument")
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
    
    def write(self, command: str):
        """
        Write command to instrument
        
        Args:
            command: SCPI command string
        """
        if not self.instrument:
            raise RuntimeError("Not connected to instrument")
        
        self.logger.debug(f"Sending: {command}")
        self.instrument.write(command)
    
    def query(self, command: str) -> str:
        """
        Query instrument and return response
        
        Args:
            command: SCPI command string
            
        Returns:
            str: Instrument response
        """
        if not self.instrument:
            raise RuntimeError("Not connected to instrument")
        
        self.logger.debug(f"Querying: {command}")
        response = self.instrument.query(command).strip()
        self.logger.debug(f"Response: {response}")
        return response
    
    def query_binary_values(self, command: str, datatype='f') -> List[float]:
        """
        Query binary data from instrument
        
        Args:
            command: SCPI command string
            datatype: Data type for binary conversion
            
        Returns:
            List[float]: Binary data as list
        """
        if not self.instrument:
            raise RuntimeError("Not connected to instrument")
        
        self.logger.debug(f"Querying binary: {command}")
        return self.instrument.query_binary_values(command, datatype=datatype)
    
    @staticmethod
    def list_resources() -> List[str]:
        """
        List available VISA resources
        
        Returns:
            List[str]: Available resource names
        """
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            rm.close()
            return list(resources)
        except Exception as e:
            logging.error(f"Failed to list resources: {e}")
            return []
    
    def is_connected(self) -> bool:
        """
        Check if instrument is connected
        
        Returns:
            bool: True if connected
        """
        try:
            if self.instrument:
                self.query("*OPC?")
                return True
        except:
            pass
        return False
