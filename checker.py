import re
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneNumberUnoccupied,
    FloodWait, ApiIdInvalid, AuthKeyUnregistered
)

class TelegramChecker:
    @staticmethod
    def format_phone_number(phone):
        """Format phone number to international format"""
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        phone = str(phone).strip()
        clean = re.sub(r'[^\d+]', '', phone)
        
        # Bangladeshi numbers
        if clean.startswith('01') and len(clean) == 10:
            clean = '+88' + clean
        elif clean.startswith('1') and len(clean) == 10:
            clean = '+88' + clean
        elif len(clean) == 11 and clean.startswith('88'):
            clean = '+' + clean
        elif len(clean) == 10:
            clean = '+88' + clean
        elif not clean.startswith('+'):
            clean = '+' + clean
        
        # Validate international format
        if re.match(r'^\+[1-9]\d{9,14}$', clean):
            return clean
        return None
    
    async def check_single_number(self, user_api_id, user_api_hash, phone_number):
        """Check if a single number has Telegram account"""
        try:
            async with Client(
                f"session_{user_api_id}",
                api_id=int(user_api_id),
                api_hash=user_api_hash,
                in_memory=True,
                no_updates=True
            ) as client:
                try:
                    await client.send_code(phone_number)
                    return True, phone_number  # Registered
                except PhoneNumberUnoccupied:
                    return False, phone_number  # Not registered
                except PhoneNumberInvalid:
                    return None, phone_number  # Invalid number
                except FloodWait as e:
                    return "flood", phone_number
                except Exception:
                    return "error", phone_number
                    
        except Exception:
            return "client_error", phone_number
    
    async def check_multiple_numbers(self, user_api_id, user_api_hash, phone_list):
        """Check multiple phone numbers"""
        registered = []
        not_registered = []
        invalid = []
        errors = []
        
        for phone in phone_list:
            formatted = self.format_phone_number(phone)
            if not formatted:
                invalid.append(phone)
                continue
            
            status, num = await self.check_single_number(user_api_id, user_api_hash, formatted)
            
            if status is True:
                registered.append(formatted)
            elif status is False:
                not_registered.append(formatted)
            elif status is None:
                invalid.append(formatted)
            else:
                errors.append(f"{formatted}: {status}")
            
            # Delay to avoid flood
            await asyncio.sleep(1)
        
        return {
            "registered": registered,
            "not_registered": not_registered,
            "invalid": invalid,
            "errors": errors
        }

# Global instance
checker = TelegramChecker()
