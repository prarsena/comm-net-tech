# --- 1. INSPECT RUNNING PROCESSES ---
# Look up process by name (returns nothing if not running)
ps -A -o pid,comm | grep -i "TV"

# Launch apps via macOS LaunchServices
open -a TV
open -a Calculator

# Reference PIDs manually: 
ps -A -o pid,comm | grep -iE "Calc|TV" | grep -v Widget
 5826 /System/Applications/Calculator.app/Contents/MacOS/Calculator
 4126 /System/Applications/TV.app/Contents/MacOS/TV

# Capture PIDs dynamically
TV_PID=$(pgrep -x TV)
CALC_PID=$(pgrep -x Calculator)
echo "TV PID: $TV_PID | Calculator PID: $CALC_PID"


# --- 2. TERMINATION SIGNALS: GRACEFUL VS FORCEFUL ---
# Graceful termination (SIGTERM, signal 15): asks app to flush buffers & clean up
kill "$TV_PID"
pkill -x TV

# Forceful termination (SIGKILL, signal 9): kernel reclaims resources immediately
kill -9 "$TV_PID"

# --- 3. OPEN FILES & NETWORK SOCKETS (lsof) ---
# Inspect all files, shared libraries (.dylib), and fonts mapped by a process
lsof -p "$CALC_PID"

# Snapshot of active network sockets (IPv4/IPv6) held by the TV app
# -a combines flags (AND); -i filters network; -P prevents slow DNS port name resolution
lsof -a -i -P -p "$TV_PID"

# --- 4. EXECUTION CONTROL: FREEZE & THAW ---
# Suspend execution (SIGSTOP): stops CPU scheduling; UI freezes completely
kill -STOP "$CALC_PID"

# Resume execution (SIGCONT): kernel resumes scheduling execution threads
kill -CONT "$CALC_PID"

# --- 5. MEMORY METRICS & LIVE TELEMETRY ---
# RSS = Resident Set Size (physical RAM currently occupied)
ps -o pid,rss,comm -p "$TV_PID"

# Interactive process monitoring filtered to a single PID (press 'q' to exit)
top -pid "$CALC_PID"


# --- MISC / OTHER ---
# Detailed breakdown of mapped regions, stack, heap, and libraries (macOS specific)
vmmap -summary $PID
# macOS tool showing live threads and call counts
sample $PID 1 1 -s