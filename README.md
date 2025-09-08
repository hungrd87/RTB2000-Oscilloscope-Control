# RTB2000 Oscilloscope Control GUI

A comprehensive Python-based GUI application for controlling R&S RTB2000 series oscilloscopes using SCPI commands and VISA communication.

## ✅ Project Status: COMPLETED & RUNNING

**Created:** September 6, 2025  
**Status:** Fully functional GUI application successfully launched  
**Environment:** Python 3.13.7 virtual environment configured  

## 🎯 Features

- **Real-time oscilloscope control** with full SCPI command support
- **4-channel control** with individual settings for each channel
- **Timebase and trigger configuration** with comprehensive options
- **Live waveform display** using matplotlib integration
- **Measurement tools** with automatic calculation and display
- **Connection management** with VISA resource discovery
- **PyQt6 modern GUI** with tabbed interface and status monitoring
- **Configuration save/load** for instrument settings
- **Screenshot capture** functionality

## 📋 Requirements

- Python 3.8+ (currently using 3.13.7)
- PyQt6 >= 6.5.0
- PyVISA >= 1.13.0
- NumPy >= 1.24.0
- Matplotlib >= 3.7.0
- R&S RTB2000 series oscilloscope
- VISA driver (NI-VISA or compatible)

## 🚀 Quick Start

The project is already set up and running! To restart the application:

```bash
# Navigate to project directory
cd "C:\Users\favor\Documents\Nortrace_Project\RTB2000"

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run the application
python src/main.py
```

Or use the VS Code task: **"Run RTB2000"**

## 🔧 Installation (Already Completed)

✅ Virtual environment created and activated  
✅ All dependencies installed via pip  
✅ Qt for Python extension installed in VS Code  
✅ Project structure scaffolded  
✅ All modules implemented and tested  

## 📖 Usage

1. **Launch the application** using the command above
2. **Connect to oscilloscope** via the Connection tab:
   - Select VISA resource from dropdown
   - Click "Connect" button
3. **Configure channels** in the Channel Control tab
4. **Set timebase** and **trigger** parameters  
5. **View waveforms** in real-time display
6. **Monitor measurements** in the Measurements tab

## Project Structure

```
RTB2000/
├── src/
│   └── rtb2000_control/
│       ├── communication/     # VISA/SCPI communication
│       ├── gui/              # PyQt6 GUI components
│       ├── instruments/      # RTB2000 device control
│       └── utils/            # Helper utilities
├── tests/                    # Unit tests
├── docs/                     # Documentation
├── examples/                 # Example scripts
└── requirements.txt          # Dependencies
```

## License

MIT License
