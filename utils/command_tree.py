from __future__ import annotations
import os
from typing import Any, NotRequired, TypedDict

try:
    import orjson as json
except ImportError:
    import json

import discord
from discord import app_commands

from discord.app_commands import (
    TranslationContext,
    TranslationContextLocation,
    TranslationContextTypes,
    locale_str,
)


class LocaleCommandEmbedAuthor(TypedDict):
    name: str | None

class LocaleCommandEmbedFooter(TypedDict):
    text: str | None

class LocaleComamndEmbedField(TypedDict):
    name: str | None
    value: str | None

class LocaleCommandEmbed(TypedDict):
    title: NotRequired[str | None]
    description: NotRequired[str | None]
    fields: NotRequired[list[LocaleComamndEmbedField]]
    footer: NotRequired[LocaleCommandEmbedFooter]
    author: NotRequired[LocaleCommandEmbedAuthor]

class LocaleCommandOption(TypedDict):
    name: str | None
    description: NotRequired[str | None]
    choices: NotRequired[list[str]]

class LocaleCommand(TypedDict):
    name: str | None
    description: NotRequired[str | None]
    options: NotRequired[dict[str, LocaleCommandOption]]
    embeds: NotRequired[list[LocaleCommandEmbed]]
    content: NotRequired[str | None]


# for type hinting the translator
class JDCommandTree(app_commands.CommandTree):
    @property
    def translator(self) -> JDCommandTranslator:
        return super().translator  # type: ignore


