# --- 1. INSPECT RUNNING PROCESSES ---
# Query running processes by name (returns empty if not found)
Get-Process -Name "Spotify" -ErrorAction SilentlyContinue

# Launch target applications
Start-Process "calc.exe"
Start-Process "spotify.exe"

# Retrieve process objects and identify PIDs
$CalcProc = Get-Process -Name "CalculatorApp", "win32calc" -ErrorAction SilentlyContinue | Select-Object -First 1
$SpotifyProc = Get-Process -Name "Spotify" -ErrorAction SilentlyContinue | Select-Object -First 1

Write-Host "Spotify PID: $($SpotifyProc.Id) | Calculator PID: $($CalcProc.Id)"

# --- 2. TERMINATING PROCESSES ---
# Polite termination: sends WM_CLOSE message to the main GUI message loop
$SpotifyProc.CloseMainWindow()

# Forceful termination (equivalent to kill -9 / SIGKILL):
# Instructs Windows kernel to immediately terminate process and all threads
Stop-Process -Id $SpotifyProc.Id -Force
# Or by name:
# Stop-Process -Name "Spotify" -Force

# --- 3. OPEN FILES & NETWORK CONNECTIONS ---
# Inspect open network sockets for Spotify (equivalent to lsof -i -P)
Get-NetTCPConnection -OwningProcess $SpotifyProc.Id | 
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State

# Inspect DLL modules loaded in memory by Calculator (equivalent to lsof libraries)
(Get-Process -Id $CalcProc.Id).Modules | Select-Object ModuleName, FileName

# --- 4. EXECUTION CONTROL: SUSPEND & RESUME ---
# Windows does not have native kill -STOP/-CONT commands, but the OS thread scheduler
# supports it via Sysinternals pssuspend or the native NtSuspendProcess NTAPI:
# Suspend (Freeze GUI):
# pssuspend.exe $CalcProc.Id
# Resume (Thaw GUI):
# pssuspend.exe -r $CalcProc.Id

# --- 5. MEMORY METRICS & TELEMETRY ---
# WS = Working Set (Physical RAM, equivalent to RSS)
# VM = Virtual Memory Size (Address space allocated, equivalent to VSZ)
Get-Process -Id $SpotifyProc.Id | 
    Select-Object Id, ProcessName, 
        @{Name="WorkingSet_MB"; Expression={[math]::Round($_.WorkingSet64 / 1MB, 2)}},
        @{Name="VirtualMemory_MB"; Expression={[math]::Round($_.VirtualMemorySize64 / 1MB, 2)}}

# Continuous monitoring (updates every 2 seconds, press Ctrl+C to exit)
while ($true) {
    Clear-Host
    Get-Process -Id $CalcProc.Id, $SpotifyProc.Id -ErrorAction SilentlyContinue | 
        Format-Table Id, ProcessName, CPU, WorkingSet64 -AutoSize
    Start-Sleep -Seconds 2
}