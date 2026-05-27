# Ejemplos de Código Mejorado - Bot Parapark

Este documento muestra cómo refactorizar problemas específicos encontrados.

---

## 1️⃣ SEGURIDAD: Mover API Key a Variable de Entorno

### ❌ ACTUAL (INSEGURO)

```python
# booking_notifier_keep_browser_opened.py:59-64
openrouter_api_key_fp = os.path.join(sys.path[0], 'data', 'openrouter_api_key.txt')
if not os.path.exists(openrouter_api_key_fp):
    with open(openrouter_api_key_fp, 'w', encoding='utf-8') as f:
        f.write('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')
with open(openrouter_api_key_fp, 'r', encoding='utf-8') as f:
    openrouter_api_key = f.read().strip()
```

### ✅ MEJORADO (SEGURO)

```python
# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener API key desde variable de entorno
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY no está configurada.\n"
        "Crear archivo .env con:\nOPENROUTER_API_KEY=sk-or-v1-..."
    )

# Validar formato básico
if not OPENROUTER_API_KEY.startswith('sk-or-v1-'):
    raise ValueError("API key de OpenRouter inválida")
```

**Crear archivo `.env.example`:**
```bash
# .env.example (sin valores reales)
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
TURITOP_COMPANY_ID=P271
TURITOP_USER=your_username
TURITOP_PASSWORD=your_password
DEBUG=False
```

**Usar en el código:**
```python
from config import OPENROUTER_API_KEY

# Uso
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://parapark.com",
}
response = requests.post(api_url, headers=headers, json=payload)
```

**Instalación de dependencia:**
```bash
pip install python-dotenv
```

---

## 2️⃣ ARQUITECTURA: Extraer Clase Browser a Módulo Compartido

### ❌ ACTUAL (DUPLICADO)

```
booking_notifier_ts.py (755 líneas)
├─ Clase Browser (~200 líneas)
└─ Código específico (~555 líneas)

booking_notifier_keep_browser_opened.py (1575 líneas)
├─ Clase Browser (~200 líneas, DUPLICADA)
└─ Código específico (~1375 líneas)

test_photo_modules.py (1046 líneas)
├─ Clase Browser (~150 líneas, DUPLICADA)
└─ Código específico (~896 líneas)

TOTAL: ~550 líneas de código duplicado
```

### ✅ MEJORADO (MODULAR)

