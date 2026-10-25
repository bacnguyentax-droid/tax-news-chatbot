import os
import subprocess

CURRENT_DIR = os.path.abspath('manage_app')
bat_path = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'Dang_Nhap_NotebookLM.bat'))
print('bat_path:', bat_path)
print('exists:', os.path.exists(bat_path))
res = subprocess.run(f'cmd.exe /c start "" "{bat_path}"', shell=True, capture_output=True, text=True)
print('returncode:', res.returncode)
print('stdout:', res.stdout)
print('stderr:', res.stderr)
