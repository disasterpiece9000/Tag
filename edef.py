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
# List of users who have opted-in
opt_in_users = []

# Read db and add users to list
def readOptIn():
	opt_in_users = []
	opt_in_DB = TinyDB("opt-in")
	for username in opt_in_DB:
		opt_in_users.append(username['username'])

# Get a random user that is not the bot
def getRandomUser(role):
	random_user = random.choice(opt_in_users)
	while random_user.name == 'shimmyjimmy97':
		random_user = random.choice(edef_users)

	return random_user

# Handle user opt-in
def addOptIn(username):
	opt_in_users.append(username)
	opt_in_DB.insert({'username': username})

# Message all users
def notifyUsers(subj, body):
	for username in opt_in_users:
		user = reddit.redditor(username)
		user.message(subj, body)

# Game object
class Game:
	def __init__(game, master, puppet):
		game.master = master
		game.puppet = puppet
		game.offerRole(master)
		game.master_accepted = False
		game.offerRole(puppet)
		game.puppet_accepted = False
		# Day the two users were offered their role
		game.day_initialized = datetime.now()

		print('Master: ' + str(master) + '\tPuppet: ' + str(puppet))

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
			user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Master in this round of Tag. ' +_
			'To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is ' +
			'recieved within 24 hours, another user will be selected. \n\n[View the rules here]' +
			'(https://www.reddit.com/r/edefinition/comments/9v31ym/would_you_like_to_play_a_game/)')

		if user == game.puppet:
			user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Puppet in this round of Tag. ' +
			'To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is ' +
			'recieved within 24 hours, another user will be selected. \n\n[View the rules here]' +
			'(https://www.reddit.com/r/edefinition/comments/9v31ym/would_you_like_to_play_a_game/)')

	# Respond to the accepted role and inform the user of the next stage of the game
	def acceptRole(game, user):
		if user == game.master and game.master_accepted == False:
			game.master_accepted = True
			game.master.message('Role accepted: Master', 'You will recieve a message asking for a phrase once the Puppet has also accepted their role.')
			print('User: ' + str(user) + '\nAccepted Role: Master')
		elif user == game.puppet and game.puppet_accepted == False:
			game.puppet_accepted = True
			game.puppet.message('Role accepted: Puppet', 'You will recieve a message informing you of the phrase once the Master has accepted their role and set a phrase')
			print('User: ' + str(user) + '\nAccepted Role: Master')

		# If both users have accepted then the master is asked to provide the phrase
		if game.puppet_accepted == True and game.master_accepted == True:
			game.master.message('Please set the phrase for the game to begin', 'Reply to this PM with !setphrase as the first text in the body, ' +
			'followed by the word or phrase of your choice. The phrase can be no longer than 3 words. You will recieve a confirmation message ' +
			'once it has been successfully set.')

	# Find a new user to fill the role
	def rejectRole(game, user):
		print('User: ' + str(user) + '\nRejected Role: Puppet')

		if user == game.master and game.master_accepted == False:
			hold_master = getRandomUser('master')

			while str(hold_puppet) == str(game.master):
				hold_puppet = getRandomUser('master')

			game.master = hold_master
			game.offerRole(game.master)

			print('User: ' + str(user) + '\nRejected Role: Master')

		if user == game.puppet and game.puppet_accepted == False:
			hold_puppet = getRandomUser('puppet')

			while str(hold_puppet) == str(game.master):
				hold_puppet = getRandomUser('puppet')

			game.puppet = hold_puppet
			game.offerRole(game.puppet)

			print('User: ' + str(user) + '\nRejected Role: Puppet')

	# Set the phrase provided by the Master and notify users about the next stage of the game
	def setPhrase(game, phrase):
		game.phrase = phrase
		# The time the phrase was set
		game.start_time = datetime.now()
		# The time the game will end (24hrs after the start time)
		game.end_time = game.start_time + timedelta(days=1)
		game.active = True

		print('Phrase: ' + phrase)

		game.master.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nThis phrase was accepted. The other user has been notified and the ' +
		'clock is now ticking. They have until ' + game.end_time.strftime("%c") + ' to leave their comment. If it is not identified in one week, then they will win.')

		game.puppet.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nYou have until ' + game.end_time.strftime("%c") + ' to leave a comment ' +
		'that contains this phrase. When the bot sees your comment, it will notify you that it has been identified. If another user does not identify the comment in a week, then you win.')

		# Notify other users about the active game
		mess_subj = 'A new game has started!'
		mess_body = 'The phrase has been set and the Puppet must now place it somewhere in the subreddit in the next 24 hours. ' +
		'After it is placed, you all will have 24 hours to find it. Once the game is over another post ' +
		'will be submitted with details of the round.'
		notifyUsers(mess_subj, mess_body)

	# Notify all users about the results of the round and initalize the next round
	def endGame(game, winner):
		print('Winner: ' + str(game.master) + '\tRole: ' + winner)
		hold_master = None
		hold_puppet = None

		if winner == 'master':
			game.master.message('You win!','Congrats! You are victorious and will remain as the Master for another round')
			game.puppet.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo')

			# If the phrase was never set change it to display that info
			if game.phrase == None:
				game.phrase = "Phrase not placed"

			# Submit end-of-round report
			mess_subj = str(game.master) + ' has won this round as Master'
			mess_body = 'Phrase: ' + game.phrase + '\n\nPuppet: ' + str(game.puppet) +
			'\n\nThe Master will remain as Master for the next round. A new Puppet will be selected now.'
			notifyUsers(mess_subj, mess_body)

			# If the Master wins, they remian the master and a new Puppet is selected
			hold_master = game.master
			hold_puppet = getRandomUser('puppet')

			while str(hold_puppet) == str(hold_master):
				hold_puppet = getRandomUser('puppet')

		if winner == 'puppet':
			game.puppet.message('You win!', 'Congrats! You are victorious and will become the Master for the next round')
			game.master.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo')

			# If the phrase was never set change it to display that info
			if game.phrase == None:
				game.phrase = "Phrase not placed"

			# Submit end-of-round report
			mess_subj = str(game.puppet) + ' has won this round as Puppet'
			mess_body = "Phrase: " + game.phrase + "\n\nMaster: " + str(game.master) +
			'\n\nThe Puppet will become the Master for the next round. A new Puppet will be selected now.'

			# If the Puppet wins, they become the Master for the next round and a new Puppet is selected
			hold_master = game.puppet
			hold_puppet = getRandomUser('puppet')

			while str(hold_puppet) == str(hold_master):
				hold_puppet = getRandomUser('puppet')

		return Game(hold_master, hold_puppet)