**Crear `src/browser.py`:**
```python
"""
browser.py - Wrapper de Selenium con métodos helper
"""
import time
import pickle
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class Browser:
    """Wrapper seguro para Selenium con manejo de errores"""

    def __init__(self, cache_dir: str = None, debug: bool = False):
        """
        Inicializar navegador Chrome

        Args:
            cache_dir: Directorio para caché del navegador
            debug: Mostrar errores detallados
        """
        self.debug = debug
        self.wait = WebDriverWait(None, 10)  # Se configura después
        self._init_driver(cache_dir)

    def _init_driver(self, cache_dir: str = None):
        """Inicializar webdriver con reintentos"""
        try:
            options = Options()

            # Usar caché dinámico si se proporciona
            if cache_dir:
                cache_path = Path(cache_dir) / 'browser_cache'
                cache_path.mkdir(parents=True, exist_ok=True)
                options.add_argument(f'--user-data-dir={cache_path}')

            options.add_argument('--log-level=3')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])

            # Descargar chromedriver con reintentos
            for attempt in range(3):
                try:
                    driver_path = ChromeDriverManager().install()
                    break
                except Exception as e:
                    logger.warning(f"Intento {attempt+1}/3 para descargar driver: {e}")
                    time.sleep(10)
            else:
                raise RuntimeError("Fallo al descargar ChromeDriver después de 3 intentos")

            service = Service(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_window_size(width=1100, height=850)
            self.wait = WebDriverWait(self.driver, 10)

            logger.info("Navegador inicializado correctamente")

        except Exception as e:
            logger.error(f"Error inicializando navegador: {e}", exc_info=True)
            raise

    def get(self, url: str, retries: int = 3) -> bool:
        """Navegar a URL con reintentos"""
        for attempt in range(retries):
            try:
                self.driver.get(url)
                return True
            except Exception as e:
                logger.warning(f"Intento {attempt+1}/{retries} para acceder a {url}: {e}")
                time.sleep(0.5)
        return False

    def click_css(self, selector: str, timeout: int = 10) -> bool:
        """Click en elemento CSS con espera explícita"""
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except Exception as e:
            logger.error(f"Error clicking {selector}: {e}")
            return False

    def click_xpath(self, xpath: str, timeout: int = 10) -> bool:
        """Click en elemento XPath con espera explícita"""
        try:
            element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return True
        except Exception as e:
            logger.error(f"Error clicking XPath {xpath}: {e}")
            return False

    def get_text(self, selector: str, by: By = By.CSS_SELECTOR) -> str:
        """Obtener texto de elemento"""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((by, selector))
            )
            return element.get_attribute('innerText').strip()
        except Exception as e:
            logger.error(f"Error getting text from {selector}: {e}")
            return ''

    def get_attr(self, selector: str, attr: str, by: By = By.CSS_SELECTOR) -> str:
        """Obtener atributo HTML"""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((by, selector))
            )
            return element.get_attribute(attr).strip()
        except Exception as e:
            logger.error(f"Error getting attribute {attr} from {selector}: {e}")
            return ''

    def send_keys(self, selector: str, text: str, clear: bool = True) -> bool:
        """Escribir en campo"""
        try:
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            if clear:
                element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            logger.error(f"Error sending keys to {selector}: {e}")
            return False

    def save_cookies(self, filepath: str) -> bool:
        """Guardar cookies de forma segura"""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            cookies = self.driver.get_cookies()

            # Aquí: En futuro, encriptar
            with open(path, 'wb') as f:
                pickle.dump(cookies, f)

            logger.info(f"Cookies guardadas en {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False

    def load_cookies(self, filepath: str) -> bool:
        """Cargar cookies"""
        try:
            path = Path(filepath)
            if not path.exists():
                logger.warning(f"Archivo de cookies no existe: {filepath}")
                return False

            with open(path, 'rb') as f:
                cookies = pickle.load(f)

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Error adding cookie: {e}")

            logger.info(f"Cookies cargadas desde {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False

    def quit(self):
        """Cerrar navegador"""
        try:
            self.driver.quit()
            logger.info("Navegador cerrado")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
```

**Usar en scripts:**
```python
# booking_notifier.py
from src.browser import Browser
from config import BROWSER_CACHE_DIR

# Inicializar
browser = Browser(cache_dir=BROWSER_CACHE_DIR)

# Usar
browser.get("https://app.turitop.com/...")
browser.click_css("button.submit")
text = browser.get_text("div.title")

# Cerrar
browser.quit()
```

---

## 3️⃣ LOGGING: Sistema Estructurado

### ❌ ACTUAL

```python
# Múltiples formas de logging inconsistentes
print("starting browser.")
print(str(error))
self.show_error(error)
# Todo a stdout, sin persistencia
```

### ✅ MEJORADO

**Crear `src/logging_config.py`:**
```python
"""
logging_config.py - Configuración centralizada de logging
"""
import logging
import logging.handlers
from pathlib import Path

def setup_logging(
    name: str = "parapark_bot",
    log_dir: Path = Path("data/logs"),
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configurar logger con handlers para archivo y consola
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formato
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler: Archivo (con rotación)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / f"{name}.log",
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler: Consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Uso
logger = setup_logging()
```

**En scripts:**
```python
from src.logging_config import setup_logging

logger = setup_logging()

logger.info("Iniciando bot")
logger.debug(f"Scraping {total} reservas")
logger.warning("Cookie expirando pronto")
logger.error("Error fatal", exc_info=True)
```

---

## 4️⃣ ERRORES: Manejo Específico

### ❌ ACTUAL

```python
try:
    return re.findall(re_pattern, raw_text)[0].strip()
except:  # Bare except - oculta bugs
    return ''

try:
    self.web_browser.find_element(By.CSS_SELECTOR, element).click()
except Exception as e:  # Demasiado genérico
    pass
```

### ✅ MEJORADO

