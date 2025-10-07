// Firebase Configuration
// Configuración de tu proyecto Firebase

import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

// TODO: Reemplazar con tu configuración de Firebase
// La encontrarás en: Firebase Console → Project Settings → General → Your apps
const firebaseConfig = {
  apiKey: "TU_API_KEY_AQUI",
  authDomain: "tu-proyecto.firebaseapp.com",
  projectId: "tu-proyecto-id",
  storageBucket: "tu-proyecto.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef123456"
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

