"""
Professional Icon System for RTB2000 Application
SVG-based scalable icons with consistent design language
"""

import base64
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QByteArray, Qt

class IconManager:
    """Manages application icons with SVG support"""
    
    # SVG Icons as base64 encoded strings
    ICONS = {
        # Connection Icons
        "connect": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 1L15 8L8 15L1 8L8 1Z" stroke="#4CAF50" stroke-width="2" fill="#4CAF50" fill-opacity="0.2"/>
            <circle cx="8" cy="8" r="3" fill="#4CAF50"/>
        </svg>""",
        
        "disconnect": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 1L15 8L8 15L1 8L8 1Z" stroke="#F44336" stroke-width="2" fill="#F44336" fill-opacity="0.2"/>
            <line x1="5" y1="5" x2="11" y2="11" stroke="#F44336" stroke-width="2"/>
            <line x1="11" y1="5" x2="5" y2="11" stroke="#F44336" stroke-width="2"/>
        </svg>""",
        
        # Acquisition Icons
        "run": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polygon points="3,2 13,8 3,14" fill="#2196F3"/>
        </svg>""",
        
        "stop": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="10" height="10" fill="#FF5722" rx="2"/>
        </svg>""",
        
        "single": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polygon points="3,2 13,8 3,14" fill="#FF9800"/>
            <rect x="13" y="2" width="2" height="12" fill="#FF9800"/>
        </svg>""",
        
        # View Icons
        "auto_scale": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="12" height="12" stroke="#9C27B0" stroke-width="1.5" fill="none" rx="2"/>
            <path d="M5 8 L8 5 L11 8" stroke="#9C27B0" stroke-width="1.5" fill="none"/>
            <path d="M5 8 L8 11 L11 8" stroke="#9C27B0" stroke-width="1.5" fill="none"/>
        </svg>""",
        
        "grid": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g stroke="#607D8B" stroke-width="0.5">
                <line x1="0" y1="4" x2="16" y2="4"/>
                <line x1="0" y1="8" x2="16" y2="8"/>
                <line x1="0" y1="12" x2="16" y2="12"/>
                <line x1="4" y1="0" x2="4" y2="16"/>
                <line x1="8" y1="0" x2="8" y2="16"/>
                <line x1="12" y1="0" x2="12" y2="16"/>
            </g>
        </svg>""",
        
        "crosshair": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="8" y1="0" x2="8" y2="16" stroke="#FFC107" stroke-width="1.5"/>
            <line x1="0" y1="8" x2="16" y2="8" stroke="#FFC107" stroke-width="1.5"/>
            <circle cx="8" cy="8" r="2" stroke="#FFC107" stroke-width="1.5" fill="none"/>
        </svg>""",
        
        "clear": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 3L13 13M13 3L3 13" stroke="#F44336" stroke-width="2" stroke-linecap="round"/>
            <rect x="1" y="1" width="14" height="14" stroke="#F44336" stroke-width="1" fill="none" rx="2"/>
        </svg>""",
        
        # Configuration Icons
        "save": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 2V14H14V4L12 2H2Z" stroke="#4CAF50" stroke-width="1.5" fill="#4CAF50" fill-opacity="0.2"/>
            <rect x="3" y="3" width="6" height="2" fill="#4CAF50"/>
            <rect x="4" y="8" width="8" height="6" stroke="#4CAF50" stroke-width="1" fill="none"/>
        </svg>""",
        
        "load": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 2V14H14V2H2Z" stroke="#2196F3" stroke-width="1.5" fill="#2196F3" fill-opacity="0.2"/>
            <path d="M6 6L8 4L10 6" stroke="#2196F3" stroke-width="1.5" fill="none"/>
            <line x1="8" y1="4" x2="8" y2="10" stroke="#2196F3" stroke-width="1.5"/>
        </svg>""",
        
        "preset": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="2" width="4" height="12" stroke="#9C27B0" stroke-width="1.5" fill="#9C27B0" fill-opacity="0.3"/>
            <rect x="6" y="6" width="4" height="8" stroke="#9C27B0" stroke-width="1.5" fill="#9C27B0" fill-opacity="0.3"/>
            <rect x="10" y="4" width="4" height="10" stroke="#9C27B0" stroke-width="1.5" fill="#9C27B0" fill-opacity="0.3"/>
        </svg>""",
        
        "delete": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 4V14C3 14.5 3.5 15 4 15H12C12.5 15 13 14.5 13 14V4" stroke="#F44336" stroke-width="1.5"/>
            <path d="M6 1H10V3H6V1Z" stroke="#F44336" stroke-width="1.5"/>
            <line x1="1" y1="3" x2="15" y2="3" stroke="#F44336" stroke-width="1.5"/>
            <line x1="6" y1="7" x2="6" y2="11" stroke="#F44336" stroke-width="1"/>
            <line x1="10" y1="7" x2="10" y2="11" stroke="#F44336" stroke-width="1"/>
        </svg>""",
        
        "refresh": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2 8C2 4.7 4.7 2 8 2C9.5 2 10.8 2.6 11.8 3.6L10 5.4" stroke="#00BCD4" stroke-width="1.5" fill="none"/>
            <path d="M14 8C14 11.3 11.3 14 8 14C6.5 14 5.2 13.4 4.2 12.4L6 10.6" stroke="#00BCD4" stroke-width="1.5" fill="none"/>
            <polygon points="8,1 12,5 8,5" fill="#00BCD4"/>
            <polygon points="8,15 4,11 8,11" fill="#00BCD4"/>
        </svg>""",
        
        # Export Icons
        "export": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 2V10M8 2L5 5M8 2L11 5" stroke="#FF9800" stroke-width="1.5" fill="none"/>
            <path d="M3 12V13C3 13.5 3.5 14 4 14H12C12.5 14 13 13.5 13 13V12" stroke="#FF9800" stroke-width="1.5"/>
        </svg>""",
        
        "screenshot": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="3" width="12" height="8" stroke="#795548" stroke-width="1.5" fill="#795548" fill-opacity="0.2"/>
            <circle cx="8" cy="7" r="2" stroke="#795548" stroke-width="1.5" fill="none"/>
            <rect x="5" y="1" width="6" height="2" stroke="#795548" stroke-width="1" fill="#795548" fill-opacity="0.3"/>
        </svg>""",
        
        # Status Icons
        "connected": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="6" fill="#4CAF50" fill-opacity="0.2" stroke="#4CAF50" stroke-width="2"/>
            <path d="M5 8L7 10L11 6" stroke="#4CAF50" stroke-width="2" fill="none"/>
        </svg>""",
        
        "disconnected": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="6" fill="#F44336" fill-opacity="0.2" stroke="#F44336" stroke-width="2"/>
            <line x1="6" y1="6" x2="10" y2="10" stroke="#F44336" stroke-width="2"/>
            <line x1="10" y1="6" x2="6" y2="10" stroke="#F44336" stroke-width="2"/>
        </svg>""",
        
        "warning": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 1L15 13H1L8 1Z" fill="#FF9800" fill-opacity="0.2" stroke="#FF9800" stroke-width="1.5"/>
            <line x1="8" y1="5" x2="8" y2="9" stroke="#FF9800" stroke-width="2"/>
            <circle cx="8" cy="11" r="1" fill="#FF9800"/>
        </svg>""",
        
        # Settings Icons
        "settings": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="3" stroke="#607D8B" stroke-width="1.5" fill="none"/>
            <path d="M8 1L9.5 3.5L12 2L13 4.5L15.5 5.5L14 8L15.5 10.5L13 11.5L12 14L9.5 12.5L8 15L6.5 12.5L4 14L3 11.5L0.5 10.5L2 8L0.5 5.5L3 4.5L4 2L6.5 3.5L8 1Z" stroke="#607D8B" stroke-width="1"/>
        </svg>""",
        
        "help": """<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="8" cy="8" r="6" stroke="#2196F3" stroke-width="1.5" fill="none"/>
            <path d="M6 6C6 4.9 6.9 4 8 4S10 4.9 10 6C10 7 9 7.5 8 8" stroke="#2196F3" stroke-width="1.5" fill="none"/>
            <circle cx="8" cy="11" r="1" fill="#2196F3"/>
        </svg>"""
    }
    
    @staticmethod
    def get_icon(name, size=16):
        """Get QIcon from SVG data"""
        if name not in IconManager.ICONS:
            return QIcon()
            
        svg_data = IconManager.ICONS[name]
        svg_bytes = QByteArray(svg_data.encode('utf-8'))
        
        pixmap = QPixmap()
        pixmap.loadFromData(svg_bytes, 'SVG')
        
        if not pixmap.isNull():
            # Scale to desired size
            scaled_pixmap = pixmap.scaled(size, size, 
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            return QIcon(scaled_pixmap)
        
        return QIcon()
    
    @staticmethod
    def get_pixmap(name, size=16):
        """Get QPixmap from SVG data"""
        if name not in IconManager.ICONS:
            return QPixmap()
            
        svg_data = IconManager.ICONS[name]
        svg_bytes = QByteArray(svg_data.encode('utf-8'))
        
        pixmap = QPixmap()
        pixmap.loadFromData(svg_bytes, 'SVG')
        
        if not pixmap.isNull():
            return pixmap.scaled(size, size, 
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        
        return QPixmap()
    
    @staticmethod
    def get_available_icons():
        """Get list of available icon names"""
        return list(IconManager.ICONS.keys())


# Icon utility functions
def create_status_icon(status, size=16):
    """Create status icon based on connection state"""
    if status == "connected":
        return IconManager.get_icon("connected", size)
    elif status == "disconnected": 
        return IconManager.get_icon("disconnected", size)
    elif status == "warning":
        return IconManager.get_icon("warning", size)
    else:
        return QIcon()

def create_themed_icon(name, theme="dark", size=16):
    """Create icon with theme-appropriate colors"""
    # Future enhancement: modify SVG colors based on theme
    return IconManager.get_icon(name, size)
