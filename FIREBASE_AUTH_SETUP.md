# 🔥 Configuración de Firebase Authentication (Google Sign-In)

Esta guía te ayudará a configurar Firebase Authentication para usar Google Sign-In en el proyecto.

---

## 📋 Pasos de Configuración

### 1️⃣ Acceder a Firebase Console

1. Ve a **[Firebase Console](https://console.firebase.google.com/)**
2. Inicia sesión con tu cuenta de Google

### 2️⃣ Seleccionar o Crear Proyecto

**Opción A: Usar proyecto existente**
- Haz clic en el proyecto que ya tienes

**Opción B: Crear nuevo proyecto**
1. Haz clic en **"Agregar proyecto"** o **"Add project"**
2. Ingresa un nombre (por ejemplo: `loraguard-secure`)
3. (Opcional) Desactiva Google Analytics si no lo necesitas
4. Haz clic en **"Crear proyecto"**

### 3️⃣ Habilitar Google Authentication

1. En el menú lateral, ve a **Authentication** (🔐 Autenticación)
2. Haz clic en **"Get Started"** si es la primera vez
3. Ve a la pestaña **"Sign-in method"**
4. Haz clic en **"Google"** en la lista de proveedores
5. **Activa** el switch de "Enable" (Habilitar)
6. Configura:
   - **Project public-facing name**: Nombre que verán los usuarios (ej: "LoRaGuard Dashboard")
   - **Project support email**: Tu email
7. Haz clic en **"Guardar"** / **"Save"**

### 4️⃣ Obtener Firebase Project ID

1. En Firebase Console, haz clic en el ⚙️ (engranaje) junto a "Project Overview"
2. Selecciona **"Configuración del proyecto"** / **"Project settings"**
3. En la pestaña **"General"**, busca **"Project ID"**
4. Copia el Project ID (ejemplo: `loraguard-secure-12345`)

### 5️⃣ Obtener Firebase Configuration

1. En **Project settings** → pestaña **"General"**
2. Baja hasta **"Your apps"** (Tus apps)
3. Haz clic en el ícono **Web** (`</>`)
4. Registra tu app:
   - App nickname: `LoRaGuard Dashboard`
   - No necesitas habilitar Firebase Hosting
5. Copia la configuración que aparece (se ve así):

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "tu-proyecto.firebaseapp.com",
  projectId: "tu-proyecto-id",
  storageBucket: "tu-proyecto.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

---

## 🔧 Configuración en el Proyecto

### Backend (Python FastAPI)

Edita el archivo `config.env` en la raíz del proyecto:

```bash
# Firebase Project ID (usado para validar tokens)
GOOGLE_CLIENT_ID=tu-proyecto-id
```

**Ejemplo real:**
```bash
GOOGLE_CLIENT_ID=loraguard-secure-12345
```

### Frontend (React Dashboard)

Edita el archivo `dashboard/src/firebaseConfig.js`:

```javascript
const firebaseConfig = {
  apiKey: "TU_API_KEY",
  authDomain: "tu-proyecto.firebaseapp.com",
  projectId: "tu-proyecto-id",
  storageBucket: "tu-proyecto.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

Reemplaza cada valor con los que obtuviste en el paso 5️⃣.

---

## 🧪 Probar la Configuración

1. **Reinicia el backend:**
   ```bash
   # Detén el servidor con Ctrl+C
   cd /Users/mrgomez/Desktop/Ejemplo
   ./venv/bin/python3 main.py
   ```

2. **Reinicia el frontend:**
   ```bash
   # Detén el servidor con Ctrl+C
   cd /Users/mrgomez/Desktop/Ejemplo/dashboard
   npm start
   ```

3. **Prueba el login:**
   - Ve a `http://localhost:3000`
   - Haz clic en **"Continuar con Google"**
   - Deberías ver el selector de cuenta de Google
   - Al seleccionar una cuenta, se te pedirá tu Telegram Chat ID (solo la primera vez)
   - Luego se te enviará un OTP por Telegram

---

## 🔍 Verificar que Funciona

### En Firebase Console:

1. Ve a **Authentication** → pestaña **"Users"**
2. Después de hacer login, deberías ver tu usuario listado

### En los logs del backend:

```
INFO: Token de Firebase validado para: tu-email@gmail.com (issuer: https://securetoken.google.com/tu-proyecto-id)
INFO: Audit event logged: user_login_success by tu-email@gmail.com (Severity: info)
```

---

## ❓ Problemas Comunes

### Error: "Token inválido: Issuer esperado..."

**Causa:** El `GOOGLE_CLIENT_ID` en `config.env` no coincide con el Project ID de Firebase.

**Solución:**
1. Verifica que el `GOOGLE_CLIENT_ID` sea exactamente el Project ID
2. Reinicia el backend después de cambiar `config.env`

### Error: "GOOGLE_CLIENT_ID (Firebase Project ID) no configurado"

**Causa:** No se cargó el archivo `config.env` o la variable está vacía.

**Solución:**
1. Asegúrate de que `config.env` existe en `/Users/mrgomez/Desktop/Ejemplo/`
2. Verifica que la línea `GOOGLE_CLIENT_ID=...` no tenga espacios extras
3. Reinicia el backend

### Error: "Firebase: Error (auth/invalid-api-key)"

**Causa:** El `apiKey` en `firebaseConfig.js` es incorrecto.

**Solución:**
1. Ve a Firebase Console → Project Settings → General
2. Copia el API Key correcto
3. Pega en `dashboard/src/firebaseConfig.js`
4. Reinicia el frontend (Ctrl+C, luego `npm start`)

### El botón de Google no aparece

**Causa:** Error de compilación en el frontend o Firebase no inicializó.

**Solución:**
1. Revisa la consola del navegador (F12 → Console)
2. Busca errores de Firebase
3. Asegúrate de que `firebaseConfig.js` tenga todos los valores correctos

---

## 📚 Recursos Adicionales

- **Firebase Authentication Docs:** https://firebase.google.com/docs/auth
- **Firebase Console:** https://console.firebase.google.com/
- **Google Sign-In para Web:** https://firebase.google.com/docs/auth/web/google-signin

---

## ✅ Checklist Final

- [ ] Proyecto creado/seleccionado en Firebase Console
- [ ] Google Authentication habilitado en Firebase
- [ ] Project ID copiado
- [ ] Firebase Config obtenido (apiKey, authDomain, etc.)
- [ ] `config.env` actualizado con `GOOGLE_CLIENT_ID`
- [ ] `firebaseConfig.js` actualizado con configuración completa
- [ ] Backend reiniciado
- [ ] Frontend reiniciado
- [ ] Login con Google probado exitosamente
- [ ] Usuario aparece en Firebase Console → Authentication → Users

---

¡Listo! Ahora tu dashboard tiene autenticación con Google usando Firebase 🎉

