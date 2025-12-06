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
        if not phone or not isinstance(phone, str):
            return None
        
        # Remove all non-digits except +
        clean = re.sub(r'[^\d+]', '', phone)
        
        # Ensure starts with +
        if not clean.startswith('+'):
            if clean.startswith('01') and len(clean) == 10:
                clean = '+88' + clean
            elif clean.startswith('1') and len(clean) == 10:
                clean = '+88' + clean
            elif len(clean) == 11 and clean.startswith('88'):
                clean = '+' + clean
            elif len(clean) == 10:
                clean = '+88' + clean
            else:
                clean = '+' + clean
        
        # Final validation
        if re.match(r'^\+[1-9]\d{9,14}$', clean):
            return clean
        return None
    
    async def validate_user_api(self, api_id, api_hash):
        """SIMPLIFIED VALIDATION - Less strict"""
        try:
            # Quick test without full validation
            async with Client(
                f"validate_{api_id}",
                api_id=int(api_id),
                api_hash=api_hash,
                in_memory=True,
                no_updates=True
            ) as app:
                # Just try to create session, don't validate fully
                return True
        except (ApiIdInvalid, AuthKeyUnregistered, ValueError):
            return False
        except Exception:
            # Other errors - assume it might work
            return True
    
    async def check_single(self, api_id, api_hash, phone):
        """Check single number"""
        try:
            async with Client(
                f"checker_{api_id}",
                api_id=int(api_id),
                api_hash=api_hash,
                in_memory=True,
                no_updates=True
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
                except Exception:
                    return "error", phone
        except Exception:
            return "client_error", phone
    
    async def check_bulk(self, api_id, api_hash, numbers):
        """Check multiple numbers - SIMPLIFIED"""
        registered = []
        not_registered = []
        invalid = []
        
        for num in numbers:
            formatted = self.validate_phone(num)
            if not formatted:
                invalid.append(num)
                continue
            
            # Try to check
            try:
                async with Client(
                    f"bulk_{api_id}",
                    api_id=int(api_id),
                    api_hash=api_hash,
                    in_memory=True,
                    no_updates=True
                ) as app:
                    try:
                        await app.send_code(formatted)
                        registered.append(formatted)
                    except PhoneNumberUnoccupied:
                        not_registered.append(formatted)
                    except Exception:
                        # Skip on error
                        pass
            except Exception:
                # Skip if client creation fails
                pass
            
            # Small delay
            await asyncio.sleep(0.5)
        
        return {
            "registered": registered,
            "not_registered": not_registered,
            "invalid": invalid
        }

checker = NumberChecker()
