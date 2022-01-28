import discord
from discord.ext import commands, tasks
from mee6_py_api import API
from discord.utils import get
from math import ceil
from utils.ids import GuildNames, GuildIDs, TGLevelRoleIDs
import utils.logger

#
#this file here gets the mee6 level and assigns the matching role
#

#this is purposefully not made into GuildIDs.TRAINING_GROUNDS.
#even in testing i want the TG leaderboard, not the leaderboard of my testing server. change it if you want to.
mee6API = API(739299507795132486)

class Mee6api(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.update_roles.start()


    def cog_unload(self):
        self.update_roles.cancel()


    #command if someone wants to do it manually
    @commands.command(aliases=["updatelvl", "updaterank"], cooldown_after_parsing=True)
    @commands.guild_only() #cant be used in dms
    @commands.cooldown(1, 300, commands.BucketType.user) #1 use, 5m cooldown, per user. since the response time of the api isnt too great, i wanted to limit these requests
    async def updatelevel(self, ctx, member: discord.Member = None):
        if ctx.guild.id != GuildIDs.TRAINING_GROUNDS:
            await ctx.send(f"This command can only be used in the {GuildNames.TRAINING_GROUNDS} Discord Server.")
            ctx.command.reset_cooldown(ctx)
            return

        if member is None:
            member = ctx.author

        if member.bot:
            await ctx.send("Please do not use this command on bots.")
            ctx.command.reset_cooldown(ctx)
            return

        botmessage = await ctx.send("Please wait a few seconds...") #again, api is sometimes very slow so we send this message out first

        userlevel = await mee6API.levels.get_user_level(member.id, dont_use_cache=True) #gets the level

        defaultrole = get(ctx.guild.roles, id=TGLevelRoleIDs.RECRUIT_ROLE)
        level10 = get(ctx.guild.roles, id=TGLevelRoleIDs.LEVEL_10_ROLE)
        level25 = get(ctx.guild.roles, id=TGLevelRoleIDs.LEVEL_25_ROLE)
        level50 = get(ctx.guild.roles, id=TGLevelRoleIDs.LEVEL_50_ROLE)
        level75 = get(ctx.guild.roles, id=TGLevelRoleIDs.LEVEL_75_ROLE)

        levelroles = [defaultrole, level10, level25, level50, level75]

        rolegiven = None
        
        if userlevel > 9 and userlevel < 25:
            if level10 not in member.roles:
                for role in levelroles:
                    if role in member.roles:
                        await member.remove_roles(role)
                await member.add_roles(level10)
                rolegiven = level10
        
        elif userlevel > 24 and userlevel < 50:
            if level25 not in member.roles:
                for role in levelroles:
                    if role in member.roles:
                        await member.remove_roles(role)
                await member.add_roles(level25)
                rolegiven = level25
            
        elif userlevel > 49 and userlevel < 75:
            if level50 not in member.roles:
                for role in levelroles:
                    if role in member.roles:
                        await member.remove_roles(role)
                await member.add_roles(level50)
                rolegiven = level50

        elif userlevel > 74:
            if level75 not in member.roles:
                for role in levelroles:
                    if role in member.roles:
                        await member.remove_roles(role)
                await member.add_roles(level75)
                rolegiven = level75


        if rolegiven is None:
            await botmessage.edit(content=f"{member.mention}, you are Level {userlevel}, so no new role for you.")
        else:
            await botmessage.edit(content=f"{member.mention}, you are Level {userlevel}, and thus I have given you the {rolegiven} role.")


    #generic error message
    @updatelevel.error
    async def updatelevel_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"{ctx.author.mention}, you are on cooldown for another {round((error.retry_after)/60)} minutes to use this command.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"This command can only be used in the {GuildNames.TRAINING_GROUNDS} Discord Server.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("Please mention a valid member, or leave it blank.")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("Something went wrong! Either the API is down or the user was not in the leaderboard yet. Please try again later.")
        else:
            raise error



    #task that assigns roles automatically
    @tasks.loop(hours=23) #have set it to 23 hours so that it doesnt overlap often with the warnloop daily task, but doesnt matter that much
    async def update_roles(self):
        #pretty much the same command as above, just with different names so that it works for everyone in the server and also in a background task

        logger = utils.logger.get_logger("bot.level")
        logger.info("Starting to update level roles...")

        guild = self.bot.get_guild(GuildIDs.TRAINING_GROUNDS)

        defaultrole = get(guild.roles, id=TGLevelRoleIDs.RECRUIT_ROLE)
        level10 = get(guild.roles, id=TGLevelRoleIDs.LEVEL_10_ROLE)
        level25 = get(guild.roles, id=TGLevelRoleIDs.LEVEL_25_ROLE)
        level50 = get(guild.roles, id=TGLevelRoleIDs.LEVEL_50_ROLE)
        level75 = get(guild.roles, id=TGLevelRoleIDs.LEVEL_75_ROLE)

        levelroles = [defaultrole, level10, level25, level50, level75]

        pageNumber = ceil(len(guild.members)/100) #gets the correct amount of pages
        for i in range(pageNumber):
            leaderboard_page = await mee6API.levels.get_leaderboard_page(i)
            for user in leaderboard_page["players"]:
                if int(user["id"]) in [guildMember.id for guildMember in guild.members]: #checks if the user is still in the guild
        
                    #need to fetch the member, since get_member is unreliable.
                    #even with member intents it kind of fails sometimes since not all members are cached
                    #this fetching step can take some time depending on guild size
                    #we also just can remove all level roles since this code only triggers if you rank up. after that add the new role
                    if user["level"] > 9 and user["level"] < 25:
                        member = await guild.fetch_member(user["id"])
                        if level10 not in member.roles:
                            for role in levelroles:
                                if role in member.roles:
                                    await member.remove_roles(role)
                            await member.add_roles(level10)
                    
                    elif user["level"] > 24 and user["level"] < 50:
                        member = await guild.fetch_member(user["id"])
                        if level25 not in member.roles:
                            for role in levelroles:
                                if role in member.roles:
                                    await member.remove_roles(role)
                            await member.add_roles(level25)
                        
                    elif user["level"] > 49 and user["level"] < 75:
                        member = await guild.fetch_member(user["id"])
                        if level50 not in member.roles:
                            for role in levelroles:
                                if role in member.roles:
                                    await member.remove_roles(role)
                            await member.add_roles(level50)
                    
                    elif user["level"] > 74:
                        member = await guild.fetch_member(user["id"])
                        if level75 not in member.roles:
                            for role in levelroles:
                                if role in member.roles:
                                    await member.remove_roles(role)
                            await member.add_roles(level75)
        
        logger.info("Successfully updated level roles!")


    @update_roles.before_loop
    async def before_update_roles(self):
        await self.bot.wait_until_ready()




def setup(bot):
    bot.add_cog(Mee6api(bot))
    print("Mee6api cog loaded")