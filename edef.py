import praw
import prawcore
import sys
import time
import random
from tinydb import TinyDB, Query
from datetime import datetime, date, timedelta
from dateutil import relativedelta

# PRAW instance
reddit = praw.Reddit('SentimentBot')
# TinyDB Querry object
find_stuff = Query()
opt_in_DB = TinyDB("opt-in")
# List of users who have opted-in
opt_in_users = []

# Automated message footer
message_footer = "\n\n**This is an automated message**" +\
				"\n\n-----\n\n[View the rules here](https://github.com/disasterpiece9000/Tag)" +\
				" | [How to opt-in](https://www.reddit.com/user/shimmyjimmy97/comments/alt7e8/how_to_optin_to_tag/)" +\
				" | [Contact the dev](https://www.reddit.com/message/compose/?to=shimmyjimmy97)"

# Read db and add users to list
def readOptIn():
	opt_in_users.clear()
	for username in opt_in_DB:
		opt_in_users.append(username['username'])
	print("Read " + str(len(opt_in_users)) + " users from opt-in")

# Get a random user that is not the bot
def getRandomUser(role):
	random_user = random.choice(opt_in_users)
	while random_user == 'shimmyjimmy97':
		random_user = random.choice(opt_in_users)

	return reddit.redditor(random_user)

# Handle user opt-in
def addOptIn(username):
	opt_in_users.append(username)
	opt_in_DB.insert({'username': username})

# Message all users
def notifyUsers(subj, body):
	for username in opt_in_users:
		user = reddit.redditor(username)
		user.message(subj, body)

# Remove a user from the opt-in list
def optOut(username):
	print("User has opted-out: " + username)
	try:
		opt_in_users.remove(username)
	except ValueError:
		print("User is not in opt-in list")
		return

	opt_in_DB.remove(find_stuff.username == username)

