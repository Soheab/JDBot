import discord
import random
import tabulate
import typing
from discord.flags import UserFlags
import io
import os
import black
import pathlib
import sys


async def google_tts(bot, text):
    mp3_fp = io.BytesIO(
        await (
            await bot.session.get(
                "https://repi.openrobot.xyz/tts",
                params={"text": text, "lang": "en"},
                headers={"Authorization": os.environ["frostiweeb_api"]},
            )
        ).read()
    )
    mp3_fp.seek(0)
    file = discord.File(mp3_fp, "tts.mp3")
    return file


async def latin_google_tts(bot, text):
    mp3_fp = io.BytesIO(
        await (
            await bot.session.get(
                "https://repi.openrobot.xyz/tts",
                params={"text": text, "lang": "la"},
                headers={"Authorization": os.environ["frostiweeb_api"]},
            )
        ).read()
    )
    mp3_fp.seek(0)
    file = discord.File(mp3_fp, "latin_tts.mp3")
    return file


def reference(message):

    reference = message.reference
    if reference and isinstance(reference.resolved, discord.Message):
        return reference.resolved.to_reference()

    return None


def profile_converter(
    _type: typing.Literal["badges", "mobile", "status", "web", "desktop", "mobile"],
    _enum: typing.Union[discord.Status, discord.UserFlags, str],
):

    badges_emoji = {
        UserFlags.staff: "<:DiscordStaff:859400539221917698>",
        UserFlags.partner: "<:partner:848402357863710762>",
        UserFlags.hypesquad: "<:hypesquad:314068430854684672>",
        UserFlags.bug_hunter: "<:bughunter:585765206769139723>",
        UserFlags.hypesquad_bravery: "<:bravery:585763004218343426>",
        UserFlags.hypesquad_brilliance: "<:brilliance:585763004495298575>",
        UserFlags.hypesquad_balance: "<:balance:585763004574859273>",
        UserFlags.early_supporter: "<:supporter:585763690868113455> ",
        "system": "<:verifiedsystem1:848399959539843082><:verifiedsystem2:848399959241261088>",
        UserFlags.bug_hunter_level_2: "<:goldbughunter:853274684337946648>",
        UserFlags.verified_bot: "<:verifiedbot1:848395737279496242><:verifiedbot2:848395736982749194>",
        UserFlags.verified_bot_developer: "<:verifiedbotdev:853277205264859156>",
        UserFlags.discord_certified_moderator: "<:certifiedmod:853274382339670046>",
        "bot": "<:bot:848395737138069514>",
    }

    status_emojis = {
        discord.Status.online: "<:online:715050614379249744>",
        discord.Status.dnd: "<:dnd:715050614429712394>",
        discord.Status.idle: "<:idle:715050614291431475>",
        discord.Status.offline: "<:offline:715050614366928906>",
    }

    devices_emojis = {
        "mobile": {
            discord.Status.online: "<:onlinemobile:715050614429712384>",
            discord.Status.dnd: "<:dndmobile:715050614047899741>",
            discord.Status.idle: "<:idlemobile:715050614278717500>",
            discord.Status.offline: "<:offline:715050614366928906>",
        },
        "desktop": {
            discord.Status.online: "",
            discord.Status.dnd: "",
            discord.Status.idle: "",
            discord.Status.offline: "",
        },
        "web": {
            discord.Status.online: "",
            discord.Status.dnd: "",
            discord.Status.idle: "",
            discord.Status.offline: "",
        },
    }

    dc = {"status": status_emojis, "badges": badges_emoji, "devices": devices_emojis}
    is_devices = False
    if _type in ("mobile", "desktop", "web"):
      is_devices = True

    dict_to_use = dc.get(_type) if not is_devices else dc["devices"][_type]
    emoji = dict_to_use.get(_enum)
    if not emoji:
      emoji = status_emojis[_enum]
    return emoji


def bit_generator():
    return hex(random.randint(0, 255))[2:]


def cc_generate():
    return f"""
 8107EC20 {bit_generator()}{bit_generator()} 
 8107EC22 {bit_generator()}00
 8107EC28 {bit_generator()}{bit_generator()}
 8107EC2A {bit_generator()}00
 8107EC38 {bit_generator()}{bit_generator()}
 8107EC3A {bit_generator()}00
 8107EC40 {bit_generator()}{bit_generator()}
 8107EC42 {bit_generator()}00
 8107EC50 {bit_generator()}{bit_generator()}
 8107EC52 {bit_generator()}00
 8107EC58 {bit_generator()}{bit_generator()}
 8107EC5A {bit_generator()}00
 8107EC68 {bit_generator()}{bit_generator()}
 8107EC6A {bit_generator()}00
 8107EC70 {bit_generator()}{bit_generator()}
 8107EC72 {bit_generator()}00
 8107EC80 {bit_generator()}{bit_generator()}
 8107EC82 {bit_generator()}00
 8107EC88 {bit_generator()}{bit_generator()}
 8107EC8A {bit_generator()}00
 8107EC98 {bit_generator()}{bit_generator()}
 8107EC9A {bit_generator()}00
 8107ECA0 {bit_generator()}{bit_generator()}
 8107ECA2 {bit_generator()}00""".upper()


