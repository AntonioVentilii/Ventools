@echo off
setlocal enabledelayedexpansion

REM Step 1: Create or reset the virtual environment

set venv_name=venv

REM Check if the virtual environment exists
if not exist %venv_name% (
    echo Virtual environment does not exist. Creating a new one...
    python -m venv %venv_name%
) else (
    echo Virtual environment already exists.
    choice /C YN /M "Do you want to reset the virtual environment"
    if errorlevel 2 goto skip_reset
    echo Resetting the virtual environment...
    rmdir /S /Q %venv_name%
    python -m venv %venv_name%
    set install_requirements=yes
)

:skip_reset

REM Activate the virtual environment
call %venv_name%\Scripts\activate

REM Step 2: Install requirements from requirements.txt
if "%install_requirements%"=="yes" (
    echo Installing requirements...
    pip install -r requirements.txt
    echo Requirements installed.
) else (
    choice /C YN /M "Do you want to install the requirements"
    if errorlevel 2 goto skip_requirements
    echo Installing requirements...
    pip install -r requirements.txt
    echo Requirements installed.
)

:skip_requirements

REM Step 3: Initiate and update submodules

REM Check if .gitmodules file exists
if not exist .gitmodules (
    echo .gitmodules file not found. Exiting...
    goto end
)

REM Initialize and update submodules
choice /C YN /M "Do you want to initiate the submodules"
if errorlevel 2 goto skip_submodules
git submodule init
git submodule update --recursive --remote

:skip_submodules

REM Iterate over each submodule defined in the .gitmodules file
for /f "tokens=*" %%a in (.gitmodules) do (
    REM Normalize the keys and values
    for /f "tokens=1,2 delims== " %%i in ("%%a") do (
        set "key=%%i"
        set "value=%%j"
    )

    REM If we found a path, enter the directory
    if "!key!"=="path" (
        set "submodule_path=!value!"
    )

    REM If we found a branch, enter the directory
    if "!key!"=="branch" (
        set "branch=!value!"

        REM Enter the submodule directory, checkout the branch and pull
        echo Entering submodule at path "!submodule_path!" and checking out branch "!submodule_branch!"
        pushd "!submodule_path!"
        git checkout "!branch!"
        git pull

        REM Return to the parent directory
        popd
    )
)

:end

REM End of script
pause
