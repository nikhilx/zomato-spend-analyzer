@echo off
setlocal

set SQLITE=E:\Softwares\sqlite-tools\sqlite3.exe
set DB=%~dp0..\zomato_orders.db
set DIR=%~dp0
set QUERY=%1
set FLAG=%2

if "%QUERY%"=="" (
  echo Usage:
  echo   zomato list
  echo   zomato ^<query_name^> [--csv]
  exit /b 1
)

if "%QUERY%"=="list" (
  for %%f in ("%DIR%*.sql") do (
    echo %%~nf
  )
  exit /b 0
)

if "%QUERY:~-4%"==".sql" (
  set FILE=%DIR%%QUERY%
) else (
  set FILE=%DIR%%QUERY%.sql
)

if not exist "%FILE%" (
  echo Query not found: %QUERY%
  exit /b 1
)

if "%FLAG%"=="--csv" (
  "%SQLITE%" "%DB%" -header -csv < "%FILE%"
) else (
  "%SQLITE%" "%DB%" < "%FILE%"
)

endlocal
