import os, aiohttp, psutil, platform, uuid, time
from dotenv import load_dotenv
from urllib.parse import quote
from asyncache import cached
from pympler import asizeof
from cachetools import TTLCache, LFUCache
from interactions import (
    Extension,
    Embed,
    AutoShardedClient,
    Message,
    SlashContext,
    __version__,
    Button,
    ButtonStyle,
    CommandType,
    ContextMenuContext,
    Modal,
    ModalContext,
    ShortText,
    slash_command,
    slash_option,
    context_menu,
    OptionType,
    cooldown,
    Buckets,
)
from utils.colorthief import get_color


class Utilities(Extension):
    bot: AutoShardedClient
    lfu_cache = LFUCache(maxsize=104857600, getsizeof=asizeof.asizeof)
    ttl_cache = TTLCache(maxsize=104857600, ttl=86400, getsizeof=asizeof.asizeof)
    start_time = time.time()
    load_dotenv()
    language_codes = {
        "english": "en",
        "russian": "ru",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
        "arabic": "ar",
        "hindi": "hi",
        "bengali": "bn",
        "portuguese": "pt",
        "italian": "it",
        "dutch": "nl",
        "greek": "el",
        "turkish": "tr",
        "swedish": "sv",
        "norwegian": "no",
        "danish": "da",
        "finnish": "fi",
        "polish": "pl",
        "czech": "cs",
        "hungarian": "hu",
        "romanian": "ro",
        "thai": "th",
        "vietnamese": "vi",
        "indonesian": "id",
        "malay": "ms",
        "hebrew": "he",
        "tagalog": "tl",
    }

    @cached(lfu_cache)
    async def get_translation(self, text: str, target: str, source: str = "auto"):
        translate_url = os.getenv("LINGVA_URL")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                translate_url
                + f"/api/v1/{source}/{target}/{quote(text.replace('/', '[⧸⧸⧸]'))}"
            ) as response:
                if not response.status == 200:
                    raise Exception(f"{translate_url} returned {response.status}")
                data = await response.json()
                translation = data.get("translation", "").replace("[⧸⧸⧸]", "/")
                detected_language = data.get("info", {}).get("detectedSource", "")
                return translation, detected_language

    @cached(ttl_cache)
    async def get_currency_conversion(
        self, base_currency: str, target_currency: str, api_key: str
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            params = {
                "apikey": api_key,
                "base_currency": base_currency.upper(),
                "currencies": target_currency.upper(),
            }

            async with session.get(
                "https://api.freecurrencyapi.com/v1/latest", params=params
            ) as response:
                if not response.status == 200:
                    return None
                data = await response.json()
                return data

    @context_menu(name="Translate Message", context_type=CommandType.MESSAGE)
    @cooldown(Buckets.USER, 2, 10)
    async def translate_ctxmenu(self, ctx: ContextMenuContext):
        message: Message = ctx.target
        jump_button = Button(
            style=ButtonStyle.URL,
            label="Jump to Original Message",
            url=message.jump_url,
        )

        translate_instance = os.getenv("LINGVA_URL")
        if not translate_instance:
            return await ctx.respond(
                "This command is unavailable because no Lingva instance is set.\nA list of instances can be found on https://github.com/thedaviddelta/lingva-translate?tab=readme-ov-file#instances.",
                ephemeral=True,
            )

        lang_modal = Modal(
            ShortText(
                label="Language to translate to",
                value="English",
                custom_id="short_text",
                min_length=2,
                max_length=10,
                required=True,
            ),
            title="Translate",
            custom_id="lang_modal",
        )

        await ctx.send_modal(modal=lang_modal)
        modal_ctx: ModalContext = await ctx.bot.wait_for_modal(lang_modal)

        to_language = self.language_codes.get(
            modal_ctx.responses["short_text"].lower(),
            modal_ctx.responses["short_text"].lower().lower(),
        )
        from_language = "auto"

        if to_language not in self.language_codes.values():
            return await modal_ctx.send(
                f"Invalid language to translate to `{to_language}`.", ephemeral=True
            )
        if (
            from_language not in self.language_codes.values()
            and from_language != "auto"
        ):
            return await modal_ctx.send(
                f"Invalid language to translate from `{from_language}`.", ephemeral=True
            )

        translation, detected_language = await self.get_translation(
            message.content, to_language, from_language
        )
        if not translation:
            return await modal_ctx.send(
                "Something went wrong trying to translate that.", ephemeral=True
            )
        embed = Embed(
            description=translation[:4096],
            color=await get_color(ctx.target.author.avatar_url),
        )
        embed.set_footer(
            text=f"{detected_language if detected_language else from_language} -> {to_language} · {str(ctx.target.author.id)}"
        )
        await modal_ctx.send(embed=embed, components=[jump_button])

    @slash_command(name="translate", description="Translate text")
    @slash_option(
        name="text",
        description="Text to translate",
        required=True,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="to_language",
        description="Language to translate to",
        required=True,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="from_language",
        description="Language to translate from",
        required=False,
        opt_type=OptionType.STRING,
    )
    @cooldown(Buckets.USER, 2, 10)
    async def translate(
        self,
        ctx: SlashContext,
        text: str,
        to_language: str,
        from_language: str = "auto",
    ):
        translate_instance = os.getenv("LINGVA_URL")
        if not translate_instance:
            return await ctx.respond(
                "This command is unavailable because no Lingva instance is set.\nA list of instances can be found on https://github.com/thedaviddelta/lingva-translate?tab=readme-ov-file#instances.",
                ephemeral=True,
            )

        to_language = self.language_codes.get(to_language.lower(), to_language.lower())
        from_language = self.language_codes.get(
            from_language.lower(), from_language.lower()
        )

        if to_language not in self.language_codes.values():
            return await ctx.respond(
                f"Invalid language to translate to `{to_language}`.", ephemeral=True
            )
        if (
            from_language not in self.language_codes.values()
            and from_language != "auto"
        ):
            return await ctx.respond(
                f"Invalid language to translate from `{from_language}`.", ephemeral=True
            )

        translation, detected_language = await self.get_translation(
            text, to_language, from_language
        )
        if not translation:
            return await ctx.respond(
                "Something went wrong trying to translate that.", ephemeral=True
            )
        embed = Embed(
            description=translation[:4096], color=await get_color(ctx.author.avatar_url)
        )
        embed.set_footer(
            text=f"{detected_language if detected_language else from_language} -> {to_language} · {str(ctx.author.id)}"
        )
        await ctx.respond(embed=embed)

    @slash_command(name="currency", description="Convert currencies")
    @slash_option(
        name="amount",
        description="Amount of money to convert",
        required=True,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="from_currency",
        description="Base currency",
        required=True,
        opt_type=OptionType.STRING,
    )
    @slash_option(
        name="to_currency",
        description="Currency to convert to",
        required=True,
        opt_type=OptionType.STRING,
    )
    @cooldown(Buckets.USER, 2, 30)
    async def currency(
        self, ctx: SlashContext, amount: str, from_currency: str, to_currency: str
    ):
        api_key = os.getenv("FREECURRENCYAPI_KEY")
        if not api_key:
            return await ctx.respond(
                "This command is unavailable because no API key is set.\nAn API key can be obtained from https://freecurrencyapi.com.",
                ephemeral=True,
            )

        currency_codes = [
            "EUR",
            "USD",
            "JPY",
            "BGN",
            "CZK",
            "DKK",
            "GBP",
            "HUF",
            "PLN",
            "RON",
            "SEK",
            "CHF",
            "ISK",
            "NOK",
            "HRK",
            "RUB",
            "TRY",
            "AUD",
            "BRL",
            "CAD",
            "CNY",
            "HKD",
            "IDR",
            "ILS",
            "INR",
            "KRW",
            "MXN",
            "MYR",
            "NZD",
            "PHP",
            "SGD",
            "THB",
            "ZAR",
        ]
        currency_symbols = "$¢€£¥₹฿₽₩₺₴₦₲₡₱₮₭₪₸₫₵₢₯₠₣₧₤₥₰₶₺₾"

        amount = amount.strip(currency_symbols)
        from_currency = from_currency.strip(currency_symbols)
        to_currency = to_currency.strip(currency_symbols)

        if not amount.isnumeric:
            return await ctx.respond("Amount must be a number.", ephemeral=True)

        if from_currency.upper() not in currency_codes:
            return await ctx.respond(
                f"Invalid base currency `{from_currency}`.", ephemeral=True
            )

        if to_currency.upper() not in currency_codes:
            return await ctx.respond(
                f"Invalid currency to convert to (`{to_currency}`).", ephemeral=True
            )

        data = await self.get_currency_conversion(from_currency, to_currency, api_key)
        if data is None:
            return await ctx.respond(
                "An error occurred while fetching the data.", ephemeral=True
            )

        result = (
            "{:,.2f}".format(
                round(data["data"].get(to_currency.upper()), 2) * float(amount)
            )
            + " "
            + to_currency.upper()
        )
        amount = "{:,.2f}".format(round(float(amount), 2)) + " " + from_currency.upper()
        embed = Embed(
            description=f"**{amount}** is equal to **{result}**.", color=0x23A55A
        )
        await ctx.respond(embed=embed)

    @slash_command(name="stats", description="View bot statistics")
    @cooldown(Buckets.GUILD, 1, 5)
    async def stats(self, ctx: SlashContext):
        ram = f"{psutil.virtual_memory().used >> 20} MB / {psutil.virtual_memory().total >> 20} MB"
        cpu = f"{psutil.cpu_percent(interval=1)}%"
        randstr = uuid.uuid4().hex.upper()[0:16]
        embed = Embed(title="Bot Stats")
        embed.color = 0x3372A6
        embed.set_image(
            url=f"https://opengraph.githubassets.com/{randstr}/stekc/Keto-Bot"
        )
        embed.add_field(name="OS", value=platform.system(), inline=True)
        embed.add_field(name="CPU", value=cpu, inline=True)
        embed.add_field(name="RAM", value=ram, inline=True)
        embed.add_field(
            name="Bot Uptime",
            value=f"<t:{int(self.start_time)}:R>\n<t:{int(self.start_time)}:D>",
            inline=True,
        )
        embed.add_field(
            name="Python Version", value=platform.python_version(), inline=True
        )
        embed.add_field(name="interactions.py Version", value=__version__, inline=True)
        await ctx.respond(embed=embed)


def setup(bot: AutoShardedClient):
    """Let interactions load the extension"""

    Utilities(bot)
