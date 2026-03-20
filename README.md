<div align="center">
  <img src="icon.ico" width="128" />
  <h1>⚡ SupeRois</h1>
  <p><strong>El Gestor Definitivo de Combos y Macros para Juegos de Lucha Retro</strong></p>
  <p>
    Soporte 100% nativo para <b>FightCade 2</b> y <b>FBNeo</b> mediante simulación de Hardware e inyección DirectInput.
  </p>
</div>

---

## 📖 Descripción

**SupeRois** (anteriormente SuperRoyce) es una herramienta de asistencia y entrenamiento para juegos arcade (Street Fighter, KOF, Mortal Kombat, etc.). Su interfaz limpia y moderna, construida con `customtkinter` en Python, te permite armar secuencias exactas, guardarlas por personaje, y ejecutarlas en tiempo real con solo tocar una tecla.

A diferencia de otras herramientas de automatización, **SupeRois está diseñado específicamente para evadir y funcionar junto a los bloqueos Anti-Macros a bajo nivel que tienen los emuladores arcade** como FBNeo gracias a sus dos motores de inyección.

## ✨ Características Principales

- **🎮 Motor de Joystick Virtual (Kernel Level)**: Utilizando **ViGEmBus**, SupeRois se hace pasar por un Joystick físico real de Xbox 360 conectado por USB a Windows, volviéndolo 100% indetectable y compatible con los inputs Raw del emulador.
- **⌨️ Inyección DirectInput Avanzada**: Para quienes no usan el modo Joystick, inyecta `Scancodes` de hardware puros y sostiene las teclas exactamente **50ms (3 frames)** para sortear el _Polling Loop (60Hz)_ de Fightcade.
- **🪞 Modo Espejo Dinámico**: Intercambia instantáneamente todas las direcciones izquierda/derecha de tu macro en función del lado en el que haya caído tu personaje.
- **⏱ Delay y "Hold" Configurable**: Ajusta tiempos individuales entre inputs, y delays previos para que te dé tiempo a hacer Alt+Tab hacia el juego.
- **📦 Base de Datos de Juegos**: Incluye plantillas y configuraciones para *SF Alpha 3, SF III 3rd Strike, MK2, KoF 98* y más.

---

## 📸 Interfaz y Pantallas

*(Agrega aquí tus capturas de pantalla de la app en la carpeta `docs/` o `images/`)*

<div align="center">
  <img src="https://via.placeholder.com/600x400?text=Captura+Principal+de+SupeRois" alt="Interfaz Principal" />
  <img src="https://via.placeholder.com/600x400?text=Editor+de+Combos" alt="Editor de Combos" />
</div>

---

## 🚀 Instalación y Uso (Usuario Final)

Si solo quieres usar el programa sin programar nada:

1. Ve a la sección de [Releases](../../releases) a la derecha de GitHub.
2. Descarga la carpeta **SupeRois_Release**.
3. Haz doble clic en `SupeRois.exe` **(IMPORTANTE: Ejecutar como Administrador para habilitar la inyección de teclado)**.
4. Elije tu juego, selecciona tu personaje y dale a "+ Nuevo Combo".

### 🕹️ Modulo ViGEmBus (Soporte Anti-Cheat)
Si Fightcade rechaza tu inyección de teclado por seguridad (ocurre a veces), sigue estos 3 pasos infalibles:
1. Instala el driver oficial de [ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) en tu PC.
2. Abre SupeRois. Verás un mensaje en verde arriba a la derecha indicando: `🎮 vgamepad: OK`.
3. Entra a las configuraciones de Fightcade (F5) y mapea tu control del Player 1 presionando los botones desde la interfaz de SupeRois (Ej: click en Ejecutar para que envíe los inputs). Ahora eres indetectable.

---

## 🛠️ Compilar y Desarrollar (Source Code)

Si quieres aportar al proyecto o compilarlo por ti mismo:

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/SupeRois.git
cd SupeRois
```

### 2. Instalar dependencias
Asegúrate de tener Python 3.10 o superior instalado.
```bash
pip install -r requirements.txt
# O manualmente:
pip install customtkinter Pillow pygame vgamepad pyinstaller
```

### 3. Ejecutar en modo desarrollo
```bash
python main.py
```

### 4. Compilar a `.exe` (Build automático)
SupeRois incluye un script de compilación para Windows en PowerShell. Limpiará todo, empaquetará la app con el ícono del rayo dorado (`icon.ico`) y organizará las carpetas `/data` y `/config` junto al binario.
```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```
Al finalizar, tendrás una carpeta limpia llamada `SupeRois_Release` lista en tu Escritorio para ser distribuida.

---

## 📂 Estructura del Código

- `/core/` - Contiene la lógica del negocio: el inyector de Scancodes (`direct_input.py`), el comunicador con ViGEmBus (`virtual_gamepad.py`), el ejecutor multi-hilo (`executor.py`) y almacenamiento (`storage.py`).
- `/ui/` - La interfaz gráfica. Ventana de configuraciones (`settings_dialog.py`) y flujo principal (`app.py`).
- `/data/` - Aquí se guardan los archivos JSON de los combos de cada juego.
- `/config/` - Archivo `settings.json` (atajos globales, etc.) y `games.json` (base de datos con el esquema de botones por juego).
- `create_icon.py` - Script secundario útil para generar `.ico` basado en Polígonos usando la librería Pillow.

---

<div align="center">
  Hecho con ⚡ & 🕹️
</div>
