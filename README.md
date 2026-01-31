# IBM AI Racing

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)

Autonomous AI racing agent built in Python using TORCS (The Open Racing Car Simulator), developed for the IBM AI Racing League. This project focuses on stable control, iterative performance tuning, and explainable design decisions, with IBM Granite used as an AI co-pilot for analysis and improvement.

## Table of Contents

- [Overview](#overview)
- [Competition Guidelines](#competition-guidelines)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the AI Driver](#running-the-ai-driver)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project implements an autonomous racing AI driver for TORCS using reinforcement learning and control algorithms. The agent communicates with TORCS through a UDP socket interface, receiving sensor data and sending control commands to navigate the race track.

**Key Features:**
- Real-time sensor processing (track position, speed, opponents, etc.)
- Adaptive control strategies for steering, acceleration, and braking
- Support for multiple racing scenarios (warm-up, qualifying, race)
- Detailed telemetry and debugging capabilities
- Modular design for easy algorithm experimentation

## Competition Guidelines

The IBM AI Racing League follows these core principles:

1. **Fair Competition**: All participants use the same TORCS simulator and SCR (Simulated Car Racing) protocol
2. **Autonomous Operation**: The AI driver must operate without human intervention during races
3. **Performance Metrics**: Drivers are evaluated on:
   - Lap times and race completion
   - Stability and crash avoidance
   - Fuel efficiency
   - Consistency across different tracks
4. **Code Quality**: Emphasis on clean, maintainable, and well-documented code
5. **Explainability**: AI decisions should be traceable and understandable

**Competition Stages:**
- **Warm-up (Stage 0)**: Practice laps to learn the track
- **Qualifying (Stage 1)**: Set fastest lap time for grid position
- **Race (Stage 2)**: Complete race distance with traffic
- **Unknown (Stage 3)**: General testing mode

## Project Structure

```
IBM-AI-Racing/
├── src/                    # Source code
│   └── gym_torcs/         # TORCS gym environment and client
│       ├── __init__.py    # Package initialization
│       └── torcs_jm_par.py # TORCS client and driver implementation
├── docs/                  # Documentation
├── examples/              # Example implementations and configurations
├── scripts/               # Utility scripts
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
└── README.md             # This file
```

## Prerequisites

- **Python 3.x** (3.7 or higher recommended)
- **TORCS** - The Open Racing Car Simulator
  - Linux: Available through package managers or [source](https://sourceforge.net/projects/torcs/)
  - macOS: Build from source or use pre-built binaries
  - Windows: Use Linux subsystem or virtual machine
- **Operating System**: Linux or macOS (recommended), Windows with WSL

## Installation

### 1. Install TORCS

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install torcs
```

**macOS (using Homebrew):**
```bash
brew install torcs
```

**From Source:**
```bash
# Download TORCS source from https://sourceforge.net/projects/torcs/
tar -xvf torcs-*.tar.gz
cd torcs-*
./configure
make
sudo make install
```

### 2. Install SCR Patch (for AI racing)

The Simulated Car Racing (SCR) patch enables the UDP server interface for AI clients:

```bash
# Download SCR patch from https://sourceforge.net/projects/cig/
# Apply patch to TORCS installation
# Follow SCR-specific installation instructions
```

### 3. Clone this Repository

```bash
git clone https://github.com/zaib-06/IBM-AI-Racing.git
cd IBM-AI-Racing
```

### 4. Install Python Dependencies

```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # If requirements file exists
```

## Running the AI Driver

### 1. Start TORCS Server

Configure TORCS to run in SCR server mode:

```bash
# Start TORCS
torcs

# In TORCS GUI:
# 1. Select "Race" → "Quick Race" → "Configure Race"
# 2. Enable "SCR server" mode
# 3. Set number of AI drivers
# 4. Start the race (server will wait for client connections)
```

### 2. Run the AI Client

```bash
cd src
python -m gym_torcs.torcs_jm_par [OPTIONS]
```

**Available Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-H, --host <host>` | TORCS server hostname | localhost |
| `-p, --port <port>` | TORCS server port | 3001 |
| `-i, --id <id>` | Driver ID for server | SCR |
| `-m, --steps <#>` | Maximum simulation steps | 100000 |
| `-e, --episodes <#>` | Maximum learning episodes | 1 |
| `-t, --track <track>` | Track name for learning | unknown |
| `-s, --stage <#>` | Race stage (0-3) | 3 |
| `-d, --debug` | Enable full telemetry output | False |
| `-h, --help` | Show help message | - |
| `-v, --version` | Show version | - |

**Example:**
```bash
# Run with debug output on port 3001
python -m gym_torcs.torcs_jm_par --port 3001 --debug

# Run qualifying session on specific track
python -m gym_torcs.torcs_jm_par --stage 1 --track "alpine-1" --episodes 5

# Run race with custom driver ID
python -m gym_torcs.torcs_jm_par --id "MyDriver" --stage 2 --steps 50000
```

### 3. Monitor Performance

When running with `--debug` flag, you'll see real-time telemetry:
- Track sensor readings (distance to track edges)
- Vehicle state (speed, position, angle)
- Control outputs (steering, acceleration, braking)
- Performance metrics (distance raced, fuel level)

## Development

### Modifying the Driver Algorithm

The main driver logic is in `src/gym_torcs/torcs_jm_par.py`. To implement your own driving strategy:

1. Create a custom `drive()` function that takes a `Client` object
2. Access sensor data via `client.S.d` (ServerState dictionary)
3. Set control outputs via `client.R.d` (DriverAction dictionary)
4. Replace the call to `drive_example()` in the main loop

**Example:**
```python
def my_drive_function(c):
    S, R = c.S.d, c.R.d
    
    # Read sensors
    speed = S['speedX']
    track_pos = S['trackPos']
    angle = S['angle']
    
    # Implement control logic
    R['steer'] = angle * 10 + track_pos * 0.5
    R['accel'] = 0.8 if speed < 100 else 0.3
    R['brake'] = 1.0 if speed > 150 else 0.0
```

### Testing

Run tests to ensure your changes work correctly:

```bash
# Run unit tests (if available)
python -m pytest tests/

# Test connection without TORCS server
python -m gym_torcs.torcs_jm_par --help
```

### Code Style

- Follow PEP 8 Python style guidelines
- Use descriptive variable names
- Comment complex algorithms
- Document functions with docstrings

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: TORCS and SCR are separate projects with their own licenses. This repository contains only the AI driver implementation, not the TORCS simulator binaries.
