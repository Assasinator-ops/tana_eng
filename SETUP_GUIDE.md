# 🚀 TanaProject Complete Autostart Setup Guide
## For Everyone - No IT Skills Needed!
*Updated: Auto-detects directory. Run once, reboot forever.*

---

## 🎯 What This Does
- PC power on → MySQL starts auto.
- User logon → Django server starts auto (waits MySQL).
- Open browser `http://localhost:8000` → Work immediately.
- **No clicks, no manual starts. Ever.**

---

## 📋 Prerequisites Check
1. **MySQL installed?** Open `MySQL Workbench` → Connect OK? Good.
2. **Django project:** In `e:\Projects\TE` (this folder).
3. **Python:** CMD → `python --version` shows 3.x.

If no, install MySQL/Python first.

---

## Step 1: MySQL Auto-Start (2 minutes)
```
1. Press Win + R
2. Type `services.msc` → Enter
3. Scroll `MySQL` or `MySQL80`
4. Right-click → Properties
5. Startup type → **Automatic** ← Select
6. **Start** button if stopped
7. OK → Close
```
✅ **Done:** MySQL starts on every boot.

**Screenshot tip:** Google "windows services.msc mysql automatic" if stuck.

---

## Step 2: Register Startup (1 minute)
```
1. Right-click `register_startup.bat` (in this folder)
2. "Run as administrator" 
3. See "SUCCESS" → Close
```
✅ **Done:** Windows now auto-runs Django on login.

**If FAILED:** Right-click again, "Run as administrator".

---

## Step 3: Test (Reboot)
```
1. Restart PC (Start → Power → Restart)
2. Login normally
3. Wait 30-60s (coffee time)
4. Browser → http://localhost:8000
```
**Green? Django page loads → PERFECT!**

**Not?** Check Step 1 MySQL running in services.msc.

---

## 🛠 Troubleshooting (Rare)
| Issue | Fix |
|-------|-----|
| No MySQL port | services.msc → MySQL → Start |
| Django error logs | Task Mgr → Details → cmd.exe → Context menu View |
| Task not run | Run register.bat as Admin again |
| Port busy | Kill other on 8000: `netstat -ano | find "8000"` → taskkill /pid PID |

**CMD Test Manual:**
```
cd /d e:\Projects\TE
start_django_auto.bat
```
Wait MySQL → Server starts.

---

## 🔄 How It Works (Tech Optional)
```
Power On
  ↓
Windows Boot + MySQL Service (Automatic)
  ↓
User Logon → Task "TanaDjango"
  ↓
start_django_auto.bat:
  Loop: Check port 3306 open? No → 5s wait
  Yes → python manage.py migrate
       python manage.py runserver 0.0.0.0:8000
  Crash? Auto restart
```

---

## ✅ Daily Use
1. Power button PC.
2. Login username/password.
3. Open Chrome `localhost:8000`
4. Work!

**That's it. Call if stuck.**

---

## Advanced (Optional)
**Stop Task:** `taskschd.msc` → Task Scheduler Library → TanaDjango → Disable/End.

**Logs:** Script echoes time-stamped. Console stays open in background.

**Production:** Later gunicorn service (ask dev).

**Backup:** Copy folder to USB.

---

**Questions? Print this guide.**

*Setup by BLACKBOXAI - Version 2.0*