```python
import re
import logging
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)

logger = logging.getLogger(__name__)

def extract_regex(pattern: str, text: str, default: str = '') -> str:
    """
    Extraer texto usando regex con manejo específico de errores
    """
    try:
        match = re.findall(pattern, text)
        if not match:
            logger.debug(f"No regex match for pattern: {pattern}")
            return default
        return match[0].strip()
    except re.error as e:
        logger.error(f"Invalid regex pattern {pattern}: {e}")
        return default
    except AttributeError as e:
        logger.error(f"Invalid input type for regex: {e}")
        return default

def safe_click(driver, selector: str, timeout: int = 10) -> bool:
    """Click seguro con manejo específico de excepciones"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        element.click()
        return True

    except NoSuchElementException:
        logger.error(f"Elemento no encontrado: {selector}")
        return False

    except TimeoutException:
        logger.error(f"Timeout esperando elemento: {selector}")
        return False

    except StaleElementReferenceException:
        logger.error(f"Elemento obsoleto (DOM cambió): {selector}")
        return False

    except Exception as e:
        logger.error(f"Error inesperado al hacer click: {e}", exc_info=True)
        return False

# Validación de datos
class BookingDataValidator:
    """Validar datos de reserva"""

    @staticmethod
    def validate_booking(booking: dict) -> tuple[bool, list]:
        """
        Validar que booking tenga todos los campos requeridos

        Returns:
            (es_válido, lista_de_errores)
        """
        errors = []
        required_fields = [
            'booking_time', 'booking_day', 'booking_month',
            'booking_place', 'wa_link'
        ]

        for field in required_fields:
            if field not in booking or not booking[field]:
                errors.append(f"Campo requerido faltante: {field}")

        # Validar formato de hora
        if 'booking_time' in booking:
            if not re.match(r'^\d{2}:\d{2}$', booking['booking_time']):
                errors.append(f"Formato de hora inválido: {booking['booking_time']}")

        # Validar formato de WhatsApp
        if 'wa_link' in booking:
            if not booking['wa_link'].startswith(('https://api.whatsapp.com', 'https://chat.whatsapp.com')):
                errors.append("URL de WhatsApp inválida")

        return len(errors) == 0, errors

# Uso
is_valid, errors = BookingDataValidator.validate_booking(booking_data)
if not is_valid:
    logger.error(f"Booking inválido: {', '.join(errors)}")
    return False
```

---

## 5️⃣ CONFIGURACIÓN: Centralizada en Archivo

### ❌ ACTUAL

```python
# Valores hardcodeados en múltiples lugares
days_to_check_for_booking = 4
send_messages_to_clients_one_day_before = 0
# ... 30+ variables más
```

### ✅ MEJORADO

**Crear `config/settings.ini`:**
```ini
[booking]
days_to_check = 4
send_one_day_before = False
min_hour = 10
max_hour = 21

[turitop]
url = https://app.turitop.com
company_id = P271
bookings_endpoint = /admin/company/{company_id}/bookings

[whatsapp]
web_url = https://web.whatsapp.com
group_link_colleagues = https://web.whatsapp.com/accept?code=...
timeout_per_message = 15

[photos]
group_name = Parapark Fotos 2026
group_link = https://chat.whatsapp.com/...
enable = True
ai_model = mistral-7b-instruct

[paths]
data_dir = ./data
logs_dir = ./data/logs
templates_dir = ./data/templates
cache_dir = ./data/cache

[openai]
provider = openrouter
# api_key viene de .env
```

**Crear `src/config.py`:**
```python
"""
config.py - Carga configuración desde archivo y variables de entorno
"""
import os
import configparser
from pathlib import Path
from typing import Any

class Config:
    """Configuración centralizada"""

    def __init__(self, config_file: str = "config/settings.ini"):
        self.parser = configparser.ConfigParser()
        self.parser.read(config_file)

        # Crear directorios si no existen
        data_dir = Path(self.get('paths', 'data_dir'))
        data_dir.mkdir(exist_ok=True)
        (data_dir / 'logs').mkdir(exist_ok=True)
        (data_dir / 'templates').mkdir(exist_ok=True)
        (data_dir / 'cache').mkdir(exist_ok=True)

    def get(self, section: str, option: str, fallback: Any = None) -> Any:
        """Obtener valor con fallback"""
        try:
            return self.parser.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise

    def get_int(self, section: str, option: str, fallback: int = None) -> int:
        try:
            return self.parser.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_bool(self, section: str, option: str, fallback: bool = None) -> bool:
        try:
            return self.parser.getboolean(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def get_env(self, key: str, fallback: str = None) -> str:
        """Obtener de variable de entorno con fallback"""
        return os.getenv(key, fallback)

# Uso global
config = Config()

# En scripts
from src.config import config

days_to_check = config.get_int('booking', 'days_to_check')
turitop_url = config.get('turitop', 'url')
openrouter_key = config.get_env('OPENROUTER_API_KEY')
```

