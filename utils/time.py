from discord.ext import commands
from zoneinfo import ZoneInfo
import datetime
from .ids import TournamentReminders

#checks if the timezone is currently in dst. we operate out of the eastern us
def is_dst(tz: str = "US/Eastern"):
    dt = datetime.datetime.now(ZoneInfo(tz))
    return dt.dst() != datetime.timedelta(0)

#if the timezone is in dst, subtracts one hour to get the "normal" timezone
#i have to do this, since datetime.time wont work with DST? at least it really sucks and this is the only solution i came up with
def get_dst_adjusted_time(dtime: datetime.time, dst: bool):
    if not dst:
        return dtime
    else:
        return dtime.replace(hour=dtime.hour - 1)

#these are here to save on imports. returns the (hopefully) right value as a UTC time.
class TournamentTimes:
    smash_overseas = get_dst_adjusted_time(datetime.time(TournamentReminders.SMASH_OVERSEAS_HOUR, TournamentReminders.SMASH_OVERSEAS_MINUTE, 0, 0), is_dst())
    trials_of_smash = get_dst_adjusted_time(datetime.time(TournamentReminders.TRIALS_OF_SMASH_HOUR, TournamentReminders.SMASH_OVERSEAS_MINUTE, 0, 0), is_dst())


#this here converts the input time into the raw seconds, plus a nice string for the user to make sense of
def convert_time(input_time:str):
    total_seconds = 0
    readable_time = ""

    current_position = 0
    for char in input_time:
        #basically searches for the key letters d/h/m/s and gets the input right before them. the order does not matter
        #so if you type in complicated querys like 1h20m it adds them up, instead of the user having to type 80m like they did with the previous method using endswith
        #if a non-int gets input, the CommandInvokeError below will get triggered. we also trigger this error here on other undesired inputs, like negative numbers.
        if char == "d":
            #only gets the input before the d
            days = input_time.split("d")[0][-current_position:]
            total_seconds += int(days) * 60 * 60 * 24
            #dont want negative numbers, just raising the error that also gets raised on a BadConversion
            if int(days) < 0:
                raise commands.CommandInvokeError
            #ignores zeroes in the returning string. if you input 0d20h it wont display the days in the string
            if int(days) > 0:
                if readable_time == "":
                    #checks if its just one or multiple for proper wording
                    if int(days) == 1:
                        #str(int(days)) looks stupid but it gets rid of leading zeroes. 00001d -> 1d
                        readable_time = f"{str(int(days))} day"
                    else:
                        readable_time = f"{str(int(days))} days"
                else:
                    if int(days) == 1:
                        readable_time = readable_time + f", {str(int(days))} day"
                    else:
                        readable_time = readable_time + f", {str(int(days))} days"
            #resets the counter for the other inputs
            current_position = 0

        #its the same for every other type
        elif char == "h":
            hours = input_time.split("h")[0][-current_position:]
            total_seconds += int(hours) * 60 * 60
            if int(hours) < 0:
                raise commands.CommandInvokeError
            if int(hours) > 0:
                if readable_time == "":
                    if int(hours) == 1:
                        readable_time = f"{str(int(hours))} hour"
                    else:
                        readable_time = f"{str(int(hours))} hours"
                else:
                    if int(hours) == 1:
                        readable_time = readable_time + f", {str(int(hours))} hour"
                    else:
                        readable_time = readable_time + f", {str(int(hours))} hours"
            current_position = 0

        elif char == "m":
            mins = input_time.split("m")[0][-current_position:]
            total_seconds += int(mins) * 60
            if int(mins) < 0:
                raise commands.CommandInvokeError
            if int(mins) > 0:
                if readable_time == "":
                    if int(mins) == 1:
                        readable_time = f"{str(int(mins))} minute"
                    else:
                        readable_time = f"{str(int(mins))} minutes"
                else:
                    if int(mins) == 1:
                        readable_time = readable_time + f", {str(int(mins))} minute"
                    else:
                        readable_time = readable_time + f", {str(int(mins))} minutes"
            current_position = 0

        elif char == "s":
            secs = input_time.split("s")[0][-current_position:]
            total_seconds += int(secs)
            if int(secs) < 0:
                raise commands.CommandInvokeError
            if int(secs) > 0:
                if readable_time == "":
                    if int(secs) == 1:
                        readable_time = f"{str(int(secs))} second"
                    else:
                        readable_time = f"{str(int(secs))} seconds"
                else:
                    if int(secs) == 1:
                        readable_time = readable_time + f", {str(int(secs))} second"
                    else:
                        readable_time = readable_time + f", {str(int(secs))} seconds"
            current_position = 0
        
        else:
            current_position += 1

    #if the last char in the string is not either d/h/m/s we will just throw an error. eg: good input: 1h49m, bad input: 1h20
    if current_position != 0:
        raise commands.CommandInvokeError

    return total_seconds, readable_time