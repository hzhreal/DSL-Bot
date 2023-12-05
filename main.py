import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from database import Db
import asyncio
import time

load_dotenv()

activity = discord.Activity(type=discord.ActivityType.watching, name="Cars")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="|", activity=activity, intents=intents)
DSLDOCS = "https://docs.google.com/document/d/1J-kznWsShh6xWMx7faJlhbWmNIMcHLvwiXS7ZEvaL2w/edit?usp=sharing/"
MAX_SALES_PER_USER = 20

# Remove all timestams more than 24 hours ago
@tasks.loop()
async def daemon() -> None:
    await Db.checkData()

@bot.event
async def on_ready() -> None:
    await Db.createTable()
    daemon.start()
    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )

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
                                    description=(
                                         "Documented your vehicle sale. However, you did not follow the daily sell limit, DO NOT SELL ANOTHER VEHICLE.\n"
                                         "Make sure to use the /check command before you sell a vehicle!\n"
                                        f"CHECK OUT [Detailed Guide About DSL]({DSLDOCS})"),
                                    color=discord.Color.yellow())
documentedWarning.set_footer(text="Created by hzh.")

checking = discord.Embed(title="Checking",
                         description="Examining if you can sell a vehicle without hitting the daily sell limit...",
                         color=discord.Color.yellow())
checking.set_footer(text="Created by hzh.")

fetching = discord.Embed(title="Fetching",
                         description="Fetching your documented sales...",
                         color=discord.Color.yellow())
fetching.set_footer(text="Created by hzh.")

noSales = discord.Embed(title="No sales found",
                        description="You have not documented any sales.",
                        color=discord.Color.red())
noSales.set_footer(text="Created by hzh.")

timedOut = discord.Embed(title="Timed out",
                         description="You took too long!",
                         color=discord.Color.red())
timedOut.set_footer(text="Created by hzh.")

maxSales = discord.Embed(title="Max sales reached",
                         description="You are using this bot incorrectly by not following the daily sell limit. Your sale is not being documented.",
                         color=discord.Color.red())
maxSales.set_footer(text="Created by hzh.")
#########################

@bot.slash_command(description="Document a vehicle sale.")
async def sale(ctx) -> None:
    await ctx.respond(embed=documenting)

    username = str(ctx.author)

    allSales = await Db.fetchData(username, fetchAll=True)
    sales = await Db.fetchData(username, fetchAll=False)

    if len(allSales) == MAX_SALES_PER_USER:
        await ctx.edit(embed=maxSales)

    elif len(sales) >= 2 or len(allSales) >= 9:
        await Db.insertData(username)
        
        await ctx.edit(embed=documentedWarning)

    else:
        await Db.insertData(username)

        await ctx.edit(embed=documented)