async def post(bot, code):

    paste_body = {
        "title": "JDBot Paste",
        "content": code,
        "description": "posted from jdbot",
        "text_colour": "#FFFFFF",
        "background_colour": "#000000",
        "embed_colour": "#FFFFFF",
    }

    response = await bot.session.post(
        "https://api.senarc.org/paste",
        json=paste_body,
        headers={"accept": "application/json", "Content-Type": "application/json"},
    )
    response = await response.json()
    return response.get("url")


async def get_paste(bot, paste_id):
    response = await bot.session.get(
        f"https://api.senarc.org/bin/{paste_id}", headers={"accept": "application/json", "headless": "true"}
    )
    response = await response.json()
    return response.get("content")


def random_history(data, number):
    return random.sample(data, number)


def groupby(iterable: list, number: int):
    resp = []
    while True:
        resp.append(iterable[:number])
        iterable = iterable[number:]
        if not iterable:
            break
    return resp


def npm_create_embed(data: dict):
    e = discord.Embed(title=f"Package information for **{data.get('name')}**")
    e.add_field(
        name="**Latest Version:**", value=f"```py\n{data.get('latest_version', 'None Provided')}```", inline=False
    )
    e.add_field(name="**Description:**", value=f"```py\n{data.get('description', 'None Provided')}```", inline=False)
    formatted_author = ""

    if isinstance(data.get("authors"), list):
        for author_data in data["authors"]:
            formatted_author += f"Email: {author_data.get('email', 'None Provided')}\nName: {author_data['name']}\n\n"

    else:
        formatted_author += f"Email: {data['authors'].get('email', 'None Provided')}\n{data['authors']['name']}"

    e.add_field(name="**Author:**", value=f"```yaml\n{formatted_author}```", inline=False)
    e.add_field(name="**License:**", value=f"```\n{data.get('license', 'None Provided')}```", inline=False)
    dependencies = []
    for lib, min_version in data.get("dependencies", {}).items():
        dependencies.append([lib, min_version])

    e.add_field(
        name="Dependencies:",
        value=f"```py\n{tabulate.tabulate(dependencies, ['Library', 'Minimum version'])}```",
        inline=False,
    )
    if data.get("next_version", "None Provided"):
        e.add_field(name="**Upcoming Version:**", value=f"```py\n{data.get('next_version', 'None Provided')}```")

    return e


def get_required_npm(data):
    latest = data["dist-tags"]["latest"]
    next = data["dist-tags"].get("next")
    version_data = data["versions"][latest]
    name = version_data["name"]
    description = version_data["description"]
    authors = data.get("author", data.get("maintainers"))
    license = version_data.get("license")
    _dependencies = version_data.get("dependencies", {})
    dependencies = {}
    for lib, ver in _dependencies.items():
        dependencies[lib] = ver.strip("^")
    return {
        "latest_version": latest,
        "next_version": next,
        "name": name,
        "description": description,
        "authors": authors,
        "license": license,
        "dependencies": dependencies,
    }


def formatter(code, boolean):
    src = code
    mode = black.Mode(line_length=120) if boolean else black.Mode()
    dst = black.format_str(src, mode=mode)
    black.dump_to_file = lambda *args, **kwargs: None
    return dst


def linecount():
    prefix = sys.prefix.replace("\\", "/")
    to_ignore = (str(prefix.split("/")[-1]), "src") if str(prefix) != str(sys.base_prefix) else "src"

    p = pathlib.Path("./")
    im = cm = cr = fn = cl = ls = fc = 0
    for f in p.rglob("*.py"):
        if f.is_dir() or str(f).startswith(to_ignore):
            continue
        fc += 1
        with f.open() as of:
            for l in of.readlines():
                l = l.strip()
                if l.startswith("class "):
                    cl += 1
                elif l.startswith("def"):
                    fn += 1
                elif l.startswith("async def"):
                    cr += 1
                elif l.startswith(("from", "import")):
                    im += 1
                if "#" in l:
                    cm += 1
                ls += 1

    return f"Files: {fc}\nLines: {ls:,}\nClasses: {cl}\nFunctions: {fn}\nCoroutines: {cr}\nComments: {cm:,}\nImports: {im:,}"
