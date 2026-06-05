@echo off
REM Example populate/packaging script for ProductA.
REM build.py rewrites the version on the line below from common_version.c before running this.
set Build_VersionNumber="000000"

echo Packaging ProductA firmware, build %Build_VersionNumber%...
REM Real scripts would call hex_converter.exe here and bundle the staged *.hex files.

REM build.py comments out the next line automatically so headless runs do not block.
set /p DUMMY=PRESS ANY KEY TO CONTINUE...
