# Django + XAMPP Autostart Setup (One-time for zero intervention)
For non-IT users: Follow once, then reboot works automatically.

## Steps:
- [ ] **XAMPP Services (5 min):** 
  1. Run `C:\xampp\xampp-control.exe` (or your path).
  2. Click MySQL/Apache `Config` → `Service` → `Install` both.
  3. `Start` both → green. Close.
- [ ] **Task Scheduler (3 min):**
  1. Win+R → `taskschd.msc`.
  2. Right Task Scheduler Library → Create Basic Task.
  3. Name: `Start TanaProject`.
  4. Trigger: `When I log on`.
  5. Action: `Start a program` → Browse `e:\Projects\TE\start_django_after_xampp.bat`.
  6. Finish → Right task → Properties → Run highest privileges → OK.
- [ ] **Test:**
  1. Reboot PC.
  2. After logon (~1min), check http://localhost:8000 (Django), XAMPP Control (services green).
- [x] Scripts created (bat + TODO.md).

Done? Reboot & work! Logs in hidden console (Task Mgr → Details → cmd.exe).
