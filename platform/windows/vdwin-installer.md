# VisiData for Windows installer

- install WinPY: https://winpython.github.io/

- cd WinPY\python-3.9.4.amd64
- ./Scripts/pip3.exe install visidata
   - [dev] https://git-scm.com/download/win
   - [dev] pip3 install git+https://github.com/saulpw/visidata.git@develop
- ./Scripts/pip3.exe install windows-curses
- ./Scripts/pip3.exe install pyinstaller

- git clone https://github.com/saulpw/vdwin.git WinPy/vdwin

- ./Scripts/pyinstaller.exe --onefile/-F --icon/-i ..\vdwin\vdicon.ico --name/-n VisiData ..\vdwin\visidata.py
- dist/visidata/visidata.exe

## Compile VisiData-setup.exe

- Inno Setup Compiler (6.1.2)
- vd.iss
