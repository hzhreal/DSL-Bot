import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import aiosqlite

load_dotenv()

activity = discord.Activity(type=discord.ActivityType.watching, name="Cars")
bot = commands.Bot(command_prefix="|", activity=activity)
DBNAME = "sales.db" # Name of the .db file

# Create table if not existent
async def createTable() -> None:
    async with aiosqlite.connect(DBNAME) as db:
        cursor = await db.cursor()

        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS UserTimestamps (
                username TEXT,
                timestamp DATETIME
            )
            """)
        
        await db.commit()

# Add a timestamp associated to an username
async def insertData(username: str) -> None:
    async with aiosqlite.connect(DBNAME) as db:
        cursor = await db.cursor()

        timestamp = datetime.now()
        await cursor.execute("INSERT INTO UserTimestamps (username, timestamp) VALUES (?, ?)", (username, timestamp))

        await db.commit()

# Fetch all timestamps less than 2 hours ago or all of them depending on the fetchAll boolean variable
async def fetchData(username: str, fetchAll: bool) -> tuple | list:
    data = []
    async with aiosqlite.connect(DBNAME) as db:
        cursor = await db.cursor()

        threshold = datetime.now() - timedelta(hours=2)

        if fetchAll:
            await cursor.execute("SELECT * FROM UserTimestamps WHERE username = ?", (username,))
        else:
            await cursor.execute("SELECT * FROM UserTimestamps WHERE username = ? AND timestamp > ?", (username, threshold))

        rows = await cursor.fetchall()

        for row in rows:
            data.append(row)
        
        return data

# Remove all timestams more than 24 hours ago
async def checkData() -> None:
    async with aiosqlite.connect(DBNAME) as db:
        cursor = await db.cursor()

        threshold = datetime.now() - timedelta(hours=24)
        await cursor.execute("DELETE FROM UserTimestamps WHERE timestamp < ?", (threshold,))

        await db.commit()

@bot.event
async def on_ready() -> None:
    await createTable()
    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )
    while True: # Run forever
        await checkData()

##### STATIC EMBEDS #####
documenting = discord.Embed(title="Documenting",
                                description="Logging your sale...",
                                color=discord.Color.yellow())
documenting.set_footer(text="Created by hzh.")

documented = discord.Embed(title="Success!",
                                    description="Documented your vehicle sale.",
                                    color=discord.Color.green())
documented.set_footer(text="Created by hzh.")

documentedWarning = discord.Embed(title="Success!",
                                    description="Documented your vehicle sale. However, you did not follow the daily sell limit. Make sure to use the check command before you sell a vehicle.",
                                    color=discord.Color.yellow())
documentedWarning.set_footer(text="Created by hzh.")

checking = discord.Embed(title="Checking",
                         description="Examining if you can sell a vehicle without hitting the daily sell limit...",
                         color=discord.Color.yellow())
#########################


@bot.slash_command(description="Document a vehicle sale.")
async def sale(ctx) -> None:
    await ctx.respond(embed=documenting)

    username = str(ctx.author)

    allSales = await fetchData(username, fetchAll=True)
    sales = await fetchData(username, fetchAll=False)

    if len(sales) >= 2 or len(allSales) >= 9:
        await insertData(username)
        
        await ctx.edit(embed=documentedWarning)

    else:
        await insertData(username)

        await ctx.edit(embed=documented)


@bot.slash_command(description="Check if you can sell a vehicle.")
async def check(ctx) -> None:
    await ctx.respond(embed=checking)

    username = str(ctx.author)

    allSales = await fetchData(username, fetchAll=True)
    if len(allSales) == 0:
        formattedAllSales = "None"     
    else:
        formattedAllSales = "\n".join([f"Username: {usernameObtained}, Timestamp: {timestamp}" for usernameObtained, timestamp in allSales])
    sales = await fetchData(username, fetchAll=False)

    if len(sales) >= 2 or len(allSales) >= 9:
        cannotSell = discord.Embed(title="DSL",
                                   description=(
                                       f"SALES LAST 24 HOURS:\n**{formattedAllSales}**\n\n"
                                        "You can not sell a vehicle without hitting the daily sell limit."
                                       f" You have sold **{len(sales)}** vehicles in the last 2 hours, the maximum is 2."
                                       f" You have sold **{len(allSales)}** vehicles in the last 24 hours, the maximum is 9."),
                                   color=discord.Color.red())
        await ctx.edit(embed=cannotSell)
    
    else:
        canSell = discord.Embed(title="DSL",
                                   description=(
                                       f"SALES LAST 24 HOURS:\n**{formattedAllSales}**\n\n"
                                        "You can sell a vehicle without hitting the daily sell limit."
                                       f" You have sold **{len(sales)}** vehicles in the last 2 hours, the maximum is 2."
                                       f" You have sold **{len(allSales)}** vehicles in the last 24 hours, the maximum is 9."),
                                   color=discord.Color.green())
        await ctx.edit(embed=canSell)
    
bot.run(str(os.getenv("TOKEN")))