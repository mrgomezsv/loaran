import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { signInWithPopup, getRedirectResult } from 'firebase/auth';
import { auth, googleProvider } from './firebaseConfig';
import './styles.css';

function App() {
  const [view, setView] = useState('login');
  const [form, setForm] = useState({
    email: '', password: '', full_name: '', telegram_chat_id: ''
  });
  const [token, setToken] = useState('');
  const [otp, setOtp] = useState('');
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState([]);
  const [usage, setUsage] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [uploadPct, setUploadPct] = useState(0);
  const [googleIdToken, setGoogleIdToken] = useState(''); // Para guardar el token de Google temporalmente

  // Manejar el resultado del redirect de Google
  useEffect(() => {
    const handleRedirectResult = async () => {
      try {
        const result = await getRedirectResult(auth);
        if (result) {
          // Usuario autenticado con Google
          const idToken = await result.user.getIdToken();
          setGoogleIdToken(idToken);
          setView('telegram_id');
          setMessage('Autenticación con Google exitosa. Ingresa tu Telegram Chat ID.');
        }
      } catch (error) {
        console.error('Error en redirect de Google:', error);
        setMessage(error.message || 'Error con autenticación de Google');
      }
    };

    handleRedirectResult();
  }, []);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const register = async () => {
    setMessage('');
    try {
      await axios.post('/api/v1/auth/register', form);
      setMessage('Registro exitoso. Ahora inicia sesión.');
      setView('login');
    } catch (e) { setMessage(e.response?.data?.detail || 'Error en registro'); }
  };

  const login = async () => {
    setMessage('');
    try {
      const { data } = await axios.post('/api/v1/auth/login', { email: form.email, password: form.password });
      setToken(data.token);
      setView('otp');
    } catch (e) { setMessage(e.response?.data?.detail || 'Error de login'); }
  };

  const requestOtp = async () => {
    setMessage('');
    try {
      await axios.post(`/api/v1/auth/request-otp?token=${encodeURIComponent(token)}`);
      setMessage('OTP enviado por Telegram. Revísalo.');
    } catch (e) { setMessage(e.response?.data?.detail || 'No se pudo enviar OTP'); }
  };

  const confirmOtp = async () => {
    setMessage('');
    try {
      // Para la demo de backend, confirm-otp acepta token y otp_code via query/body simplificado
      const res = await axios.post(`/api/v1/auth/confirm-otp?token=${encodeURIComponent(token)}&otp_code=${encodeURIComponent(otp)}`);
      if (res.data?.success) {
        setView('dashboard');
        // setup carpeta y cargar lista
        await axios.post(`/api/v1/auth/post-login-setup?token=${encodeURIComponent(token)}`);
        await loadFiles();
      } else {
        setMessage('OTP inválido');
      }
    } catch (e) { setMessage(e.response?.data?.detail || 'OTP inválido o expirado'); }
  };

  const loadFiles = async () => {
    const list = await axios.get(`/api/v1/files?token=${encodeURIComponent(token)}&page=${page}&size=10`);
    setFiles(list.data.items || []);
    setUsage(list.data.total_size_bytes || 0);
    setPages(list.data.pages || 1);
  };

  const logout = async () => {
    try {
      // Llamar endpoint de logout para auditoría
      await axios.post(`/api/v1/auth/logout?token=${encodeURIComponent(token)}`);
    } catch (e) {
      console.error('Error en logout:', e);
    }
    setToken('');
    setOtp('');
    setFiles([]);
    setUsage(0);
    setForm({ email: '', password: '', full_name: '', telegram_chat_id: '' });
    setView('login');
  };

  const handleGoogleLogin = async () => {
    setMessage('');
    try {
      // 1. Autenticar con Firebase
      const result = await signInWithPopup(auth, googleProvider);
      
      // 2. Obtener el ID Token de Firebase
      const idToken = await result.user.getIdToken();

      // 3. Guardar el token y mostrar pantalla para Telegram Chat ID
      setGoogleIdToken(idToken);
      setView('telegram_id');
      setMessage('Autenticación con Google exitosa. Ingresa tu Telegram Chat ID.');
    } catch (e) {
      console.error('Error en Google login:', e);
      setMessage(e.response?.data?.detail || e.message || 'Error con autenticación de Google');
    }
  };

  const completeTelegramSetup = async () => {
    setMessage('');
    if (!form.telegram_chat_id) {
      setMessage('Por favor ingresa tu Telegram Chat ID');
      return;
    }

    try {
      // Debug: Verificar que el token existe
      console.log('Token de Google disponible:', !!googleIdToken);
      console.log('Longitud del token:', googleIdToken ? googleIdToken.length : 0);
      
      if (!googleIdToken) {
        setMessage('Error: No se encontró el token de Google. Por favor intenta de nuevo.');
        setView('login');
        return;
      }

      // Enviar token de Firebase al backend con el Telegram Chat ID
      const { data } = await axios.post('/api/v1/auth/google/login', {
        id_token: googleIdToken,
        telegram_chat_id: form.telegram_chat_id
      });

      setToken(data.token);
      setView('otp');
      setMessage('Configuración completa. Ahora solicita el OTP.');
    } catch (e) {
      console.error('Error completando setup:', e);
      console.error('Detalle del error:', e.response?.data);
      setMessage(e.response?.data?.detail || 'Error al completar la configuración');
    }
  };

  return (
    <div className="container">
      <div className="card">
        <div className="brand">
          <div className="brand-badge">LG</div>
          <div>
            <div style={{ fontWeight: 700 }}>LoRaGuard</div>
            <div className="subtitle mt-2">Seguridad IoT con 3FA y cifrado</div>
          </div>
        </div>

        {message && <div className="note">{message}</div>}

        {view === 'register' && (
          <div className="login-container">
            <div className="login-card">
              <div className="stack">
                <div className="section-title">Registro</div>
                <input className="input" name="full_name" placeholder="Nombre completo" value={form.full_name} onChange={onChange} />
                <input className="input" name="email" placeholder="Correo electrónico" value={form.email} onChange={onChange} />
                <input className="input" type="password" name="password" placeholder="Contraseña" value={form.password} onChange={onChange} />
                <input className="input" name="telegram_chat_id" placeholder="Telegram Chat ID" value={form.telegram_chat_id} onChange={onChange} />
                <div className="row">
                  <button className="button secondary" onClick={() => setView('login')}>Ya tengo cuenta</button>
                  <button className="button" onClick={register}>Registrarse</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'login' && (
          <div className="login-container">
            <div className="login-card">
              <div className="stack">
                <div className="section-title">Login</div>
                <input className="input" name="email" placeholder="Correo electrónico" value={form.email} onChange={onChange} />
                <input className="input" type="password" name="password" placeholder="Contraseña" value={form.password} onChange={onChange} />
                <div className="row">
                  <button className="button secondary" onClick={() => setView('register')}>Crear cuenta</button>
                  <button className="button" onClick={login}>Entrar</button>
                </div>
                
                  {/* Divider */}
                  <div className="divider-container">
                    <div className="divider-line"></div>
                    <span className="divider-text">O</span>
                    <div className="divider-line"></div>
                  </div>
                  
                  {/* Google Sign-In Button con Firebase */}
                  <button className="google-button" onClick={handleGoogleLogin}>
                    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
                      <path d="M9.003 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.96v2.332C2.44 15.983 5.485 18 9.003 18z" fill="#34A853"/>
                      <path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71 0-.593.102-1.17.282-1.71V4.958H.957C.347 6.173 0 7.548 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                      <path d="M9.003 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.464.891 11.426 0 9.003 0 5.485 0 2.44 2.017.96 4.958L3.967 7.29c.708-2.127 2.692-3.71 5.036-3.71z" fill="#EA4335"/>
                    </svg>
                    Continuar con Google
                  </button>
              </div>
            </div>
          </div>
        )}

        {view === 'telegram_id' && (
          <div className="login-container">
            <div className="login-card">
              <div className="stack">
                <div className="section-title">Configuración de Telegram</div>
                <p style={{ color: '#9ca3af', fontSize: '0.875rem', marginBottom: '1rem' }}>
                  Para recibir notificaciones de seguridad y códigos OTP, necesitamos tu Telegram Chat ID.
                </p>
                <input 
                  className="input" 
                  name="telegram_chat_id"
                  placeholder="Telegram Chat ID (ej: 5858877153)" 
                  value={form.telegram_chat_id} 
                  onChange={onChange}
                />
                <p style={{ color: '#6b7280', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                  💡 Para obtener tu Chat ID, habla con <a href="https://t.me/userinfobot" target="_blank" rel="noopener noreferrer" style={{ color: '#6366f1' }}>@userinfobot</a> en Telegram
                </p>
                <div className="row" style={{ marginTop: '1.5rem' }}>
                  <button className="button secondary" onClick={() => setView('login')}>Cancelar</button>
                  <button className="button" onClick={completeTelegramSetup}>Continuar</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'otp' && (
          <div className="login-container">
            <div className="login-card">
              <div className="stack">
                <div className="section-title">Verificación OTP</div>
                <button className="button" onClick={requestOtp}>Enviar OTP a Telegram</button>
                <input className="input" placeholder="Código OTP" value={otp} onChange={(e)=>setOtp(e.target.value)} />
                <div className="row">
                  <div />
                  <button className="button" onClick={confirmOtp}>Confirmar</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'dashboard' && (
          <div className="dashboard-layout">
            {/* Top Bar */}
            <div className="top-bar">
              <div className="top-bar-left">
                <div className="logo">
                  <div className="brand-badge">📁</div>
                  <span>LoRaGuard</span>
                </div>
                <input 
                  type="text" 
                  placeholder="Buscar en archivos cifrados..." 
                  className="search-bar"
                />
              </div>
              <div className="top-bar-right">
                <div className="user-info">
                  <span>{(usage/1024).toFixed(1)} KB usados</span>
                  <span>•</span>
                  <span>{files.length} archivos</span>
                </div>
                <button className="toolbar-button" onClick={logout}>Cerrar sesión</button>
              </div>
            </div>

            {/* Main Content */}
            <div className="main-content">
              {/* Sidebar */}
              <div className="sidebar">
                <div className="sidebar-section">
                  <div className="sidebar-title">Archivos</div>
                  <div className="sidebar-item active">
                    <div className="sidebar-icon">📁</div>
                    <span>Mis archivos</span>
                  </div>
                  <div className="sidebar-item">
                    <div className="sidebar-icon">⭐</div>
                    <span>Destacados</span>
                  </div>
                  <div className="sidebar-item">
                    <div className="sidebar-icon">🕒</div>
                    <span>Recientes</span>
                  </div>
                </div>
                <div className="sidebar-section">
                  <div className="sidebar-title">Almacenamiento</div>
                  <div className="sidebar-item">
                    <div className="sidebar-icon">💾</div>
                    <span>Almacenamiento usado</span>
                  </div>
                </div>
              </div>

              {/* File Area */}
              <div className="file-area">
                {/* Toolbar */}
                <div className="toolbar">
                  <div className="toolbar-left">
                    <div className="toolbar-title">Mis archivos</div>
                    <div className="toolbar-actions">
                      <button className="toolbar-button">📋</button>
                      <button className="toolbar-button">📊</button>
                    </div>
                  </div>
                  <div className="toolbar-right">
                    <button className="toolbar-button">🔄</button>
                    <button className="toolbar-button">⚙️</button>
                  </div>
                </div>

                {/* Upload Area */}
                <div className="upload-area">
                  <label htmlFor="file-upload" className="upload-label">
                    📤 Subir archivo cifrado
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    onChange={async (e)=>{
                      const f = e.target.files?.[0];
                      if (!f) return;
                      const fd = new FormData();
                      fd.append('file', f);
                      await axios.post(`/api/v1/files/upload?token=${encodeURIComponent(token)}`, fd, {
                        headers: { 'Content-Type': 'multipart/form-data' },
                        onUploadProgress: (evt)=>{
                          if (!evt.total) return;
                          setUploadPct(Math.round((evt.loaded * 100) / evt.total));
                        }
                      });
                      setMessage(`Archivo '${f.name}' subido y cifrado correctamente.`);
                      await loadFiles();
                      e.target.value = '';
                      setUploadPct(0);
                    }}
                  />
                  <div className="upload-progress">
                    {uploadPct ? `Subiendo: ${uploadPct}%` : 'Los archivos se almacenan cifrados en la carpeta segura.'}
                  </div>
                </div>

                {/* Files Grid */}
                <div className="file-grid">
                  {files.map((f)=> (
                    <div className="file-card" key={f.id}>
                      <div className="file-icon">📄</div>
                      <div className="file-name">{f.name}</div>
                      <div className="file-meta">{f.algo} · {(f.size_bytes/1024).toFixed(2)} KB</div>
                      <div className="file-actions">
                        <button className="file-action-btn" onClick={async ()=>{
                          const { data } = await axios.get(`/api/v1/files/${encodeURIComponent(f.id)}?token=${encodeURIComponent(token)}&action=view`);
                          setMessage(`Contenido de ${f.name}:\n` + data.content);
                        }}>👁️</button>
                        <button className="file-action-btn" onClick={async ()=>{
                          const { data } = await axios.get(`/api/v1/files/${encodeURIComponent(f.id)}?token=${encodeURIComponent(token)}&action=download`);
                          const blob = new Blob([data.content], { type: 'text/plain;charset=utf-8' });
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = f.name;
                          document.body.appendChild(a);
                          a.click();
                          a.remove();
                          window.URL.revokeObjectURL(url);
                        }}>⬇️</button>
                        <button className="file-action-btn danger" onClick={async ()=>{
                          if (!window.confirm(`Eliminar '${f.name}'?`)) return;
                          await axios.delete(`/api/v1/files/${encodeURIComponent(f.id)}?token=${encodeURIComponent(token)}`);
                          await loadFiles();
                        }}>🗑️</button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                <div className="pagination">
                  <button className="pagination-button" disabled={page<=1} onClick={async ()=>{ setPage(p=>p-1); setTimeout(loadFiles, 0); }}>← Anterior</button>
                  <div className="pagination-info">Página {page} de {pages}</div>
                  <button className="pagination-button" disabled={page>=pages} onClick={async ()=>{ setPage(p=>p+1); setTimeout(loadFiles, 0); }}>Siguiente →</button>
                </div>
              </div>
            </div>

            {/* File Content Display */}
            {message && <div className="file-content">{message}</div>}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;