class JDCommandTranslator(app_commands.Translator):
    LOCALS_PATH = "./locales"
    # dynamically loaded in load
    LOCALE_TO_FILE: dict[discord.Locale, str] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # locale: {command_name: LocaleCommand}
        self.cached_locales: dict[discord.Locale, dict[str, LocaleCommand]] = {}

    async def load(self) -> None:
        for file in os.listdir(self.LOCALS_PATH):
            if file.endswith(".json"):
                try:
                    locale = discord.Locale(file.split(".")[0])
                except ValueError:
                    raise ValueError(f"Invalid locale file {file}. Expected a file like `en-US.json`.")

                self.LOCALE_TO_FILE[locale] = file
                await self.get_locale(locale)

    async def unload(self) -> None:
        self.cached_locales.clear()
        self.LOCALE_TO_FILE.clear()

    async def get_locale(self, locale: discord.Locale,) -> dict[str, LocaleCommand]:
        if locale in self.cached_locales:
            return self.cached_locales[locale]

        file = self.LOCALE_TO_FILE[locale]
        with open(f"{self.LOCALS_PATH}/{file}") as f:
            self.cached_locales[locale] = data = json.loads(f.read())

        return data
    
    async def get_command(self, locale: discord.Locale, command_name: str) -> LocaleCommand | None:
        return (await self.get_locale(locale)).get(command_name)
    
    async def translate_embeds(self, interaction: discord.Interaction, embeds: list[discord.Embed], **string_formats: Any) -> list[discord.Embed]:
        new_embeds: list[discord.Embed] = []

        async def do_translate(value: str | None, key: str) -> str | None:
            if not value:
                return None

            translated = await interaction.translate(locale_str(value, key=key), data=interaction.command)
            return (translated or value).format(**string_formats)
        
        for idx, embed in enumerate(embeds):
            embed = embed.copy()
            embed.title = await do_translate(embed.title, f"embed:{idx}:title")
            embed.description = await do_translate(embed.description, f"embed:{idx}:description")
            embed.set_footer(text=await do_translate(embed.footer.text, f"embed:{idx}:footer"))
            embed.set_author(name=await do_translate(embed.author.name, f"embed:{idx}:author"))

            for field_idx, field in enumerate(embed.fields.copy()):
                field.name = await do_translate(field.name, f"embed:{idx}:fields:{field_idx}:name")
                field.value = await do_translate(field.value, f"embed:{idx}:fields:{field_idx}:value")
                embed.set_field_at(field_idx, name=field.name, value=field.value, inline=field.inline)

            new_embeds.append(embed)

        return new_embeds
    
    async def translate_content(self, interaction: discord.Interaction, content: str, **string_formats: Any) -> str:
        translated = await interaction.translate(locale_str(content, key="content"), data=interaction.command)
        if translated and string_formats:
            return translated.format(**string_formats)
        
        return translated or content

    async def translate(
        self, 
        string: app_commands.locale_str,
        locale: discord.Locale, 
        context: TranslationContextTypes
    ) -> str | None:
        if locale not in self.LOCALE_TO_FILE:
            return None

        command_name: str | None = None

        if context.data:
            if isinstance(context.data, (discord.app_commands.Command, discord.app_commands.ContextMenu, discord.app_commands.Group)):
                command_name = context.data.qualified_name
            elif isinstance(context.data, discord.app_commands.Parameter):
                command_name = context.data.command.qualified_name

        command_name = string.extras.get("command") or command_name

        if not command_name:
            raise ValueError(
                (
                    f"locale_str for location {context.location} requires you to pass the"
                    f"command name in extras. Like `locale_str('key', command='command name')`"
                    " or a command/parameter as context.data."
                )
            )

        if context.location is TranslationContextLocation.other:
            key = string.extras.get("key")  # type: ignore
            if not key:
                raise ValueError

        if not command_name:
            raise ValueError("Command name is not provided. Expected a command name in context.data or extras.")
        
        command = await self.get_command(locale, command_name)
        if not command:
            return None
        
        if context.location in (
            TranslationContextLocation.command_name,
            TranslationContextLocation.parameter_name,
        ):
            return command.get("name")
        
        elif context.location in (
            TranslationContextLocation.command_description,
            TranslationContextLocation.group_description,
        ):
            return command.get("description")
        
        elif context.location in (
            TranslationContextLocation.parameter_name,
            TranslationContextLocation.parameter_description,
        ):
            parameter = command.get("options", {}).get(string.message)
            if not parameter:
                return None
            
            if context.location is TranslationContextLocation.parameter_name:
                return parameter.get("name")
            
            return parameter.get("description")
        
        elif context.location is TranslationContextLocation.choice_name:
            idx = string.extras.get("index")
            if idx is None:
                raise ValueError("Choice name requires you to pass the index in extras. Like `locale_str('key', index=0)`")
            
            option_name = string.extras.get("option")
            if not option_name:
                raise ValueError("Choice name requires you to pass the option name in extras. Like `locale_str('key', option='option')`")
            
            choices = command.get("options", {}).get(option_name, {}).get("choices")
            if not choices:
                return None
            
            return choices[idx]

        elif context.location is TranslationContextLocation.other:
            key: str = string.extras.get("key") or ""
            if not key:
                raise ValueError("locale_str for location other requires you to pass the type in extras. Like `locale_str('string', key='type')`")

            if key.startswith("embed"):
                try:
                    _, idx, field, *fields_extra = key.split(":")
                except ValueError:
                    raise ValueError(f"Invalid type for embed. Expected `embed:<index>:<field>`. Got {key}. Example: `embed:0:title`.")
                
                idx = int(idx)
                field = field.lower()
                embed = command.get("embeds", [{}])[idx]
                if not embed:
                    return None
                
                if field == "title":
                    return embed.get("title")
                elif field == "description":
                    return embed.get("description")
                elif field == "footer":
                    return embed.get("footer", {}).get("text")
                elif field == "author":
                    return embed.get("author", {}).get("name")
                elif field == "fields":
                    if not fields_extra:
                        raise ValueError(f"Invalid type for embed. Expected `embed:<index>:fields:<field_index>:name`. Got {key}. Example: `embed:0:fields:0:name`.")
                    
                    try:
                        field_idx, field_type = fields_extra
                    except ValueError:
                        raise ValueError(f"Invalid type for embed. Expected `embed:<index>:fields:<field_index>:name`. Got {key}. Example: `embed:0:fields:0:name`.")
                    
                    field_idx = int(field_idx)

                    field = embed.get("fields", [{}])[field_idx]
                    if not field:
                        return None
                    
                    if field_type == "name":
                        return field.get("name")
                    elif field_type == "value":
                        return field.get("value")
                    else:
                        raise ValueError(f"Field type {field_type} is not valid. Expected `name` or `value`.")
                    
                else:
                    raise ValueError(f"Field {field} is not valid. Expected `title`, `description`, `footer`, `author` or `fields`.")
                
            elif key == "content":
                return command.get("content")