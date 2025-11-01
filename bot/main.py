import discord
from discord import app_commands # Used for slash commands
from discord.ext import tasks, commands
import os
import random
from dotenv import load_dotenv

# --- 1. LOAD ENVIRONMENT VARIABLES ---
# Load variables from a .env file (for DISCORD_TOKEN, GUILD_ID, CHANNEL_ID)
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID") # Your Hackathon's Server ID
CHANNEL_ID = os.getenv("CHANNEL_ID") # The channel ID for reminder messages

# A quick check to make sure all env variables are set
if not all([DISCORD_TOKEN, GUILD_ID, CHANNEL_ID]):
    print("FATAL ERROR: Missing one or more environment variables.")
    print("Please check your .env file and ensure DISCORD_TOKEN, GUILD_ID, and CHANNEL_ID are set.")
    exit()

try:
    # Convert IDs from string to int
    MY_GUILD = discord.Object(id=int(GUILD_ID))
    REMINDER_CHANNEL_ID = int(CHANNEL_ID)
except ValueError:
    print("FATAL ERROR: GUILD_ID or CHANNEL_ID in your .env file is not a valid number.")
    exit()


# --- 2. BOT AND INTENTS SETUP ---
# Intents are permissions for your bot. Default is fine for slash commands.
intents = discord.Intents.default()
# We set command_prefix but won't use it for slash commands
bot = commands.Bot(command_prefix="!", intents=intents)


# --- 3. ON_READY EVENT (When Bot Connects) ---
@bot.event
async def on_ready():
    """Called when the bot successfully logs in."""
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
    try:
        # Sync the slash commands to our specific guild.
        # This is *instant* for a single guild, but can take hours globally.
        # For a hackathon, always sync to your guild.
        await bot.tree.sync(guild=MY_GUILD)
        print(f"Synced commands to guild {GUILD_ID}.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Start the reminder loop
    if not send_reminder.is_running():
        send_reminder.start()
        print("Started the 2-hour reminder loop.")


# --- 4. SLASH COMMANDS (Data Collection) ---

@bot.tree.command(name="roast", description="Roast your team's GitHub repo!", guild=MY_GUILD)
@app_commands.describe(text="Your witty (or sad) roast")
async def roast(interaction: discord.Interaction, text: str):
    """Saves a user's text submission."""
    user_name = interaction.user.display_name
    
    # --- !!! SAVE TO YOUR DATABASE HERE !!! ---
    # Example: db.collection("roasts").add({"user": user_name, "roast": text})
    print(f"[DATA] Got ROAST from {user_name}: {text}")
    
    # Send a private confirmation
    await interaction.response.send_message(
        "🔥 Your roast has been submitted to the Rewind! 🔥", 
        ephemeral=True # 'ephemeral=True' makes the reply visible ONLY to the user
    )

@bot.tree.command(name="selfie", description="Submit your awesome team selfie!", guild=MY_GUILD)
@app_commands.describe(image="Upload your team photo")
async def selfie(interaction: discord.Interaction, image: discord.Attachment):
    """Saves a user's image submission."""
    user_name = interaction.user.display_name

    # Basic validation: Check if the attachment is actually an image
    if not image.content_type or not image.content_type.startswith("image/"):
        await interaction.response.send_message(
            "That doesn't look like an image! Please upload a .png, .jpg, or .gif.", 
            ephemeral=True
        )
        return
        
    image_url = image.url
    
    # --- !!! SAVE TO YOUR DATABASE HERE !!! ---
    # Example: db.collection("selfies").add({"user": user_name, "url": image_url})
    print(f"[DATA] Got SELFIE from {user_name}: {image_url}")
    
    await interaction.response.send_message(
        f"📸 Selfie saved! You all look great. {image_url}", 
        ephemeral=True
    )

@bot.tree.command(name="vote_sponsor", description="Vote for your favourite sponsor!", guild=MY_GUILD)
@app_commands.describe(sponsor="Who was the best?")
@app_commands.choices(sponsor=[ # Define the dropdown options
    app_commands.Choice(name="Sponsor A (The Cool One)", value="sponsor_a"),
    app_commands.Choice(name="Sponsor B (The One with Swag)", value="sponsor_b"),
    app_commands.Choice(name="Sponsor C (The Free Food One)", value="sponsor_c"),
])
async def vote_sponsor(interaction: discord.Interaction, sponsor: app_commands.Choice[str]):
    """Saves a user's poll choice."""
    user_name = interaction.user.display_name
    vote_name = sponsor.name  # The user-friendly name, e.g., "Sponsor A"
    vote_value = sponsor.value # The internal value, e.g., "sponsor_a"
    
    # --- !!! SAVE TO YOUR DATABASE HERE !!! ---
    # This is much cleaner than counting reactions!
    # Example: db.collection("sponsor_votes").add({"user": user_name, "vote": vote_value})
    print(f"[DATA] Got VOTE from {user_name} for: {vote_value}")
    
    await interaction.response.send_message(
        f"Got it. Your vote for {vote_name} is in!", 
        ephemeral=True
    )

# --- 5. TASK LOOP (The "Hype Man") ---

@tasks.loop(hours=2.0)
async def send_reminder():
    """Posts a random reminder message in the main channel every 2 hours."""
    
    # A list of messages to cycle through
    reminders = [
        "📣 **REWIND REMINDER!** 📣 Don't forget to submit your **team selfie** using the `/selfie` command!",
        "🔥 **KEEP IT COMING!** 🔥 We're still collecting your **repo roasts**! Use `/roast` to share the pain.",
        "😅 **WHAT'S YOUR BIGGEST SCREWUP?** 😅 We know you have one. Let us know with `/screwup` (if you build it!)",
        "🗳️ **VOTE!** 🗳️ Have you voted for your favourite sponsor yet? Use `/vote_sponsor`!"
    ]
    
    try:
        # Get the channel object from its ID
        channel = bot.get_channel(REMINDER_CHANNEL_ID)
        if channel:
            message = random.choice(reminders)
            await channel.send(message)
            print(f"Sent reminder: {message}")
        else:
            print(f"Error: Could not find channel with ID {REMINDER_CHANNEL_ID}")
            
    except Exception as e:
        print(f"Error in task loop: {e}")

@send_reminder.before_loop
async def before_reminder():
    """Waits until the bot is fully ready before starting the loop."""
    await bot.wait_until_ready()


# --- 6. RUN THE BOT ---
if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("FATAL ERROR: Invalid DISCORD_TOKEN. Please check your .env file.")
    except Exception as e:
        print(f"An error occurred while running the bot: {e}")

