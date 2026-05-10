# SOPantallasADI - Sistema de Kiosco para Salas de Reuniones

SOPantallasADI es una aplicación de interfaz táctil/kiosco diseñada para optimizar la experiencia en salas de reuniones corporativas. Permite a los usuarios lanzar aplicaciones esenciales, controlar el volumen del sistema y visualizar el calendario de reuniones de Microsoft 365 de forma intuitiva y segura.

## 🚀 Características Principales

- **Modo Kiosco Estricto**: Bloqueo de teclas del sistema (Windows, Alt+Tab, etc.) para mantener la aplicación en primer plano.
- **Lanzador de Aplicaciones**: Acceso rápido a herramientas como Chrome, Teams, WinRAR y aplicaciones personalizadas.
- **Integración con Microsoft 365**: Visualización en tiempo real de las reuniones programadas en la sala mediante Microsoft Graph API.
- **Control de Volumen**: Deslizador integrado para gestionar el audio del sistema sin salir de la aplicación.
- **Panel de Administración**: Protegido por contraseña para configurar aplicaciones, IDs de Azure y otros ajustes.
- **Gestión de Sesión**: Botón de "Finalizar Reunión" que cierra automáticamente todas las aplicaciones abiertas para dejar la sala lista para el siguiente usuario.
- **Interfaz Corporativa**: Diseño moderno y limpio con estilos QSS personalizables.

## 🛠️ Tecnologías Utilizadas

- **Lenguaje**: Python 3.x
- **Interfaz Gráfica**: PyQt6
- **Seguridad**: MSAL (Microsoft Authentication Library) y `python-dotenv`
- **Utilidades de Sistema**: `psutil`, `keyboard` y ganchos de sistema (hooks).

## 📋 Requisitos Previos

- Python 3.8 o superior.
- Una aplicación registrada en **Microsoft Entra ID (Azure AD)** si se desea usar el calendario.
- Permisos de Administrador (necesarios para el bloqueo de teclas del sistema).

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/JuanitoJJ/SOPantallasADI.git
   cd SOPantallasADI
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   Copia el archivo de ejemplo y rellena tus datos:
   ```bash
   cp .env.example .env
   ```
   Edita el archivo `.env`:
   - `ADMIN_PASSWORD`: Contraseña para acceder al panel de configuración.
   - `CLIENT_ID`: ID de aplicación de Azure.
   - `TENANT_ID`: ID de inquilino de Azure (o `common`).

4. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```

## 🔒 Seguridad

Este proyecto utiliza variables de entorno para proteger información sensible. 
- **NUNCA** subas tu archivo `.env` o `token_cache.bin` a repositorios públicos.
- El archivo `.gitignore` ya está configurado para evitar fugas de datos accidentales.

## 🖥️ Estructura del Proyecto

- `main.py`: Punto de entrada de la aplicación.
- `core/`: Lógica de negocio (calendario, configuración, lanzador, hooks).
- `ui/`: Ventanas, diálogos y estilos (QSS).
- `assets/`: Iconos y recursos visuales.

---
Desarrollado para la gestión eficiente de entornos colaborativos.
