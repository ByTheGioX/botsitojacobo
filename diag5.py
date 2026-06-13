from selenium import webdriver
from selenium.webdriver.chrome.options import Options
o = Options()
o.add_argument('--user-data-dir=C:\\Users\\AI\\Desktop\\bcache5')
o.add_argument('--no-sandbox')
o.add_argument('--disable-gpu')
o.add_experimental_option('prefs', {"profile.exit_type": "Normal", "profile.exited_cleanly": True})
print("Test 5 = solo PREFS")
try:
    b = webdriver.Chrome(options=o)
    print(">>> EXITO (prefs OK)")
    b.quit()
except Exception as e:
    print(">>> FALLO (prefs es el culpable):", str(e)[:200])