# Game object
class Game:
	def __init__(game, master, puppet):
		# Set users and offer roles
		game.master = master
		game.puppet = puppet
		game.offerRole(master)
		game.master_accepted = False
		game.offerRole(puppet)
		game.puppet_accepted = False
		# Day the two users were offered their role
		game.day_initialized = datetime.now()
		# One guess per user per round
		game.used_guess = []
		# Store location of phrase
		game.target_comment = None
		game.phrase_permalink = None
		# Store the user who tagged the phrase
		game.tagger = None

		print('Master: ' + str(master) + '\tPuppet: ' + str(puppet) + '\n')

		# Master's phrase
		game.phrase = None
		# Phrase has been set and delivered to both users
		game.active = False
		# Phrase has been successfully used by the Puppet
		game.phrase_placed = False
		# Phrase has been identified by another user
		game.phrase_identified = False
		# User who won the round
		game.victor = None

	# Notify the user that they have been selected
	def offerRole(game, user):
		# Reset the timer everytime a new user is offered a role
		game.day_initialized = datetime.now()

		if user == game.master:
			user.message('Would you like to play a game?',
			'You have been randomly selected to play the role of Master in this round of Tag. ' +
			'To accept this invitation, reply to this message with !accept. To reject this invitation, ' +
			'reply with !reject. If no response is recieved within 24 hours, another user will be selected.' +
			message_footer)

		if user == game.puppet:
			user.message('Would you like to play a game?',
			'You have been randomly selected to play the role of Puppet in this round of Tag. ' +
			'To accept this invitation, reply to this message with !accept. To reject this invitation, ' +
			'reply with !reject. If no response is recieved within 24 hours, another user will be selected. '+
			message_footer)

	# Respond to the accepted role and inform the user of the next stage of the game
	def acceptRole(game, user):
		if user == game.master and game.master_accepted == False:
			game.master_accepted = True

			game.master.message(
				'Role accepted: Master', 'You will recieve a message asking for a phrase once the Puppet has also accepted their role.' +
				message_footer)

			print('User: ' + str(user) + '\nAccepted Role: Master')
		elif user == game.puppet and game.puppet_accepted == False:
			game.puppet_accepted = True

			game.puppet.message(
				'Role accepted: Puppet', 'You will recieve a message informing you of the phrase once the Master has accepted their ' +
				'role and set a phrase.' +
				message_footer)

			print('User accepted role: ' + str(user))

		# If both users have accepted then the master is asked to provide the phrase
		if game.puppet_accepted == True and game.master_accepted == True:
			game.master.message('Please set the phrase for the game to begin', 'Reply to this PM with !setphrase as the first text in the body, ' +
			'followed by the word or phrase of your choice. The phrase can be no longer than 3 words and it cannot contain any user mentions. ' +
			'You will recieve a confirmation message once it has been successfully set.' +
			message_footer)

	# Find a new user to fill the role
	def rejectRole(game, user):
		print('User: ' + str(user) + '\nRejected Role: Puppet')

		if user == game.master and game.master_accepted == False:
			hold_master = getRandomUser('master')

			while str(hold_master) == str(game.puppet):
				hold_master = getRandomUser('master')

			game.master = hold_master
			game.offerRole(game.master)

			print('User: ' + str(user) + '\nRejected Role: Master')

		if user == game.puppet and game.puppet_accepted == False:
			hold_puppet = getRandomUser('puppet')

			while str(hold_puppet) == str(game.master):
				hold_puppet = getRandomUser('puppet')

			game.puppet = hold_puppet
			game.offerRole(game.puppet)

			print('User rejected role: ' + str(user))

	# Notify all users about the results of the round and initalize the next round
	def endGame(game, winner):
		print('Winner: ' + str(game.master) + '\tRole: ' + winner)
		hold_master = None
		hold_puppet = None

		# If the phrase was never set change it to display that info
		if game.phrase == None:
			game.phrase = "Phrase not placed"
		else:
			game.phrase = '[' + game.phrase + '](' + game.phrase_permalink + ')'

		if winner == 'master':
			game.master.message('You win!', 'Congrats! You are victorious and will remain the Master for another round' +
								message_footer)
			game.puppet.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo' +
								message_footer)

			# Submit end-of-round report
			mess_subj = str(game.master) + ' has won this round as Master'
			mess_body = 'Phrase: ' + game.phrase + '\n\nPuppet: ' + str(game.puppet) + '\n\n' +\
						'\n\nThe Master will remain as the Master for the next round. A new Puppet will be selected now.' +\
						message_footer
			notifyUsers(mess_subj, mess_body)

			# If the Master wins, they remian the master and a new Puppet is selected
			hold_master = game.master
			hold_puppet = getRandomUser('puppet')

			while str(hold_puppet) == str(hold_master):
				hold_puppet = getRandomUser('puppet')

		if winner == 'puppet':
			game.puppet.message('You win!', 'Congrats! You are victorious and will become the Master for the next round' +
								message_footer)
			game.master.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo' +
								message_footer)

			# Submit end-of-round report
			mess_subj = str(game.puppet) + ' has won this round as Puppet'
			mess_body = ("Phrase: " + game.phrase + "\n\nMaster: " + str(game.master) +
						 '\n\nThe Puppet will become the Master for the next round. A new Puppet will be selected now.' +
						 message_footer)
			notifyUsers(mess_subj, mess_body)

			# If the Puppet wins, they become the Master for the next round and a new Puppet is selected
			hold_master = game.puppet
			hold_puppet = getRandomUser('puppet')

			while str(hold_puppet) == str(hold_master):
				hold_puppet = getRandomUser('puppet')

		return Game(hold_master, hold_puppet)

	# Set the phrase provided by the Master and notify users about the next stage of the game
	def setPhrase(game, phrase):
		game.phrase = phrase
		# The time the phrase was set
		game.start_time = datetime.now()
		# The time the game will end (24hrs after the start time)
		game.end_time = game.start_time + timedelta(days=1)
		game.active = True

		print('Phrase: ' + phrase)

		game.master.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nThis phrase was accepted. The Puppet has been ' +
							'notified and the clock is now ticking. If the comment is not identified in 24 hours, then they will win.' +
							'The Puppet must leave the phrase under a post that was created 3 hours before the round started or later\n\n' +
							'Posts created after ' + (game.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
							'\n\nEnd time: ' + game.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
							message_footer)

		game.puppet.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nThis phrase was accepted. The Master has been ' +
							'notified and the clock is now ticking. If the comment is not identified in 24 hours, then you will win.' +
							'You must leave the phrase under a post that was created 3 hours before the round started or later\n\n' +
							'Posts created after ' + (game.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
							'\n\nEnd time: ' + game.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
							message_footer)

		# Notify other users about the active game
		mess_subj = 'A new game has started!'
		mess_body = ('The phrase has been set and the Puppet must now place it somewhere in the subreddit in the next 24 hours. ' +
					'After it is placed, you all will have another 24 hours to find it. Once the game is over another PM ' +
					'will be sent with details of the round.' +
					'The Puppet must leave the phrase under a post that was created 3 hours before the round started or later\n\n' +
					'Posts created after ' + (game.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
					'\n\nEnd time: ' + game.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
					message_footer)

		notifyUsers(mess_subj, mess_body)

	# Resolve "!you're it" comments
	def handleTag(game, comment):
		# If the user placed a guess and isn't opted-in then add them to opt-in
		if str(comment.author) not in opt_in_users:
			addOptIn(str(comment.author))
			comment.reply("You have just opted-in to Tag. If you would like to opt-out then send /u/shimmyjimmy a PM with !opt-out as the body." +
						message_footer)

			print("User has opted-in: " + str(comment.author))

		# If user has already guessed this round, then always return incorrect guess
		if comment.author in game.used_guess:
			comment.reply("Not so fast. You have already tagged another user this round. Please wait until next round to try again!" +
						message_footer)

			print("User has already guessed this round: " + str(comment.author))

		# If user is the master or the puppet, then always return incorrect guess
		elif comment.author == game.master or comment.author == game.puppet:
			comment.reply("Not it. This comment does not contain the phrase" +
						message_footer)

			game.used_guess.append(comment.author)
			print("User is Puppet or Master: " + str(comment.author))

		# If the phrase hasn't been placed yet, then always return incorrect guess
		elif game.phrase_placed == False:
			comment.reply("Not it. This comment does not contain the phrase" +
						message_footer)

			game.used_guess.append(comment.author)
			print("User guessed before phrase was placed: " + str(comment.author))

		# If the phrase is placed, check if it was left under the Puppet's comment
		elif game.phrase_placed == True:
			# Correct guess: The Master wins the round
			if game.target_comment == comment.parent_id[3:]:
				comment.reply("They're it! The next game shall being in 3...2...1...\n\n    COMMENCE START UP SEQUENCE" +
							message_footer)

				print("User guessed correctly:" + str(comment.author))
				game = game.endGame('master')
			# Incorrect guess
			else:
				comment.reply("Not it. This comment does not contain the phrase" +
							message_footer)

				game.used_guess.append(comment.author)
				print("User guessed incorrectly: " + str(comment.author))

		print('\n')

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
			if message.author == game.puppet or message.author == game.master:
				if command.lower() == '!setphrase' and message.author == game.master:
					# Check if the phrase has already been place
					if game.phrase != None:
						game.master.message(
							'Phrase rejected', 'The phrase has already been set for this game.\n\nPhrase: ' + game.phrase +
							message_footer)
						message.mark_read()
						print('Phrase rejected: Phrase already set')
						continue

					# Check if the phrase is too long
					elif len(message_words) > 4:
						game.master.message('Phrase rejected', 'The phrase is longer than 3 words.\n\nPhrase: ' + game.phrase +
											'\n\nNumber of words: ' + str(len(message_words - 1)) +
											message_footer)

						message.mark_read()
						print('Phrase rejected: Phrase to long\nPhrase: ' + message.body[11:])
						continue
					# Check if the phrase contains a user mention
					elif ("u/" in message.body):
						game.master.message("Phrase rejected", "The phrase cannot contain a user mention.\n\n" +
											"Phrase: " + game.phrase +
											message_footer)

					# Check that both Master and Puppet have accepted their roles
					elif game.master_accepted and game.puppet_accepted:
						game.setPhrase(message.body[11:])
						message.mark_read()
						print('Phrase accepted\nPhrase: ' + message.body[11:])
						continue
				# Accept role
				if command.lower() == '!accept':
					game.acceptRole(message.author)
					message.mark_read()
					continue
				# Reject role
				if command.lower() == '!reject':
					game.rejectRole(message.author)
					message.mark_read()
					continue

			elif str(message.author) in opt_in_users:
				if command == "!opt-out":
					optOut(str(message.author))
					message.reply("Opt-out", "You have opted-out of Tag. If you wish to opt-in later, just leave a " +
								  "comment with '!you're it' in it and you will automatically opt-in to the game again." +
								  message_footer)

			print('\n')

readOptIn()
# Initial Master and Puppet
first_master = reddit.redditor('olderkj')
#first_master = getRandomUser('master')
first_puppet = reddit.redditor('CaelestisInteritum')
#first_puppet = getRandomUser('puppet')

# Check that a user wasn't selected for both roles
while first_master == first_puppet:
	first_puppet = getRandomUser('puppet')

# Create initial Game object
game = Game(first_master, first_puppet)

# Main method
while True:
	# Catch disconnect errors
	try:
		# Stream of comments from target subreddit
		for comment in reddit.subreddit('edefinition').stream.comments(skip_existing=True, pause_after=1):

			# If there are no new comments, check PMs
			if comment == None:
				readPMs(game)
				continue

			# Check for user opt-in
			if ("!you're it" in comment.body or "!you’re it" in comment.body or "!youre it" in comment.body):
				game.handleTag(comment)

			# Check if game has been inactive for < 24hrs
			if game.active == False:
				if (datetime.now() - game.day_initialized).days >= 1:
					# Select a new user if the role has not been accepted
					if game.puppet_accepted == False:
						game.puppet = getRandomUser('puppet')
						game.offerRole(game.puppet)
					if game.master_accepted == False:
						game.master = getRandomUser('master')
						game.offerRole(game.master)

			# Both users have accepted their roles and the phrase is set
			if game.active == True:

				# The Puppet has not used the phrase
				if game.phrase_placed == False:

					# End the game if the Puppet has not used the phrase in 24hrs
					if (game.end_time - datetime.now()).days < 0:
						print('Times up')
						game = game.endGame('master')

					# Check if comment is from the Puppet
					elif str(comment.author).lower() == str(game.puppet).lower():
						print('Comment from puppet')

						# Check if the phrase is in the comment
						if game.phrase.lower() in comment.body.lower():
							print("Phrase in comment")
							post = comment.submission
							post_time = post.created_utc
							post_time = datetime.fromtimestamp(post_time)

							# Check if the comment is under a post that was made after the game started
							if (game.start_time - timedelta(hours=3)) < post_time:
								print('Phrase found')
								game.phrase_placed = True
								game.end_time = datetime.now() + timedelta(days=1)

								# Notify the Master and Puppet that the comment was identified by the bot
								game.target_comment = comment.id
								game.phrase_permalink = comment.permalink
								game.tagger = str(comment.author)


								game.puppet.message(
									'Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body +
									"\n\nIf another user doesn't tag the comment within the next 24hrs then you win." +
									"\n\nEnd Time: " + game.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
									message_footer)
								game.master.message(
									'Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body +
									"\n\nIf another user tags the comment within the next 24hrs then you win." +
									"\n\nEnd Time: " + game.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
									message_footer)

							else:
								print("Comment found under old post and was not accpeted")
								game.puppet.message(
									"Phrase not accepted", "You must leave the phrase under a post that was created 3 hours before" +
									"the round started or later.\n\nPosts created after " +
									(game.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
									message_footer)

				# The Puppet has used the phrase
				if game.phrase_placed == True:

					# If the game is past the end time, then the Puppet wins the round
					if datetime.now() > game.end_time:
						game = game.endGame('puppet')

	except (prawcore.exceptions.ResponseException):
		print('Error connecting to servers. Sleeping for 1 min')
		time.sleep(60)
