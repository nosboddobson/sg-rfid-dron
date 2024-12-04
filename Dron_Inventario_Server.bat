
@echo off
call C:\ProgramData\Anaconda3\Scripts\activate.bat
set PYTHONPATH=D:\dev\sg-rfid-dron;C:\Users\ra-pvega\AppData\Roaming\Python\Python39\site-packages;%PYTHONPATH%
C:\ProgramData\Anaconda3\python.exe "D:\dev\sg-rfid-dron\Server.py"