@bot.slash_command(description="Check if you can sell a vehicle.")
async def check(ctx) -> None:
    await ctx.respond(embed=checking)

    username = str(ctx.author)

    allSales = await Db.fetchData(username, fetchAll=True)
    if len(allSales) == 0:
        formattedAllSales = "None"     
    else:
        formattedAllSales = "\n".join([f"{index + 1}. Username: {usernameObtained}, Timestamp: {timestamp}" for index, (_, usernameObtained, timestamp) in enumerate(allSales)])
    sales = await Db.fetchData(username, fetchAll=False)

    if (len(sales) == 2 and len(allSales) == 9) or (len(allSales) == 9 and len(sales) < 2):
        timestamps = [timestamp for _, _, timestamp in allSales]
        timestamp_datetime = datetime.now() - datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S.%f")
        timeLeft = (timedelta(hours=24) - timestamp_datetime).total_seconds()

        epoch = time.time()
        epochFormatted = f"<t:{round(epoch + timeLeft)}:R>"

        cannotSell = discord.Embed(title="DSL",
                                   description=(
                                       f"SALES LAST 24 HOURS:\n**{formattedAllSales}**\n\n"
                                       f"You have sold **{len(sales)}** vehicles in the last 2 hours, the maximum is 2.\n"
                                       f"You have sold **{len(allSales)}** vehicles in the last 24 hours, the maximum is 9.\n"
                                       f"You can not sell a vehicle without hitting the daily sell limit, {epochFormatted}."),
                                   color=discord.Color.red())
        cannotSell.set_footer(text="Created by hzh.")
        await ctx.edit(embed=cannotSell)
    
    elif len(sales) == 2 and len(allSales) < 9:
        timestamps = [timestamp for _, _, timestamp in sales]
        timestamp_datetime = datetime.now() - datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S.%f")
        timeLeft = (timedelta(hours=2) - timestamp_datetime).total_seconds()
      
        epoch = time.time()
        epochFormatted = f"<t:{round(epoch + timeLeft)}:R>"

        cannotSell = discord.Embed(title="DSL",
                                   description=(
                                       f"SALES LAST 24 HOURS:\n**{formattedAllSales}**\n\n"
                                       f"You have sold **{len(sales)}** vehicles in the last 2 hours, the maximum is 2.\n"
                                       f"You have sold **{len(allSales)}** vehicles in the last 24 hours, the maximum is 9.\n"
                                       f"You can not sell a vehicle without hitting the daily sell limit, {epochFormatted}."),
                                   color=discord.Color.red())
        cannotSell.set_footer(text="Created by hzh.")
        await ctx.edit(embed=cannotSell)

    elif len(sales) > 2 or len(allSales) > 9:
        cannotSell = discord.Embed(title="DSL",
                                   description=(
                                       f"SALES LAST 24 HOURS:\n**{formattedAllSales}**\n\n"
                                       f"You have sold **{len(sales)}** vehicles in the last 2 hours, the maximum is 2.\n"
                                       f"You have sold **{len(allSales)}** vehicles in the last 24 hours, the maximum is 9.\n"
                                       f"DO NOT SELL ANOTHER VEHICLE! CHECK OUT [Detailed Guide About DSL]({DSLDOCS})"),
                                   color=discord.Color.red())
        cannotSell.set_footer(text="Created by hzh.")
        await ctx.edit(embed=cannotSell)

    else:
        canSell = discord.Embed(title="DSL",
                                   description=(
                                       f"SALES LAST 24 HOURS:\n**{formattedAllSales}**\n\n"
                                        "You can sell a vehicle without hitting the daily sell limit."
                                       f" You have sold **{len(sales)}** vehicles in the last 2 hours, the maximum is 2."
                                       f" You have sold **{len(allSales)}** vehicles in the last 24 hours, the maximum is 9."),
                                   color=discord.Color.green())
        canSell.set_footer(text="Created by hzh.")
        await ctx.edit(embed=canSell)

@bot.slash_command(description="Remove an accidental sale you documented using the bot.")
async def remove(ctx) -> None:
    await ctx.respond(embed=fetching)

    username = str(ctx.author)
    allSales = await Db.fetchData(username, fetchAll=True)
    formattedAllSales = "\n".join([f"{rowid}. Username: {usernameObtained}, Timestamp: {timestamp}" for rowid, usernameObtained, timestamp in allSales])
    rowids = [rowid for rowid, _, _ in allSales]
    saleCount = len(allSales)

    if saleCount == 0:
        await ctx.edit(embed=noSales)
    
    else:  
        timeout_seconds = 300
        salesFound = discord.Embed(title="Sales found",
                           description=f"Send the number here in this channel representing your sale to remove it from the database. Send 'NONE' to exit, message times out in {timeout_seconds / 60} minutes.\n\n**{formattedAllSales}**",
                           color=discord.Color.blue())
        salesFound.set_footer(text="Created by hzh.")
        
        await ctx.edit(embed=salesFound)

        def check(message, ctx):
            if message.author == ctx.author and message.channel == ctx.channel:
                return (message.content and message.content != "0" and (message.content == "NONE" or message.content.isdigit()))
        
        try:
            message = await bot.wait_for('message', check=lambda message: check(message, ctx), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            await ctx.edit(embed=timedOut)
            return
        
        try:
            await message.delete()
        except:
            pass
        
        if message.content == "NONE":
            await ctx.delete()

        else:
            rowid = int(message.content)
            if rowid in rowids:
                await Db.removeData(username, rowid)

                removed = discord.Embed(title="Removed successfully",
                                        description=f"Deleted sale number **{rowid}** from the database.",
                                        color=discord.Color.green())
                removed.set_footer(text="Created by hzh.")
                await ctx.edit(embed=removed)
            
            else:
                removedError = discord.Embed(title="Error",
                                        description=f"Sale number **{rowid}** does not exist in the database.",
                                        color=discord.Color.red())
                removedError.set_footer(text="Created by hzh.")
                await ctx.edit(embed=removedError)
        
bot.run(str(os.getenv("TOKEN")))
