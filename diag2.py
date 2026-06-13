from selenium import webdriver
from selenium.webdriver.chrome.options import Options

o = Options()
o.add_argument('--no-sandbox')
o.add_argument('--disable-gpu')
o.add_argument('--user-data-dir=C:\\Users\\AI\\Desktop\\browser_cache')

print("Probando con el perfil del bot (Desktop\\browser_cache)...")
try:
    b = webdriver.Chrome(options=o)
    print(">>> EXITO: el perfil del Desktop funciona")
    b.quit()
    print(">>> cerro limpio")
except Exception as e:
    print(">>> FALLO:", str(e)[:400])
