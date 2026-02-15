import os
import sys
import time
import asyncio
import logging
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"⚠ .env file not found at {env_path}")

from telegram import Bot
from telegram.error import TelegramError
from db_layer import db_manager
from config_schema import ServiceType, config_manager
from templates import template_engine, OfferData

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable required")
    logger.error("   Please ensure TELEGRAM_BOT_TOKEN is set in your .env file or environment.")
    sys.exit(1)

logger.info("✓ TELEGRAM_BOT_TOKEN loaded successfully")

bot = Bot(BOT_TOKEN)

class PostingScheduler:

    def __init__(self):
        self.bot = bot
        self.posted_count = 0
        self.failed_count = 0

    def _row_to_offer(self, row: tuple) -> OfferData:
        return OfferData(
            service_type=row[1],
            provider=row[2],
            title_en=row[3],
            title_hi=row[4],
            title_gu=row[5],
            description_en=row[6],
            description_hi=row[7],
            description_gu=row[8],
            referral_link=row[9],
            validity=row[10],
            terms=row[11]
        )

    async def post_by_service(self, service_type: ServiceType) -> bool:
        """
        Post next queued offer for specific service type

        Args:
            service_type: Service to post from

        Returns:
            bool: True if posted, False if queue empty
        """
        row = db_manager.next_queued_by_service(service_type)

        if not row:
            logger.info(f"No queued offers for {service_type.value}")
            return False

        offer_id = row[0]
        channel_id = row[12]
        rotation_index = row[13]

        offer = self._row_to_offer(row)

        service_config = config_manager.get_service_config(service_type)

        message = template_engine.render(offer, service_config, rotation_index)

        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )

            db_manager.mark_posted(offer_id, success=True)
            self.posted_count += 1

            logger.info(
                f"✓ Posted offer #{offer_id} to {channel_id} "
                f"({service_config.display_name_en})"
            )
            return True

        except TelegramError as e:
            error_msg = str(e)
            logger.error(f"✗ Telegram error for offer #{offer_id}: {error_msg}")
            db_manager.mark_posted(offer_id, success=False, error_message=error_msg)
            self.failed_count += 1
            return False

        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ Unexpected error for offer #{offer_id}: {error_msg}")
            db_manager.mark_posted(offer_id, success=False, error_message=error_msg)
            self.failed_count += 1
            return False

    async def post_by_channel(self, channel_id: str) -> bool:
        """
        Post next queued offer for specific channel

        Args:
            channel_id: Target channel ID

        Returns:
            bool: True if posted, False if queue empty
        """
        row = db_manager.next_queued_by_channel(channel_id)

        if not row:
            logger.info(f"No queued offers for {channel_id}")
            return False

        offer_id = row[0]
        service_type = ServiceType(row[1])
        rotation_index = row[13]

        offer = self._row_to_offer(row)

        service_config = config_manager.get_service_config(service_type)

        message = template_engine.render(offer, service_config, rotation_index)

        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )

            db_manager.mark_posted(offer_id, success=True)
            self.posted_count += 1

            logger.info(
                f"✓ Posted offer #{offer_id} to {channel_id} "
                f"({service_config.display_name_en})"
            )
            return True

        except TelegramError as e:
            error_msg = str(e)
            logger.error(f"✗ Telegram error for offer #{offer_id}: {error_msg}")
            db_manager.mark_posted(offer_id, success=False, error_message=error_msg)
            self.failed_count += 1
            return False

        except Exception as e:
            error_msg = str(e)
            logger.error(f"✗ Unexpected error for offer #{offer_id}: {error_msg}")
            db_manager.mark_posted(offer_id, success=False, error_message=error_msg)
            self.failed_count += 1
            return False

    async def post_round_robin(self) -> int:
        """
        Post one offer from each enabled service (round-robin)

        Returns:
            int: Number of offers posted
        """
        services = config_manager.list_enabled_services()
        posted = 0

        for service in services:
            if await self.post_by_service(service):
                posted += 1

        return posted

    async def post_batch(self, max_posts: int = 10) -> int:
        posted = 0
        services = config_manager.list_enabled_services()
        for _ in range(max_posts):
            for service in services:
                if await self.post_by_service(service):
                    posted += 1
                if posted >= max_posts:
                    return posted
        return posted

    async def run_continuous(self, interval_hours: float = 1.6):
        interval_seconds = interval_hours * 3600
        logger.info(f"Starting continuous auto-posting every {interval_hours} hours...")
        
        while True:
            try:
                logger.info("Running scheduled post cycle...")
                posted = await self.post_round_robin()
                logger.info(f"Cycle complete. Posted {posted} offers.")
                
                logger.info(f"Sleeping for {interval_hours} hours...")
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in continuous run: {e}")
                await asyncio.sleep(60) # Wait a bit before retry on error

    def get_summary(self) -> str:
        return f"Posted: {self.posted_count}, Failed: {self.failed_count}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="FinReferrals Posting Scheduler")
    parser.add_argument(
        "--mode",
        choices=["service", "channel", "round-robin", "batch"],
        default="round-robin",
        help="Posting mode"
    )
    parser.add_argument(
        "--service",
        type=str,
        help="Service type for service mode"
    )
    parser.add_argument(
        "--channel",
        type=str,
        help="Channel ID for channel mode"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        help="Max posts for batch mode"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuously at intervals"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.6,
        help="Interval in hours for continuous mode"
    )

    args = parser.parse_args()

    scheduler = PostingScheduler()

    logger.info(f"Starting scheduler in {args.mode} mode...")

    try:
        if args.continuous:
            asyncio.run(scheduler.run_continuous(args.interval))
            return

        if args.mode == "service":
            if not args.service:
                logger.error("--service required for service mode")
                sys.exit(1)

            service_type = ServiceType(args.service)
            asyncio.run(scheduler.post_by_service(service_type))

        elif args.mode == "channel":
            if not args.channel:
                logger.error("--channel required for channel mode")
                sys.exit(1)

            asyncio.run(scheduler.post_by_channel(args.channel))

        elif args.mode == "round-robin":
            posted = asyncio.run(scheduler.post_round_robin())
            logger.info(f"Round-robin complete: {posted} posts")

        elif args.mode == "batch":
            posted = asyncio.run(scheduler.post_batch(args.max))
            logger.info(f"Batch complete: {posted} posts")

        logger.info(f"Summary: {scheduler.get_summary()}")

    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()