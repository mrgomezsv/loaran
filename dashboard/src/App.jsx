import React, { useState } from 'react';
import axios from 'axios';
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
        // load files
        const list = await axios.get(`/api/v1/files?token=${encodeURIComponent(token)}`);
        setFiles(list.data.items || []);
      } else {
        setMessage('OTP inválido');
      }
    } catch (e) { setMessage(e.response?.data?.detail || 'OTP inválido o expirado'); }
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
        )}

        {view === 'login' && (
          <div className="stack">
            <div className="section-title">Login</div>
            <input className="input" name="email" placeholder="Correo electrónico" value={form.email} onChange={onChange} />
            <input className="input" type="password" name="password" placeholder="Contraseña" value={form.password} onChange={onChange} />
            <div className="row">
              <button className="button secondary" onClick={() => setView('register')}>Crear cuenta</button>
              <button className="button" onClick={login}>Entrar</button>
            </div>
          </div>
        )}

        {view === 'otp' && (
          <div className="stack">
            <div className="section-title">Verificación OTP</div>
            <button className="button" onClick={requestOtp}>Enviar OTP a Telegram</button>
            <input className="input" placeholder="Código OTP" value={otp} onChange={(e)=>setOtp(e.target.value)} />
            <div className="row">
              <div />
              <button className="button" onClick={confirmOtp}>Confirmar</button>
            </div>
          </div>
        )}

        {view === 'dashboard' && (
          <div className="dash">
            <div className="section-title">Dashboard</div>
          {files.map((f)=> (
            <div className="dash-item" key={f.id}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div>
                  <div style={{ fontWeight:600 }}>{f.name}</div>
                  <div className="muted">{f.algo}</div>
                </div>
                <div style={{ display:'flex', gap:8 }}>
                  <button className="button secondary" onClick={async ()=>{
                    const { data } = await axios.get(`/api/v1/files/${encodeURIComponent(f.id)}?token=${encodeURIComponent(token)}`);
                    setMessage(`Contenido de ${f.name}:\n` + data.content);
                  }}>Ver contenido</button>
                  <button className="button" onClick={async ()=>{
                    const { data } = await axios.get(`/api/v1/files/${encodeURIComponent(f.id)}?token=${encodeURIComponent(token)}`);
                    const blob = new Blob([data.content], { type: 'text/plain;charset=utf-8' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = f.name;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                  }}>Descargar</button>
                </div>
              </div>
            </div>
          ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;


