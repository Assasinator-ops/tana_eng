# TanaProject Django + MySQL Autostart (One-time setup for power-on ready)

## For users: Do once, then reboot & work!

## 1. MySQL Service Auto-start (2 min)
1. Win+R `services.msc`
2. Find `MySQL80` or `MySQL` → Right Properties.
3. Startup type: **Automatic** → Apply → Start (if stopped) → OK.
4. Close.

## 2. Task Scheduler (3 min)
1. Win+R `taskschd.msc`
2. Right **Task Scheduler Library** → **Create Basic Task...**
3. Name: `Start TanaProject`
4. Trigger: **When I log on**
5. Action: **Start a program** → Next → Browse `e:\Projects\TE\start_django_auto.bat`
6. Finish.
7. Right new task → **Properties** → Check **Run with highest privileges** → OK.

## 3. Test
1. Reboot PC.
2. Log on → wait 1min.
3. Open http://localhost:8000 → Django ready!
4. Check services.msc: MySQL running.

## Logs
Task Mgr → Details → cmd.exe (server console).

Ready! No more manual starts.