---

## 6️⃣ TESTING: Ejemplo de Test Unitario

### ✅ NUEVO

**Crear `tests/test_browser.py`:**
```python
"""
test_browser.py - Tests para clase Browser
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.browser import Browser
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class TestBrowser:
    """Suite de tests para Browser"""

    @pytest.fixture
    def browser(self):
        """Fixture: crear browser mock para tests"""
        with patch('src.browser.ChromeDriverManager'):
            with patch('src.browser.webdriver.Chrome'):
                browser = Browser()
                browser.driver = MagicMock()
                browser.wait = MagicMock()
                return browser

    def test_get_url_success(self, browser):
        """Test: navegación exitosa"""
        result = browser.get("https://example.com")
        assert result is True
        browser.driver.get.assert_called_once()

    def test_get_url_with_retry(self, browser):
        """Test: reintento después de fallo"""
        browser.driver.get.side_effect = [Exception("Network"), None]
        result = browser.get("https://example.com", retries=2)
        assert result is True
        assert browser.driver.get.call_count == 2

    def test_click_css_success(self, browser):
        """Test: click exitoso"""
        mock_element = MagicMock()
        browser.wait.until.return_value = mock_element

        result = browser.click_css("button.submit")
        assert result is True
        mock_element.click.assert_called_once()

    def test_click_css_element_not_found(self, browser):
        """Test: elemento no encontrado"""
        browser.wait.until.side_effect = NoSuchElementException()
        result = browser.click_css("button.missing")
        assert result is False

    def test_click_css_timeout(self, browser):
        """Test: timeout esperando elemento"""
        browser.wait.until.side_effect = TimeoutException()
        result = browser.click_css("button.slow", timeout=1)
        assert result is False

    def test_get_text_success(self, browser):
        """Test: extracción de texto"""
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "  Hello World  "
        browser.wait.until.return_value = mock_element

        result = browser.get_text("div.content")
        assert result == "Hello World"

    def test_save_cookies(self, browser, tmp_path):
        """Test: guardar cookies"""
        cookies = [{'name': 'test', 'value': '123'}]
        browser.driver.get_cookies.return_value = cookies

        filepath = tmp_path / "cookies.pkl"
        result = browser.save_cookies(str(filepath))

        assert result is True
        assert filepath.exists()

    def test_load_cookies(self, browser, tmp_path):
        """Test: cargar cookies"""
        import pickle

        cookies = [{'name': 'test', 'value': '123'}]
        filepath = tmp_path / "cookies.pkl"

        with open(filepath, 'wb') as f:
            pickle.dump(cookies, f)

        result = browser.load_cookies(str(filepath))
        assert result is True
        assert browser.driver.add_cookie.called

# Ejecutar: pytest tests/test_browser.py
```

---

## 7️⃣ ESTRUCTURA: Propuesta de Reorganización

### ✅ NUEVA ESTRUCTURA

