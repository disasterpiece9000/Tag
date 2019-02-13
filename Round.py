import praw
import prawcore
import sys
import time
import random
from tinydb import TinyDB, Query
from datetime import datetime, date, timedelta
from dateutil import relativedelta
from Game import Game

# PRAW instance
reddit = praw.Reddit('SentimentBot')

# Automated message footer
message_footer = "\n\n**This is an automated message**" +\
				"\n\n-----\n\n[View the rules here](https://github.com/disasterpiece9000/Tag)" +\
				" | [How to opt-in](https://www.reddit.com/user/shimmyjimmy97/comments/alt7e8/how_to_optin_to_tag/)" +\
				" | [Contact the dev](https://www.reddit.com/message/compose/?to=shimmyjimmy97)"

# Round object
class Round:
	def __init__(round, game, master, puppet):
		round.game = game

		# Set users and offer roles
		round.master = master
		round.puppet = puppet
		round.offerRole(master)
		round.master_accepted = False
		round.offerRole(puppet)
		round.puppet_accepted = False

		# Day the two users were offered their role
		round.day_initialized = datetime.now()

		# One guess per user per round
		round.used_guess = []

		# Store location of phrase
		round.target_comment = None
		round.phrase_permalink = None

		# Store the user who tagged the phrase
		round.tagger = None

		print('Master: ' + str(master) + '\tPuppet: ' + str(puppet) + '\n')

		# Master's phrase
		round.phrase = None
		# Phrase has been set and delivered to both users
		round.active = False
		# Phrase has been successfully used by the Puppet
		round.phrase_placed = False
		# Phrase has been identified by another user
		round.phrase_identified = False
		# User who won the round
		round.victor = None

	# Message all users
	def notifyUsers(round, subj, body):
		for username in round.game.opt_in_users:
			user = reddit.redditor(username)
			user.message(subj, body)

	# Notify the user that they have been selected
	def offerRole(round, user):
		# Reset the timer everytime a new user is offered a role
		round.day_initialized = datetime.now()

		if user == round.master:
			user.message('Would you like to play a round?',
			'You have been randomly selected to play the role of Master in this round of Tag. ' +
			'To accept this invitation, reply to this message with !accept. To reject this invitation, ' +
			'reply with !reject. If no response is recieved within 24 hours, another user will be selected.' +
			message_footer)

		if user == round.puppet:
			user.message('Would you like to play a round?',
			'You have been randomly selected to play the role of Puppet in this round of Tag. ' +
			'To accept this invitation, reply to this message with !accept. To reject this invitation, ' +
			'reply with !reject. If no response is recieved within 24 hours, another user will be selected. '+
			message_footer)

	# Respond to the accepted role and inform the user of the next stage of the round
	def acceptRole(round, user):
		if user == round.master and round.master_accepted == False:
			round.master_accepted = True

			round.master.message(
				'Role accepted: Master', 'You will recieve a message asking for a phrase once the Puppet has also accepted their role.' +
				message_footer)

			print('User: ' + str(user) + '\nAccepted Role: Master')
		elif user == round.puppet and round.puppet_accepted == False:
			round.puppet_accepted = True

			round.puppet.message(
				'Role accepted: Puppet', 'You will recieve a message informing you of the phrase once the Master has accepted their ' +
				'role and set a phrase.' +
				message_footer)

			print('User accepted role: ' + str(user))

		# If both users have accepted then the master is asked to provide the phrase
		if round.puppet_accepted == True and round.master_accepted == True:
			round.master.message('Please set the phrase for the round to begin', 'Reply to this PM with !setphrase as the first text in the body, ' +
			'followed by the word or phrase of your choice. The phrase can be no longer than 3 words and it cannot contain any user mentions. ' +
			'You will recieve a confirmation message once it has been successfully set.' +
			message_footer)

	# Find a new user to fill the role
	def rejectRole(round, user):
		print('User: ' + str(user) + '\nRejected Role: Puppet')

		if user == round.master and round.master_accepted == False:
			hold_master = round.game.getRandomUser('master')

			while str(hold_master) == str(round.puppet):
				hold_master = round.game.getRandomUser('master')

			round.master = hold_master
			round.offerRole(round.master)

			print('User: ' + str(user) + '\nRejected Role: Master')

		if user == round.puppet and round.puppet_accepted == False:
			hold_puppet = round.game.getRandomUser('puppet')

			while str(hold_puppet) == str(round.master):
				hold_puppet = round.game.getRandomUser('puppet')

			round.puppet = hold_puppet
			round.offerRole(round.puppet)

			print('User rejected role: ' + str(user))

	

	# Set the phrase provided by the Master and notify users about the next stage of the round
	def setPhrase(round, phrase):
		round.phrase = phrase
		# The time the phrase was set
		round.start_time = datetime.now()
		# The time the round will end (24hrs after the start time)
		round.end_time = round.start_time + timedelta(days=1)
		round.active = True

		print('Phrase: ' + phrase)

		round.master.message('Let the rounds begin', 'Phrase: ' + round.phrase + '\n\nThis phrase was accepted. The Puppet has been ' +
							'notified and the clock is now ticking. If the comment is not identified in 24 hours, then they will win.' +
							'The Puppet must leave the phrase under a post that was created 3 hours before the round started or later\n\n' +
							'Posts created after ' + (round.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
							'\n\nEnd time: ' + round.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
							message_footer)

		round.puppet.message('Let the rounds begin', 'Phrase: ' + round.phrase + '\n\nThis phrase was accepted. The Master has been ' +
							'notified and the clock is now ticking. If the comment is not identified in 24 hours, then you will win.' +
							'You must leave the phrase under a post that was created 3 hours before the round started or later\n\n' +
							'Posts created after ' + (round.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
							'\n\nEnd time: ' + round.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
							message_footer)

		# Notify other users about the active round
		mess_subj = 'A new round has started!'
		mess_body = ('The phrase has been set and the Puppet must now place it somewhere in the subreddit in the next 24 hours. ' +
					'After it is placed, you all will have another 24 hours to find it. Once the round is over another PM ' +
					'will be sent with details of the round.' +
					'The Puppet must leave the phrase under a post that was created 3 hours before the round started or later\n\n' +
					'Posts created after ' + (round.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
					'\n\nEnd time: ' + round.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
					message_footer)

		notifyUsers(mess_subj, mess_body)

	# Resolve "!you're it" comments
	def handleTag(round, comment):
		# If the user placed a guess and isn't opted-in then add them to opt-in
		if str(comment.author) not in opt_in_users:
			addOptIn(str(comment.author))
			comment.reply("You have just opted-in to Tag. If you would like to opt-out then send /u/shimmyjimmy a PM with !opt-out as the body." +
						message_footer)

			print("User has opted-in: " + str(comment.author))

		# If user has already guessed this round, then always return incorrect guess
		if comment.author in round.used_guess:
			comment.reply("Not so fast. You have already tagged another user this round. Please wait until next round to try again!" +
						message_footer)

			print("User has already guessed this round: " + str(comment.author))

		# If user is the master or the puppet, then always return incorrect guess
		elif comment.author == round.master or comment.author == round.puppet:
			comment.reply("Not it. This comment does not contain the phrase" +
						message_footer)

			round.used_guess.append(comment.author)
			print("User is Puppet or Master: " + str(comment.author))

		# If the phrase hasn't been placed yet, then always return incorrect guess
		elif round.phrase_placed == False:
			comment.reply("Not it. This comment does not contain the phrase" +
						message_footer)

			round.used_guess.append(comment.author)
			print("User guessed before phrase was placed: " + str(comment.author))

		# If the phrase is placed, check if it was left under the Puppet's comment
		elif round.phrase_placed == True:
			# Correct guess: The Master wins the round
			if round.target_comment == comment.parent_id[3:]:
				comment.reply("They're it! The next round shall being in 3...2...1...\n\n    COMMENCE START UP SEQUENCE" +
							message_footer)

				print("User guessed correctly:" + str(comment.author))
				round.game.endRound('master')
			# Incorrect guess
			else:
				comment.reply("Not it. This comment does not contain the phrase" +
							message_footer)

				round.used_guess.append(comment.author)
				print("User guessed incorrectly: " + str(comment.author))

		print('\n')

	# Notify all users about the results of the round and initalize the next round
	def endRound(round, winner):
		print('Winner: ' + str(round.master) + '\tRole: ' + winner)
		hold_master = None
		hold_puppet = None

		# If the phrase was never set change it to display that info
		if round.phrase == None:
			round.phrase = "Phrase not placed"

		elif round.phrase_permalink == None:
			round.phrase += " - Phrase not palced by Puppet"

		else:
			round.phrase = '[' + round.phrase + '](' + round.phrase_permalink + ')'

		# Master wins
		if winner == 'master':
			round.master.message('You win!', 'Congrats! You are victorious and will remain the Master for another round' +
								message_footer)
			round.puppet.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo' +
								message_footer)

			# Submit end-of-round report
			mess_subj = str(round.master) + ' has won this round as Master'
			mess_body = 'Phrase: ' + round.phrase + '\n\nPuppet: ' + str(round.puppet) + '\n\n' +\
						'\n\nThe Master will remain as the Master for the next round. A new Puppet will be selected now.' +\
						message_footer
			notifyUsers(mess_subj, mess_body)

			# If the Master wins, they remian the master and a new Puppet is selected
			hold_master = round.master
			hold_puppet = round.game.getRandomUser('puppet')

			while str(hold_puppet) == str(hold_master):
				hold_puppet = round.game.getRandomUser('puppet')

		# Puppet wins
		if winner == 'puppet':
			round.puppet.message('You win!', 'Congrats! You are victorious and will become the Master for the next round' +
								message_footer)
			round.master.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo' +
								message_footer)

			# Submit end-of-round report
			mess_subj = str(round.puppet) + ' has won this round as Puppet'
			mess_body = ("Phrase: " + round.phrase + "\n\nMaster: " + str(round.master) +
						 '\n\nThe Puppet will become the Master for the next round. A new Puppet will be selected now.' +
						 message_footer)
			notifyUsers(mess_subj, mess_body)

			# If the Puppet wins, they become the Master for the next round and a new Puppet is selected
			hold_master = round.puppet
			hold_puppet = round.game.getRandomUser('puppet')

			while str(hold_puppet) == str(hold_master):
				hold_puppet = round.game.getRandomUser('puppet')

		# Create next round
		round.game.current_round = Round(round.game, hold_master, hold_puppet)

	def runRound(round):
		while True:
			# Catch disconnect errors
			try:
				# Stream of comments from target subreddit
				for comment in reddit.subreddit('edefinition').stream.comments(skip_existing=True, pause_after=1):

					# If there are no new comments, check PMs
					if comment == None:
						round.game.readPMs()
						continue

					# Check for user opt-in
					if ("!you're it" in comment.body or "!you’re it" in comment.body or "!youre it" in comment.body):
						round.handleTag(comment)

					# Check if round has been inactive for < 24hrs
					if round.active == False:
						if (datetime.now() - round.day_initialized).days >= 1:
							# Select a new user if the role has not been accepted
							if round.puppet_accepted == False:
								round.puppet = round.game.getRandomUser('puppet')
								round.offerRole(round.puppet)

							if round.master_accepted == False:
								round.master = round.game.getRandomUser('master')
								round.offerRole(round.master)

					# Both users have accepted their roles and the phrase is set
					if round.active == True:

						# The Puppet has not used the phrase
						if round.phrase_placed == False:

							# End the round if the Puppet has not used the phrase in 24hrs
							if (round.end_time - datetime.now()).days < 0:
								print('Times up')
								round = round.endRound('master')

							# Check if comment is from the Puppet
							elif str(comment.author).lower() == str(round.puppet).lower():
								print('Comment from puppet')

								# Check if the phrase is in the comment
								if round.phrase.lower() in comment.body.lower():
									print("Phrase in comment")
									post = comment.submission
									post_time = post.created_utc
									post_time = datetime.fromtimestamp(post_time)

									# Check if the comment is under a post that was made after the round started
									if (round.start_time - timedelta(hours=3)) < post_time:
										print('Phrase found')
										round.phrase_placed = True
										round.end_time = datetime.now() + timedelta(days=1)

										# Notify the Master and Puppet that the comment was identified by the bot
										round.target_comment = comment.id
										round.phrase_permalink = comment.permalink
										round.tagger = str(comment.author)

										round.puppet.message(
											'Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body +
											"\n\nIf another user doesn't tag the comment within the next 24hrs then you win." +
											"\n\nEnd Time: " + round.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
											message_footer)

										round.master.message(
											'Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body +
											"\n\nIf another user tags the comment within the next 24hrs then you win." +
											"\n\nEnd Time: " + round.end_time.strftime("%m/%d/%Y, %H:%M:%S") + ' EST' +
											message_footer)

									# Comment placed under old post
									else:
										print("Comment found under old post and was not accpeted")
										round.puppet.message(
											"Phrase not accepted", "You must leave the phrase under a post that was created 3 hours before" +
											"the round started or later.\n\nPosts created after " +
											(round.start_time - timedelta(hours=3)).strftime("%m/%d/%Y, %H:%M:%S") + ' EST are valid' +
											message_footer)

						# The Puppet has used the phrase
						if round.phrase_placed == True:

							# If the round is past the end time, then the Puppet wins the round
							if datetime.now() > round.end_time:
								round = round.endRound('puppet')

			except (prawcore.exceptions.ResponseException, prawcore.exceptions.RequestException):
				print('Error connecting to servers. Sleeping for 1 min')
				time.sleep(60)




