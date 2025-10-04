"""
LoRaWAN Sensor Simulator for LoRaGuard Demo
"""
import asyncio
import httpx
import json
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

class LoRaWANSensorSimulator:
    """Simulator for LoRaWAN sensors"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.devices = {
            "sensor-tanque-01": {
                "name": "Sensor Tanque Principal",
                "type": "tank_level",
                "location": "Zona A - Tanque Principal",
                "min_value": 0,
                "max_value": 100,
                "unit": "%"
            },
            "sensor-mov-01": {
                "name": "Sensor Movimiento Entrada",
                "type": "motion",
                "location": "Zona A - Entrada Principal",
                "min_value": 0,
                "max_value": 1,
                "unit": None
            },
            "sensor-puerta-01": {
                "name": "Sensor Puerta Principal",
                "type": "door_open",
                "location": "Zona A - Puerta Principal",
                "min_value": 0,
                "max_value": 1,
                "unit": None
            },
            "sensor-tanque-02": {
                "name": "Sensor Tanque Secundario",
                "type": "tank_level",
                "location": "Zona B - Tanque Secundario",
                "min_value": 0,
                "max_value": 100,
                "unit": "%"
            },
            "sensor-mov-02": {
                "name": "Sensor Movimiento Patio",
                "type": "motion",
                "location": "Zona B - Patio Trasero",
                "min_value": 0,
                "max_value": 1,
                "unit": None
            }
        }
    
    async def send_event(self, device_id: str, event_data: Dict[str, Any]) -> bool:
        """Send event to LoRaGuard API"""
        try:
            url = f"{self.api_base_url}/api/v1/events/lora"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=event_data)
                response.raise_for_status()
                
                print(f"✅ Event sent successfully: {device_id} - {event_data['decoded']['type']}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to send event for {device_id}: {e}")
            return False
    
    def generate_tank_level_event(self, device_id: str, level: Optional[float] = None) -> Dict[str, Any]:
        """Generate tank level event"""
        if level is None:
            level = random.uniform(0, 100)
        
        return {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload_raw": f"tank_level_{level:.1f}",
            "decoded": {
                "type": "nivel",
                "level": round(level, 1),
                "unit": "%",
                "temperature": random.uniform(15, 35),
                "pressure": round(random.uniform(1.0, 3.0), 2),
                "battery_level": random.randint(20, 100)
            }
        }
    
    def generate_motion_event(self, device_id: str, motion: Optional[int] = None) -> Dict[str, Any]:
        """Generate motion detection event"""
        if motion is None:
            motion = random.choice([0, 1])
        
        return {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload_raw": f"motion_{motion}",
            "decoded": {
                "type": "movimiento",
                "motion": motion,
                "confidence": round(random.uniform(0.7, 1.0), 2),
                "duration": random.randint(1, 10),
                "battery_level": random.randint(20, 100)
            }
        }
    
    def generate_door_event(self, device_id: str, door_open: Optional[int] = None) -> Dict[str, Any]:
        """Generate door open event"""
        if door_open is None:
            door_open = random.choice([0, 1])
        
        return {
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload_raw": f"door_{door_open}",
            "decoded": {
                "type": "puerta",
                "door_open": door_open,
                "magnetic_field": round(random.uniform(0.1, 0.9), 2),
                "battery_level": random.randint(20, 100)
            }
        }
    
    async def simulate_random_events(self, count: int = 10, interval: float = 2.0):
        """Simulate random events"""
        print(f"🎲 Starting random simulation: {count} events with {interval}s interval")
        
        for i in range(count):
            device_id = random.choice(list(self.devices.keys()))
            device = self.devices[device_id]
            
            if device["type"] == "tank_level":
                event_data = self.generate_tank_level_event(device_id)
            elif device["type"] == "motion":
                event_data = self.generate_motion_event(device_id)
            elif device["type"] == "door_open":
                event_data = self.generate_door_event(device_id)
            else:
                continue
            
            await self.send_event(device_id, event_data)
            
            if i < count - 1:  # Don't sleep after the last event
                await asyncio.sleep(interval)
        
        print(f"✅ Random simulation completed: {count} events sent")
    
    async def simulate_tank_fill_scenario(self):
        """Simulate tank filling scenario (Case A)"""
        print("🚰 Simulating tank fill scenario (Case A)")
        
        device_id = "sensor-tanque-01"
        
        # Gradual fill simulation
        levels = [75, 80, 85, 90, 95, 98]
        
        for level in levels:
            event_data = self.generate_tank_level_event(device_id, level)
            await self.send_event(device_id, event_data)
            await asyncio.sleep(1)
        
        print("✅ Tank fill scenario completed")
    
    async def simulate_false_positive_scenario(self):
        """Simulate false positive scenario (Case B) - debounce test"""
        print("🔄 Simulating false positive scenario (Case B) - debounce test")
        
        device_id = "sensor-mov-01"
        
        # Send multiple motion events in quick succession
        for i in range(5):
            event_data = self.generate_motion_event(device_id, 1)
            await self.send_event(device_id, event_data)
            await asyncio.sleep(0.5)  # Very quick succession
        
        print("✅ False positive scenario completed")
    
    async def simulate_correlation_scenario(self):
        """Simulate correlation scenario (Case C) - motion + door"""
        print("🔗 Simulating correlation scenario (Case C) - motion + door")
        
        # Motion event first
        motion_event = self.generate_motion_event("sensor-mov-01", 1)
        await self.send_event("sensor-mov-01", motion_event)
        
        await asyncio.sleep(2)
        
        # Door event 30 seconds later (simulated)
        door_event = self.generate_door_event("sensor-puerta-01", 1)
        await self.send_event("sensor-puerta-01", door_event)
        
        print("✅ Correlation scenario completed")
    
    async def simulate_night_movement_scenario(self):
        """Simulate night movement scenario (Case D)"""
        print("🌙 Simulating night movement scenario (Case D)")
        
        # Create timestamp for 3 AM
        night_time = datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Motion event at night
        motion_event = self.generate_motion_event("sensor-mov-01", 1)
        motion_event["timestamp"] = night_time.isoformat()
        
        await self.send_event("sensor-mov-01", motion_event)
        
        print("✅ Night movement scenario completed")
    
    async def simulate_continuous_monitoring(self, duration_minutes: int = 5):
        """Simulate continuous monitoring"""
        print(f"📊 Starting continuous monitoring for {duration_minutes} minutes")
        
        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        while datetime.utcnow() < end_time:
            device_id = random.choice(list(self.devices.keys()))
            device = self.devices[device_id]
            
            if device["type"] == "tank_level":
                # Gradual level changes
                level = random.uniform(20, 80)
                event_data = self.generate_tank_level_event(device_id, level)
            elif device["type"] == "motion":
                # Occasional motion
                motion = 1 if random.random() < 0.3 else 0
                event_data = self.generate_motion_event(device_id, motion)
            elif device["type"] == "door_open":
                # Occasional door events
                door_open = 1 if random.random() < 0.2 else 0
                event_data = self.generate_door_event(device_id, door_open)
            else:
                continue
            
            await self.send_event(device_id, event_data)
            await asyncio.sleep(random.uniform(5, 15))  # Random interval
        
        print("✅ Continuous monitoring completed")
    
    async def run_test_case(self, case: str):
        """Run specific test case"""
        if case == "tank_fill":
            await self.simulate_tank_fill_scenario()
        elif case == "false_positive":
            await self.simulate_false_positive_scenario()
        elif case == "correlation":
            await self.simulate_correlation_scenario()
        elif case == "night_movement":
            await self.simulate_night_movement_scenario()
        elif case == "random":
            await self.simulate_random_events(10, 2.0)
        elif case == "continuous":
            await self.simulate_continuous_monitoring(2)
        else:
            print(f"❌ Unknown test case: {case}")
            print("Available cases: tank_fill, false_positive, correlation, night_movement, random, continuous")

async def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="LoRaWAN Sensor Simulator for LoRaGuard")
    parser.add_argument("--case", choices=["tank_fill", "false_positive", "correlation", "night_movement", "random", "continuous"], 
                       help="Test case to run")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--count", type=int, default=10, help="Number of events for random simulation")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval between events in seconds")
    parser.add_argument("--duration", type=int, default=5, help="Duration in minutes for continuous monitoring")
    
    args = parser.parse_args()
    
    simulator = LoRaWANSensorSimulator(args.api_url)
    
    print("🚀 LoRaWAN Sensor Simulator Starting...")
    print(f"📡 API URL: {args.api_url}")
    print(f"🎯 Test Case: {args.case}")
    
    if args.case:
        await simulator.run_test_case(args.case)
    else:
        # Interactive mode
        print("\nAvailable test cases:")
        print("1. tank_fill - Tank filling scenario")
        print("2. false_positive - Debounce test")
        print("3. correlation - Motion + door correlation")
        print("4. night_movement - Night movement detection")
        print("5. random - Random events")
        print("6. continuous - Continuous monitoring")
        
        choice = input("\nSelect test case (1-6): ").strip()
        
        cases = {
            "1": "tank_fill",
            "2": "false_positive", 
            "3": "correlation",
            "4": "night_movement",
            "5": "random",
            "6": "continuous"
        }
        
        if choice in cases:
            await simulator.run_test_case(cases[choice])
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())
