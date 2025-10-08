# LoRaGuard - Prototipo de Sistema de Seguridad IoT con LoRaWAN

**LoRaGuard** es un prototipo de sistema de seguridad IoT usando LoRaWAN y backend Python. Detecta eventos (llenado, movimiento, apertura), aplica filtros inteligentes y envía alertas por App, WhatsApp y Telegram. Ideal para demo técnico y prueba de concepto.

## 🎯 Objetivo

Crear un prototipo funcional que demuestre el flujo end-to-end de sensores IoT usando LoRaWAN hasta un backend en Python que aplica filtros/algoritmos y envía alertas por App, WhatsApp y Telegram.

## 🏗️ Arquitectura

```
Sensores (simulados) → Gateway → Servidor LoRaWAN → Backend Python → Base de datos → Filtros/Algoritmos → Notificaciones → App/WhatsApp/Telegram → Dashboard
```

## 🚀 Características

- **3 tipos de sensores simulados**: nivel de tanque, sensor de movimiento, sensor de apertura de puerta
- **Backend Python con FastAPI**: API REST para recibir y procesar eventos
- **Base de datos PostgreSQL**: Almacenamiento de eventos y configuración
- **Sistema de filtros inteligentes**:
  - Filtro de llenado (nivel >= 90%)
  - Filtro de rebote (descarta duplicados en < 30s)
  - Filtro horario (movimiento fuera de horario)
  - Correlación de eventos simultáneos
- **Alertas multicanal**: WhatsApp, Telegram, Firebase Cloud Messaging
- **Dashboard web**: Visualización de eventos y estado del sistema
- **Simulador de sensores**: Generación de eventos de prueba

## 📋 Requisitos

- Python 3.11+
- PostgreSQL 13+
- Node.js 18+ (para el dashboard)
- Cuentas de API: Telegram Bot, WhatsApp Cloud API, Firebase

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd LoRaGuard
```

2. **Configurar entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**
```bash
# Crear base de datos PostgreSQL
createdb loraguard

# Ejecutar migraciones
python -m alembic upgrade head
```

5. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

6. **Ejecutar el sistema**
```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Dashboard (opcional)
cd dashboard && npm install && npm start

# Terminal 3: Simulador
python simulator/sensor_simulator.py
```

## 🧪 Casos de Prueba

### Caso A: Llenado de Tanque
```bash
python simulator/test_cases.py --case tank_fill
```

### Caso B: Falso Positivo (Debounce)
```bash
python simulator/test_cases.py --case false_positive
```

### Caso C: Correlación de Eventos
```bash
python simulator/test_cases.py --case correlation
```

### Caso D: Movimiento Fuera de Horario
```bash
python simulator/test_cases.py --case night_movement
```

## 📊 API Endpoints

### Recibir evento LoRaWAN
```http
POST /api/v1/events/lora
Content-Type: application/json

{
  "device_id": "sensor-tanque-01",
  "timestamp": "2025-01-03T12:34:56Z",
  "payload_raw": "base64-or-hex",
  "decoded": {
    "type": "nivel",
    "level": 95,
    "unit": "%"
  }
}
```

### Obtener eventos
```http
GET /api/v1/events?device_id=sensor-tanque-01&limit=50
```

### Simular evento
```http
POST /api/v1/admin/simulate
Content-Type: application/json

{
  "device_id": "sensor-mov-01",
  "type": "motion",
  "timestamp": "2025-01-03T00:10:00Z",
  "value": 1
}
```

## 🎬 Guion de Demo (10 minutos)

1. **Explicar arquitectura** (1 min)
2. **Ejecutar simulador - Caso A** (llenado) (3 min)
3. **Mostrar llegada de evento al backend** (1 min)
4. **Verificar notificaciones en Telegram/WhatsApp** (2 min)
5. **Ejecutar Caso C** (correlación) (2 min)
6. **Mostrar dashboard y código de filtros** (1 min)

## 🔧 Configuración de APIs

### Telegram Bot
1. Crear bot con @BotFather
2. Obtener token
3. Configurar en `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### WhatsApp Cloud API
1. Configurar cuenta de desarrollador
2. Obtener access token
3. Configurar en `.env`:
```
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
```

### Firebase Cloud Messaging
1. Crear proyecto en Firebase Console
2. Obtener server key
3. Configurar en `.env`:
```
FCM_SERVER_KEY=your_server_key
```

## 📁 Estructura del Proyecto

```
LoRaGuard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── alembic/
│   └── tests/
├── dashboard/
│   ├── src/
│   └── public/
├── simulator/
│   ├── sensor_simulator.py
│   └── test_cases.py
├── docs/
├── requirements.txt
├── .env.example
└── main.py
```

## 🚧 Próximos Pasos

- [ ] Integración con hardware real
- [ ] Autenticación y autorización
- [ ] Órdenes remotas a dispositivos
- [ ] Machine Learning para detección de anomalías
- [ ] Escalabilidad horizontal

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

---

**Desarrollado para demostración técnica y aprendizaje** 🚀

cd /Users/mrgomez/Desktop/Ejemplo && /Users/mrgomez/Desktop/Ejemplo/venv/bin/python3 /Users/mrgomez/Desktop/Ejemplo/simulate_telegram_alerts.py

## 🔐 Flujo 3FA (Contraseña + OTP Telegram + Cifrado)

### Variables necesarias
- En `config.env` define:
```
TELEGRAM_BOT_TOKEN=<token_de_tu_bot>
TELEGRAM_CHAT_ID=<tu_chat_id>
MASTER_KEY_B64=<clave_base64_de_32_bytes>
```
Para generar la clave: `python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"`.

### Backend
```bash
cd /Users/mrgomez/Desktop/Ejemplo
source venv/bin/activate
python main.py  # expone http://localhost:8000
```

### Frontend (Dashboard)
```bash
cd /Users/mrgomez/Desktop/Ejemplo/dashboard
npm install
npm start  # http://localhost:3000 con proxy a la API
```

### Pasos de uso en la UI
1. Registro: correo, contraseña, nombre completo y tu Telegram Chat ID.
2. Login: email + contraseña → la app pedirá OTP.
3. OTP: pulsa "Enviar OTP a Telegram", ingresa el código recibido y confirma.
4. Dashboard: verás la lista de archivos sensibles (cifrados en reposo). Puedes ver contenido o descargar `.txt` (descifrado tras OTP).

### Endpoints relevantes
- `POST /api/v1/auth/register` (registro en SQLite)
- `POST /api/v1/auth/login` (crea token de sesión persistente)
- `POST /api/v1/auth/request-otp?token=...` (envía OTP por Telegram)
- `POST /api/v1/auth/confirm-otp?token=...&otp_code=...` (valida OTP y habilita acceso)
- `GET /api/v1/files?token=...` (lista archivos)
- `GET /api/v1/files/{file_id}?token=...` (devuelve contenido descifrado)

Notas:
- Los archivos se almacenan cifrados con "envelope encryption" (AES-256-GCM) usando `MASTER_KEY_B64`.
- El token de sesión y el estado de OTP se persisten en SQLite (`session_tokens`).

cd /Users/mrgomez/Desktop/Ejemplo && source venv/bin/activate && python main.py
cd /Users/mrgomez/Desktop/Ejemplo/dashboard && npm start