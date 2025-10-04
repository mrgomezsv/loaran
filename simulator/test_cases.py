"""
Test cases for LoRaGuard demo scenarios
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class TestCaseRunner:
    """Runner for specific test cases"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
    
    async def run_case_a_tank_fill(self):
        """Case A: Tank filling scenario"""
        print("🚰 Running Case A: Tank Fill Scenario")
        print("=" * 50)
        
        device_id = "sensor-tanque-01"
        levels = [75, 80, 85, 90, 95, 98]
        
        for i, level in enumerate(levels):
            print(f"📊 Sending tank level: {level}%")
            
            event_data = {
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "payload_raw": f"tank_level_{level}",
                "decoded": {
                    "type": "nivel",
                    "level": level,
                    "unit": "%",
                    "temperature": 25.0,
                    "pressure": 2.1,
                    "battery_level": 85
                }
            }
            
            success = await self._send_event(event_data)
            if success:
                print(f"✅ Level {level}% sent successfully")
            else:
                print(f"❌ Failed to send level {level}%")
            
            await asyncio.sleep(1)
        
        print("\n🎯 Expected Results:")
        print("- Alert should be triggered at 90%+")
        print("- Notifications sent to Telegram/WhatsApp")
        print("- Dashboard should show HIGH severity events")
        print("=" * 50)
    
    async def run_case_b_false_positive(self):
        """Case B: False positive (debounce) test"""
        print("🔄 Running Case B: False Positive (Debounce) Test")
        print("=" * 50)
        
        device_id = "sensor-mov-01"
        
        print("📡 Sending 5 motion events in quick succession...")
        
        for i in range(5):
            print(f"🚨 Motion event {i+1}/5")
            
            event_data = {
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "payload_raw": f"motion_1",
                "decoded": {
                    "type": "movimiento",
                    "motion": 1,
                    "confidence": 0.95,
                    "duration": 3,
                    "battery_level": 78
                }
            }
            
            success = await self._send_event(event_data)
            if success:
                print(f"✅ Motion event {i+1} sent")
            else:
                print(f"❌ Failed to send motion event {i+1}")
            
            await asyncio.sleep(0.5)  # Very quick succession
        
        print("\n🎯 Expected Results:")
        print("- Only 1 alert should be created (debounce filter)")
        print("- Subsequent events should be filtered out")
        print("- Dashboard should show LOW severity for filtered events")
        print("=" * 50)
    
    async def run_case_c_correlation(self):
        """Case C: Correlation scenario"""
        print("🔗 Running Case C: Correlation Scenario")
        print("=" * 50)
        
        print("🚨 Step 1: Motion detected")
        motion_event = {
            "device_id": "sensor-mov-01",
            "timestamp": datetime.utcnow().isoformat(),
            "payload_raw": "motion_1",
            "decoded": {
                "type": "movimiento",
                "motion": 1,
                "confidence": 0.92,
                "duration": 5,
                "battery_level": 82
            }
        }
        
        success1 = await self._send_event(motion_event)
        if success1:
            print("✅ Motion event sent")
        else:
            print("❌ Failed to send motion event")
        
        await asyncio.sleep(2)
        
        print("🚪 Step 2: Door opened (30 seconds later)")
        door_event = {
            "device_id": "sensor-puerta-01",
            "timestamp": datetime.utcnow().isoformat(),
            "payload_raw": "door_1",
            "decoded": {
                "type": "puerta",
                "door_open": 1,
                "magnetic_field": 0.15,
                "battery_level": 75
            }
        }
        
        success2 = await self._send_event(door_event)
        if success2:
            print("✅ Door event sent")
        else:
            print("❌ Failed to send door event")
        
        print("\n🎯 Expected Results:")
        print("- CRITICAL_HIGH severity alert should be created")
        print("- Correlation filter should detect motion + door")
        print("- Priority notifications should be sent")
        print("=" * 50)
    
    async def run_case_d_night_movement(self):
        """Case D: Night movement scenario"""
        print("🌙 Running Case D: Night Movement Scenario")
        print("=" * 50)
        
        # Create timestamp for 3 AM
        night_time = datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
        
        print(f"🕐 Simulating movement at {night_time.strftime('%H:%M')} (night time)")
        
        event_data = {
            "device_id": "sensor-mov-01",
            "timestamp": night_time.isoformat(),
            "payload_raw": "motion_night",
            "decoded": {
                "type": "movimiento",
                "motion": 1,
                "confidence": 0.88,
                "duration": 8,
                "battery_level": 91
            }
        }
        
        success = await self._send_event(event_data)
        if success:
            print("✅ Night movement event sent")
        else:
            print("❌ Failed to send night movement event")
        
        print("\n🎯 Expected Results:")
        print("- CRITICAL severity alert (outside safe hours)")
        print("- Immediate notification due to night detection")
        print("- Dashboard should highlight critical night event")
        print("=" * 50)
    
    async def run_load_test(self, count: int = 20):
        """Load test with multiple events"""
        print(f"⚡ Running Load Test: {count} events")
        print("=" * 50)
        
        devices = ["sensor-tanque-01", "sensor-mov-01", "sensor-puerta-01", "sensor-tanque-02", "sensor-mov-02"]
        
        for i in range(count):
            device_id = devices[i % len(devices)]
            
            if "tanque" in device_id:
                level = 20 + (i * 3) % 80  # Gradual increase
                event_data = {
                    "device_id": device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload_raw": f"tank_{level}",
                    "decoded": {
                        "type": "nivel",
                        "level": level,
                        "unit": "%",
                        "temperature": 20 + (i % 15),
                        "pressure": 1.5 + (i % 10) * 0.1,
                        "battery_level": 100 - (i % 20)
                    }
                }
            elif "mov" in device_id:
                motion = 1 if i % 3 == 0 else 0
                event_data = {
                    "device_id": device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload_raw": f"motion_{motion}",
                    "decoded": {
                        "type": "movimiento",
                        "motion": motion,
                        "confidence": 0.7 + (i % 30) * 0.01,
                        "duration": 1 + (i % 10),
                        "battery_level": 100 - (i % 25)
                    }
                }
            elif "puerta" in device_id:
                door_open = 1 if i % 4 == 0 else 0
                event_data = {
                    "device_id": device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload_raw": f"door_{door_open}",
                    "decoded": {
                        "type": "puerta",
                        "door_open": door_open,
                        "magnetic_field": 0.1 + (i % 8) * 0.1,
                        "battery_level": 100 - (i % 30)
                    }
                }
            else:
                continue
            
            success = await self._send_event(event_data)
            if success:
                print(f"✅ Event {i+1}/{count} sent for {device_id}")
            else:
                print(f"❌ Failed to send event {i+1}/{count}")
            
            await asyncio.sleep(0.5)
        
        print(f"\n✅ Load test completed: {count} events sent")
        print("=" * 50)
    
    async def _send_event(self, event_data: Dict[str, Any]) -> bool:
        """Send event to API"""
        try:
            url = f"{self.api_base_url}/api/v1/events/lora"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=event_data)
                response.raise_for_status()
                return True
                
        except Exception as e:
            print(f"❌ API Error: {e}")
            return False
    
    async def check_api_status(self) -> bool:
        """Check if API is running"""
        try:
            url = f"{self.api_base_url}/api/v1/health"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                print(f"✅ API Status: {data['status']}")
                return True
                
        except Exception as e:
            print(f"❌ API not available: {e}")
            return False

