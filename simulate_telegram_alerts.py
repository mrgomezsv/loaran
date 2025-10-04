"""
Script para simular alertas directas a Telegram
"""
import asyncio
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('config.env')

async def send_telegram_alert(message: str):
    """Enviar alerta a Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Configuración de Telegram no encontrada")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            print("✅ Alerta enviada a Telegram")
            return True
            
    except Exception as e:
        print(f"❌ Error enviando alerta: {e}")
        return False

async def simulate_tank_alert():
    """Simular alerta de tanque lleno"""
    message = """🚨 <b>Alerta LoRaGuard</b>
🚰 <b>Tanque Sensor Tanque Principal al 95%</b> (llenado)
📍 Ubicación: Zona A - Tanque Principal
⏰ Timestamp: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
🔧 Acción recomendada: Programar vaciado inmediatamente"""
    
    await send_telegram_alert(message)

async def simulate_motion_alert():
    """Simular alerta de movimiento nocturno"""
    message = """🚨 <b>¡ALERTA CRÍTICA!</b>
🏃 <b>Movimiento detectado en Zona A</b>
📍 Ubicación: Zona A - Entrada Principal
🕐 Hora: """ + datetime.now().strftime("%H:%M") + """ (fuera de horario seguro)
⚠️ Severidad: CRÍTICA
🔧 Acción: Revisar inmediatamente"""
    
    await send_telegram_alert(message)

async def simulate_door_alert():
    """Simular alerta de puerta abierta"""
    message = """🚪 <b>Alerta de Seguridad</b>
🚪 <b>Puerta abierta en Zona A</b>
📍 Ubicación: Zona A - Puerta Principal
⏰ Timestamp: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
🔧 Acción: Verificar acceso autorizado"""
    
    await send_telegram_alert(message)

async def simulate_correlation_alert():
    """Simular alerta de correlación (movimiento + puerta)"""
    message = """🚨 <b>¡ALERTA CRÍTICA ALTA!</b>
🔗 <b>Correlación detectada: Movimiento + Puerta</b>
📍 Ubicación: Zona A
⏰ Timestamp: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
⚠️ Severidad: CRÍTICA ALTA
🔧 Acción: REVISAR INMEDIATAMENTE - Posible intrusión"""
    
    await send_telegram_alert(message)

async def main():
    """Función principal"""
    print("🚀 Simulador de Alertas Telegram - LoRaGuard")
    print("=" * 50)
    
    # Verificar configuración
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Configuración de Telegram no encontrada")
        print("📝 Verifica que config.env tenga TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
        return
    
    print(f"🤖 Bot: {bot_token[:20]}...")
    print(f"💬 Chat ID: {chat_id}")
    print()
    
    # Simular diferentes tipos de alertas
    print("📱 Enviando alertas de prueba...")
    
    print("1. 🚰 Alerta de tanque lleno...")
    await simulate_tank_alert()
    await asyncio.sleep(2)
    
    print("2. 🏃 Alerta de movimiento nocturno...")
    await simulate_motion_alert()
    await asyncio.sleep(2)
    
    print("3. 🚪 Alerta de puerta abierta...")
    await simulate_door_alert()
    await asyncio.sleep(2)
    
    print("4. 🔗 Alerta de correlación crítica...")
    await simulate_correlation_alert()
    
    print()
    print("✅ ¡Todas las alertas enviadas!")
    print("📱 Revisa tu teléfono para ver las notificaciones")

if __name__ == "__main__":
    asyncio.run(main())
