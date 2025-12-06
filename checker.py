import re
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneNumberUnoccupied,
    FloodWait, ApiIdInvalid, AuthKeyUnregistered
)

class NumberChecker:
    @staticmethod
    def validate_phone(phone):
        """Validate and format phone number"""
        clean = re.sub(r'[\s\-\(\)+]', '', str(phone))
        
        # Bangladesh numbers
        if clean.startswith('01') and len(clean) == 10:
            clean = '+88' + clean
        elif clean.startswith('1') and len(clean) == 10:
            clean = '+88' + clean
        elif len(clean) == 11 and clean.startswith('88'):
            clean = '+' + clean
        elif len(clean) == 10:
            clean = '+88' + clean
        
        if re.match(r'^\+[1-9]\d{9,14}$', clean):
            return clean
        return None
    
    async def validate_user_api(self, api_id, api_hash):
        """Validate user's API credentials"""
        try:
            async with Client(
                "validation_session",
                api_id=int(api_id),
                api_hash=api_hash,
                in_memory=True
            ) as app:
                try:
                    await app.get_me()
                    return True
                except (AuthKeyUnregistered, ApiIdInvalid):
                    return False
                except Exception:
                    return True  # Other errors might be okay
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    async def check_single(self, api_id, api_hash, phone):
        """Check single number"""
        try:
            async with Client(
                f"checker_{api_id}",
                api_id=int(api_id),
                api_hash=api_hash,
                in_memory=True
            ) as app:
                try:
                    await app.send_code(phone)
                    return "registered", phone
                except PhoneNumberUnoccupied:
                    return "not_registered", phone
                except PhoneNumberInvalid:
                    return "invalid", phone
                except FloodWait as e:
                    return "flood", phone
                except Exception as e:
                    return "error", phone
        except Exception as e:
            return "client_error", phone
    
    async def check_bulk(self, api_id, api_hash, numbers):
        """Check multiple numbers"""
        registered = []
        not_registered = []
        invalid = []
        
        for num in numbers:
            formatted = self.validate_phone(num)
            if not formatted:
                invalid.append(num)
                continue
            
            status, phone = await self.check_single(api_id, api_hash, formatted)
            
            if status == "registered":
                registered.append(phone)
            elif status == "not_registered":
                not_registered.append(phone)
            elif status == "invalid":
                invalid.append(phone)
            
            await asyncio.sleep(1)  # Avoid flood
        
        return {
            "registered": registered,
            "not_registered": not_registered,
            "invalid": invalid
        }

checker = NumberChecker()