async def main():
    """Main function for running test cases"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LoRaGuard Test Cases")
    parser.add_argument("--case", choices=["a", "b", "c", "d", "load", "all"], 
                       help="Test case to run")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--count", type=int, default=20, help="Number of events for load test")
    
    args = parser.parse_args()
    
    runner = TestCaseRunner(args.api_url)
    
    print("🧪 LoRaGuard Test Cases")
    print(f"📡 API URL: {args.api_url}")
    
    # Check API status first
    api_available = await runner.check_api_status()
    if not api_available:
        print("❌ API is not available. Please start the backend first.")
        return
    
    print("\n" + "="*60)
    
    if args.case == "a":
        await runner.run_case_a_tank_fill()
    elif args.case == "b":
        await runner.run_case_b_false_positive()
    elif args.case == "c":
        await runner.run_case_c_correlation()
    elif args.case == "d":
        await runner.run_case_d_night_movement()
    elif args.case == "load":
        await runner.run_load_test(args.count)
    elif args.case == "all":
        print("🎬 Running All Test Cases")
        await runner.run_case_a_tank_fill()
        await asyncio.sleep(2)
        await runner.run_case_b_false_positive()
        await asyncio.sleep(2)
        await runner.run_case_c_correlation()
        await asyncio.sleep(2)
        await runner.run_case_d_night_movement()
    else:
        print("Available test cases:")
        print("--case a     : Tank fill scenario")
        print("--case b     : False positive (debounce) test")
        print("--case c     : Correlation scenario")
        print("--case d     : Night movement scenario")
        print("--case load  : Load test")
        print("--case all   : Run all test cases")

if __name__ == "__main__":
    asyncio.run(main())
