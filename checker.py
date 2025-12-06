import re
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneNumberUnoccupied,
    FloodWait, ApiIdInvalid, AuthKeyUnregistered
)

class TelegramChecker:
    def __init__(self):
        self.active_clients = {}
    
    def validate_phone(self, phone):
        """Validate phone number format"""
        # Clean number
        clean = re.sub(r'[\s\-\(\)]', '', str(phone))
        
        # Bangladesh format support
        if clean.startswith('01') and len(clean) == 10:
            clean = '+88' + clean
        elif clean.startswith('1') and len(clean) == 10:
            clean = '+88' + clean
        elif not clean.startswith('+') and len(clean) == 11 and clean.startswith('88'):
            clean = '+' + clean
        
        # International validation
        if re.match(r'^\+[1-9]\d{1,14}$', clean):
            return clean
        return None
    
    async def validate_user_credentials(self, api_id, api_hash):
        """Validate user-provided API credentials"""
        try:
            test_client = Client(
                f"validate_{api_id}",
                api_id=int(api_id),
                api_hash=api_hash,
                in_memory=True,
                no_updates=True
            )
            
            async with test_client:
                # Try to get own info
                try:
                    await test_client.get_me()
                    return True
                except (AuthKeyUnregistered, ApiIdInvalid):
                    return False
                except Exception:
                    # Other errors might mean credentials are valid
                    return True
                    
        except Exception:
            return False
    
    async def check_single_number(self, user_api_id, user_api_hash, phone_number):
        """Check if a phone number has Telegram account"""
        client_key = f"user_{user_api_id}"
        
        try:
            # Create client with user's credentials
            async with Client(
                client_key,
                api_id=int(user_api_id),
                api_hash=user_api_hash,
                in_memory=True,
                no_updates=True
            ) as client:
                
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
    
    async def check_numbers(self, user_api_id, user_api_hash, phone_list):
        """Check multiple numbers"""
        results = {
            "registered": [],
            "not_registered": [],
            "invalid_format": [],
            "errors": []
        }
        
        total = len(phone_list)
        
        for index, phone in enumerate(phone_list):
            # Validate format
            validated_phone = self.validate_phone(phone)
            if not validated_phone:
                results["invalid_format"].append(phone)
                continue
            
            # Check number
            result = await self.check_single_number(user_api_id, user_api_hash, validated_phone)
            
            if result["status"] == "registered":
                results["registered"].append(validated_phone)
            elif result["status"] == "not_registered":
                results["not_registered"].append(validated_phone)
            elif result["status"] == "invalid":
                results["invalid_format"].append(validated_phone)
            else:
                results["errors"].append({
                    "phone": validated_phone,
                    "error": result.get("error", "Unknown")
                })
            
            # Delay to avoid flood (1.5 seconds between checks)
            if index < total - 1:
                await asyncio.sleep(1.5)
        
        return results

# Global instance
checker = TelegramChecker()
