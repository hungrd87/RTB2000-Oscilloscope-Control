"""
Enhanced VISA Communication Module for RTB2000 Oscilloscope
Version 2.0 - September 8, 2025
"""

import pyvisa
import logging
import warnings
from typing import Optional, Union, List

# Suppress PyVISA-py warnings for optional packages
warnings.filterwarnings('ignore', category=UserWarning, module='pyvisa_py')

class EnhancedVisaInstrument:
    """Enhanced base class for VISA instrument communication with better error handling"""
    
    def __init__(self, resource_name: str = None):
        """
        Initialize VISA instrument
        
        Args:
            resource_name: VISA resource identifier (e.g., 'USB0::0x0AAD::0x0119::100001::INSTR')
        """
        self.resource_name = resource_name
        self.instrument = None
        self.resource_manager = None
        self.logger = self._setup_logger()
        self.connection_timeout = 5000  # 5 seconds
        self.query_timeout = 2000      # 2 seconds
        
    def _setup_logger(self) -> logging.Logger:
        """Setup enhanced logging"""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
        
    def connect(self, resource_name: str = None, timeout: int = None) -> tuple[bool, str]:
        """
        Connect to the instrument with enhanced error handling
        
        Args:
            resource_name: VISA resource identifier
            timeout: Connection timeout in milliseconds
            
        Returns:
            tuple[bool, str]: (success, message/error_description)
        """
        try:
            if resource_name:
                self.resource_name = resource_name
                
            if not self.resource_name:
                return False, "Resource name not specified"
                
            self.resource_manager = pyvisa.ResourceManager()
            
            # Set timeout if provided
            if timeout:
                self.connection_timeout = timeout
                
            self.instrument = self.resource_manager.open_resource(
                self.resource_name,
                timeout=self.connection_timeout
            )
            
            # Configure communication settings
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            
            # Test connection with error handling
            try:
                idn = self.query("*IDN?")
                self.logger.info(f"Successfully connected to: {idn}")
                return True, f"Connected to {idn}"
                
            except Exception as e:
                self.logger.warning(f"Connection test failed: {e}")
                return True, "Connected (ID query failed)"
                
        except pyvisa.VisaIOError as e:
            error_msg = f"VISA IO Error: {e}"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Connection failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def disconnect(self) -> tuple[bool, str]:
        """
        Disconnect from instrument with proper cleanup
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            if self.instrument:
                self.instrument.close()
                self.instrument = None
                
            if self.resource_manager:
                self.resource_manager.close()
                self.resource_manager = None
                
            self.logger.info("Successfully disconnected from instrument")
            return True, "Disconnected successfully"
            
        except Exception as e:
            error_msg = f"Disconnect error: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def write(self, command: str) -> tuple[bool, str]:
        """
        Write command to instrument with error handling
        
        Args:
            command: SCPI command string
            
        Returns:
            tuple[bool, str]: (success, message/error)
        """
        if not self.instrument:
            return False, "Not connected to instrument"
        
        try:
            self.logger.debug(f"Sending: {command}")
            self.instrument.write(command)
            return True, "Command sent successfully"
            
        except pyvisa.VisaIOError as e:
            error_msg = f"VISA IO Error writing '{command}': {e}"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Error writing '{command}': {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def query(self, command: str, timeout: int = None) -> str:
        """
        Query instrument and return response with error handling
        
        Args:
            command: SCPI command string
            timeout: Query timeout in milliseconds
            
        Returns:
            str: Instrument response
            
        Raises:
            RuntimeError: If not connected or query fails
        """
        if not self.instrument:
            raise RuntimeError("Not connected to instrument")
        
        try:
            # Set temporary timeout if provided
            original_timeout = self.instrument.timeout
            if timeout:
                self.instrument.timeout = timeout
            
            self.logger.debug(f"Querying: {command}")
            response = self.instrument.query(command).strip()
            self.logger.debug(f"Response: {response}")
            
            # Restore original timeout
            if timeout:
                self.instrument.timeout = original_timeout
                
            return response
            
        except pyvisa.VisaIOError as e:
            raise RuntimeError(f"VISA IO Error querying '{command}': {e}")
            
        except Exception as e:
            raise RuntimeError(f"Error querying '{command}': {e}")
    
    def query_binary_values(self, command: str, datatype='f', timeout: int = None) -> List[float]:
        """
        Query binary data from instrument with error handling
        
        Args:
            command: SCPI command string
            datatype: Data type for binary conversion
            timeout: Query timeout in milliseconds
            
        Returns:
            List[float]: Binary data as list
            
        Raises:
            RuntimeError: If not connected or query fails
        """
        if not self.instrument:
            raise RuntimeError("Not connected to instrument")
        
        try:
            # Set temporary timeout if provided
            original_timeout = self.instrument.timeout
            if timeout:
                self.instrument.timeout = timeout
            
            self.logger.debug(f"Querying binary: {command}")
            data = self.instrument.query_binary_values(command, datatype=datatype)
            
            # Restore original timeout
            if timeout:
                self.instrument.timeout = original_timeout
                
            return data
            
        except pyvisa.VisaIOError as e:
            raise RuntimeError(f"VISA IO Error in binary query '{command}': {e}")
            
        except Exception as e:
            raise RuntimeError(f"Error in binary query '{command}': {e}")
    
    @staticmethod
    def list_resources() -> tuple[List[str], List[str]]:
        """
        List available VISA resources with enhanced discovery
        
        Returns:
            tuple[List[str], List[str]]: (resources, errors)
        """
        resources = []
        errors = []
        
        try:
            # Suppress warnings during resource discovery
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                rm = pyvisa.ResourceManager()
                found_resources = rm.list_resources()
                rm.close()
                
            resources = list(found_resources)
            
            if not resources:
                errors.append("No VISA resources found")
                
        except Exception as e:
            errors.append(f"Failed to list resources: {e}")
            
        return resources, errors
    
    def is_connected(self) -> bool:
        """
        Check if instrument is connected with enhanced validation
        
        Returns:
            bool: True if connected and responsive
        """
        if not self.instrument:
            return False
            
        try:
            # Quick test with short timeout
            self.query("*OPC?", timeout=1000)
            return True
            
        except:
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get detailed connection information
        
        Returns:
            dict: Connection details and status
        """
        info = {
            'resource_name': self.resource_name,
            'connected': self.is_connected(),
            'timeout': getattr(self.instrument, 'timeout', None) if self.instrument else None,
        }
        
        if self.is_connected():
            try:
                info['identification'] = self.query("*IDN?")
            except:
                info['identification'] = "Unknown"
                
        return info


# Maintain backward compatibility
class VisaInstrument(EnhancedVisaInstrument):
    """Backward compatibility wrapper"""
    pass
