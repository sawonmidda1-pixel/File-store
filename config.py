import os

class Config:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
        self.ADMIN_IDS = [
            x.strip() for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
        ]
        self.OWNER_USERNAME = os.getenv("OWNER_USERNAME", "").strip().lstrip("@")
        self.REFERRAL_COINS = int(os.getenv("REFERRAL_COINS", "10"))
        self.NEW_USER_REF_COINS = int(os.getenv("NEW_USER_REF_COINS", "5"))

        # Example: FORCE_CHANNELS=channel_one,channel_two
        channel_names = [
            x.strip().lstrip("@")
            for x in os.getenv("FORCE_CHANNELS", "").split(",")
            if x.strip()
        ]
        self.FORCE_CHANNELS = [{"username": name} for name in channel_names]

        if not self.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN is missing. Add it in your hosting provider's "
                "Environment Variables / Secrets."
            )
