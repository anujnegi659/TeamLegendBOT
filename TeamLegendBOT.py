import discord
from discord.ext import commands
import json
import os
import urllib.parse
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

COC_API_TOKEN = os.getenv("COC_API_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")


LINK_FILE = 'linked_clans.json'
PROFILE_FILE = 'linked_profiles.json'
MAIL_CHANNEL_FILE = 'mail_channel.json'

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!!"), intents=intents)
bot.remove_command("help")

# Your Discord ID and authorized role IDs
BOT_OWNER_ID = 667011170229682201
AUTHORIZED_ROLE_IDS = {1389876000569032764}

def user_is_authorized(ctx):
    if ctx.author.id == BOT_OWNER_ID:
        return True
    user_role_ids = {role.id for role in ctx.author.roles}
    return bool(user_role_ids.intersection(AUTHORIZED_ROLE_IDS))

async def get_mail_channel(bot):
    if not os.path.exists(MAIL_CHANNEL_FILE):
        return None
    try:
        with open(MAIL_CHANNEL_FILE, 'r') as f:
            data = json.load(f)
        channel_id = data.get("channel_id")
        if channel_id is None:
            return None
        return bot.get_channel(channel_id)
    except Exception:
        return None

def is_valid_tag(tag: str) -> bool:
    valid_chars = "0289PYLQGRJCUV"
    tag = tag.upper().replace("#", "")
    return len(tag) > 0 and all(c in valid_chars for c in tag)

