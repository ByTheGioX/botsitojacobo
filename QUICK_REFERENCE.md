# Referencia Rápida - Bot Parapark

## 📄 Documentos de la Revisión

```
📋 EXECUTIVE_SUMMARY.md
   └─ Empieza aquí (10 min read)
   └─ Overview general y top problemas

📋 CODE_REVIEW.md
   └─ Análisis técnico detallado (30 min read)
   └─ 16 problemas específicos con código

📋 FUNCTIONAL_ANALYSIS.md
   └─ ¿Cómo funciona? (20 min read)
   └─ Flujos de datos y módulos

📋 IMPROVEMENT_EXAMPLES.md
   └─ ¿Cómo arreglarlo? (25 min read)
   └─ Código mejorado y ejemplos
```

---

## 🎯 Checklist: Problemas Críticos

### AHORA (Hoy - 30 minutos)

- [ ] **API KEY EXPUESTA**
  - ⚠️ Ubicación: `bot/data/openrouter_api_key.txt`
  - 📋 Acción: Rotar en OpenRouter
  - 📋 Mover a `.env` en variable `OPENROUTER_API_KEY`

- [ ] **CREAR .gitignore**
  - 📋 Agregar: `.env`, `*.pkl`, `data/logs/`

- [ ] **CREAR .env**
  - 📋 Copiar desde `.env.example`
  - 📋 Llenar credenciales

- [ ] **GIT CLEANUP**
  - Ejecutar: `git rm --cached bot/data/openrouter_api_key.txt`

---

### ESTA SEMANA (2-3 horas)

- [ ] **EXTRAER Browser a módulo**
  - Crear: `src/browser.py`
  - Remover de: `booking_notifier_ts.py`
  - Remover de: `booking_notifier_keep_browser_opened.py`
  - Remover de: `test_photo_modules.py`

- [ ] **AGREGAR LOGGING**
  - Crear: `src/logging_config.py`
  - Implementar en todos los scripts

- [ ] **CREAR requirements.txt**
  - Ejecutar: `pip freeze > requirements.txt`
  - Revisar y limpiar versiones

---

### PRÓXIMA SEMANA (4-5 horas)

- [ ] **REFACTORIZAR EXCEPCIONES**
  - Remover bare `except:`
  - Usar excepciones específicas
  - Agregar logging

- [ ] **CREAR ESTRUCTURA**
  - Crear carpetas: `src/`, `tests/`, `config/`
  - Reorganizar archivos

- [ ] **CREAR CONFIG.INI**
  - Crear: `config/settings.ini`
  - Mover valores hardcodeados

---

### PRÓXIMO MES (8-10 horas)

- [ ] **TESTS UNITARIOS**
  - Crear: `tests/test_browser.py`
  - Crear: `tests/test_validators.py`
  - Target: 50% coverage

- [ ] **DOCUMENTACIÓN**
  - API pública
  - Guía de instalación
  - Guía de configuración

- [ ] **USAR WebDriverWait**
  - Reemplazar loops de espera
  - Usar `EC.*` (expected_conditions)

---

## 🔍 Auditoría Rápida

### Verificar Estos Archivos Primero

```
❓ ¿API key en el código?
   grep -r "sk-or-v1-" bot/
   grep -r "openrouter_api_key" bot/
   ❌ Si encuentra algo: CRÍTICO

❓ ¿Credenciales hardcodeadas?
   grep -r "password\|usuario" bot/
   grep -r "api_key\|token" bot/
   ❌ Si encuentra algo: CRÍTICO

❓ ¿URLs privadas?
   grep -r "chat.whatsapp.com" bot/
   grep -r "g.page/r/" bot/
   ❌ Si encuentra algo: ALTO

❓ ¿Bare exceptions?
   grep -r "except:" bot/*.py
   ❌ Deberían ser: NINGUNO

❓ ¿Archivos sin cerrar?
   grep -r "open(" bot/*.py | grep -v "with"
   ❌ Deberían ser: NINGUNO
```

---

## 📊 Estadísticas Actuales

