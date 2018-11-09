import praw
import prawcore
import sys
import time
import random
from tinydb import TinyDB, Query
from datetime import datetime, date, timedelta
from dateutil import relativedelta

reddit = praw.Reddit('SentimentBot')

def getRandomUser(role):
	edef_users = []
	for user in reddit.subreddit('edefinition').contributor():
		edef_users.append(user)
		
	random_user = random.choice(edef_users)
	while random_user.name == 'shimmyjimmy97':
		random_user = random.choice(edef_users)

	return random_user

class Game:
	def __init__(game, master, puppet):
		game.master = master
		game.puppet = puppet
		game.offerRole(master)
		game.master_accepted = False
		game.offerRole(puppet)
		game.puppet_accepted = False
		game.day_initialized = datetime.now()
		
		print('Master: ' + str(master) + '\tPuppet: ' + str(puppet))
		
		game.phrase = None
		game.active = False
		game.phrase_placed = False
		game.phrase_identified = False
		game.victor = None
		
	def offerRole(game, user):
		if user == game.master:
			user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Master in this round of Tag. To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is recieved within 24 hours, another user will be selected.')
		if user == game.puppet:
			user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Puppet in this round of Tag. To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is recieved within 24 hours, another user will be selected.')
	
	def acceptRole(game, user):
		if user == game.master and game.master_accepted == False:
			game.master_accepted = True
			game.master.message('Role accepted: Master', 'You will recieve a message asking for a phrase once the Puppet has also accepted their role.')
			print('User: ' + str(user) + '\nAccepted Role: Master')
		elif user == game.puppet and game.puppet_accepted == False:
			game.puppet_accepted = True
			game.puppet.message('Role accepted: Puppet', 'You will recieve a message informing you of the phrase once the Master has accepted their role and set a phrase')
			print('User: ' + str(user) + '\nAccepted Role: Master')
			
		if game.puppet_accepted == True and game.master_accepted == True:
			game.master.message('Please set the phrase for the game to begin', 'Reply to this PM with !setphrase as the first text in the body, followed by the word or phrase of your choice. The phrase can be no longer than 3 words. You will recieve a confirmation message once it has been successfully set.')
			
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
	
	def setPhrase(game, phrase):
		game.phrase = phrase
		game.start_day = datetime.today()
		game.end_day = game.start_day + timedelta(days=6)
		game.active = True
		
		print('Phrase: ' + phrase)
		
		game.master.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nThis phrase was accepted. The other user has been notified and the clock is now ticking. They have until ' + str(game.end_day) + ' to leave their comment. If it is not identified in one week, then they will win.')
		game.puppet.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nYou have until ' + str(game.end_day) + ' to leave a comment that contains this phrase. When the bot sees your comment, it will notify you that it has been identified. If another user does not identify the comment in a week, then you win.')
	
	def endGame(game, winner):
		print('Winner: ' + str(game.master) + '\tRole: ' + winner)
		hold_master = None
		hold_puppet = None
		
		if winner == 'master':
			game.master.message('You win!','Congrats! You are victorious and will remain as the Master for another round')
			game.puppet.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo')
			
			hold_master = game.master
			hold_puppet = getRandomUser('puppet')
			while str(hold_puppet) == str(hold_master):
				hold_puppet = getRandomUser('puppet')
			
		if winner == 'puppet':
			game.puppet.message('You win!', 'Congrats! You are victorious and will become the Master for the next round')
			game.master.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo')
			
			hold_master = game.puppet
			hold_puppet = getRandomUser('puppet')
			while str(hold_puppet) == str(hold_master):
				hold_puppet = getRandomUser('puppet')
		
		return Game(hold_master, hold_puppet)

def readPMs(game):
	messages = reddit.inbox.unread()
	for message in messages:
		print('Message ' + message.body)
		print('Author: ' + str(message.author))
		if message.body.startswith('!') and (message.author == game.puppet or message.author == game.master):
			message_words = message.body.split()
			command = message_words[0]
			print('Command: ' + command)
			
			if command.lower() == '!setphrase' and message.author == game.master:
				if game.phrase != None:
					game.master.message('Phrase rejected', 'The phrase has already been set for this game.\n\nPhrase: ' + game.phrase)
					message.mark_read()
					print('Phrase rejected: Phrase already set')
					continue
				elif len(message_words) > 4:
					game.master.message('Phrase rejected', 'The phrase is longer than 3 words.\n\nPhrase: ' + game.phrase + '\n\nNumber of words: ' + str(len(message_words - 1)))
					message.mark_read()
					print('Phrase rejected: Phrase to long\nPhrase: ' + message.body[11:])
					continue
				elif game.master_accepted and game.puppet_accepted:
					game.setPhrase(message.body[11:])
					message.mark_read()
					print ('Phrase accepted\nPhrase: ' + message.body[11:])
					continue
					
			if command.lower() == '!accept':
				game.acceptRole(message.author)
				message.mark_read()
				continue
				
			if command.lower() == '!reject':
				game.rejectRole(message.author)
				message.mark_read()
				continue


first_master = getRandomUser('master')
first_puppet = getRandomUser('puppet')

while first_master == first_puppet:
	first_puppet = getRandomUser('puppet')
	
game = Game(first_master, first_puppet)

while True:
	for comment in reddit.subreddit('edefinition').stream.comments(pause_after=1):
		if comment == None:
			readPMs(game)
			continue
		
		if game.active == False:
			if (datetime.now() - game.day_initialized).days >= 1:
				if game.puppet_accepted == False:
					game.puppet = getRandomUser('puppet')
					game.offerRole(game.puppet)
				if game.master_accepted == False:
					game.master = getRandomUser('master')
					game.offerRole(game.master)
			
		if game.active == True:
			if game.phrase_placed == False:
				
				if (game.end_day - datetime.now()).days == 0:
					print('Times up')
					game = game.endGame('master')
					
			
				elif str(comment.author).lower() == str(game.puppet).lower():
					print('Comment from puppet')

					if game.phrase.lower() in comment.body.lower():
						print('Phrase found')
						game.phrase_placed = True
						game.end_day = game.end_day + timedelta(days=1)
						print(game.end_day)
						game.target_comment = comment.id
						game.puppet.message('Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body)
						game.master.message('Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body)
					
				elif comment.author != game.master and comment.author != game.puppet and (comment.body.lower() == "!you're it" or comment.body.lower() == "!youre it"):
					comment.reply("Incorrect. This comment does not contain the word/phrase. Keep trying bb")
					
			if game.phrase_placed == True:
				print('Phrase is placed')
				if (game.end_day - datetime.now()).days == 0:
					game = game.endGame('puppet')
				
				elif comment.body.lower() == "!you're it" or comment.body.lower() == "!youre it":
					print('Tag')
					print(game.target_comment)
					print(comment.parent_id)
					if game.target_comment == comment.parent_id[3:]:
						comment.reply('Correct! The next game shall being in 3...2...1...\n\n    COMMENCE START UP SEQUENCE')
						game = game.endGame('master')
					else:
						comment.reply("Incorrect. This comment does not contain the word/phrase. Keep trying bb")