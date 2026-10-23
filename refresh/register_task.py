"""Register the monthly refresh as a Windows scheduled task (D-42).

    python refresh/register_task.py           register (or replace) the task
    python refresh/register_task.py --show    print the task as Windows holds it
    python refresh/register_task.py --remove  delete it

The task, "andrewsilvestri.com monthly refresh":
  - runs refresh/monthly.py with the user's own Python, in this folder;
  - triggers on the 2nd of every month at 06:00, and every day at 06:30;
    monthly.py does nothing on a day when this month is already done (it reads
    RUNLOG), so the daily trigger is only the retry for a month whose run was
    missed, busy or red-then-fixed;
  - StartWhenAvailable: a start missed because the laptop was off or asleep
    runs as soon as it is back ("run task as soon as possible after a
    scheduled start is missed", D-42);
  - only when Andrew is logged on (git push and the mirror use his
    credentials), only with a network, on battery as well as mains, at most
    eight hours, never two at once.

schtasks /create takes the task as XML because its own flags cannot set
StartWhenAvailable. --show reads the registered task back so the setting can
be checked as Windows applied it, not as this file wrote it (trap 31).
"""
import getpass
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NAME = "andrewsilvestri.com monthly refresh"


def xml():
    py = sys.executable
    user = os.environ.get("USERDOMAIN", "") + "\\" + getpass.getuser()
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Monthly data refresh for andrewsilvestri.com (D-42): fetch, rebuild, full suite set, publish only if green. Written by refresh/register_task.py.</Description>
    <URI>\\{name}</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-11-02T06:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <DaysOfMonth><Day>2</Day></DaysOfMonth>
        <Months><January/><February/><March/><April/><May/><June/><July/><August/><September/><October/><November/><December/></Months>
      </ScheduleByMonth>
    </CalendarTrigger>
    <CalendarTrigger>
      <StartBoundary>2026-10-24T06:30:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{user}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT8H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{py}</Command>
      <Arguments>"{script}"</Arguments>
      <WorkingDirectory>{root}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
""".format(name=esc(NAME), user=esc(user), py=esc(py),
           script=esc(os.path.join(HERE, "monthly.py")), root=esc(ROOT))


def schtasks(*a):
    r = subprocess.run(["schtasks"] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    if "--show" in sys.argv:
        rc, out = schtasks("/query", "/tn", NAME, "/xml")
        print(out)
        return rc
    if "--remove" in sys.argv:
        rc, out = schtasks("/delete", "/tn", NAME, "/f")
        print(out.strip())
        return rc
    fd, path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    with open(path, "w", encoding="utf-16") as fh:
        fh.write(xml())
    try:
        rc, out = schtasks("/create", "/tn", NAME, "/xml", path, "/f")
    finally:
        os.remove(path)
    print(out.strip())
    return rc


if __name__ == "__main__":
    sys.exit(main())
