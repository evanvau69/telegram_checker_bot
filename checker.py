import re
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneNumberUnoccupied,
    FloodWait, ApiIdInvalid, AuthKeyUnregistered
)

class NumberChecker:
    def __init__(self):
        self.active_clients = {}
    
    def validate_phone(self, phone):
        """Validate and format phone number"""
        # Remove spaces, dashes, parentheses
        clean = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Bangladesh specific formatting
        if clean.startswith('01') and len(clean) == 10:
            clean = '+88' + clean
        elif clean.startswith('1') and len(clean) == 10:
            clean = '+88' + clean
        elif not clean.startswith('+') and len(clean) == 11 and clean.startswith('88'):
            clean = '+' + clean
        
        # International format validation
        if re.match(r'^\+[1-9]\d{1,14}$', clean):
            return clean
        return None
    
    async def validate_api_credentials(self, api_id, api_hash):
        """Quick validation of API credentials"""
        try:
            test_client = Client(
                "validation_session",
                api_id=int(api_id),
                api_hash=api_hash,
                no_updates=True
            )
            
            await test_client.connect()
            
            # Quick test - try to get own info
            try:
                await test_client.get_me()
                valid = True
            except (AuthKeyUnregistered, ApiIdInvalid):
                valid = False
            except Exception:
                valid = True  # Other errors might be okay
            
            await test_client.disconnect()
            return valid
            
        except Exception:
            return False
    
    async def check_number(self, api_id, api_hash, phone_number):
        """Check single phone number"""
        client_key = f"{api_id}_{api_hash}"
        
        try:
            # Create or reuse client
            if client_key not in self.active_clients:
                client = Client(
                    client_key,
                    api_id=int(api_id),
                    api_hash=api_hash,
                    no_updates=True
                )
                await client.connect()
                self.active_clients[client_key] = client
            else:
                client = self.active_clients[client_key]
            
            # Try to send code
            try:
                await client.send_code(phone_number)
                return {"status": "registered", "phone": phone_number}
            except PhoneNumberUnoccupied:
                return {"status": "not_registered", "phone": phone_number}
            except PhoneNumberInvalid:
                return {"status": "invalid", "phone": phone_number}
            except FloodWait as e:
                return {"status": "flood", "phone": phone_number, "wait": e.value}
            except Exception as e:
                return {"status": "error", "phone": phone_number, "error": str(e)}
                
        except Exception as e:
            return {"status": "client_error", "phone": phone_number, "error": str(e)}
    
    async def check_bulk(self, api_id, api_hash, phone_list):
        """Check multiple numbers"""
        results = {
            "registered": [],
            "not_registered": [],
            "invalid": [],
            "errors": []
        }
        
        validated_numbers = []
        
        # First, validate all numbers
        for phone in phone_list:
            formatted = self.validate_phone(phone)
            if formatted:
                validated_numbers.append(formatted)
            else:
                results["invalid"].append(phone)
        
        # Check validated numbers
        for phone in validated_numbers:
            result = await self.check_number(api_id, api_hash, phone)
            
            if result["status"] == "registered":
                results["registered"].append(phone)
            elif result["status"] == "not_registered":
                results["not_registered"].append(phone)
            elif result["status"] == "invalid":
                results["invalid"].append(phone)
            else:
                results["errors"].append(f"{phone}: {result.get('error', 'Unknown error')}")
            
            # Small delay to avoid flood
            await asyncio.sleep(1.5)
        
        return results
    
    def cleanup(self):
        """Cleanup clients"""
        for client in self.active_clients.values():
            try:
                client.disconnect()
            except:
                pass
        self.active_clients.clear()

# Global instance
checker = NumberChecker()
