#!/usr/bin/env python3
"""
RTB2000 Automation Engine Module
===============================

Advanced automation capabilities for measurement routines:
- Programmable measurement sequences
- Conditional measurement logic
- Multi-step measurement workflows
- Results validation and reporting
"""

import time
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QPushButton, QTextEdit, QProgressBar,
                            QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
                            QTableWidget, QTableWidgetItem, QTabWidget)
from typing import Dict, List, Any, Optional, Callable, Union
import logging
from dataclasses import dataclass, field
from enum import Enum
import json


class SequenceStatus(Enum):
    """Status of measurement sequence"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(Enum):
    """Types of measurement steps"""
    MEASUREMENT = "measurement"
    DELAY = "delay"
    CONDITION = "condition"
    SET_PARAMETER = "set_parameter"
    TRIGGER_SETUP = "trigger_setup"
    DATA_ACQUISITION = "data_acquisition"
    ANALYSIS = "analysis"
    EXPORT = "export"


@dataclass
class MeasurementStep:
    """Single step in a measurement sequence"""
    step_id: str
    step_type: StepType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0  # seconds
    retry_count: int = 0
    enabled: bool = True
    description: str = ""


@dataclass
class SequenceResult:
    """Result of a measurement sequence execution"""
    sequence_id: str
    status: SequenceStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    step_results: Dict[str, Any] = field(default_factory=dict)


class MeasurementSequence(QObject):
    """Programmable measurement sequence"""
    
    # Signals
    sequence_started = pyqtSignal(str)  # sequence_id
    sequence_completed = pyqtSignal(object)  # SequenceResult
    sequence_failed = pyqtSignal(str, str)  # sequence_id, error
    step_started = pyqtSignal(str, object)  # sequence_id, MeasurementStep
    step_completed = pyqtSignal(str, str, object)  # sequence_id, step_id, result
    step_failed = pyqtSignal(str, str, str)  # sequence_id, step_id, error
    progress_updated = pyqtSignal(str, int)  # sequence_id, percentage
    
    def __init__(self, sequence_id: str, name: str = ""):
        super().__init__()
        self.sequence_id = sequence_id
        self.name = name or sequence_id
        self.logger = logging.getLogger(__name__)
        
        # Sequence configuration
        self.steps: List[MeasurementStep] = []
        self.variables: Dict[str, Any] = {}
        self.global_timeout = 300.0  # 5 minutes default
        
        # Execution state
        self.status = SequenceStatus.IDLE
        self.current_step_index = 0
        self.result: Optional[SequenceResult] = None
        self.execution_thread: Optional[QThread] = None
        
        # Automation dependencies
        self.oscilloscope = None
        self.measurement_engine = None
        self.analysis_engine = None
        
        self.logger.info(f"Measurement sequence '{self.name}' created")
    
    def add_step(self, step: MeasurementStep) -> None:
        """Add a step to the sequence"""
        self.steps.append(step)
        self.logger.debug(f"Added step '{step.name}' to sequence '{self.name}'")
    
    def add_measurement_step(self, name: str, measurement_type: str, 
                           channel: str = "CH1", **kwargs) -> MeasurementStep:
        """Add a measurement step"""
        step_id = f"meas_{len(self.steps)}"
        parameters = {
            'measurement_type': measurement_type,
            'channel': channel,
            **kwargs
        }
        
        step = MeasurementStep(
            step_id=step_id,
            step_type=StepType.MEASUREMENT,
            name=name,
            parameters=parameters
        )
        
        self.add_step(step)
        return step
    
    def add_delay_step(self, name: str, delay_seconds: float) -> MeasurementStep:
        """Add a delay step"""
        step_id = f"delay_{len(self.steps)}"
        parameters = {'delay': delay_seconds}
        
        step = MeasurementStep(
            step_id=step_id,
            step_type=StepType.DELAY,
            name=name,
            parameters=parameters
        )
        
        self.add_step(step)
        return step
    
    def add_condition_step(self, name: str, condition: str, 
                          action: str = "continue") -> MeasurementStep:
        """Add a conditional step"""
        step_id = f"cond_{len(self.steps)}"
        parameters = {
            'condition': condition,
            'action': action  # continue, skip, abort, repeat
        }
        
        step = MeasurementStep(
            step_id=step_id,
            step_type=StepType.CONDITION,
            name=name,
            parameters=parameters
        )
        
        self.add_step(step)
        return step
    
    def add_parameter_step(self, name: str, parameter: str, 
                         value: Any, channel: str = "CH1") -> MeasurementStep:
        """Add a parameter setting step"""
        step_id = f"param_{len(self.steps)}"
        parameters = {
            'parameter': parameter,
            'value': value,
            'channel': channel
        }
        
        step = MeasurementStep(
            step_id=step_id,
            step_type=StepType.SET_PARAMETER,
            name=name,
            parameters=parameters
        )
        
        self.add_step(step)
        return step
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a sequence variable"""
        self.variables[name] = value
        self.logger.debug(f"Set variable '{name}' = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a sequence variable"""
        return self.variables.get(name, default)
    
    def start_execution(self) -> bool:
        """Start sequence execution"""
        try:
            if self.status != SequenceStatus.IDLE:
                raise ValueError(f"Sequence is not idle (current status: {self.status})")
            
            if not self.steps:
                raise ValueError("No steps defined in sequence")
            
            # Initialize result
            self.result = SequenceResult(
                sequence_id=self.sequence_id,
                status=SequenceStatus.RUNNING,
                start_time=datetime.now()
            )
            
            self.status = SequenceStatus.RUNNING
            self.current_step_index = 0
            
            # Start execution in separate thread
            self.execution_thread = SequenceExecutionThread(self)
            self.execution_thread.step_completed.connect(self._on_step_completed)
            self.execution_thread.step_failed.connect(self._on_step_failed)
            self.execution_thread.sequence_completed.connect(self._on_sequence_completed)
            self.execution_thread.sequence_failed.connect(self._on_sequence_failed)
            self.execution_thread.start()
            
            self.sequence_started.emit(self.sequence_id)
            self.logger.info(f"Started execution of sequence '{self.name}'")
            return True
            
        except Exception as e:
            error_msg = f"Failed to start sequence: {e}"
            self.logger.error(error_msg)
            self.sequence_failed.emit(self.sequence_id, error_msg)
            return False
    
    def pause_execution(self) -> bool:
        """Pause sequence execution"""
        if self.status == SequenceStatus.RUNNING:
            self.status = SequenceStatus.PAUSED
            if self.execution_thread:
                self.execution_thread.pause()
            self.logger.info(f"Paused sequence '{self.name}'")
            return True
        return False
    
    def resume_execution(self) -> bool:
        """Resume sequence execution"""
        if self.status == SequenceStatus.PAUSED:
            self.status = SequenceStatus.RUNNING
            if self.execution_thread:
                self.execution_thread.resume()
            self.logger.info(f"Resumed sequence '{self.name}'")
            return True
        return False
    
    def cancel_execution(self) -> bool:
        """Cancel sequence execution"""
        if self.status in [SequenceStatus.RUNNING, SequenceStatus.PAUSED]:
            self.status = SequenceStatus.CANCELLED
            if self.execution_thread:
                self.execution_thread.cancel()
            self.logger.info(f"Cancelled sequence '{self.name}'")
            return True
        return False
    
    def _on_step_completed(self, step_id: str, result: Any):
        """Handle step completion"""
        if self.result:
            self.result.step_results[step_id] = result
        
        self.step_completed.emit(self.sequence_id, step_id, result)
        
        # Update progress
        progress = int(((self.current_step_index + 1) / len(self.steps)) * 100)
        self.progress_updated.emit(self.sequence_id, progress)
        
        self.current_step_index += 1
    
    def _on_step_failed(self, step_id: str, error: str):
        """Handle step failure"""
        if self.result:
            self.result.errors.append(f"Step {step_id}: {error}")
        
        self.step_failed.emit(self.sequence_id, step_id, error)
        
        # Decide whether to continue or abort based on step configuration
        # For now, abort on any error
        self._on_sequence_failed(f"Step {step_id} failed: {error}")
    
    def _on_sequence_completed(self):
        """Handle sequence completion"""
        if self.result:
            self.result.status = SequenceStatus.COMPLETED
            self.result.end_time = datetime.now()
        
        self.status = SequenceStatus.COMPLETED
        self.sequence_completed.emit(self.result)
        self.logger.info(f"Completed sequence '{self.name}'")
    
    def _on_sequence_failed(self, error: str):
        """Handle sequence failure"""
        if self.result:
            self.result.status = SequenceStatus.FAILED
            self.result.end_time = datetime.now()
            self.result.errors.append(error)
        
        self.status = SequenceStatus.FAILED
        self.sequence_failed.emit(self.sequence_id, error)
        self.logger.error(f"Sequence '{self.name}' failed: {error}")
    
    def get_progress(self) -> int:
        """Get current progress percentage"""
        if not self.steps:
            return 0
        return int((self.current_step_index / len(self.steps)) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sequence to dictionary for serialization"""
        return {
            'sequence_id': self.sequence_id,
            'name': self.name,
            'steps': [
                {
                    'step_id': step.step_id,
                    'step_type': step.step_type.value,
                    'name': step.name,
                    'parameters': step.parameters,
                    'conditions': step.conditions,
                    'timeout': step.timeout,
                    'retry_count': step.retry_count,
                    'enabled': step.enabled,
                    'description': step.description
                }
                for step in self.steps
            ],
            'variables': self.variables,
            'global_timeout': self.global_timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeasurementSequence':
        """Create sequence from dictionary"""
        sequence = cls(data['sequence_id'], data.get('name', ''))
        sequence.variables = data.get('variables', {})
        sequence.global_timeout = data.get('global_timeout', 300.0)
        
        for step_data in data.get('steps', []):
            step = MeasurementStep(
                step_id=step_data['step_id'],
                step_type=StepType(step_data['step_type']),
                name=step_data['name'],
                parameters=step_data.get('parameters', {}),
                conditions=step_data.get('conditions', {}),
                timeout=step_data.get('timeout', 30.0),
                retry_count=step_data.get('retry_count', 0),
                enabled=step_data.get('enabled', True),
                description=step_data.get('description', '')
            )
            sequence.add_step(step)
        
        return sequence


class SequenceExecutionThread(QThread):
    """Thread for executing measurement sequences"""
    
    step_completed = pyqtSignal(str, object)  # step_id, result
    step_failed = pyqtSignal(str, str)  # step_id, error
    sequence_completed = pyqtSignal()
    sequence_failed = pyqtSignal(str)  # error
    
    def __init__(self, sequence: MeasurementSequence):
        super().__init__()
        self.sequence = sequence
        self.logger = logging.getLogger(__name__)
        self.paused = False
        self.cancelled = False
    
    def run(self):
        """Execute the sequence"""
        try:
            for i, step in enumerate(self.sequence.steps):
                if self.cancelled:
                    break
                
                # Wait if paused
                while self.paused and not self.cancelled:
                    self.msleep(100)
                
                if self.cancelled:
                    break
                
                if not step.enabled:
                    continue
                
                # Execute step
                self.sequence.step_started.emit(self.sequence.sequence_id, step)
                
                try:
                    result = self.execute_step(step)
                    self.step_completed.emit(step.step_id, result)
                except Exception as e:
                    error_msg = str(e)
                    self.step_failed.emit(step.step_id, error_msg)
                    return  # Stop execution on error
            
            if not self.cancelled:
                self.sequence_completed.emit()
            
        except Exception as e:
            self.sequence_failed.emit(str(e))
    
    def execute_step(self, step: MeasurementStep) -> Any:
        """Execute a single step"""
        self.logger.debug(f"Executing step: {step.name}")
        
        if step.step_type == StepType.MEASUREMENT:
            return self.execute_measurement_step(step)
        elif step.step_type == StepType.DELAY:
            return self.execute_delay_step(step)
        elif step.step_type == StepType.CONDITION:
            return self.execute_condition_step(step)
        elif step.step_type == StepType.SET_PARAMETER:
            return self.execute_parameter_step(step)
        elif step.step_type == StepType.TRIGGER_SETUP:
            return self.execute_trigger_step(step)
        elif step.step_type == StepType.DATA_ACQUISITION:
            return self.execute_acquisition_step(step)
        else:
            raise ValueError(f"Unknown step type: {step.step_type}")
    
    def execute_measurement_step(self, step: MeasurementStep) -> Any:
        """Execute a measurement step"""
        measurement_type = step.parameters.get('measurement_type')
        channel = step.parameters.get('channel', 'CH1')
        
        # Simulate measurement execution
        # In real implementation, this would call the measurement engine
        self.msleep(500)  # Simulate measurement time
        
        # Return simulated result
        return {
            'measurement_type': measurement_type,
            'channel': channel,
            'value': np.random.random(),
            'unit': 'V',
            'timestamp': datetime.now().isoformat()
        }
    
    def execute_delay_step(self, step: MeasurementStep) -> Any:
        """Execute a delay step"""
        delay = step.parameters.get('delay', 1.0)
        self.msleep(int(delay * 1000))
        return {'delay': delay, 'completed': True}
    
    def execute_condition_step(self, step: MeasurementStep) -> Any:
        """Execute a condition step"""
        condition = step.parameters.get('condition', 'True')
        action = step.parameters.get('action', 'continue')
        
        # Simple condition evaluation (in real implementation, this would be more sophisticated)
        result = eval(condition, {'__builtins__': {}}, self.sequence.variables)
        
        return {
            'condition': condition,
            'result': result,
            'action': action
        }
    
    def execute_parameter_step(self, step: MeasurementStep) -> Any:
        """Execute a parameter setting step"""
        parameter = step.parameters.get('parameter')
        value = step.parameters.get('value')
        channel = step.parameters.get('channel', 'CH1')
        
        # Simulate parameter setting
        self.msleep(100)
        
        return {
            'parameter': parameter,
            'value': value,
            'channel': channel,
            'success': True
        }
    
    def execute_trigger_step(self, step: MeasurementStep) -> Any:
        """Execute a trigger setup step"""
        # Simulate trigger setup
        self.msleep(200)
        return {'trigger_setup': step.parameters, 'success': True}
    
    def execute_acquisition_step(self, step: MeasurementStep) -> Any:
        """Execute a data acquisition step"""
        # Simulate data acquisition
        self.msleep(1000)
        return {
            'data_acquired': True,
            'points': step.parameters.get('points', 1000),
            'timestamp': datetime.now().isoformat()
        }
    
    def pause(self):
        """Pause execution"""
        self.paused = True
    
    def resume(self):
        """Resume execution"""
        self.paused = False
    
    def cancel(self):
        """Cancel execution"""
        self.cancelled = True
        self.paused = False


class AutomationEngine(QObject):
    """Main automation engine for managing sequences"""
    
    # Signals
    sequence_registered = pyqtSignal(str)  # sequence_id
    sequence_started = pyqtSignal(str)  # sequence_id
    sequence_completed = pyqtSignal(str, object)  # sequence_id, result
    sequence_failed = pyqtSignal(str, str)  # sequence_id, error
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Sequence management
        self.sequences: Dict[str, MeasurementSequence] = {}
        self.active_sequences: Dict[str, MeasurementSequence] = {}
        
        # Automation dependencies
        self.oscilloscope = None
        self.measurement_engine = None
        self.analysis_engine = None
        
        self.logger.info("Automation Engine initialized")
    
    def register_sequence(self, sequence: MeasurementSequence) -> bool:
        """Register a measurement sequence"""
        try:
            if sequence.sequence_id in self.sequences:
                raise ValueError(f"Sequence '{sequence.sequence_id}' already registered")
            
            # Connect sequence signals
            sequence.sequence_started.connect(self._on_sequence_started)
            sequence.sequence_completed.connect(self._on_sequence_completed)
            sequence.sequence_failed.connect(self._on_sequence_failed)
            
            # Set dependencies
            sequence.oscilloscope = self.oscilloscope
            sequence.measurement_engine = self.measurement_engine
            sequence.analysis_engine = self.analysis_engine
            
            self.sequences[sequence.sequence_id] = sequence
            self.sequence_registered.emit(sequence.sequence_id)
            
            self.logger.info(f"Registered sequence '{sequence.name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register sequence: {e}")
            return False
    
    def start_sequence(self, sequence_id: str) -> bool:
        """Start a sequence"""
        try:
            if sequence_id not in self.sequences:
                raise ValueError(f"Sequence '{sequence_id}' not found")
            
            sequence = self.sequences[sequence_id]
            if sequence.start_execution():
                self.active_sequences[sequence_id] = sequence
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start sequence '{sequence_id}': {e}")
            return False
    
    def pause_sequence(self, sequence_id: str) -> bool:
        """Pause a sequence"""
        if sequence_id in self.active_sequences:
            return self.active_sequences[sequence_id].pause_execution()
        return False
    
    def resume_sequence(self, sequence_id: str) -> bool:
        """Resume a sequence"""
        if sequence_id in self.active_sequences:
            return self.active_sequences[sequence_id].resume_execution()
        return False
    
    def cancel_sequence(self, sequence_id: str) -> bool:
        """Cancel a sequence"""
        if sequence_id in self.active_sequences:
            result = self.active_sequences[sequence_id].cancel_execution()
            if result:
                del self.active_sequences[sequence_id]
            return result
        return False
    
    def get_sequence_status(self, sequence_id: str) -> Optional[SequenceStatus]:
        """Get sequence status"""
        if sequence_id in self.sequences:
            return self.sequences[sequence_id].status
        return None
    
    def get_sequence_progress(self, sequence_id: str) -> int:
        """Get sequence progress"""
        if sequence_id in self.sequences:
            return self.sequences[sequence_id].get_progress()
        return 0
    
    def list_sequences(self) -> List[str]:
        """List all registered sequences"""
        return list(self.sequences.keys())
    
    def list_active_sequences(self) -> List[str]:
        """List active sequences"""
        return list(self.active_sequences.keys())
    
    def save_sequence(self, sequence_id: str, file_path: str) -> bool:
        """Save sequence to file"""
        try:
            if sequence_id not in self.sequences:
                raise ValueError(f"Sequence '{sequence_id}' not found")
            
            sequence = self.sequences[sequence_id]
            with open(file_path, 'w') as f:
                json.dump(sequence.to_dict(), f, indent=2)
            
            self.logger.info(f"Saved sequence '{sequence_id}' to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save sequence: {e}")
            return False
    
    def load_sequence(self, file_path: str) -> Optional[str]:
        """Load sequence from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            sequence = MeasurementSequence.from_dict(data)
            if self.register_sequence(sequence):
                self.logger.info(f"Loaded sequence '{sequence.sequence_id}' from {file_path}")
                return sequence.sequence_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load sequence: {e}")
            return None
    
    def _on_sequence_started(self, sequence_id: str):
        """Handle sequence started"""
        self.sequence_started.emit(sequence_id)
    
    def _on_sequence_completed(self, result: SequenceResult):
        """Handle sequence completed"""
        sequence_id = result.sequence_id
        if sequence_id in self.active_sequences:
            del self.active_sequences[sequence_id]
        self.sequence_completed.emit(sequence_id, result)
    
    def _on_sequence_failed(self, sequence_id: str, error: str):
        """Handle sequence failed"""
        if sequence_id in self.active_sequences:
            del self.active_sequences[sequence_id]
        self.sequence_failed.emit(sequence_id, error)


class AutomationWidget(QWidget):
    """Widget for automation control"""
    
    def __init__(self, automation_engine: AutomationEngine):
        super().__init__()
        self.automation_engine = automation_engine
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the automation UI"""
        layout = QVBoxLayout(self)
        
        # Create tabs for different automation features
        tab_widget = QTabWidget()
        
        # Sequence Management tab
        sequence_tab = QWidget()
        self.setup_sequence_tab(sequence_tab)
        tab_widget.addTab(sequence_tab, "Sequences")
        
        # Sequence Builder tab
        builder_tab = QWidget()
        self.setup_builder_tab(builder_tab)
        tab_widget.addTab(builder_tab, "Builder")
        
        # Execution Monitor tab
        monitor_tab = QWidget()
        self.setup_monitor_tab(monitor_tab)
        tab_widget.addTab(monitor_tab, "Monitor")
        
        layout.addWidget(tab_widget)
    
    def setup_sequence_tab(self, parent):
        """Setup sequence management tab"""
        layout = QVBoxLayout(parent)
        
        # Sequence list
        list_layout = QHBoxLayout()
        list_layout.addWidget(QLabel("Available Sequences:"))
        
        self.sequence_list = QListWidget()
        list_layout.addWidget(self.sequence_list)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("Start")
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        button_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Resume")
        button_layout.addWidget(self.resume_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.load_btn = QPushButton("Load...")
        button_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("Save...")
        button_layout.addWidget(self.save_btn)
        
        list_layout.addLayout(button_layout)
        layout.addLayout(list_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
    
    def setup_builder_tab(self, parent):
        """Setup sequence builder tab"""
        layout = QVBoxLayout(parent)
        
        # Sequence info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Sequence Name:"))
        
        self.sequence_name_edit = QTextEdit()
        self.sequence_name_edit.setMaximumHeight(30)
        info_layout.addWidget(self.sequence_name_edit)
        
        layout.addLayout(info_layout)
        
        # Step builder
        builder_layout = QHBoxLayout()
        
        # Step type selection
        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("Step Type:"))
        
        self.step_type_combo = QComboBox()
        self.step_type_combo.addItems([
            "Measurement", "Delay", "Condition", "Set Parameter"
        ])
        type_layout.addWidget(self.step_type_combo)
        
        self.add_step_btn = QPushButton("Add Step")
        type_layout.addWidget(self.add_step_btn)
        
        builder_layout.addLayout(type_layout)
        
        # Step list
        self.step_table = QTableWidget()
        self.step_table.setColumnCount(4)
        self.step_table.setHorizontalHeaderLabels(['Type', 'Name', 'Parameters', 'Enabled'])
        builder_layout.addWidget(self.step_table)
        
        layout.addLayout(builder_layout)
        
        # Builder controls
        control_layout = QHBoxLayout()
        
        self.create_sequence_btn = QPushButton("Create Sequence")
        control_layout.addWidget(self.create_sequence_btn)
        
        self.clear_builder_btn = QPushButton("Clear")
        control_layout.addWidget(self.clear_builder_btn)
        
        layout.addLayout(control_layout)
    
    def setup_monitor_tab(self, parent):
        """Setup execution monitor tab"""
        layout = QVBoxLayout(parent)
        
        # Active sequences
        layout.addWidget(QLabel("Active Sequences:"))
        
        self.active_table = QTableWidget()
        self.active_table.setColumnCount(4)
        self.active_table.setHorizontalHeaderLabels(['Sequence', 'Status', 'Progress', 'Started'])
        layout.addWidget(self.active_table)
        
        # Detailed log
        layout.addWidget(QLabel("Execution Log:"))
        
        self.execution_log = QTextEdit()
        self.execution_log.setReadOnly(True)
        layout.addWidget(self.execution_log)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Automation engine signals
        self.automation_engine.sequence_registered.connect(self.update_sequence_list)
        self.automation_engine.sequence_started.connect(self.on_sequence_started)
        self.automation_engine.sequence_completed.connect(self.on_sequence_completed)
        self.automation_engine.sequence_failed.connect(self.on_sequence_failed)
        
        # Button connections
        self.start_btn.clicked.connect(self.start_selected_sequence)
        self.pause_btn.clicked.connect(self.pause_selected_sequence)
        self.resume_btn.clicked.connect(self.resume_selected_sequence)
        self.cancel_btn.clicked.connect(self.cancel_selected_sequence)
        
        # Update sequence list initially
        self.update_sequence_list()
    
    def update_sequence_list(self):
        """Update the sequence list"""
        self.sequence_list.clear()
        sequences = self.automation_engine.list_sequences()
        self.sequence_list.addItems(sequences)
    
    def start_selected_sequence(self):
        """Start the selected sequence"""
        current_item = self.sequence_list.currentItem()
        if current_item:
            sequence_id = current_item.text()
            if self.automation_engine.start_sequence(sequence_id):
                self.status_text.append(f"Started sequence: {sequence_id}")
            else:
                self.status_text.append(f"Failed to start sequence: {sequence_id}")
    
    def pause_selected_sequence(self):
        """Pause the selected sequence"""
        current_item = self.sequence_list.currentItem()
        if current_item:
            sequence_id = current_item.text()
            if self.automation_engine.pause_sequence(sequence_id):
                self.status_text.append(f"Paused sequence: {sequence_id}")
    
    def resume_selected_sequence(self):
        """Resume the selected sequence"""
        current_item = self.sequence_list.currentItem()
        if current_item:
            sequence_id = current_item.text()
            if self.automation_engine.resume_sequence(sequence_id):
                self.status_text.append(f"Resumed sequence: {sequence_id}")
    
    def cancel_selected_sequence(self):
        """Cancel the selected sequence"""
        current_item = self.sequence_list.currentItem()
        if current_item:
            sequence_id = current_item.text()
            if self.automation_engine.cancel_sequence(sequence_id):
                self.status_text.append(f"Cancelled sequence: {sequence_id}")
    
    def on_sequence_started(self, sequence_id: str):
        """Handle sequence started"""
        self.status_text.append(f"Sequence started: {sequence_id}")
        self.update_active_sequences()
    
    def on_sequence_completed(self, sequence_id: str, result: SequenceResult):
        """Handle sequence completed"""
        self.status_text.append(f"Sequence completed: {sequence_id}")
        self.update_active_sequences()
    
    def on_sequence_failed(self, sequence_id: str, error: str):
        """Handle sequence failed"""
        self.status_text.append(f"Sequence failed: {sequence_id} - {error}")
        self.update_active_sequences()
    
    def update_active_sequences(self):
        """Update active sequences table"""
        active_sequences = self.automation_engine.list_active_sequences()
        
        self.active_table.setRowCount(len(active_sequences))
        
        for row, sequence_id in enumerate(active_sequences):
            status = self.automation_engine.get_sequence_status(sequence_id)
            progress = self.automation_engine.get_sequence_progress(sequence_id)
            
            self.active_table.setItem(row, 0, QTableWidgetItem(sequence_id))
            self.active_table.setItem(row, 1, QTableWidgetItem(status.value if status else "Unknown"))
            self.active_table.setItem(row, 2, QTableWidgetItem(f"{progress}%"))
            self.active_table.setItem(row, 3, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        
        self.active_table.resizeColumnsToContents()