# Check inbox for messages to process
def readPMs(game):
	messages = reddit.inbox.unread()

	for message in messages:
		# Message from Master or Puppet
		if message.body.startswith('!') and (message.author == game.puppet or message.author == game.master):
			message_words = message.body.split()
			command = message_words[0]
			print('Command: ' + command)

			if command.lower() == '!setphrase' and message.author == game.master:
				# Check if the phrase has already been placed
				if game.phrase != None:
					game.master.message('Phrase rejected', 'The phrase has already been set for this game.\n\nPhrase: ' + game.phrase)
					message.mark_read()
					print('Phrase rejected: Phrase already set')
					continue
				# Check if the phrase is too long
				elif len(message_words) > 4:
					game.master.message('Phrase rejected', 'The phrase is longer than 3 words.\n\nPhrase: ' + game.phrase +
					'\n\nNumber of words: ' + str(len(message_words - 1)))
					
					message.mark_read()
					print('Phrase rejected: Phrase to long\nPhrase: ' + message.body[11:])
					continue
				# Check that both Master and Puppet have accepted their roles
				elif game.master_accepted and game.puppet_accepted:
					game.setPhrase(message.body[11:])
					message.mark_read()
					print ('Phrase accepted\nPhrase: ' + message.body[11:])
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

# Initial Master and Puppet
first_master = reddit.redditor('connlocks')
#first_master = getRandomUser('master')
first_puppet = reddit.redditor('the_b00ts')
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
		for comment in reddit.subreddit('edefinition').stream.comments(pause_after=1):

			# If there are no new comments, check PMs
			if comment == None:
				readPMs(game)
				continue

			# Check for user opt-in
			if ("!you're it" in comment or "!youre it" in comment) and str(comment.author) not in opt_in_users:
				addOptIn(str(comment.author))
				comment.reply("You have just opted-in to Tag. If you would like to opt-out then send /u/shimmyjimmy a PM with !opt-out as the subject.")

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
							post = comment.submission
							post_time = post.created_utc
							post_time = datetime.fromtimestamp(post_time)

							# Check if the comment is under a post that was made after the game started
							if game.start_time < post_time:
								print('Phrase found')
								game.phrase_placed = True
								game.end_time = game.end_time + timedelta(days=1)
								print(game.end_time)

								# Notify the Master and Puppet that the comment was identified by the bot
								game.target_comment = comment.id
								game.puppet.message('Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body)
								game.master.message('Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body)

					# If the phrase isn't placed then the guess is always wrong
					if "!you're it" in comment.body.lower() or "!youre it" in comment.body.lower():
						comment.reply("Incorrect. This comment does not contain the word/phrase. Keep trying bb")

				# The Puppet has used the phrase
				if game.phrase_placed == True:
					print('Phrase is placed')

					# If the game is past the end time, then the Puppet wins the round
					if (game.end_time - datetime.now()).days < 0:
						game = game.endGame('puppet')

					# Check if user's guess is correct
					elif comment.body.lower() == "!you're it" or comment.body.lower() == "!youre it":
						print('Tag')
						print(game.target_comment)
						print(comment.parent_id)

						# Correct guess: The Master wins the round
						if game.target_comment == comment.parent_id[3:]:
							comment.reply('Correct! The next game shall being in 3...2...1...\n\n    COMMENCE START UP SEQUENCE')
							game = game.endGame('master')
						# Incorrect guess
						else:
							comment.reply("Incorrect. This comment does not contain the word/phrase. Keep trying bb")

	except praw.prawcore.exceptions.ResponseException:
		print('Error connecting to servers. Sleeping for 1 min')
		time.sleep(60)
