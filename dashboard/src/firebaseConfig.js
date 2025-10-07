// Firebase Configuration
// Configuración de tu proyecto Firebase

import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

// Configuración de Firebase para LoRaWan-TecWave
// Obtenida de: Firebase Console → Project Settings → General → Your apps
const firebaseConfig = {
  apiKey: "AIzaSyC9-XdDg1n-mYvASFOuwC8LUjcGo2_MxSI",
  authDomain: "lorawan-tecwave.firebaseapp.com",
  projectId: "lorawan-tecwave",
  storageBucket: "lorawan-tecwave.firebasestorage.app",
  messagingSenderId: "402218569115",
  appId: "1:402218569115:web:6d7dff86186d2fd287a53e",
  measurementId: "G-M4EBXVNHHS"
};

// Inicializar Firebase
const app = initializeApp(firebaseConfig);

// Inicializar Firebase Authentication
export const auth = getAuth(app);

// Provider de Google
export const googleProvider = new GoogleAuthProvider();

// Configuración adicional del provider (opcional)
googleProvider.setCustomParameters({
  prompt: 'select_account' // Siempre mostrar selector de cuenta
});

export default app;