```
parapark-bot/
├── .env.example              # Plantilla de variables de entorno
├── .env                       # Variables de entorno (GITIGNORED)
├── .gitignore                 # Ignorar archivos sensibles
├── requirements.txt           # Dependencias
├── README.md                  # Documentación
├── config/
│   └── settings.ini           # Configuración centralizada
├── src/
│   ├── __init__.py
│   ├── browser.py             # Clase Browser compartida
│   ├── config.py              # Gestión de configuración
│   ├── logging_config.py      # Setup de logging
│   ├── validators.py          # Validadores de datos
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── turitop.py         # Web scraper de Turitop
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   ├── client.py          # Envío a clientes
│   │   └── group.py           # Envío a grupo
│   ├── photos/
│   │   ├── __init__.py
│   │   ├── downloader.py      # Descargar fotos
│   │   ├── matcher.py         # Matching con IA
│   │   └── sender.py          # Envío de fotos
│   └── models/
│       ├── __init__.py
│       └── booking.py         # Modelo de datos
├── tests/
│   ├── __init__.py
│   ├── test_browser.py
│   ├── test_scrapers.py
│   ├── test_validators.py
│   └── fixtures/
│       └── sample_data.json
├── data/
│   ├── logs/                  # Archivos de log (GITIGNORED)
│   ├── cache/                 # Cache del navegador (GITIGNORED)
│   ├── templates/             # Plantillas de mensajes
│   │   ├── client_message.txt
│   │   └── thank_you.txt
│   └── migrations/            # Schema de DB si se usa
├── scripts/
│   ├── booking_notifier.py    # Script principal
│   ├── photo_manager.py       # Gestor de fotos
│   └── maintenance.py         # Tareas de mantenimiento
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEPLOYMENT.md
```

**Crear `.gitignore`:**
```bash
# Archivos de sistema
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
.eggs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Secretos y credenciales
.env
.env.local
*.pkl
data/logs/
data/cache/
data/*.txt
data/*.json
!data/templates/
!data/migrations/

# Pytest
.pytest_cache/
.coverage
htmlcov/

# Otros
*.log
*.tmp
build/
dist/
*.egg-info/
```

---

## 8️⃣ SCRIPT PRINCIPAL: Refactorizado

**Crear `scripts/booking_notifier.py`:**
```python
"""
booking_notifier.py - Script principal para notificaciones de reservas
"""
import logging
import time
from pathlib import Path
from datetime import datetime

from src.config import config
from src.logging_config import setup_logging
from src.browser import Browser
from src.scrapers.turitop import TuritopScraper
from src.whatsapp.client import WhatsAppClientNotifier
from src.whatsapp.group import WhatsAppGroupNotifier

# Setup logging
logger = setup_logging()

def main():
    """Función principal"""
    browser = None

    try:
        logger.info("=" * 50)
        logger.info("Iniciando Parapark Notification Bot")
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info("=" * 50)

        # Configuración
        cache_dir = Path(config.get('paths', 'cache_dir'))
        days_to_check = config.get_int('booking', 'days_to_check')

        # Inicializar componentes
        browser = Browser(cache_dir=str(cache_dir))
        scraper = TuritopScraper(browser)
        client_notifier = WhatsAppClientNotifier(browser)
        group_notifier = WhatsAppGroupNotifier(browser)

        # Scraping
        logger.info(f"Scraping reservas próximos {days_to_check} días")
        bookings = scraper.get_bookings(days=days_to_check)
        logger.info(f"Se encontraron {len(bookings)} reservas")

        # Envío a clientes
        logger.info("Enviando confirmaciones a clientes")
        for booking in bookings:
            try:
                client_notifier.notify(booking)
                time.sleep(15)  # Esperar entre mensajes
            except Exception as e:
                logger.error(f"Error enviando a cliente: {e}", exc_info=True)

        # Notificación al grupo
        logger.info("Sincronizando con grupo de colegas")
        group_notifier.sync(bookings)

        logger.info("Bot completado exitosamente")

    except KeyboardInterrupt:
        logger.info("Bot interrumpido por usuario")
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        return 1
    finally:
        if browser:
            browser.quit()

    return 0

if __name__ == "__main__":
    exit(main())
```

---

## Resumen de Cambios

| Problema | Solución | Archivo |
|----------|----------|---------|
| API key expuesta | Variables de entorno | `.env`, `config.py` |
| Código duplicado | Módulo compartido | `src/browser.py` |
| Sin logging | Sistema centralizado | `src/logging_config.py` |
| Errores genéricos | Excepciones específicas | `src/validators.py` |
| Valores hardcodeados | Archivo de configuración | `config/settings.ini` |
| Sin tests | Suite de pytest | `tests/` |
| Estructura caótica | Modular y escalable | Nueva estructura |

---

**Continúa con la implementación de estos cambios en orden de prioridad**
