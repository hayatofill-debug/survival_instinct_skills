@echo off
chcp 65001 > nul

:select_mode
cls
echo ==================================================
echo   Select Base Language Mode
echo ==================================================
echo   [1] Japanese Base (Extract Japanese text)
echo   [2] English Base  (Extract English text)
echo ==================================================
set /p LANG_MODE="Choose mode (1-2): "

if "%LANG_MODE%"=="1" (
    set BASE_MODE=ja
    goto get_id
)
if "%LANG_MODE%"=="2" (
    set BASE_MODE=en
    goto get_id
)
echo Invalid choice.
pause
goto select_mode

:get_id
cls
set /p IDENTIFIER="Identifier (ex: sis): "

:menu
cls
echo ==================================================
echo   Minecraft Skill Translation Tool : %IDENTIFIER% (Mode: %BASE_MODE%)
echo ==================================================
echo   [1] Step1: Make patched JSON and blank.json
echo   [2] Step2: Output as en_us.json
echo   [3] Step2: Output as custom language (ex: zh_cn, ja_jp)
echo   [4] Change Base Language Mode
echo   [5] Exit
echo ==================================================
set /p CHOICE="Choose (1-5): "

if "%CHOICE%"=="1" (
    echo.
    python process_skills.py 1 %IDENTIFIER% %BASE_MODE%
    pause
    goto menu
)
if "%CHOICE%"=="2" (
    echo.
    python process_skills.py 2 %IDENTIFIER% en_us
    pause
    goto menu
)
if "%CHOICE%"=="3" (
    echo.
    set /p LANGNAME="Input language name (ex: zh_cn, ja_jp): "
    echo.
    python process_skills.py 2 %IDENTIFIER% %LANGNAME%
    pause
    goto menu
)
if "%CHOICE%"=="4" (
    goto select_mode
)
if "%CHOICE%"=="5" (
    exit
)

echo Invalid choice.
pause
goto menu