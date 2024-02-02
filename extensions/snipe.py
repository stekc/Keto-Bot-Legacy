from interactions import (
    listen,
    AutoShardedClient,
    Extension,
    Embed,
    SlashContext,
    slash_command,
    Permissions,
    slash_default_member_permission,
)
from interactions.api.events import MessageCreate
from utils.colorthief import get_color
from collections import deque


class Snipe(Extension):
    bot: AutoShardedClient
    deleted_msgs = deque(maxlen=100000)

    @listen()
    async def on_message_delete(self, event):
        message = event.message
        if not message or not message.guild:
            return
        try:
            if not message.content and message.attachments:
                return
        except AttributeError:
            return

        snipe_data = {
            "channel_id": str(message.channel.id),
            "message": message.content,
            "member_id": message.author.id,
            "embed": message.embeds[0].to_dict() if message.embeds else None,
        }

        self.deleted_msgs.appendleft(snipe_data)

    @slash_command(
        name="snipe", description="View the last deleted message in a channel"
    )
    @slash_default_member_permission(Permissions.MANAGE_MESSAGES)
    async def snipe(self, ctx: SlashContext):
        channel = ctx.channel

        snipe_data = next(
            (
                snipe
                for snipe in self.deleted_msgs
                if snipe["channel_id"] == str(channel.id)
            ),
            None,
        )

        if not snipe_data:
            await ctx.respond(
                f"I couldn't find any deleted messages in this channel.", ephemeral=True
            )
            return

        member = await self.bot.fetch_user(snipe_data["member_id"])
        message = snipe_data["message"]
        old_embed = snipe_data["embed"]

        if old_embed:
            author_text = f"Embed from {member} deleted in #{channel.name}"
            icon_url = member.avatar_url
            color = await get_color(member.avatar_url)

            if message:
                author_text = (
                    f"Message and embed from {member} deleted in #{channel.name}"
                )
                description = f"```diff\n- {message}```"
            else:
                description = None

            embed = Embed(
                author={"name": author_text, "icon_url": icon_url},
                color=color,
                description=description,
                footer=str(member.id),
            )

            await ctx.respond(embeds=[embed, old_embed])
        else:
            author_text = f"Message from {member} deleted in #{channel.name}"
            icon_url = member.avatar_url
            color = await get_color(member.avatar_url)

            if message:
                description = f"```diff\n- {message}```"
            else:
                description = None

            embed = Embed(
                author={"name": author_text, "icon_url": icon_url},
                color=color,
                description=description,
                footer=str(member.id),
            )

            await ctx.respond(embed=embed)


def setup(bot: AutoShardedClient):
    """Let interactions load the extension"""
    Snipe(bot)
