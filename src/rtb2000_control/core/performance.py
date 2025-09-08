"""
Performance Monitoring and Optimization System for RTB2000
Advanced performance profiling, memory management, and optimization tools
"""

import time
import psutil
import gc
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import deque
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget
import numpy as np


@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    fps: float
    frame_time_ms: float
    active_threads: int
    waveform_points: int
    update_rate_hz: float


class PerformanceMonitor(QObject):
    """Real-time performance monitoring system"""
    
    metrics_updated = pyqtSignal(PerformanceMetrics)
    performance_warning = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Performance tracking
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 measurements
        self.frame_times = deque(maxlen=60)  # Last 60 frames for FPS calculation
        self.update_times = deque(maxlen=100)  # Update timing
        
        # Monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.collect_metrics)
        self.monitor_interval = 1000  # 1 second
        
        # Performance thresholds
        self.cpu_warning_threshold = 80.0  # %
        self.memory_warning_threshold = 85.0  # %
        self.fps_warning_threshold = 10.0  # FPS
        
        # Process reference
        self.process = psutil.Process()
        
        # Frame timing
        self.last_frame_time = time.time()
        self.frame_count = 0
        
        # Performance state
        self.monitoring_enabled = False
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_enabled = True
        self.monitor_timer.start(self.monitor_interval)
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_enabled = False
        self.monitor_timer.stop()
        
    def record_frame(self):
        """Record frame timing for FPS calculation"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        self.last_frame_time = current_time
        self.frame_count += 1
        
    def record_update_time(self, update_time: float):
        """Record update operation timing"""
        self.update_times.append(update_time)
        
    def collect_metrics(self):
        """Collect comprehensive performance metrics"""
        try:
            current_time = time.time()
            
            # CPU and Memory metrics
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            memory_percent = self.process.memory_percent()
            
            # Threading metrics
            active_threads = threading.active_count()
            
            # FPS calculation
            fps = self.calculate_fps()
            frame_time_ms = self.calculate_average_frame_time() * 1000
            
            # Update rate calculation
            update_rate_hz = self.calculate_update_rate()
            
            # Waveform metrics (estimated)
            waveform_points = self.estimate_waveform_points()
            
            # Create metrics object
            metrics = PerformanceMetrics(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                fps=fps,
                frame_time_ms=frame_time_ms,
                active_threads=active_threads,
                waveform_points=waveform_points,
                update_rate_hz=update_rate_hz
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Check for performance warnings
            self.check_performance_warnings(metrics)
            
            # Emit metrics update
            self.metrics_updated.emit(metrics)
            
        except Exception as e:
            print(f"Error collecting performance metrics: {e}")
            
    def calculate_fps(self) -> float:
        """Calculate current FPS"""
        if len(self.frame_times) < 2:
            return 0.0
            
        # Average frame time over last frames
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return 0.0
        
    def calculate_average_frame_time(self) -> float:
        """Calculate average frame time"""
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)
        
    def calculate_update_rate(self) -> float:
        """Calculate update rate in Hz"""
        if len(self.update_times) < 2:
            return 0.0
            
        # Calculate rate based on recent updates
        recent_updates = list(self.update_times)[-10:]  # Last 10 updates
        if len(recent_updates) >= 2:
            time_span = recent_updates[-1] - recent_updates[0]
            if time_span > 0:
                return (len(recent_updates) - 1) / time_span
        return 0.0
        
    def estimate_waveform_points(self) -> int:
        """Estimate current waveform data points"""
        # This would be updated by the waveform widget
        # For now, return estimated value
        return 4000  # 4 channels × 1000 points each
        
    def check_performance_warnings(self, metrics: PerformanceMetrics):
        """Check for performance issues and emit warnings"""
        if metrics.cpu_percent > self.cpu_warning_threshold:
            self.performance_warning.emit(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if metrics.memory_percent > self.memory_warning_threshold:
            self.performance_warning.emit(f"High memory usage: {metrics.memory_percent:.1f}%")
            
        if metrics.fps < self.fps_warning_threshold and metrics.fps > 0:
            self.performance_warning.emit(f"Low FPS: {metrics.fps:.1f}")
            
    def get_performance_summary(self) -> Dict:
        """Get performance summary statistics"""
        if not self.metrics_history:
            return {}
            
        recent_metrics = list(self.metrics_history)[-60:]  # Last minute
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_mb for m in recent_metrics]
        fps_values = [m.fps for m in recent_metrics if m.fps > 0]
        
        return {
            'cpu_avg': np.mean(cpu_values) if cpu_values else 0,
            'cpu_max': np.max(cpu_values) if cpu_values else 0,
            'memory_avg': np.mean(memory_values) if memory_values else 0,
            'memory_max': np.max(memory_values) if memory_values else 0,
            'fps_avg': np.mean(fps_values) if fps_values else 0,
            'fps_min': np.min(fps_values) if fps_values else 0,
            'sample_count': len(recent_metrics)
        }


class MemoryOptimizer:
    """Memory optimization and management system"""
    
    def __init__(self):
        self.optimization_enabled = True
        self.gc_threshold = 100  # MB
        self.last_gc_time = time.time()
        self.gc_interval = 30.0  # seconds
        
    def optimize_memory(self) -> Dict:
        """Perform memory optimization"""
        if not self.optimization_enabled:
            return {}
            
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear numpy cache if possible
        try:
            np.set_printoptions(threshold=1000)  # Limit numpy print cache
        except:
            pass
            
        end_time = time.time()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        optimization_time = (end_time - start_time) * 1000  # ms
        memory_freed = initial_memory - final_memory
        
        self.last_gc_time = end_time
        
        return {
            'objects_collected': collected,
            'memory_freed_mb': memory_freed,
            'optimization_time_ms': optimization_time,
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory
        }
        
    def should_optimize(self) -> bool:
        """Check if memory optimization should be performed"""
        current_time = time.time()
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Time-based optimization
        if current_time - self.last_gc_time > self.gc_interval:
            return True
            
        # Memory threshold-based optimization
        if current_memory > self.gc_threshold:
            return True
            
        return False
        
    def auto_optimize(self) -> Optional[Dict]:
        """Automatically optimize memory if needed"""
        if self.should_optimize():
            return self.optimize_memory()
        return None


class CPUOptimizer:
    """CPU usage optimization system"""
    
    def __init__(self):
        self.adaptive_fps_enabled = True
        self.min_fps = 10
        self.max_fps = 60
        self.target_cpu = 70.0  # Target CPU usage %
        self.current_fps_limit = 30
        
    def optimize_cpu_usage(self, current_cpu: float, current_fps: float) -> int:
        """Optimize CPU usage by adjusting FPS limit"""
        if not self.adaptive_fps_enabled:
            return self.current_fps_limit
            
        # Adaptive FPS based on CPU usage
        if current_cpu > self.target_cpu:
            # Reduce FPS to save CPU
            new_fps = max(self.min_fps, self.current_fps_limit - 5)
        elif current_cpu < self.target_cpu * 0.8:
            # Increase FPS if CPU has headroom
            new_fps = min(self.max_fps, self.current_fps_limit + 2)
        else:
            # Keep current FPS
            new_fps = self.current_fps_limit
            
        self.current_fps_limit = new_fps
        return new_fps
        
    def get_recommended_update_interval(self) -> int:
        """Get recommended update interval in milliseconds"""
        return int(1000 / self.current_fps_limit)


class PerformanceOptimizer(QObject):
    """Comprehensive performance optimization system"""
    
    optimization_performed = pyqtSignal(dict)
    fps_limit_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        # Sub-optimizers
        self.memory_optimizer = MemoryOptimizer()
        self.cpu_optimizer = CPUOptimizer()
        self.monitor = PerformanceMonitor()
        
        # Optimization timer
        self.optimization_timer = QTimer()
        self.optimization_timer.timeout.connect(self.perform_optimization)
        self.optimization_interval = 5000  # 5 seconds
        
        # Performance state
        self.optimization_enabled = True
        self.adaptive_optimization = True
        
        # Connect monitor signals
        self.monitor.metrics_updated.connect(self.on_metrics_updated)
        
    def start_optimization(self):
        """Start performance optimization system"""
        self.monitor.start_monitoring()
        if self.optimization_enabled:
            self.optimization_timer.start(self.optimization_interval)
            
    def stop_optimization(self):
        """Stop performance optimization system"""
        self.monitor.stop_monitoring()
        self.optimization_timer.stop()
        
    def on_metrics_updated(self, metrics: PerformanceMetrics):
        """Handle updated performance metrics"""
        if not self.adaptive_optimization:
            return
            
        # Adaptive CPU optimization
        new_fps_limit = self.cpu_optimizer.optimize_cpu_usage(
            metrics.cpu_percent, metrics.fps
        )
        
        # Emit FPS limit change if needed
        current_interval = self.cpu_optimizer.get_recommended_update_interval()
        self.fps_limit_changed.emit(current_interval)
        
    def perform_optimization(self):
        """Perform comprehensive optimization"""
        optimization_results = {}
        
        try:
            # Memory optimization
            memory_result = self.memory_optimizer.auto_optimize()
            if memory_result:
                optimization_results['memory'] = memory_result
                
            # Get current performance summary
            performance_summary = self.monitor.get_performance_summary()
            optimization_results['performance_summary'] = performance_summary
            
            # Emit optimization results
            if optimization_results:
                self.optimization_performed.emit(optimization_results)
                
        except Exception as e:
            print(f"Error during performance optimization: {e}")
            
    def force_optimization(self) -> Dict:
        """Force immediate comprehensive optimization"""
        results = {}
        
        # Force memory optimization
        memory_result = self.memory_optimizer.optimize_memory()
        results['memory'] = memory_result
        
        # Get performance metrics
        performance_summary = self.monitor.get_performance_summary()
        results['performance_summary'] = performance_summary
        
        return results
        
    def get_optimization_settings(self) -> Dict:
        """Get current optimization settings"""
        return {
            'optimization_enabled': self.optimization_enabled,
            'adaptive_optimization': self.adaptive_optimization,
            'memory_gc_threshold': self.memory_optimizer.gc_threshold,
            'cpu_target': self.cpu_optimizer.target_cpu,
            'fps_range': (self.cpu_optimizer.min_fps, self.cpu_optimizer.max_fps),
            'current_fps_limit': self.cpu_optimizer.current_fps_limit
        }
        
    def update_optimization_settings(self, settings: Dict):
        """Update optimization settings"""
        if 'optimization_enabled' in settings:
            self.optimization_enabled = settings['optimization_enabled']
            
        if 'adaptive_optimization' in settings:
            self.adaptive_optimization = settings['adaptive_optimization']
            
        if 'memory_gc_threshold' in settings:
            self.memory_optimizer.gc_threshold = settings['memory_gc_threshold']
            
        if 'cpu_target' in settings:
            self.cpu_optimizer.target_cpu = settings['cpu_target']
    
    def set_auto_optimization(self, enabled: bool):
        """Enable or disable automatic optimization"""
        self.optimization_enabled = enabled
        self.adaptive_optimization = enabled
        
        if enabled:
            self.optimization_timer.start(self.optimization_interval)
        else:
            self.optimization_timer.stop()
    
    def optimize_performance(self):
        """Run comprehensive performance optimization"""
        return self.force_optimization()
    
    def get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        metrics = self.monitor.get_performance_summary()
        metrics['optimization_level'] = self.get_optimization_level()
        metrics['auto_optimization'] = self.optimization_enabled
        return metrics
    
    def get_optimization_level(self) -> str:
        """Get current optimization level based on performance"""
        summary = self.monitor.get_performance_summary()
        cpu_percent = summary.get('cpu_percent', 0)
        memory_percent = summary.get('memory_percent', 0)
        
        if cpu_percent > 80 or memory_percent > 80:
            return "Aggressive"
        elif cpu_percent > 60 or memory_percent > 60:
            return "Balanced"
        else:
            return "Standard"
