import subprocess

ADB = r"C:\Users\dmill\Documents\AntigravityWorkingDir\platform-tools\adb.exe"
SERIAL = "ff152647"

cmd = [ADB, "-s", SERIAL, "shell", "find /storage/EEEF-F762/ -iname '*arcade*racing*' -o -iname '*road*trip*'"]
res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, errors="ignore")
print(res.stdout)
