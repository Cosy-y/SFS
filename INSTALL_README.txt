# SFS - Steganographic File System
## Windows Executable Installation

This package contains standalone executable files for the Steganographic File System (SFS) on Windows.

### Files:
- `gui.exe` - Graphical User Interface (recommended for most users)
- `sfs.exe` - Command-Line Interface

### Installation:
1. Extract all files to a folder of your choice
2. Run `gui.exe` for the graphical interface, or `sfs.exe` for command-line usage
3. No additional installation required - these are self-contained executables

### First Time Setup:
1. Run the executable
2. Initialize the system with a master password when prompted
3. Start storing and retrieving files

### Features:
- Hide encrypted files inside PNG images
- Military-grade AES-256 encryption with Argon2id key derivation
- Plausible deniability - files appear as normal photos
- Automatic file chunking for large files
- Integrity verification with SHA-256 checksums

### System Requirements:
- Windows 10 or later
- No Python installation required

### Security Note:
- Keep your master password secure
- The system creates a hidden `.sfs` folder in your home directory for storage
- Files are encrypted and hidden in PNG images in the storage directory

For more information, visit the GitHub repository: https://github.com/Cosy-y/SFS