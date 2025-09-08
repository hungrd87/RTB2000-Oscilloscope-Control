"""
Professional Styling System for RTB2000 Application
Advanced QSS Themes with Professional Design Language
"""

# Dark Professional Theme
DARK_PROFESSIONAL_THEME = """
/* Main Application Styling */
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 9pt;
}

/* Menu Bar Styling */
QMenuBar {
    background-color: #2d2d30;
    color: #ffffff;
    border: none;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 2px;
}

QMenuBar::item:selected {
    background-color: #3e3e42;
    color: #ffffff;
}

QMenuBar::item:pressed {
    background-color: #007acc;
    color: #ffffff;
}

/* Menu Styling */
QMenu {
    background-color: #2d2d30;
    color: #ffffff;
    border: 1px solid #3e3e42;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
    margin: 1px;
}

QMenu::item:selected {
    background-color: #007acc;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #3e3e42;
    margin: 4px 16px;
}

/* Toolbar Styling */
QToolBar {
    background-color: #2d2d30;
    border: none;
    spacing: 4px;
    padding: 4px;
}

QToolBar::separator {
    background-color: #3e3e42;
    width: 1px;
    margin: 4px 8px;
}

/* Button Styling */
QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #1177bb;
    transform: translateY(-1px);
}

QPushButton:pressed {
    background-color: #005a9e;
    transform: translateY(0px);
}

QPushButton:disabled {
    background-color: #3e3e42;
    color: #6d6d6d;
}

/* Action Button Styling */
QAction {
    color: #ffffff;
    padding: 4px 8px;
}

QToolBar QToolButton {
    background-color: transparent;
    color: #ffffff;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 2px;
}

QToolBar QToolButton:hover {
    background-color: #3e3e42;
    color: #ffffff;
}

QToolBar QToolButton:pressed {
    background-color: #007acc;
    color: #ffffff;
}

/* ComboBox Styling */
QComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #5a5a5a;
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #007acc;
    background-color: #404040;
}

QComboBox:focus {
    border-color: #007acc;
    outline: none;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iI0ZGRkZGRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
    width: 12px;
    height: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d30;
    color: #ffffff;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    selection-background-color: #007acc;
    outline: none;
}

/* Label Styling */
QLabel {
    color: #ffffff;
    background-color: transparent;
    padding: 2px 4px;
}

QLabel[class="preset-label"] {
    color: #cccccc;
    font-weight: 600;
    margin-right: 8px;
}

QLabel[class="status-label"] {
    color: #4fc3f7;
    font-style: italic;
    padding: 4px 8px;
}

QLabel[class="test-label"] {
    color: #81c784;
    font-weight: bold;
    padding: 4px 8px;
}

/* Tab Widget Styling */
QTabWidget::pane {
    border: 1px solid #3e3e42;
    background-color: #252526;
    border-radius: 6px;
    margin-top: 4px;
}

QTabBar::tab {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid #3e3e42;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #252526;
    color: #ffffff;
    border-color: #007acc;
    border-bottom: 1px solid #252526;
}

QTabBar::tab:hover:!selected {
    background-color: #3e3e42;
    color: #ffffff;
}

/* Slider Styling */
QSlider::groove:horizontal {
    background-color: #3e3e42;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #007acc;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #1177bb;
}

QSlider::handle:horizontal:pressed {
    background-color: #005a9e;
}

/* Splitter Styling */
QSplitter::handle {
    background-color: #3e3e42;
    width: 4px;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background-color: #007acc;
}

/* Status Bar Styling */
QStatusBar {
    background-color: #2d2d30;
    color: #cccccc;
    border-top: 1px solid #3e3e42;
    padding: 4px;
}

QStatusBar::item {
    border: none;
    padding: 2px 8px;
}

/* Scroll Bar Styling */
QScrollBar:vertical {
    background-color: #2d2d30;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #5a5a5a;
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6a6a6a;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

/* Group Box Styling */
QGroupBox {
    font-weight: 600;
    color: #ffffff;
    border: 2px solid #3e3e42;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #4fc3f7;
    background-color: #1e1e1e;
}

/* Input Field Styling */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #5a5a5a;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 9pt;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #007acc;
    outline: none;
}

/* Animation Classes */
.fade-in {
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.slide-in {
    animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
    from { transform: translateY(-10px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Tooltip Styling */
QToolTip {
    background-color: #2d2d30;
    color: #ffffff;
    border: 1px solid #007acc;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 9pt;
    opacity: 240;
}

/* Message Box Styling */
QMessageBox {
    background-color: #1e1e1e;
    color: #ffffff;
    border-radius: 8px;
}

QMessageBox QPushButton {
    min-width: 100px;
    padding: 8px 16px;
}

/* Progress Bar Styling */
QProgressBar {
    background-color: #3e3e42;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 4px;
}
"""

# Light Professional Theme
LIGHT_PROFESSIONAL_THEME = """
/* Main Application Styling - Light Theme */
QMainWindow {
    background-color: #f5f5f5;
    color: #333333;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 9pt;
}

/* Menu Bar Styling */
QMenuBar {
    background-color: #ffffff;
    color: #333333;
    border-bottom: 1px solid #e0e0e0;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
    margin: 2px;
}

QMenuBar::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

/* Button Styling */
QPushButton {
    background-color: #1976d2;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #1565c0;
}

QPushButton:pressed {
    background-color: #0d47a1;
}

/* ComboBox Styling */
QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #1976d2;
}

/* Continue with other light theme elements... */
"""

# High Contrast Theme for Accessibility
HIGH_CONTRAST_THEME = """
/* High Contrast Theme for Accessibility */
QMainWindow {
    background-color: #000000;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    font-weight: 500;
}

QPushButton {
    background-color: #ffff00;
    color: #000000;
    border: 2px solid #ffffff;
    padding: 10px 18px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #ffffff;
    color: #000000;
}

/* Continue with high contrast elements... */
"""

# Theme management functions
def get_theme_stylesheet(theme_name="dark"):
    """Get stylesheet for specified theme"""
    themes = {
        "dark": DARK_PROFESSIONAL_THEME,
        "light": LIGHT_PROFESSIONAL_THEME,
        "high_contrast": HIGH_CONTRAST_THEME
    }
    
    return themes.get(theme_name, DARK_PROFESSIONAL_THEME)

def apply_theme_to_application(app, theme_name="dark"):
    """Apply theme to QApplication"""
    stylesheet = get_theme_stylesheet(theme_name)
    app.setStyleSheet(stylesheet)
    
def get_available_themes():
    """Get list of available themes"""
    return ["dark", "light", "high_contrast"]
