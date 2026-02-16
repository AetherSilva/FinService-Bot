#!/usr/bin/env python3
"""
MCP Server for FinService-Bot Database Operations
Exposes database operations through the Model Context Protocol
"""

import json
import logging
import sys
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database layer
try:
    from db_layer_universal import db_manager, DatabaseType
    from config_schema import ServiceType, config_manager
    from templates import OfferData
except ImportError as e:
    logger.error(f"❌ Import failed: {e}")
    sys.exit(1)

class MCPServer:
    """MCP Server for database operations"""
    
    def __init__(self):
        self.tools = {
            "get_offers": self.get_offers,
            "add_offer": self.add_offer,
            "get_stats": self.get_stats,
            "get_services": self.get_services,
            "get_channel": self.get_channel,
            "update_channel": self.update_channel,
            "block_user": self.block_user,
            "unblock_user": self.unblock_user,
            "get_next_offer": self.get_next_offer,
            "mark_offer_posted": self.mark_offer_posted,
            "health_check": self.health_check,
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool request"""
        try:
            tool_name = request.get("tool")
            params = request.get("params", {})
            
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": list(self.tools.keys())
                }
            
            result = await self.tools[tool_name](**params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"❌ Error handling request: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_offers(self, service_type: str = None, status: str = "queued", limit: int = 10) -> List[Dict]:
        """Get offers from database"""
        try:
            con = db_manager.connect()
            cur = con.cursor()
            
            if service_type:
                if db_manager.db_type == DatabaseType.POSTGRESQL:
                    query = "SELECT id, service_type, provider, title_en, status, created_at FROM offers WHERE service_type = %s AND status = %s ORDER BY created_at DESC LIMIT %s"
                    cur.execute(query, (service_type, status, limit))
                else:
                    query = "SELECT id, service_type, provider, title_en, status, created_at FROM offers WHERE service_type = ? AND status = ? ORDER BY created_at DESC LIMIT ?"
                    cur.execute(query, (service_type, status, limit))
            else:
                if db_manager.db_type == DatabaseType.POSTGRESQL:
                    query = "SELECT id, service_type, provider, title_en, status, created_at FROM offers WHERE status = %s ORDER BY created_at DESC LIMIT %s"
                    cur.execute(query, (status, limit))
                else:
                    query = "SELECT id, service_type, provider, title_en, status, created_at FROM offers WHERE status = ? ORDER BY created_at DESC LIMIT ?"
                    cur.execute(query, (status, limit))
            
            rows = cur.fetchall()
            con.close()
            
            return [
                {
                    "id": row[0],
                    "service_type": row[1],
                    "provider": row[2],
                    "title": row[3],
                    "status": row[4],
                    "created_at": row[5]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"❌ Failed to get offers: {e}")
            return []
    
    async def add_offer(self, service_type: str, provider: str, title_en: str, 
                       referral_link: str, title_hi: str = None, title_gu: str = None,
                       description_en: str = None, description_hi: str = None,
                       description_gu: str = None, validity: str = None, terms: str = None) -> Dict:
        """Add new offer"""
        try:
            offer = OfferData(
                service_type=service_type,
                provider=provider,
                title_en=title_en,
                title_hi=title_hi,
                title_gu=title_gu,
                description_en=description_en,
                description_hi=description_hi,
                description_gu=description_gu,
                referral_link=referral_link,
                validity=validity,
                terms=terms
            )
            
            success, message = db_manager.insert_offer(offer)
            return {"success": success, "message": message}
        except Exception as e:
            logger.error(f"❌ Failed to add offer: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_stats(self) -> Dict[str, Dict]:
        """Get database statistics"""
        try:
            stats = db_manager.get_stats()
            return {
                "database_type": db_manager.db_type.value,
                "by_service": stats,
                "total_queued": sum(s["queued"] for s in stats.values()),
                "total_posted": sum(s["posted"] for s in stats.values()),
                "total_failed": sum(s["failed"] for s in stats.values()),
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
    
    async def get_services(self) -> List[Dict]:
        """Get all enabled services"""
        try:
            services = config_manager.list_enabled_services()
            return [
                {
                    "type": s.value,
                    "name": config_manager.get_service_config(s).display_name_en,
                    "emoji": config_manager.get_service_config(s).icon,
                    "channel": config_manager.get_service_config(s).channel.channel_id,
                }
                for s in services
            ]
        except Exception as e:
            logger.error(f"❌ Failed to get services: {e}")
            return []
    
    async def get_channel(self, service_type: str) -> Dict:
        """Get channel for service"""
        try:
            service = ServiceType(service_type)
            channel_id = config_manager.get_channel_for_service(service)
            return {"service": service_type, "channel": channel_id}
        except Exception as e:
            logger.error(f"❌ Failed to get channel: {e}")
            return {"error": str(e)}
    
    async def update_channel(self, service_type: str, channel_id: str) -> Dict:
        """Update channel for service"""
        try:
            if not channel_id.startswith("@"):
                return {"success": False, "message": "Channel ID must start with @"}
            
            service = ServiceType(service_type)
            config_manager.update_channel_id(service, channel_id)
            return {"success": True, "message": f"Updated {service_type} to {channel_id}"}
        except Exception as e:
            logger.error(f"❌ Failed to update channel: {e}")
            return {"success": False, "message": str(e)}
    
    async def block_user(self, user_id: int) -> Dict:
        """Block user"""
        try:
            db_manager.set_user_block_status(user_id, True)
            return {"success": True, "message": f"User {user_id} blocked"}
        except Exception as e:
            logger.error(f"❌ Failed to block user: {e}")
            return {"success": False, "message": str(e)}
    
    async def unblock_user(self, user_id: int) -> Dict:
        """Unblock user"""
        try:
            db_manager.set_user_block_status(user_id, False)
            return {"success": True, "message": f"User {user_id} unblocked"}
        except Exception as e:
            logger.error(f"❌ Failed to unblock user: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_next_offer(self, service_type: str = None, channel_id: str = None) -> Dict:
        """Get next queued offer"""
        try:
            if service_type:
                service = ServiceType(service_type)
                offer_row = db_manager.next_queued_by_service(service)
            elif channel_id:
                offer_row = db_manager.next_queued_by_channel(channel_id)
            else:
                return {"error": "Must provide service_type or channel_id"}
            
            if not offer_row:
                return {"found": False, "message": "No queued offers"}
            
            return {
                "found": True,
                "offer_id": offer_row[0],
                "service_type": offer_row[1],
                "provider": offer_row[2],
                "title_en": offer_row[3],
                "channel_id": offer_row[12]
            }
        except Exception as e:
            logger.error(f"❌ Failed to get next offer: {e}")
            return {"error": str(e)}
    
    async def mark_offer_posted(self, offer_id: int, success: bool = True, error_message: str = None) -> Dict:
        """Mark offer as posted"""
        try:
            db_manager.mark_posted(offer_id, success, error_message)
            return {"success": True, "message": f"Offer {offer_id} marked as {'posted' if success else 'failed'}"}
        except Exception as e:
            logger.error(f"❌ Failed to mark offer: {e}")
            return {"success": False, "message": str(e)}
    
    async def health_check(self) -> Dict:
        """Health check endpoint"""
        try:
            stats = await self.get_stats()
            return {
                "status": "healthy",
                "database": db_manager.db_type.value,
                "stats": stats
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Server instance
mcp_server = MCPServer()

async def main():
    """Main server loop"""
    logger.info("=" * 50)
    logger.info("🚀 FinService-Bot MCP Server Starting")
    logger.info("=" * 50)
    logger.info(f"Database: {db_manager.db_type.value}")
    logger.info(f"Available tools: {', '.join(mcp_server.tools.keys())}")
    logger.info("=" * 50)
    
    # Example: handle stdin/file-based requests
    try:
        while True:
            try:
                line = input()
                request = json.loads(line)
                response = await mcp_server.handle_request(request)
                print(json.dumps(response))
            except EOFError:
                break
            except json.JSONDecodeError as e:
                print(json.dumps({"error": f"Invalid JSON: {e}"}))
            except Exception as e:
                print(json.dumps({"error": str(e)}))
    except KeyboardInterrupt:
        logger.info("\n🛑 MCP Server stopped")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
