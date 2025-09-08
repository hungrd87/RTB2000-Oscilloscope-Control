#!/usr/bin/env python3
"""
RTB2000 Scripting Engine Module
===============================

Python scripting capabilities for automation:
- Custom measurement scripts with parameter management
- Script templates for common operations
- Interactive script editor with syntax highlighting
- Script library and sharing capabilities
"""

import sys
import traceback
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
import logging
from dataclasses import dataclass, field
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTextEdit, QPushButton, QListWidget, QSplitter,
                            QTabWidget, QComboBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QGroupBox, QTableWidget, QTableWidgetItem,
                            QFileDialog, QMessageBox, QProgressBar, QLineEdit)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter
# Try to import QScintilla for syntax highlighting, fall back to QTextEdit
try:
    from PyQt6.Qsci import QsciScintilla, QsciLexerPython
    QSCINTILLA_AVAILABLE = True
except ImportError:
    QSCINTILLA_AVAILABLE = False

import numpy as np


class ScriptType(Enum):
    """Types of automation scripts"""
    MEASUREMENT = "measurement"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    CALIBRATION = "calibration"
    TESTING = "testing"
    CUSTOM = "custom"


class ScriptStatus(Enum):
    """Script execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScriptParameter:
    """Script parameter definition"""
    name: str
    param_type: str  # int, float, str, bool, list
    default_value: Any
    description: str = ""
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    choices: Optional[List[Any]] = None
    required: bool = True


@dataclass
class ScriptTemplate:
    """Script template definition"""
    template_id: str
    name: str
    description: str
    script_type: ScriptType
    code_template: str
    parameters: List[ScriptParameter] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0"
    created_date: str = ""


@dataclass
class ScriptResult:
    """Result of script execution"""
    script_id: str
    status: ScriptStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: str = ""
    error: str = ""
    return_value: Any = None
    execution_time: float = 0.0


class ScriptContext:
    """Execution context for scripts"""
    
    def __init__(self):
        # RTB2000 components
        self.oscilloscope = None
        self.measurement_engine = None
        self.analysis_engine = None
        self.automation_engine = None
        self.trigger_manager = None
        self.multi_channel_controller = None
        
        # Data and results
        self.current_data = None
        self.measurement_results = {}
        self.analysis_results = {}
        
        # Utilities
        self.logger = logging.getLogger(__name__)
        self.parameters = {}
        
        # Script execution state
        self.should_stop = False
        self.progress_callback: Optional[Callable[[float], None]] = None
        self.output_callback: Optional[Callable[[str], None]] = None
    
    def log(self, message: str, level: str = "info"):
        """Log a message"""
        if self.output_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.output_callback(f"[{timestamp}] {level.upper()}: {message}")
        
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
    
    def set_progress(self, progress: float):
        """Set execution progress (0.0 to 1.0)"""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def check_stop(self):
        """Check if script should stop"""
        if self.should_stop:
            raise InterruptedError("Script execution cancelled")
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get script parameter value"""
        return self.parameters.get(name, default)
    
    def measure(self, measurement_type: str, channel: str = "CH1", **kwargs) -> float:
        """Perform a measurement"""
        self.log(f"Measuring {measurement_type} on {channel}")
        
        # Simulate measurement
        import random
        if measurement_type.lower() == "amplitude":
            return random.uniform(0.1, 5.0)
        elif measurement_type.lower() == "frequency":
            return random.uniform(100, 10000)
        elif measurement_type.lower() == "period":
            return random.uniform(1e-6, 1e-3)
        else:
            return random.uniform(-1.0, 1.0)
    
    def acquire_waveform(self, channel: str = "CH1") -> tuple:
        """Acquire waveform data"""
        self.log(f"Acquiring waveform from {channel}")
        
        # Simulate waveform data
        t = np.linspace(0, 1e-3, 1000)
        freq = self.get_parameter("signal_frequency", 1000)
        amplitude = self.get_parameter("signal_amplitude", 1.0)
        y = amplitude * np.sin(2 * np.pi * freq * t)
        
        return t, y
    
    def wait(self, seconds: float):
        """Wait for specified time"""
        self.log(f"Waiting {seconds} seconds")
        import time
        time.sleep(seconds)


