import discord
from discord import app_commands
from discord.ui import View, Button
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
token = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents=intents)

class MyView(View):
    def __init__(self, suggestion_name: str, target_channel_id: int):
        super().__init__()
        self.suggestion_name = suggestion_name
        self.target_channel_id = target_channel_id

        accept_button = Button(label="Accept", style=discord.ButtonStyle.success)
        accept_button.callback = self.accept
        self.add_item(accept_button)

        deny_button = Button(label="Deny", style=discord.ButtonStyle.danger)
        deny_button.callback = self.deny
        self.add_item(deny_button)

    async def accept(self, interaction: discord.Interaction):
        target_channel = bot.get_channel(self.target_channel_id)
        roles = interaction.user.roles
        role = interaction.guild.get_role(1338408541974696026)
        if role in roles:
            if target_channel:
                await target_channel.send(interaction.message.content)
                await interaction.response.edit_message(content="Suggestion accepted and sent to another channel.", view=None)
            else:
                await interaction.response.send_message("Target channel not found.", ephemeral=True)
        else:
            await interaction.response.send_message("You don't have permission to accept/deny suggestions.", ephemeral=True)

    async def deny(self, interaction: discord.Interaction):
        roles = interaction.user.roles
        role = interaction.guild.get_role(1338408541974696026)
        if role in roles:
            await interaction.response.edit_message(content=f"{self.suggestion_name} - Denied", view=None)
        else:
            await interaction.response.send_message("You don't have permission to accept/deny suggestions.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s) globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

if os.path.exists('audit.json'):
    with open('audit.json', 'r') as f:
        bot_audit = json.load(f)
else:
    bot_audit = {}

def audit_dump():
    with open('audit.json', 'w') as file:
        json.dump(bot_audit, file, indent=4)

@bot.tree.command(name="location_suggest", description="Suggest a location to be archived in the locations channel.")
@app_commands.describe(img="The image file to upload.")
async def location_suggest(inter: discord.Interaction, name: str, desc: str, img: discord.Attachment):
    if img.content_type.startswith('image/'):
        suggestion = f'Suggested location ({name.lower()}) with attachment ({img.filename.lower()}).'
        if suggestion in bot_audit.get('audit', {}):
            await inter.response.send_message("This location has already been suggested.", ephemeral=True)
        else:
            bot_audit.setdefault('audit', {})[suggestion] = 1
            bot_audit['suggested'] = bot_audit.get('suggested', 0) + 1
            audit_dump()
            img_url = img.url
            message = (
                f"# Suggested Location {bot_audit['suggested']}\n"
                f"**Location Name: {name.capitalize()}**\n"
                f"**Location description: {desc}**\n"
                f"**Location visual:** {img_url}"
            )
            bot_audit.setdefault('messages', {})[bot_audit['suggested']] = message
            audit_dump()
            view = MyView(name.capitalize(), 1046450199184289875)
            await inter.response.send_message(message, view=view)
    else:
        await inter.response.send_message(f"{img.filename} is not an image file. Please upload an image.", ephemeral=True)
    audit_dump()

@bot.command(name='shutdown')
@commands.has_any_role('owner')
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    print("Shutting down...")
    await bot.close()

bot.run(token)
    