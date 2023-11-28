import discord
from discord.ext import commands, tasks
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
submissions = {}  # Global dictionary to store submission information
imgUrl = {} #store image link
winnerUrl = None

bot = commands.Bot(command_prefix='!', intents=intents)

# Replace these with your channel IDs
submission_channel_id = 1178822639570124810
voting_channel_id = 1178822946886787072

# Global variable to track whether voting has ended
voting_ended = True


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
@bot.event
async def on_reaction_add(reaction, user):
    if user != bot.user and reaction.message.channel.id == voting_channel_id and str(reaction.emoji) == '👍':
        # Assuming only upvotes are counted
        vote_count = reaction.count
        print(f"Submission {reaction.message.id} received an upvote. Total votes: {vote_count}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == submission_channel_id and message.attachments:
        voting_channel = bot.get_channel(voting_channel_id)

        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                sent_message = await voting_channel.send(attachment.url)
                await sent_message.add_reaction('👍')
                #await sent_message.add_reaction('👎')
                submissions[sent_message.id] = message.author.id
                imgUrl[sent_message.id] = attachment.url

        # Delete the original message from the submission channel
        await message.delete()
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def start_voting(ctx):
    global voting_ended
    voting_ended = False
    await ctx.send("Voting has started!")

@bot.command()
@commands.has_permissions(administrator=True)  # Ensure only admins can use this command
async def end_voting(ctx):
    await count_votes()
    await ctx.send("Voting has ended and the winner has been announced.")

# Function to count votes
async def count_votes():
    global voting_ended
    if voting_ended:
        return

    voting_channel = bot.get_channel(voting_channel_id)
    winner = None
    max_votes = 0
    winning_user_id = None

    # Iterate over each submission in the submissions dictionary
    for message_id, user_id in submissions.items():
        try:
            # Fetch the message from the voting channel
            message = await voting_channel.fetch_message(message_id)

            # Count votes if the reaction is '👍'
            votes = message.reactions[0].count if message.reactions and message.reactions[0].emoji == '👍' else 0
            await voting_channel.send(f"Counting votes for submission {message.id}: {votes} votes")

            # Check if this submission has the highest votes so far
            if votes > max_votes:
                max_votes = votes
                winner = message
                winning_user_id = user_id
                winnerUrl = imgUrl[message.id] 
        except discord.NotFound:
            # The message was not found, which can happen if it was deleted
            continue

    # Announce the winner
    if winner and winning_user_id:
        winning_user = await bot.fetch_user(winning_user_id)
        await voting_channel.send(f"The winning submission is  {winning_user.mention} with {max_votes} votes!")
        await voting_channel.send(winnerUrl)
        #for attachment in winner.attachments:
        #    await voting_channel.send(f"The winning submission is {attachment.url} by {winning_user.mention} with {max_votes} votes!")
    else:
        await voting_channel.send("No submissions or votes this time.")

    voting_ended = True


# Run the bot with the token from an environment variable
bot_token = os.getenv('DISCORD_BOT_TOKEN')
bot.run(bot_token)
