import praw
import prawcore
import sys
import time
import random
from tinydb import TinyDB, Query
from datetime import datetime, date, timedelta
from dateutil import relativedelta
from Round import Round


# PRAW instance
reddit = praw.Reddit('SentimentBot')

# TinyDB Querry object
find_stuff = Query()

# Automated message footer
message_footer = "\n\n**This is an automated message**" +\
				"\n\n-----\n\n[View the rules here](https://github.com/disasterpiece9000/Tag)" +\
				" | [How to opt-in](https://www.reddit.com/user/shimmyjimmy97/comments/alt7e8/how_to_optin_to_tag/)" +\
				" | [Contact the dev](https://www.reddit.com/message/compose/?to=shimmyjimmy97)"


class Game:
	def __init__(game):
		# Get opted-in user list
		game.opt_in_DB = TinyDB("opt-in.json")
		game.opt_in_users = game.readOptIn()

		# Initial Master and Puppet
		first_master = reddit.redditor('olderkj')
		#first_master = game.getRandomUser('master')
		#first_puppet = reddit.redditor('AccursedShade')
		first_puppet = game.getRandomUser('puppet')

		# Check that a user wasn't selected for both roles
		while first_master == first_puppet:
			first_puppet = game.getRandomUser('puppet')

		# Create initial Round object
		game.current_round = Round(game, first_master, first_puppet)

	# Get a random user that is not the bot
	def getRandomUser(game, role):
		random_user = random.choice(game.opt_in_users)
		while random_user == 'shimmyjimmy97':
			random_user = random.choice(game.opt_in_users)

		return reddit.redditor(random_user)

	# Read db and add users to list
	def readOptIn(game):
		hold_opt_in = []
		for username in game.opt_in_DB:
			hold_opt_in.append(username['username'])
		print("Read " + str(len(hold_opt_in)) + " users from opt-in")
		return hold_opt_in

	# Handle user opt-in
	def addOptIn(game, username):
		game.opt_in_users.append(username)
		game.opt_in_DB.insert({'username': username})

	# Remove a user from the opt-in list
	def optOut(game, username):
		print("User has opted-out: " + username)

		try:
			game.opt_in_users.remove(username)
		except ValueError:
			print("User is not in opt-in list")
			return

		game.opt_in_DB.remove(find_stuff.username == username)

	# Check inbox for messages to process
	def readPMs(game):
		messages = reddit.inbox.unread()

		for message in messages:
			# Message from Master or Puppet
			if message.body.startswith('!'):
				message_words = message.body.split()
				command = message_words[0]
				author = str(message.author)
				print('User: ' + author + '\tCommand: ' + command)

				# Puppet/Master specific commands
				if message.author == game.current_round.puppet or message.author == game.current_round.master:
					if command.lower() == '!setphrase' and message.author == game.current_round.master:
						# Check if the phrase has already been place
						if game.current_round.phrase != None:
							game.current_round.master.message(
								'Phrase rejected', 'The phrase has already been set for this round.\n\nPhrase: ' + game.current_round.phrase +
								message_footer)
							message.mark_read()
							print('Phrase rejected: Phrase already set')
							continue

						# Check if the phrase is too long
						elif len(message_words) > 4:
							game.current_round.master.message('Phrase rejected', 'The phrase is longer than 3 words.\n\nPhrase: ' + game.current_round.phrase +
												'\n\nNumber of words: ' + str(len(message_words - 1)) +
												message_footer)

							message.mark_read()
							print('Phrase rejected: Phrase to long\nPhrase: ' + message.body[11:])
							continue
						# Check if the phrase contains a user mention
						elif ("u/" in message.body):
							game.current_round.master.message("Phrase rejected", "The phrase cannot contain a user mention.\n\n" +
												"Phrase: " + game.current_round.phrase +
												message_footer)

						# Check that both Master and Puppet have accepted their roles
						elif game.current_round.master_accepted and game.current_round.puppet_accepted:
							game.current_round.setPhrase(message.body[11:])
							message.mark_read()
							print('Phrase accepted\nPhrase: ' + message.body[11:])
							continue
					# Accept role
					if command.lower() == '!accept':
						game.current_round.acceptRole(message.author)
						message.mark_read()
						continue
					# Reject role
					if command.lower() == '!reject':
						game.current_round.rejectRole(message.author)
						message.mark_read()
						continue

				elif str(message.author) in opt_in_users:
					if command == "!opt-out":
						game.optOut(str(message.author))
						message.reply("Opt-out", "You have opted-out of Tag. If you wish to opt-in later, just leave a " +
									  "comment with '!you're it' in it and you will automatically opt-in to the round again." +
									  message_footer)

				print('\n')