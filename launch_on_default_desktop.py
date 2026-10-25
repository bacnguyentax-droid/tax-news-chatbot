import subprocess
import sys
import os

si = subprocess.STARTUPINFO()
si.lpDesktop = r"WinSta0\Default"

cmd = [sys.executable, "run_vpdt_login.py"]
cwd = os.path.dirname(os.path.abspath(__file__))

stdout_log = open("scratch/gui_desk_stdout.log", "w", encoding="utf-8")
stderr_log = open("scratch/gui_desk_stderr.log", "w", encoding="utf-8")

p = subprocess.Popen(
    cmd,
    cwd=cwd,
    startupinfo=si,
    stdout=stdout_log,
    stderr=stderr_log,
    creationflags=subprocess.CREATE_NEW_CONSOLE
)
print("Launched on WinSta0\\Default with PID:", p.pid)
