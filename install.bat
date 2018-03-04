@echo off
SET PYTHON35PATH=%APPDATA%\..\Local\Programs\Python\Python35\

ECHO ################################################
ECHO ######  VKAnalysis installing script v.0  ######
ECHO ######       (c) Sergey Migalin 2018      ######
ECHO ################################################
ECHO.

:CHECKDIR
echo Checking Python 3.5 folder in %PYTHON35PATH%
IF EXIST %PYTHON35PATH% (
    echo Python 3.5 was find in %PYTHON35PATH%
) ELSE (
    echo Python 3.5 was not found
    SET /P PYTHON35PATH=Enter Python 3.5 directory: 
    GOTO CHECKDIR
)
ECHO.

:CREATEVENV
echo Creating virtual environment
%PYTHON35PATH%\python.exe -m venv vkvenv/
echo Enter into environment
call vkvenv\Scripts\activate.bat
ECHO.

:INSTCORE
echo Installing CORE python packets
pip install -r std_req.txt
ECHO.

:INSTPICT
echo Do you want to install VKPhotoAnalysis module?
SET /P PHOTONEED=y(es) or [n(o)]:
IF "%PHOTONEED%"=="y" (
    echo Now we need to install numpy+mkl and scipy
:INSTPICTPROMPT
    echo Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy and download numpy+mkl and scipy to this folder for your computer. For example, if you have Win10 x64, you need to download numpy-1.13.3+mkl-cp35-cp35m-win_amd64.whl and scipy-1.0.0-cp35-cp35m-win_amd64.whl
    echo If you downloaded them to this folder, press any key.
    pause

    IF NOT EXIST numpy*.whl (
        GOTO INSTPICTPROMPT
    )
    IF NOT EXIST scipy*.whl (
        GOTO INSTPICTPROMPT
    )
    
    FOR %%f IN (numpy*.*) DO (
        echo Installing numpy
        pip install %%f
    )
    FOR %%f IN (scipy*.*) DO (
        echo Installing scipy
        pip install %%f
    )
    
    echo Installing other PICTURE python packets
    pip install -r pic_req.txt

) ELSE (
    ECHO Deleting VKPhotoAnalysis module
    python .\VKAnalysis\manage.py delete VKPhotoAnalysis
)
ECHO.

:RUN
SET /P RUN=Done. Run VKAnalysis? y(es) or [n(no)]
IF "%RUN%"=="y" (
    python .\VKAnalysis\VKAnalysis.py
) ELSE (
    pause
)