```
Líneas totales de código:        3,603
Líneas de código duplicado:       ~550 (45%)
Archivos Python:                    4
Métodos en Browser:                15
Problemas identificados:            16
Problemas críticos:                 5
Problemas altos:                    5
Problemas medios:                   6

Coverage de tests:              0% (NULO)
Archivos con logging:            0% (NULO)
Archivos con docstrings:        10% (MUY BAJO)
Configuración centralizada:      0% (NULO)
```

---

## 🚀 Scripts de Utilidad

### Verificar Código

```bash
# Buscar problemas de seguridad
python -m bandit bot/*.py

# Verificar estilo PEP8
python -m pylint bot/*.py

# Encontrar código duplicado
python -m radon cc bot/*.py

# Analizar complejidad
python -m radon metrics bot/*.py
```

### Limpiar & Preparar

```bash
# Crear estructura
mkdir -p src/scrapers src/whatsapp src/photos tests config

# Crear .gitignore
cat > .gitignore << 'EOF'
.env
.env.local
*.pkl
data/logs/
data/cache/
data/downloaded_photos/
__pycache__/
.pytest_cache/
.coverage
*.pyc
.venv/
EOF

# Instalar dev dependencies
pip install black pylint pytest pytest-cov selenium webdriver-manager python-dotenv
```

---

## 📞 Preguntas Frecuentes

### P: ¿Por dónde empiezo?
R: Lee `EXECUTIVE_SUMMARY.md` (10 min), luego decide prioridades.

### P: ¿Qué es lo más urgente?
R: Rotar API key de OpenRouter y mover a `.env` (30 min)

### P: ¿Necesito detener el bot?
R: No, puedes ir arreglando gradualmente.

### P: ¿Cuánto tiempo toma refactorizar todo?
R: ~20-30 horas distribuidas en 2-3 meses si haces todo.

### P: ¿Necesito reescribir todo?
R: No. Mantener la funcionalidad, mejorar estructura e seguridad.

### P: ¿Qué pasa si alguien usa mi API key?
R: 1. Rotar inmediatamente 2. Revisar factura OpenRouter

---

## 🛠️ Herramientas Recomendadas

### Instalación (pip)

```bash
# Dependencias principales
pip install selenium webdriver-manager requests

# Desarrollo
pip install pytest pytest-cov black pylint bandit

# Seguridad
pip install python-dotenv cryptography

# Logging
pip install python-json-logger

# Configuración
pip install configparser
```

### Editor/IDE

- VS Code (recomendado)
- PyCharm Community
- Vim/Neovim

### Git

```bash
# Ver cambios
git diff

# Ver commits
git log --oneline

# Crear rama
git checkout -b feature/refactor-browser
```

---

## 📈 Métricas Antes/Después

### Actual
```
Seguridad:            2/10 🔴
Mantenibilidad:       3/10 🔴
Escalabilidad:        4/10 🔴
Tests:                0/10 🔴
Documentación:        1/10 🔴
```

### Después de Refactorizar
```
Seguridad:            8/10 ✅
Mantenibilidad:       8/10 ✅
Escalabilidad:        8/10 ✅
Tests:                7/10 ✅
Documentación:        8/10 ✅
```

---

## 📚 Recursos Rápidos

### Python & Selenium
- [Selenium Docs](https://selenium-python.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)
- [pytest Documentation](https://docs.pytest.org/)

### Seguridad
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
- [cryptography](https://cryptography.io/)

### Best Practices
- [12 Factor App](https://12factor.net/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Real Python Articles](https://realpython.com/)

---

## ✅ Checklist Final

Antes de considerar "completo":

- [ ] Todas las credenciales en `.env`
- [ ] `.gitignore` creado y actualizado
- [ ] `Browser` en módulo compartido
- [ ] Logging centralizado
- [ ] Exceptions específicas
- [ ] Tests básicos (50%+ coverage)
- [ ] Documentación de API
- [ ] Código formateado (black)
- [ ] Sin warnings (pylint)
- [ ] Sin vulnerabilidades (bandit)

---

## 🎯 TL;DR

1. **Leer:** EXECUTIVE_SUMMARY.md
2. **Hacer:** Rotar API key + crear .env
3. **Seguir:** Plan de acción por prioridad
4. **Implementar:** Ejemplos de IMPROVEMENT_EXAMPLES.md
5. **Validar:** Checklist final

---

**Última actualización:** 24/03/2026
**Versión:** 1.0
**Estado:** Listo para implementar
