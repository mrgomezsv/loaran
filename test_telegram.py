"""
Script de prueba para verificar conexión con Telegram
"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('config.env')

async def test_telegram_connection():
    """Probar conexión con Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or bot_token == 'TU_TOKEN_AQUI':
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        print("📝 Edita config.env y agrega tu token de BotFather")
        return False
    
    if not chat_id or chat_id == 'TU_CHAT_ID_AQUI':
        print("❌ TELEGRAM_CHAT_ID no configurado")
        print("📝 Edita config.env y agrega tu chat ID")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "🤖 ¡Hola! LoRaGuard está funcionando correctamente. Este es un mensaje de prueba.",
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            print("✅ ¡Conexión con Telegram exitosa!")
            print("📱 Revisa tu teléfono - deberías haber recibido un mensaje")
            return True
            
    except Exception as e:
        print(f"❌ Error conectando con Telegram: {e}")
        print("🔧 Verifica que:")
        print("   - El token sea correcto")
        print("   - El chat ID sea correcto")
        print("   - Hayas enviado al menos un mensaje al bot")
        return False

if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