# Initialize JSON files if they do not exist
for file in [LINK_FILE, PROFILE_FILE, MAIL_CHANNEL_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

    intro_channel = bot.get_channel(1400207435834069025)
    if intro_channel:
        await intro_channel.send("https://i.ibb.co/3ysZHc4T/Real-TEAM-LEGEND.png")

        embed = discord.Embed(
            title="🤖 Welcome to Team Legend's Official Bot!",
            description=(
                "This Discord server is powered by a custom-built **Clash of Clans bot** "
                "tailored for **Team Legend**!\n\n"
                "🛠️ **Use the bot to manage:**\n"
                "• Clan & profile links\n"
                "• War mails\n"
                "• CWL coordination\n"
                "• And much more...\n\n"
                "📌 **Prefix:** `#`\n"
                "📖 **Type `#help` to explore all available commands.**\n\n"
                f"👑 **Bot Owner:** <@{BOT_OWNER_ID}>"
            ),
            color=discord.Color.teal()
        )
        await intro_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    added_roles = [role for role in after.roles if role not in before.roles]
    special_role_id = 1387690633614987346
    welcome_channel_id = 1387813891311931412

    for role in added_roles:
        if role.id == special_role_id:
            channel = bot.get_channel(welcome_channel_id)
            if channel is not None:
                user_mention = after.mention
                message = (
                    f"🎉 Welcome {user_mention} to Team Legend! You just got the special role! 🎉\n\n"
                    "Please check these important channels for updates and info:\n\n"
                    "**Win/Loss mail:** <#1387697234757554296>\n"
                    "**CWL clan links:** <#1387806286422347916>\n"
                    "**CWL Registration:** <#1387817486350815423>\n"
                )
                await channel.send(message)
            break

# --- HELLO COMMAND ---
@bot.command()
async def hello(ctx):
    bot_creator_mention = f"<@{BOT_OWNER_ID}>"
    embed = discord.Embed(
        title="《《 Clan Profile 》》",
        description=f"⟦ Welcome {ctx.author.mention} ⟧",
        color=discord.Color.teal()
    )
    embed.add_field(name="≪ Clan Name ≫", value="» Team Legend «", inline=False)
    embed.add_field(name="≪ Clan Tag ≫", value="» #2L80RLGJ8 «", inline=False)
    embed.set_footer(text=f"Bot developed by {bot_creator_mention}")
    await ctx.send(embed=embed)

# --- LINKCLAN ---
@bot.command()
async def linkclan(ctx, tag: str):
    tag = tag.upper().replace("#", "")
    if not is_valid_tag(tag):
        embed = discord.Embed(title="<< Invalid Tag >>",
                              description="!! Please provide a valid clan tag !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    encoded_tag = urllib.parse.quote(f"#{tag}")
    url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            embed = discord.Embed(title="<< Clan Not Found >>",
                                  description=f"!! Could not find a clan with that tag. Check and try again !!\n\nStatus: {response.status_code} - {response.text}",
                                  color=discord.Color.red())
            await ctx.send(embed=embed)
            return
    except Exception as e:
        embed = discord.Embed(title="<< API Error >>",
                              description=f"!! Failed to connect to Clash of Clans API. Try again later. !!\n\nError: {e}",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    clan_data = response.json()
    clan_name = clan_data.get("name", "Unknown Clan")

    with open(LINK_FILE, 'r') as f:
        data = json.load(f)

    user_id = str(ctx.author.id)
    if user_id not in data:
        data[user_id] = []

    if tag in data[user_id]:
        embed = discord.Embed(title="<< Already Linked >>",
                              description=f"!! You have already linked clan => #{tag} !!",
                              color=discord.Color.orange())
        await ctx.send(embed=embed)
        return

    data[user_id].append(tag)
    with open(LINK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    embed = discord.Embed(title="<< Clan Linked >>",
                          description="++ Successfully linked clan ++",
                          color=discord.Color.green())
    embed.add_field(name=":: Clan Name ::", value=f"=> {clan_name}", inline=False)
    embed.add_field(name=":: Clan Tag ::", value=f"=> #{tag}", inline=False)
    await ctx.send(embed=embed)

@linkclan.error
async def linkclan_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="<< Missing Argument >>",
                              description="!! Kindly provide the clan tag to proceed. !!\nUsage: !!linkclan <clan_tag>",
                              color=discord.Color.orange())
        await ctx.send(embed=embed)

# --- DEBUG TOKEN ---
@bot.command()
async def debugtoken(ctx, tag: str = "2L80RLGJ8"):
    tag = tag.upper().replace("#", "")
    encoded_tag = urllib.parse.quote(f"#{tag}")
    url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}"
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            clan_name = response.json().get("name")
            embed = discord.Embed(
                title="✅ API Token is Valid",
                description=f"Successfully fetched clan: `{clan_name}`",
                color=discord.Color.green()
            )
        elif response.status_code == 403:
            embed = discord.Embed(
                title="🚫 Invalid or Unauthorized Token",
                description="The token may be expired, incorrect, or the IP is not authorized.\n\n"
                            "Go to https://developer.clashofclans.com to generate a new token.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="⚠️ Unknown Error",
                description=f"Status code: {response.status_code}\n{response.text}",
                color=discord.Color.orange()
            )
    except Exception as e:
        embed = discord.Embed(
            title="❌ API Error",
            description=f"Exception occurred: {e}",
            color=discord.Color.red()
        )

    await ctx.send(embed=embed)





# --- UNLINKCLAN ---
@bot.command()
async def unlinkclan(ctx, tag: str):
    tag = tag.upper().replace("#", "")
    if not os.path.exists(LINK_FILE):
        embed = discord.Embed(title="<< Not Linked >>",
                              description="!! You haven't linked any clan yet !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    with open(LINK_FILE, 'r') as f:
        data = json.load(f)

    user_id = str(ctx.author.id)
    if user_id not in data or tag not in data[user_id]:
        embed = discord.Embed(title="<< Not Linked >>",
                              description="!! You haven't linked this clan !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    data[user_id].remove(tag)
    if not data[user_id]:
        del data[user_id]

    with open(LINK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    embed = discord.Embed(title="<< Clan Unlinked >>",
                          description=f"++ Successfully unlinked clan tag => #{tag} ++",
                          color=discord.Color.green())
    await ctx.send(embed=embed)

@unlinkclan.error
async def unlinkclan_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="<< Missing Argument >>",
                              description="!! Please provide the clan tag to unlink.\nUsage: !unlinkclan <clan_tag> !!",
                              color=discord.Color.orange())
        await ctx.send(embed=embed)

# --- MYCLAN ---
@bot.command()
async def myclan(ctx):
    if not os.path.exists(LINK_FILE):
        embed = discord.Embed(title="≪ No Linked Clans ≫",
                              description="❗ You haven't linked any clans yet.",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    with open(LINK_FILE, 'r') as f:
        data = json.load(f)

    tags = data.get(str(ctx.author.id))
    if not tags:
        embed = discord.Embed(title="≪ No Linked Clans ≫",
                              description="❗ You haven't linked any clans yet.",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    embed = discord.Embed(
        title=f"《 Linked Clans for {ctx.author.display_name} 》",
        color=discord.Color.blue()
    )
    
    separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

    for tag in tags:
        try:
            url = f"https://api.clashofclans.com/v1/clans/%23{tag}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                clan_data = response.json()
                clan_name = clan_data.get("name", "Unknown Clan")
                clan_tag_display = f"◆ Tag : #{tag}"
            else:
                clan_name = "Unknown Clan"
                clan_tag_display = f"!! Could not fetch info for #{tag} !!"
        except Exception:
            clan_name = "Unknown Clan"
            clan_tag_display = f"!! Could not fetch info for #{tag} !!"

        embed.add_field(name="\u200b", value=separator, inline=False)
        embed.add_field(name=f"◈ Clan : {clan_name}", value=clan_tag_display, inline=False)

    embed.add_field(name="\u200b", value=separator, inline=False)

    await ctx.send(embed=embed)

# --- LINKPROFILE ---
@bot.command()
async def linkprofile(ctx, tag: str):
    tag = tag.upper().replace("#", "")
    if not is_valid_tag(tag):
        embed = discord.Embed(title="<< Invalid Tag >>",
                              description="!! Please provide a valid player tag !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    url = f"https://api.clashofclans.com/v1/players/%23{tag}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            embed = discord.Embed(title="<< Player Not Found >>",
                                  description="!! Could not find a player with that tag. Check and try again !!",
                                  color=discord.Color.red())
            await ctx.send(embed=embed)
            return
    except Exception:
        embed = discord.Embed(title="<< API Error >>",
                              description="!! Failed to connect to Clash of Clans API. Try again later. !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    player_data = response.json()
    player_name = player_data.get("name", "Unknown Player")

    with open(PROFILE_FILE, 'r') as f:
        data = json.load(f)

    user_id = str(ctx.author.id)
    if user_id not in data:
        data[user_id] = []

    if tag in data[user_id]:
        embed = discord.Embed(title="<< Already Linked >>",
                              description=f"!! You have already linked profile => #{tag} !!",
                              color=discord.Color.orange())
        await ctx.send(embed=embed)
        return

    data[user_id].append(tag)
    with open(PROFILE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    embed = discord.Embed(title="<< Profile Linked >>",
                          description="++ Successfully linked player profile ++",
                          color=discord.Color.green())
    embed.add_field(name="◈ Player :", value=f"{player_name}", inline=False)
    embed.add_field(name="◆ Tag :", value=f"#{tag}", inline=False)
    await ctx.send(embed=embed)

@linkprofile.error
async def linkprofile_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="<< Missing Argument >>",
                              description="!! Kindly provide the player tag to proceed. !!\nUsage: !linkprofile <player_tag>",
                              color=discord.Color.orange())
        await ctx.send(embed=embed)

# --- UNLINKPROFILE ---
@bot.command()
async def unlinkprofile(ctx, tag: str):
    tag = tag.upper().replace("#", "")
    if not os.path.exists(PROFILE_FILE):
        embed = discord.Embed(title="<< Not Linked >>",
                              description="!! You haven't linked any player profiles yet !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    with open(PROFILE_FILE, 'r') as f:
        data = json.load(f)

    user_id = str(ctx.author.id)
    if user_id not in data or tag not in data[user_id]:
        embed = discord.Embed(title="<< Not Linked >>",
                              description="!! You haven't linked this player profile !!",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    data[user_id].remove(tag)
    if not data[user_id]:
        del data[user_id]

    with open(PROFILE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    embed = discord.Embed(title="<< Profile Unlinked >>",
                          description=f"++ Successfully unlinked player profile => #{tag} ++",
                          color=discord.Color.green())
    await ctx.send(embed=embed)

@unlinkprofile.error
async def unlinkprofile_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="<< Missing Argument >>",
                              description="!! Please provide the player tag to unlink.\nUsage: !unlinkprofile <player_tag> !!",
                              color=discord.Color.orange())
        await ctx.send(embed=embed)

# --- MYPROFILE ---
@bot.command()
async def myprofile(ctx):
    if not os.path.exists(PROFILE_FILE):
        embed = discord.Embed(title="≪ No Linked Profiles ≫",
                              description="❗ You haven't linked any player profiles yet.",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    with open(PROFILE_FILE, 'r') as f:
        data = json.load(f)

    tags = data.get(str(ctx.author.id))
    if not tags:
        embed = discord.Embed(title="≪ No Linked Profiles ≫",
                              description="❗ You haven't linked any player profiles yet.",
                              color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    embed = discord.Embed(
        title=f"《 Linked Player Profiles for {ctx.author.display_name} 》",
        color=discord.Color.blue()
    )
    
    separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

    for tag in tags:
        try:
            url = f"https://api.clashofclans.com/v1/players/%23{tag}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                player_data = response.json()
                player_name = player_data.get("name", "Unknown Player")
                tag_display = f"◆ Tag : #{tag}"
            else:
                player_name = "Unknown Player"
                tag_display = f"!! Could not fetch info for #{tag} !!"
        except Exception:
            player_name = "Unknown Player"
            tag_display = f"!! Could not fetch info for #{tag} !!"

        embed.add_field(name="\u200b", value=separator, inline=False)
        embed.add_field(name=f"◈ Player : {player_name}", value=tag_display, inline=False)

    embed.add_field(name="\u200b", value=separator, inline=False)

    await ctx.send(embed=embed)

# --- WAR MESSAGE FUNCTION ---
async def send_war_message(ctx, war_type: str):
    if not user_is_authorized(ctx):
        await ctx.send("⛔ You do not have permission to run this command.")
        return

    mail_channel = await get_mail_channel(bot)
    if mail_channel is None:
        authorized_mentions = " and ".join(f"<@&{role_id}>" for role_id in AUTHORIZED_ROLE_IDS)
        alert_msg = (
            f"⚠️ Mail channel is not set yet! Please set it using `!setmailchannel` command.\n"
            f"Only {ctx.author.mention} and roles {authorized_mentions} can run war commands."
        )
        embed = discord.Embed(title="<< Mail Channel Not Set >>", description=alert_msg, color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    clan_tag = "2L80RLGJ8"  # Your clan tag WITHOUT #
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    war_url = f"https://api.clashofclans.com/v1/clans/%23{clan_tag}/currentwar"

    response = requests.get(war_url, headers=headers)
    if response.status_code != 200:
        await ctx.send("❌ Could not fetch current war info. Maybe no war is running?")
        return

    war_data = response.json()
    opponent_clan = war_data.get("opponent")
    if not opponent_clan:
        await ctx.send("⚠️ Opponent clan data not found in current war info.")
        return

    opponent_name = opponent_clan.get("name", "Unknown Opponent")
    opponent_tag = opponent_clan.get("tag", "#UNKNOWN").upper()

    # Send role mention at top
    role_mention = "<@&1387690633614987346>"
    await mail_channel.send(role_mention)

    separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    clan_name = "Team Legend"
    clan_tag_display = f"#{clan_tag}"

    if war_type == "win":
        title = f"✨🏆 ══ 𝗪𝗜𝗡 𝗪𝗔𝗥 𝘝𝘚 ✦ {opponent_name} ══ 🏆✨"
        description = (
            f"🔥 {clan_name} {clan_tag_display} 🔥 VS 🔥 {opponent_name} {opponent_tag} 🔥\n\n"
            f"{separator}\n\n"
            "🅰️ 1st attack: Mirror (opposite same base) for **3 stars** 🌟 (Compulsory)\n\n"
            "🅱️ 2nd attack: BASE-1 for **1 star** 🌟 (After no. 1 takes mirror)\n\n"
            "♻️ Clean up: In last 12 hours, all bases open for **3 stars** 🌟\n\n"
            "❌ Don't fill war CC. 💰 Enjoy loot 💰\n\n"
            "🏆 Target: Reach **150 stars**\n\n"
            f"{separator}\n\n"
            "⚔️ 𝗚𝗼𝗼𝗱 𝗹𝘂𝗰𝗸, 𝗧𝗲𝗮𝗺 𝗟𝗲𝗴𝗲𝗻𝗱! ⚔️"
        )
    else:
        title = f"❄️⚔️ ══ 𝗟𝗢𝗦𝗦 𝗪𝗔𝗥 𝘝𝘚 ✦ {opponent_name} ══ ⚔️❄️"
        description = (
            f"🔥 {clan_name} {clan_tag_display} 🔥 VS 🔥 {opponent_name} {opponent_tag} 🔥\n\n"
            f"{separator}\n\n"
            "🅰️ First Attack: Hit the same number as your position. Go for a strong **2 stars** 🌟\n\n"
            "🅱️ Second Attack: Hit the #1 enemy base for **1 star** (only after our #1 has done their hit)\n\n"
            "♻️ Last 12 hours: Attack any non-attacked bases for **2 stars** 🌟\n\n"
            "❌ Don't fill war CC. 💰 Enjoy loot 💰\n\n"
            "🏆 Target: Reach **100 stars**\n\n"
            f"{separator}\n\n"
            "⚔️ 𝗚𝗼𝗼𝗱 𝗹𝘂𝗰𝗸, 𝗧𝗲𝗮𝗺 𝗟𝗲𝗴𝗲𝗻𝗱! ⚔️"
        )

    embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
    await mail_channel.send(embed=embed)
    await ctx.send(f"✅ War {war_type} message sent in {mail_channel.mention}")




# --- TLWIN COMMAND ---
@bot.command()
async def TLwin(ctx):
    await send_war_message(ctx, "win")

@bot.command()
async def TLloss(ctx):
    await send_war_message(ctx, "loss")





# --- SETMAILCHANNEL COMMAND ---
@bot.command()
async def setmailchannel(ctx, channel: discord.TextChannel = None):
    if not user_is_authorized(ctx):
        await ctx.send("⛔ You do not have permission to set the mail channel.")
        return
    if channel is None:
        await ctx.send("⚠️ Please mention a valid text channel.\nUsage: `!setmailchannel #channel`")
        return
    with open(MAIL_CHANNEL_FILE, 'w') as f:
        json.dump({"channel_id": channel.id}, f)
    await ctx.send(f"✅ Mail channel successfully set to {channel.mention}")




# ------------------------------
# 📬 Custom Win/Loss Mail Command (Multi-tag) — Anyone can use
# ------------------------------

def sanitize_tag(tag: str) -> str:
    return tag.upper().replace("#", "").strip()

async def fetch_war_info(clan_tag: str):
    headers = {"Authorization": f"Bearer {COC_API_TOKEN}"}
    url = f"https://api.clashofclans.com/v1/clans/%23{clan_tag}/currentwar"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json()

async def send_war_mail_for_tags(ctx, tags: list, war_type: str):
    for raw_tag in tags:
        clan_tag = sanitize_tag(raw_tag)

        if not is_valid_tag(clan_tag):
            await ctx.send(f"❌ Invalid tag: `{raw_tag.strip()}`")
            continue

        war_data = await fetch_war_info(clan_tag)
        if not war_data or "clan" not in war_data or "opponent" not in war_data:
            await ctx.send(f"⚠️ Could not fetch war info for `#{clan_tag}`. Make sure the clan is in an active war.")
            continue

        clan_name = war_data["clan"].get("name", "Unknown")
        clan_tag_display = war_data["clan"].get("tag", f"#{clan_tag}")

        opponent_name = war_data["opponent"].get("name", "Unknown Opponent")
        opponent_tag = war_data["opponent"].get("tag", "#UNKNOWN")

        separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if war_type == "win":
            title = f"✨🏆 ══ 𝗪𝗜𝗡 𝗪𝗔𝗥 𝘝𝘚 ✦ {opponent_name} ══ 🏆✨"
            description = (
                f"🔥 {clan_name} {clan_tag_display} 🔥 VS 🔥 {opponent_name} {opponent_tag} 🔥\n\n"
                f"{separator}\n\n"
                "🅰️ 1st attack: Mirror (opposite same base) for **3 stars** 🌟 (Compulsory)\n\n"
                "🅱️ 2nd attack: BASE-1 for **1 star** 🌟 (After no. 1 takes mirror)\n\n"
                "♻️ Clean up: In last 12 hours, all bases open for **3 stars** 🌟\n\n"
                "❌ Don't fill war CC. 💰 Enjoy loot 💰\n\n"
                "🏆 Target: Reach **150 stars**\n\n"
                f"{separator}\n\n"
                "⚔️ 𝗚𝗼𝗼𝗱 𝗟𝘂𝗰𝗸 𝗪𝗮𝗿𝗿𝗶𝗼𝗿𝘀! ⚔️"
            )
        else:
            title = f"❄️⚔️ ══ 𝗟𝗢𝗦𝗦 𝗪𝗔𝗥 𝘝𝘚 ✦ {opponent_name} ══ ⚔️❄️"
            description = (
                f"🔥 {clan_name} {clan_tag_display} 🔥 VS 🔥 {opponent_name} {opponent_tag} 🔥\n\n"
                f"{separator}\n\n"
                "🅰️ First Attack: Hit the same number as your position. Go for a strong **2 stars** 🌟\n\n"
                "🅱️ Second Attack: Hit the #1 enemy base for **1 star** (only after our #1 has done their hit)\n\n"
                "♻️ Last 12 hours: Attack any non-attacked bases for **2 stars** 🌟\n\n"
                "❌ Don't fill war CC. 💰 Enjoy loot 💰\n\n"
                "🏆 Target: Reach **100 stars**\n\n"
                f"{separator}\n\n"
                "⚔️ 𝗙𝗶𝗴𝗵𝘁 𝗧𝗶𝗹𝗹 𝗧𝗵𝗲 𝗘𝗻𝗱! ⚔️"
            )

        embed = discord.Embed(title=title, description=description, color=discord.Color.dark_blue())
        await ctx.send(embed=embed)

# --- !!winmail <tag1,tag2,...>
@bot.command()
async def winmail(ctx, *, tags: str = None):
    if not tags:
        embed = discord.Embed(
            title="🚨 Missing Clan Tag(s)",
            description=(
                "Please provide at least one valid clan tag.\n\n"
                "**Example Usage:**\n"
                "`!winmail #CLANTAG1, #CLANTAG2, ...`"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    tag_list = tags.split(",")
    await send_war_mail_for_tags(ctx, tag_list, "win")

# --- !lossmail <tag1,tag2,...>
@bot.command()
async def lossmail(ctx, *, tags: str = None):
    if not tags:
        embed = discord.Embed(
            title="🚨 Missing Clan Tag(s)",
            description=(
                "Please provide at least one valid clan tag.\n\n"
                "**Example Usage:**\n"
                "`!lossmail #CLANTAG1, #CLANTAG2, ...`"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    tag_list = tags.split(",")
    await send_war_mail_for_tags(ctx, tag_list, "loss")







# ===== HELP COMMAND PAGES =====
HELP_PAGES = {
    "General Commands": (
        "🌟 **General Commands:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "`!!hello` - Show clan profile info.\n"
        "`!!myclan` - Show your linked clans.\n"
        "`!!myprofile` - Show your linked player profiles.\n"
        "`!!linkclan <clan_tag>` - Link your clan.\n"
        "`!!unlinkclan <clan_tag>` - Unlink your clan.\n"
        "`!!linkprofile <player_tag>` - Link your player profile.\n"
        "`!!unlinkprofile <player_tag>` - Unlink your player profile.\n"
    ),
    "War Mail Commands": (
        "⚔️ **War Mail Commands:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "`!!winmail <clan_tag(s)>` - Send WIN war message for any clan.\n"
        "`!!lossmail <clan_tag(s)>` - Send LOSS war message for any clan.\n"
        "Note: Multiple clan tags separated by commas.\n"
    ),
    "Clan/Profile Linking": (
        "🔗 **Clan & Profile Linking:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Link or unlink your Clash of Clans clans and player profiles.\n"
        "Commands: `!!linkclan`, `!!unlinkclan`, `!!linkprofile`, `!!unlinkprofile`.\n"
    ),
    "Admin Commands": (
        "🛡️ **Admin Commands:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "`!!setmailchannel #channel` - Set channel to send war mails.\n"
        "`!!TLwin` - Send Team Legend WIN war message (Admin only).\n"
        "`!!TLloss` - Send Team Legend LOSS war message (Admin only).\n"
        "Only users with admin role or bot owner can run these.\n"
    ),
    "Bot Info": (
        "🤖 **Bot Information:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "This bot helps you manage Clash of Clans clan & player linking, war mail announcements, and more!\n"
        "Bot Creator: <@667011170229682201>\n"
        "Use the dropdown below to navigate help pages.\n"
    ),
}

# ===== HELP SELECT MENU CLASS =====
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=key, description=f"View commands for {key}") for key in HELP_PAGES.keys()
        ]
        super().__init__(placeholder="Select a help category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        page = self.values[0]
        content = HELP_PAGES.get(page, "Page not found.")
        embed = discord.Embed(title=page, description=content, color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=self.view)

# ===== HELP VIEW WITH SELECT MENU =====
class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

# ===== HELP COMMAND =====
@bot.command(name="help")
async def help_command(ctx):
    """Show help pages with dropdown menu"""
    # Default page to show initially
    initial_page = "Bot Info"
    embed = discord.Embed(title=initial_page, description=HELP_PAGES[initial_page], color=discord.Color.blue())
    await ctx.send(embed=embed, view=HelpView())







# --- RUN BOT ---
bot.run(os.getenv("DISCORD_TOKEN"))