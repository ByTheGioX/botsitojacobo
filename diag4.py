from selenium import webdriver
from selenium.webdriver.chrome.options import Options

o = Options()
o.add_argument('--user-data-dir=C:\\Users\\AI\\Desktop\\browser_cache')
o.add_argument('--no-sandbox')
o.add_argument('--disable-gpu')
o.add_argument('--log-level=3')
o.add_argument('--disable-session-crashed-bubble')
o.add_experimental_option('excludeSwitches', ['enable-automation'])
o.add_experimental_option('prefs', {"profile.exit_type": "Normal", "profile.exited_cleanly": True})

print("Probando config FINAL del bot...")
try:
    b = webdriver.Chrome(options=o)
    print(">>> EXITO: config final funciona")
    b.quit()
    print(">>> cerro limpio")
except Exception as e:
    print(">>> FALLO:", str(e)[:400])
