import os
from interactions import (
    AutoShardedClient,
    Extension,
    SlashContext,
    File,
    Embed,
    Permissions,
    slash_command,
    slash_default_member_permission,
)
from io import BytesIO
from extensions.fixsocials import FixSocials
from extensions.songs import Songs
from extensions.utils import Utilities
from utils.colorthief import lru_cache as lru_size_colorthief


class Admin(Extension):
    bot: AutoShardedClient

    fix_socials_instance = FixSocials(bot=AutoShardedClient())
    songs_instance = Songs(bot=AutoShardedClient())
    utils_instance = Utilities(bot=AutoShardedClient())

    async def convert_bytes_to_mb(self, bytes):
        mb = bytes / (1024 * 1024)
        return "{:.2f} MB".format(mb)

    @slash_command(
        name="admin",
        description="Admin commands",
        group_name="cache",
        group_description="Cache commands",
        sub_cmd_name="view",
        sub_cmd_description="View detailed cache info",
        scopes=[os.getenv("MAIN_GUILD_ID")],
    )
    @slash_default_member_permission(Permissions.ADMINISTRATOR)
    async def cache(self, ctx: SlashContext):
        if ctx.author != self.bot.owner:
            return await ctx.send(
                "This command is restricted to the bot's owner.", ephemeral=True
            )

        cache_instances = [
            ("FixSocials TTL Cache", self.fix_socials_instance.ttl_cache),
            ("FixSocials LRU Cache", self.fix_socials_instance.lru_cache),
            ("Songs LRU Cache", self.songs_instance.lru_cache),
            ("Utils LRU Cache", self.utils_instance.lru_cache),
            ("ColorThief LRU Cache", lru_size_colorthief),
        ]

        total_size = 0
        total_items = 0
        public_msg = Embed(title="Caches", color=0xFF3366)
        file_msg = ""

        for cache_name, cache_instance in cache_instances:
            cache_size = cache_instance.currsize
            cache_max_size = cache_instance.maxsize
            cache_size_mb = await self.convert_bytes_to_mb(cache_size)
            cache_max_size_mb = await self.convert_bytes_to_mb(cache_max_size)
            cache_items = cache_instance.items()

            total_size += cache_size
            total_items += len(cache_items)

            public_msg.add_field(
                name=cache_name,
                value=f"Size: {cache_size_mb}/{cache_max_size_mb}\nItems: {len(cache_items)}",
                inline=True if "FixSocials" in cache_name else False,
            )

            file_msg += (
                f"- {cache_name}\n+ Size: {cache_size_mb}\n+ Items: {cache_items}\n\n"
            )

        total_size_mb = await self.convert_bytes_to_mb(total_size)
        file_msg += f"- Total Size: {total_size_mb}\n- Total Items: {total_items}"

        public_msg.set_footer(
            text=f"Total Size: {total_size_mb} - Total Items: {total_items}"
        )

        file = BytesIO(file_msg.encode())

        if len(file.getbuffer()) >= 8 * 1024 * 1024:
            with open("logs/cache_info.txt", "wb") as f:
                f.write(file.getbuffer())
            await ctx.send(
                "The file was too large to send, it has been saved to the logs folder.",
                embed=public_msg,
                ephemeral=True,
            )
        else:
            await ctx.send(
                embed=public_msg,
                file=File(BytesIO(file_msg.encode()), "caches.txt"),
                ephemeral=True,
            )


def setup(bot: AutoShardedClient):
    Admin(bot)
