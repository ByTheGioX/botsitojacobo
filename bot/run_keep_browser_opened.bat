cd /d "%~dp0"
taskkill /f /im python.exe
taskkill /f /im chrome.exe
taskkill /f /im chromedriver.exe
python booking_notifier_keep_browser_opened.py
pause