class AutomationScript(QObject):
    """Automation script with execution capabilities"""
    
    # Signals
    execution_started = pyqtSignal(str)  # script_id
    execution_completed = pyqtSignal(object)  # ScriptResult
    execution_failed = pyqtSignal(str, str)  # script_id, error
    progress_updated = pyqtSignal(str, float)  # script_id, progress
    output_updated = pyqtSignal(str, str)  # script_id, output
    
    def __init__(self, script_id: str, name: str, code: str = ""):
        super().__init__()
        self.script_id = script_id
        self.name = name
        self.code = code
        self.logger = logging.getLogger(__name__)
        
        # Script metadata
        self.description = ""
        self.script_type = ScriptType.CUSTOM
        self.parameters: List[ScriptParameter] = []
        self.tags: List[str] = []
        self.author = ""
        self.version = "1.0"
        self.created_date = datetime.now().isoformat()
        
        # Execution state
        self.status = ScriptStatus.IDLE
        self.execution_thread: Optional[QThread] = None
        self.context: Optional[ScriptContext] = None
        self.last_result: Optional[ScriptResult] = None
    
    def add_parameter(self, parameter: ScriptParameter):
        """Add a parameter to the script"""
        self.parameters.append(parameter)
    
    def set_parameter_value(self, name: str, value: Any):
        """Set parameter value for execution"""
        if not self.context:
            self.context = ScriptContext()
        self.context.parameters[name] = value
    
    def get_parameter_value(self, name: str, default: Any = None) -> Any:
        """Get parameter value"""
        if self.context:
            return self.context.parameters.get(name, default)
        return default
    
    def validate_parameters(self) -> tuple[bool, List[str]]:
        """Validate all required parameters are set"""
        errors = []
        
        for param in self.parameters:
            if param.required:
                value = self.get_parameter_value(param.name)
                if value is None:
                    errors.append(f"Required parameter '{param.name}' is not set")
                    continue
                
                # Type validation
                if param.param_type == "int" and not isinstance(value, int):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{param.name}' must be an integer")
                
                elif param.param_type == "float" and not isinstance(value, (int, float)):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"Parameter '{param.name}' must be a number")
                
                elif param.param_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Parameter '{param.name}' must be a boolean")
                
                # Range validation
                if param.min_value is not None and value < param.min_value:
                    errors.append(f"Parameter '{param.name}' must be >= {param.min_value}")
                
                if param.max_value is not None and value > param.max_value:
                    errors.append(f"Parameter '{param.name}' must be <= {param.max_value}")
                
                # Choice validation
                if param.choices and value not in param.choices:
                    errors.append(f"Parameter '{param.name}' must be one of {param.choices}")
        
        return len(errors) == 0, errors
    
    def execute(self, context: Optional[ScriptContext] = None) -> bool:
        """Execute the script"""
        try:
            if self.status != ScriptStatus.IDLE:
                raise ValueError(f"Script is not idle (current status: {self.status})")
            
            # Validate parameters
            valid, errors = self.validate_parameters()
            if not valid:
                error_msg = "Parameter validation failed:\n" + "\n".join(errors)
                self.execution_failed.emit(self.script_id, error_msg)
                return False
            
            # Setup context
            if context:
                self.context = context
            elif not self.context:
                self.context = ScriptContext()
            
            # Setup callbacks
            self.context.progress_callback = lambda p: self.progress_updated.emit(self.script_id, p)
            self.context.output_callback = lambda o: self.output_updated.emit(self.script_id, o)
            
            # Start execution in thread
            self.execution_thread = ScriptExecutionThread(self)
            self.execution_thread.execution_completed.connect(self._on_execution_completed)
            self.execution_thread.execution_failed.connect(self._on_execution_failed)
            self.execution_thread.start()
            
            self.status = ScriptStatus.RUNNING
            self.execution_started.emit(self.script_id)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to start script execution: {e}"
            self.logger.error(error_msg)
            self.execution_failed.emit(self.script_id, error_msg)
            return False
    
    def cancel(self) -> bool:
        """Cancel script execution"""
        if self.status == ScriptStatus.RUNNING:
            if self.context:
                self.context.should_stop = True
            
            if self.execution_thread:
                self.execution_thread.cancel()
            
            self.status = ScriptStatus.CANCELLED
            return True
        
        return False
    
    def _on_execution_completed(self, result: ScriptResult):
        """Handle execution completion"""
        self.status = ScriptStatus.COMPLETED
        self.last_result = result
        self.execution_completed.emit(result)
    
    def _on_execution_failed(self, error: str):
        """Handle execution failure"""
        self.status = ScriptStatus.FAILED
        result = ScriptResult(
            script_id=self.script_id,
            status=ScriptStatus.FAILED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            error=error
        )
        self.last_result = result
        self.execution_failed.emit(self.script_id, error)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert script to dictionary"""
        return {
            'script_id': self.script_id,
            'name': self.name,
            'description': self.description,
            'script_type': self.script_type.value,
            'code': self.code,
            'parameters': [
                {
                    'name': p.name,
                    'param_type': p.param_type,
                    'default_value': p.default_value,
                    'description': p.description,
                    'min_value': p.min_value,
                    'max_value': p.max_value,
                    'choices': p.choices,
                    'required': p.required
                }
                for p in self.parameters
            ],
            'tags': self.tags,
            'author': self.author,
            'version': self.version,
            'created_date': self.created_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationScript':
        """Create script from dictionary"""
        script = cls(
            script_id=data['script_id'],
            name=data['name'],
            code=data.get('code', '')
        )
        
        script.description = data.get('description', '')
        script.script_type = ScriptType(data.get('script_type', 'custom'))
        script.tags = data.get('tags', [])
        script.author = data.get('author', '')
        script.version = data.get('version', '1.0')
        script.created_date = data.get('created_date', datetime.now().isoformat())
        
        # Load parameters
        for param_data in data.get('parameters', []):
            param = ScriptParameter(
                name=param_data['name'],
                param_type=param_data['param_type'],
                default_value=param_data['default_value'],
                description=param_data.get('description', ''),
                min_value=param_data.get('min_value'),
                max_value=param_data.get('max_value'),
                choices=param_data.get('choices'),
                required=param_data.get('required', True)
            )
            script.add_parameter(param)
        
        return script


class ScriptExecutionThread(QThread):
    """Thread for script execution"""
    
    execution_completed = pyqtSignal(object)  # ScriptResult
    execution_failed = pyqtSignal(str)  # error
    
    def __init__(self, script: AutomationScript):
        super().__init__()
        self.script = script
        self.logger = logging.getLogger(__name__)
        self.cancelled = False
    
    def run(self):
        """Execute the script"""
        start_time = datetime.now()
        output_buffer = []
        
        try:
            # Capture output
            def capture_output(text):
                output_buffer.append(text)
            
            if self.script.context:
                original_callback = self.script.context.output_callback
                self.script.context.output_callback = capture_output
            
            # Create execution environment
            exec_globals = {
                '__builtins__': __builtins__,
                'np': np,
                'context': self.script.context,
                'log': self.script.context.log if self.script.context else print,
                'measure': self.script.context.measure if self.script.context else lambda *args, **kwargs: 0.0,
                'acquire_waveform': self.script.context.acquire_waveform if self.script.context else lambda *args: (np.array([]), np.array([])),
                'wait': self.script.context.wait if self.script.context else lambda x: None,
                'check_stop': self.script.context.check_stop if self.script.context else lambda: None,
                'set_progress': self.script.context.set_progress if self.script.context else lambda x: None,
                'get_parameter': self.script.context.get_parameter if self.script.context else lambda x, d=None: d
            }
            
            exec_locals = {}
            
            # Execute script
            exec(self.script.code, exec_globals, exec_locals)
            
            # Get return value
            return_value = exec_locals.get('result', None)
            
            # Create result
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            result = ScriptResult(
                script_id=self.script.script_id,
                status=ScriptStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                output='\n'.join(output_buffer),
                return_value=return_value,
                execution_time=execution_time
            )
            
            if not self.cancelled:
                self.execution_completed.emit(result)
            
        except InterruptedError:
            # Script was cancelled
            pass
        except Exception as e:
            error_msg = f"Script execution error: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            if not self.cancelled:
                self.execution_failed.emit(error_msg)
    
    def cancel(self):
        """Cancel script execution"""
        self.cancelled = True


class ScriptTemplateManager:
    """Manager for script templates"""
    
    def __init__(self):
        self.templates: Dict[str, ScriptTemplate] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load built-in templates
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in script templates"""
        # Basic measurement template
        measurement_template = ScriptTemplate(
            template_id="basic_measurement",
            name="Basic Measurement",
            description="Perform basic measurements on a channel",
            script_type=ScriptType.MEASUREMENT,
            code_template='''# Basic Measurement Script
# Perform amplitude and frequency measurements

channel = get_parameter("channel", "CH1")
measurement_type = get_parameter("measurement_type", "amplitude")

log(f"Starting {measurement_type} measurement on {channel}")

# Perform measurement
result = measure(measurement_type, channel)

log(f"Measurement result: {result}")

# Store result for return
result = {"measurement": measurement_type, "value": result, "channel": channel}
''',
            parameters=[
                ScriptParameter("channel", "str", "CH1", "Channel to measure", choices=["CH1", "CH2", "CH3", "CH4"]),
                ScriptParameter("measurement_type", "str", "amplitude", "Type of measurement", 
                              choices=["amplitude", "frequency", "period", "rms"])
            ]
        )
        self.add_template(measurement_template)
        
        # Automated sweep template
        sweep_template = ScriptTemplate(
            template_id="frequency_sweep",
            name="Frequency Sweep",
            description="Perform measurements across frequency range",
            script_type=ScriptType.AUTOMATION,
            code_template='''# Frequency Sweep Script
# Measure amplitude across frequency range

start_freq = get_parameter("start_frequency", 100)
stop_freq = get_parameter("stop_frequency", 10000)
num_points = get_parameter("num_points", 10)
channel = get_parameter("channel", "CH1")

log(f"Starting frequency sweep from {start_freq} to {stop_freq} Hz")

frequencies = np.linspace(start_freq, stop_freq, num_points)
amplitudes = []

for i, freq in enumerate(frequencies):
    check_stop()  # Check if cancelled
    
    log(f"Measuring at {freq:.1f} Hz")
    
    # Set frequency (simulated)
    # In real implementation, this would control signal generator
    
    # Wait for settling
    wait(0.1)
    
    # Measure amplitude
    amplitude = measure("amplitude", channel)
    amplitudes.append(amplitude)
    
    # Update progress
    progress = (i + 1) / len(frequencies)
    set_progress(progress)

log("Frequency sweep completed")

# Store results
result = {
    "frequencies": frequencies.tolist(),
    "amplitudes": amplitudes,
    "channel": channel
}
''',
            parameters=[
                ScriptParameter("start_frequency", "float", 100.0, "Start frequency (Hz)", min_value=1.0),
                ScriptParameter("stop_frequency", "float", 10000.0, "Stop frequency (Hz)", min_value=1.0),
                ScriptParameter("num_points", "int", 10, "Number of measurement points", min_value=2, max_value=1000),
                ScriptParameter("channel", "str", "CH1", "Channel to measure", choices=["CH1", "CH2", "CH3", "CH4"])
            ]
        )
        self.add_template(sweep_template)
        
        # Data analysis template
        analysis_template = ScriptTemplate(
            template_id="waveform_analysis",
            name="Waveform Analysis",
            description="Analyze acquired waveform data",
            script_type=ScriptType.ANALYSIS,
            code_template='''# Waveform Analysis Script
# Analyze time-domain and frequency-domain characteristics

channel = get_parameter("channel", "CH1")
window_function = get_parameter("window_function", "hanning")

log(f"Acquiring waveform from {channel}")

# Acquire waveform
time_axis, voltage_data = acquire_waveform(channel)

log(f"Acquired {len(voltage_data)} samples")

# Time domain analysis
mean_value = np.mean(voltage_data)
rms_value = np.sqrt(np.mean(voltage_data**2))
peak_to_peak = np.max(voltage_data) - np.min(voltage_data)

log(f"Mean: {mean_value:.3f} V")
log(f"RMS: {rms_value:.3f} V")
log(f"Peak-to-Peak: {peak_to_peak:.3f} V")

# Frequency domain analysis
if len(voltage_data) > 1:
    # Apply window function
    if window_function == "hanning":
        window = np.hanning(len(voltage_data))
    elif window_function == "blackman":
        window = np.blackman(len(voltage_data))
    else:
        window = np.ones(len(voltage_data))
    
    windowed_data = voltage_data * window
    
    # FFT
    fft_data = np.fft.fft(windowed_data)
    freq_axis = np.fft.fftfreq(len(voltage_data), time_axis[1] - time_axis[0])
    
    # Find dominant frequency
    magnitude = np.abs(fft_data)
    positive_freqs = freq_axis[:len(freq_axis)//2]
    positive_magnitude = magnitude[:len(magnitude)//2]
    
    if len(positive_magnitude) > 1:
        dominant_freq_idx = np.argmax(positive_magnitude[1:]) + 1  # Skip DC
        dominant_freq = positive_freqs[dominant_freq_idx]
        
        log(f"Dominant frequency: {dominant_freq:.1f} Hz")
    else:
        dominant_freq = 0.0

# Store results
result = {
    "time_domain": {
        "mean": mean_value,
        "rms": rms_value,
        "peak_to_peak": peak_to_peak
    },
    "frequency_domain": {
        "dominant_frequency": dominant_freq
    },
    "channel": channel
}
''',
            parameters=[
                ScriptParameter("channel", "str", "CH1", "Channel to analyze", choices=["CH1", "CH2", "CH3", "CH4"]),
                ScriptParameter("window_function", "str", "hanning", "Window function for FFT", 
                              choices=["none", "hanning", "blackman"])
            ]
        )
        self.add_template(analysis_template)
    
    def add_template(self, template: ScriptTemplate):
        """Add a script template"""
        self.templates[template.template_id] = template
        self.logger.debug(f"Added template: {template.name}")
    
    def get_template(self, template_id: str) -> Optional[ScriptTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, script_type: Optional[ScriptType] = None) -> List[ScriptTemplate]:
        """List templates, optionally filtered by type"""
        if script_type:
            return [t for t in self.templates.values() if t.script_type == script_type]
        return list(self.templates.values())
    
    def create_script_from_template(self, template_id: str, script_id: str, name: str) -> Optional[AutomationScript]:
        """Create a script from a template"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        script = AutomationScript(script_id, name, template.code_template)
        script.description = template.description
        script.script_type = template.script_type
        script.parameters = template.parameters.copy()
        script.tags = template.tags.copy()
        
        return script


class ScriptingEngine(QObject):
    """Main scripting engine"""
    
    # Signals
    script_registered = pyqtSignal(str)  # script_id
    script_executed = pyqtSignal(str, object)  # script_id, result
    script_failed = pyqtSignal(str, str)  # script_id, error
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Script management
        self.scripts: Dict[str, AutomationScript] = {}
        self.template_manager = ScriptTemplateManager()
        
        # Execution context
        self.global_context = ScriptContext()
        
        self.logger.info("Scripting Engine initialized")
    
    def register_script(self, script: AutomationScript) -> bool:
        """Register a script"""
        try:
            if script.script_id in self.scripts:
                raise ValueError(f"Script '{script.script_id}' already registered")
            
            # Connect signals
            script.execution_completed.connect(self._on_script_completed)
            script.execution_failed.connect(self._on_script_failed)
            
            self.scripts[script.script_id] = script
            self.script_registered.emit(script.script_id)
            
            self.logger.info(f"Registered script: {script.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register script: {e}")
            return False
    
    def execute_script(self, script_id: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Execute a script"""
        if script_id not in self.scripts:
            self.logger.error(f"Script '{script_id}' not found")
            return False
        
        script = self.scripts[script_id]
        
        # Set parameters
        if parameters:
            for name, value in parameters.items():
                script.set_parameter_value(name, value)
        
        # Set global context
        script.context = self.global_context
        
        return script.execute()
    
    def cancel_script(self, script_id: str) -> bool:
        """Cancel script execution"""
        if script_id in self.scripts:
            return self.scripts[script_id].cancel()
        return False
    
    def get_script_status(self, script_id: str) -> Optional[ScriptStatus]:
        """Get script status"""
        if script_id in self.scripts:
            return self.scripts[script_id].status
        return None
    
    def list_scripts(self) -> List[str]:
        """List all registered scripts"""
        return list(self.scripts.keys())
    
    def save_script(self, script_id: str, file_path: str) -> bool:
        """Save script to file"""
        try:
            if script_id not in self.scripts:
                raise ValueError(f"Script '{script_id}' not found")
            
            script = self.scripts[script_id]
            with open(file_path, 'w') as f:
                json.dump(script.to_dict(), f, indent=2)
            
            self.logger.info(f"Saved script '{script_id}' to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save script: {e}")
            return False
    
    def load_script(self, file_path: str) -> Optional[str]:
        """Load script from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            script = AutomationScript.from_dict(data)
            if self.register_script(script):
                self.logger.info(f"Loaded script '{script.script_id}' from {file_path}")
                return script.script_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load script: {e}")
            return None
    
    def _on_script_completed(self, result: ScriptResult):
        """Handle script completion"""
        self.script_executed.emit(result.script_id, result)
    
    def _on_script_failed(self, script_id: str, error: str):
        """Handle script failure"""
        self.script_failed.emit(script_id, error)


class ScriptingWidget(QWidget):
    """Widget for script management and execution"""
    
    def __init__(self, scripting_engine: ScriptingEngine):
        super().__init__()
        self.scripting_engine = scripting_engine
        self.current_script: Optional[AutomationScript] = None
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the scripting UI"""
        layout = QHBoxLayout(self)
        
        # Create splitter
        splitter = QSplitter()
        
        # Left panel - Script list and templates
        left_panel = QWidget()
        self.setup_left_panel(left_panel)
        splitter.addWidget(left_panel)
        
        # Right panel - Script editor and execution
        right_panel = QWidget()
        self.setup_right_panel(right_panel)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
    
    def setup_left_panel(self, parent):
        """Setup left panel with script list"""
        layout = QVBoxLayout(parent)
        
        # Script list
        layout.addWidget(QLabel("Scripts:"))
        
        self.script_list = QListWidget()
        layout.addWidget(self.script_list)
        
        # Script controls
        script_controls = QHBoxLayout()
        
        self.new_script_btn = QPushButton("New")
        script_controls.addWidget(self.new_script_btn)
        
        self.load_script_btn = QPushButton("Load")
        script_controls.addWidget(self.load_script_btn)
        
        self.save_script_btn = QPushButton("Save")
        script_controls.addWidget(self.save_script_btn)
        
        layout.addLayout(script_controls)
        
        # Templates
        layout.addWidget(QLabel("Templates:"))
        
        self.template_list = QListWidget()
        layout.addWidget(self.template_list)
        
        self.use_template_btn = QPushButton("Use Template")
        layout.addWidget(self.use_template_btn)
        
        # Update template list
        self.update_template_list()
    
    def setup_right_panel(self, parent):
        """Setup right panel with editor and execution"""
        layout = QVBoxLayout(parent)
        
        # Script info
        info_layout = QHBoxLayout()
        
        info_layout.addWidget(QLabel("Name:"))
        self.script_name_edit = QLineEdit()
        info_layout.addWidget(self.script_name_edit)
        
        info_layout.addWidget(QLabel("Type:"))
        self.script_type_combo = QComboBox()
        self.script_type_combo.addItems([t.value for t in ScriptType])
        info_layout.addWidget(self.script_type_combo)
        
        layout.addLayout(info_layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Code editor tab
        self.setup_editor_tab(tab_widget)
        
        # Parameters tab
        self.setup_parameters_tab(tab_widget)
        
        # Execution tab
        self.setup_execution_tab(tab_widget)
        
        layout.addWidget(tab_widget)
        
        # Execution controls
        exec_controls = QHBoxLayout()
        
        self.execute_btn = QPushButton("Execute")
        exec_controls.addWidget(self.execute_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        exec_controls.addWidget(self.cancel_btn)
        
        exec_controls.addStretch()
        
        self.progress_bar = QProgressBar()
        exec_controls.addWidget(self.progress_bar)
        
        layout.addLayout(exec_controls)
    
    def setup_editor_tab(self, tab_widget):
        """Setup code editor tab"""
        editor_widget = QWidget()
        layout = QVBoxLayout(editor_widget)
        
        # Code editor with syntax highlighting if available
        if QSCINTILLA_AVAILABLE:
            self.code_editor = QsciScintilla()
            self.code_editor.setLexer(QsciLexerPython())
            self.code_editor.setTabWidth(4)
            self.code_editor.setIndentationsUseTabs(False)
            self.code_editor.setAutoIndent(True)
        else:
            # Fall back to QTextEdit
            self.code_editor = QTextEdit()
            font = QFont("Consolas", 10)
            self.code_editor.setFont(font)
        
        layout.addWidget(self.code_editor)
        
        tab_widget.addTab(editor_widget, "Code")
    
    def setup_parameters_tab(self, tab_widget):
        """Setup parameters tab"""
        params_widget = QWidget()
        layout = QVBoxLayout(params_widget)
        
        # Parameters table
        self.params_table = QTableWidget()
        self.params_table.setColumnCount(5)
        self.params_table.setHorizontalHeaderLabels([
            'Name', 'Type', 'Default', 'Value', 'Description'
        ])
        layout.addWidget(self.params_table)
        
        # Parameter controls
        param_controls = QHBoxLayout()
        
        self.add_param_btn = QPushButton("Add Parameter")
        param_controls.addWidget(self.add_param_btn)
        
        self.remove_param_btn = QPushButton("Remove Parameter")
        param_controls.addWidget(self.remove_param_btn)
        
        layout.addLayout(param_controls)
        
        tab_widget.addTab(params_widget, "Parameters")
    
    def setup_execution_tab(self, tab_widget):
        """Setup execution tab"""
        exec_widget = QWidget()
        layout = QVBoxLayout(exec_widget)
        
        # Output display
        layout.addWidget(QLabel("Output:"))
        
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.output_display)
        
        # Results display
        layout.addWidget(QLabel("Results:"))
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setMaximumHeight(150)
        layout.addWidget(self.results_display)
        
        tab_widget.addTab(exec_widget, "Execution")
    
    def setup_connections(self):
        """Setup signal connections"""
        # Scripting engine signals
        self.scripting_engine.script_registered.connect(self.update_script_list)
        self.scripting_engine.script_executed.connect(self.on_script_executed)
        self.scripting_engine.script_failed.connect(self.on_script_failed)
        
        # Button connections
        self.new_script_btn.clicked.connect(self.create_new_script)
        self.load_script_btn.clicked.connect(self.load_script)
        self.save_script_btn.clicked.connect(self.save_script)
        self.use_template_btn.clicked.connect(self.use_template)
        self.execute_btn.clicked.connect(self.execute_script)
        self.cancel_btn.clicked.connect(self.cancel_script)
        
        # Script list selection
        self.script_list.currentTextChanged.connect(self.on_script_selected)
        
        # Script editing
        self.script_name_edit.textChanged.connect(self.on_script_name_changed)
        self.code_editor.textChanged.connect(self.on_code_changed)
    
    def update_script_list(self):
        """Update the script list"""
        self.script_list.clear()
        scripts = self.scripting_engine.list_scripts()
        self.script_list.addItems(scripts)
    
    def update_template_list(self):
        """Update the template list"""
        self.template_list.clear()
        templates = self.scripting_engine.template_manager.list_templates()
        for template in templates:
            self.template_list.addItem(f"{template.name} ({template.script_type.value})")
    
    def create_new_script(self):
        """Create a new script"""
        import random
        script_id = f"script_{random.randint(1000, 9999)}"
        
        script = AutomationScript(script_id, f"New Script {script_id}")
        script.code = "# New automation script\n\nlog('Script started')\n\n# Add your code here\n\nlog('Script completed')\n"
        
        if self.scripting_engine.register_script(script):
            self.script_list.setCurrentRow(self.script_list.count() - 1)
    
    def load_script(self):
        """Load script from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Script", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            script_id = self.scripting_engine.load_script(file_path)
            if script_id:
                self.update_script_list()
                # Select the loaded script
                items = self.script_list.findItems(script_id, 0)
                if items:
                    self.script_list.setCurrentItem(items[0])
    
    def save_script(self):
        """Save current script to file"""
        if not self.current_script:
            QMessageBox.warning(self, "Warning", "No script selected")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", f"{self.current_script.name}.json", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.scripting_engine.save_script(self.current_script.script_id, file_path)
    
    def use_template(self):
        """Create script from template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template_text = current_item.text()
        template_name = template_text.split(' (')[0]
        
        # Find template by name
        templates = self.scripting_engine.template_manager.list_templates()
        template = None
        for t in templates:
            if t.name == template_name:
                template = t
                break
        
        if template:
            import random
            script_id = f"script_{random.randint(1000, 9999)}"
            script = self.scripting_engine.template_manager.create_script_from_template(
                template.template_id, script_id, f"{template.name} Script"
            )
            
            if script and self.scripting_engine.register_script(script):
                self.script_list.setCurrentRow(self.script_list.count() - 1)
    
    def execute_script(self):
        """Execute current script"""
        if not self.current_script:
            QMessageBox.warning(self, "Warning", "No script selected")
            return
        
        # Get parameter values from table
        parameters = {}
        for row in range(self.params_table.rowCount()):
            name_item = self.params_table.item(row, 0)
            value_item = self.params_table.item(row, 3)
            
            if name_item and value_item:
                name = name_item.text()
                value_text = value_item.text()
                
                # Find parameter definition for type conversion
                param_def = None
                for p in self.current_script.parameters:
                    if p.name == name:
                        param_def = p
                        break
                
                if param_def:
                    try:
                        if param_def.param_type == "int":
                            value = int(value_text)
                        elif param_def.param_type == "float":
                            value = float(value_text)
                        elif param_def.param_type == "bool":
                            value = value_text.lower() in ['true', '1', 'yes']
                        else:
                            value = value_text
                        
                        parameters[name] = value
                    except ValueError:
                        QMessageBox.warning(self, "Warning", f"Invalid value for parameter '{name}'")
                        return
        
        # Clear output
        self.output_display.clear()
        self.results_display.clear()
        self.progress_bar.setValue(0)
        
        # Execute script
        self.scripting_engine.execute_script(self.current_script.script_id, parameters)
    
    def cancel_script(self):
        """Cancel current script execution"""
        if self.current_script:
            self.scripting_engine.cancel_script(self.current_script.script_id)
    
    def on_script_selected(self, script_id: str):
        """Handle script selection"""
        if script_id and script_id in self.scripting_engine.scripts:
            self.current_script = self.scripting_engine.scripts[script_id]
            self.load_script_ui()
        else:
            self.current_script = None
    
    def load_script_ui(self):
        """Load script data into UI"""
        if not self.current_script:
            return
        
        # Update script info
        self.script_name_edit.setText(self.current_script.name)
        self.script_type_combo.setCurrentText(self.current_script.script_type.value)
        
        # Update code editor
        if QSCINTILLA_AVAILABLE:
            self.code_editor.setText(self.current_script.code)
        else:
            self.code_editor.setPlainText(self.current_script.code)
        
        # Update parameters table
        self.update_parameters_table()
    
    def update_parameters_table(self):
        """Update parameters table"""
        if not self.current_script:
            return
        
        self.params_table.setRowCount(len(self.current_script.parameters))
        
        for row, param in enumerate(self.current_script.parameters):
            self.params_table.setItem(row, 0, QTableWidgetItem(param.name))
            self.params_table.setItem(row, 1, QTableWidgetItem(param.param_type))
            self.params_table.setItem(row, 2, QTableWidgetItem(str(param.default_value)))
            self.params_table.setItem(row, 3, QTableWidgetItem(str(param.default_value)))
            self.params_table.setItem(row, 4, QTableWidgetItem(param.description))
        
        self.params_table.resizeColumnsToContents()
    
    def on_script_name_changed(self, name: str):
        """Handle script name change"""
        if self.current_script:
            self.current_script.name = name
    
    def on_code_changed(self):
        """Handle code change"""
        if self.current_script:
            if QSCINTILLA_AVAILABLE:
                self.current_script.code = self.code_editor.text()
            else:
                self.current_script.code = self.code_editor.toPlainText()
    
    def on_script_executed(self, script_id: str, result: ScriptResult):
        """Handle script execution completion"""
        if self.current_script and script_id == self.current_script.script_id:
            self.output_display.append(result.output)
            
            if result.return_value is not None:
                self.results_display.setText(json.dumps(result.return_value, indent=2))
            
            self.progress_bar.setValue(100)
    
    def on_script_failed(self, script_id: str, error: str):
        """Handle script execution failure"""
        if self.current_script and script_id == self.current_script.script_id:
            self.output_display.append(f"ERROR: {error}")
            self.progress_bar.setValue(0)
