import praw
import prawcore
import sys
import time
import random
from tinydb import TinyDB, Query
from datetime import datetime, date
from dateutil import relativedelta

def getRandomUser(role):
	edef_users = ()
	for user in reddit.subreddit('edefinition').contributor():
		edef_users.append
		
	random_user = random.choice(edef_users)
	while random_user.name == 'shimmyjimmy97':
		random_user = random.choice(edef_users)
	
	if role == 'master':
		random_user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Master in this round of the game. To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is recieved by the start of the next day, another user will be selected.')
	if role == 'puppet':
		random_user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Puppet in this round of the game. To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is recieved by the start of the next day, another user will be selected.')
	
	print('User: ' + str(random_user) + '\tRole: ' + role)
	return random_user

class Game:
	def __init__(game, master, puppet):
		game.master = master
		game.offerRole(master)
		game.master_accepted = False
		game.puppet = puppet
		game.offerRole(puppet)
		game.puppet_accepted = False
		game.day_initialized = datetime.now()
		
		print('Master: ' + str(master) + '\tPuppet ' + str(puppet))
		
		game.phrase = None
		game.active = False
		game.phrase_placed = False
		game.phrase_identified = False
		game.victor = None
		
	def offerRole(game, user):
		if user == game.master:
			user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Master in this round of the game. To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is recieved by the start of the next day, another user will be selected.')
		if user == game.puppet:
			user.message('Would you like to play a game?', 'You have been randomly selected to play the role of Puppet in this round of the game. To accept this invitation, reply to this message with !accept. To reject this invitation, reply with !reject. If no response is recieved by the start of the next day, another user will be selected.')
	
	def acceptRole(game, user):
		if user == game.master and game.master_accepted == False:
			game.master_accepted = True
			game.master.message('Role accepted: Master', 'You will recieve a message asking for a phrase once the Puppet has also accepted their role.')
			print('User: ' + str(user) + '\nAccepted Role: Master')
		elif user == game.puppet and game.puppet_accepted == False:
			game.puppet_accepted = True
			game.puppet.message('Role accepted: Puppet', 'You will recieve a message informing you of the phrase once the Master has accepted their role and set a phrase')
			print('User: ' + str(user) + '\nAccepted Role: Master')
			
		if puppet_accepted == True and master_accepted == True:
			game.master.message('Please set the phrase for the game to begin', 'Reply to this PM with !setphrase as the first text in the body, followed by the word or phrase of your choice. The phrase can be no longer than 3 words. You will recieve a confirmation message once it has been successfully set.')
			
	def rejectRole(game, user):
		if user == game.master and game.master_accepted == False:
			game.master = getRandomUser('master')
			print('User: ' + str(user) + '\nRejected Role: Master')
		if user == game.puppet and game.puppet_accepted == False:
			game.puppet = getRandomUser('puppet')
			print('User: ' + str(user) + '\nRejected Role: Puppet')
	
	def setPhrase(game, phrase):
		game.phrase = phrase
		game.start_day = datetime.today()
		game.end_day = game.start_day + timedelta(days=6)
		game.active = True
		
		print('Phrase: ' + phrase)
		
		game.master.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\nThis phrase was accepted. The other user has been notified and the clock is now ticking. They have until ' + str(game.end_day) + ' to leave their comment. If it is not identified in one week, then they will win.')
		game.puppet.message('Let the games begin', 'Phrase: ' + game.phrase + '\n\You have until ' + str(game.end_day) + ' to leave a comment that contains this phrase. When the bot sees your comment, it will notify you that it has been identified. If another user does not identify the comment in a week, then you win.')
	
	def endGame(game, winner):
		print('Winner: ' + str(game.master) + '\tRole: ' + winner)
		
		if winner == 'master':
			game.master.message('You win!','Congrats! You are victorious and will remain as the Master for another round')
			game.puppet.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo')
			return Game(game.master, getRandomUser('puppet'))
		if winner == 'puppet':
			game.puppet.message('You win!', 'Congrats! You are victorious and will become the Master for the next round')
			game.master.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo'
			return Game(game.puppet, getRandomUser('puppet')

def readPMs(game):
	messages = reddit.inbox.unread()
	for message in messages:
		if message.body.startswith('!') and (message.author == game.puppet or message.author == game.master):
			message_words = message.body.split()
			command = message_words[0]
			
			if command.lower() == '!setphrase' and message.author == game.master:
				if game.phrase != None:
					game.master.message('Phrase rejected', 'The phrase has already been set for this game.\n\nPhrase: ' + game.phrase)
					message.mark_read()
					print('Phrase rejected: Phrase already set')
					continue
				elif len(message_words) > 4:
					game.master.message('Phrase rejected', 'The phrase is longer than 3 words.\n\nPhrase: ' + game.phrase + '\n\nNumber of words: ' str(len(message_words - 1)))\
					message.mark_read()
					print('Phrase rejected: Phrase to long\nPhrase: ' + message.body[11:])
					continue
				else:
					game.setPhrase(message.body[11:])
					message.mark_read()
					print ('Phrase accepted\nPhrase: ' + message.body[11:])
					continue
					
			if command.lower() == '!accept' and (message.author == game.master or message.author == game.puppet):
				game.acceptRole(message.author)
				message.mark_read()
				continue
				
			if command.lower() == '!reject' and (message.author == game.master or message.author == game.puppet):
				game.rejectRole(message.author)
				message.mark_read()
				continue


first_master = getRandomUser('master')
first_puppet = getRandomUser('puppet')
game = Game(first_master, first_puppet)

while True:
	for comment in reddit.subreddit('edefinition').stream.comments(pause_after=1):
		if comment == None:
			readPMs(game)
		
		if game.active == False:
			if relativedelta.relativedelta(datetime.now(), game.day_initialized).days >= 1:
				if game.puppet_accepted == False:
					game.puppet = getRandomUser('puppet')
					game.offerRole(game.puppet)
				if game.master_accepted == False:
					game.master = getRandomUser('master')
					game.offerRole(game.master)
			
		if game.active == True:
			if game.phrased_placed == False:
				if relativedelta.relativedelta(game.end_day, datetime.now()).days == 0:
					game = game.endGame('master')
			
				elif comment.author == game.puppet and game.phrase.lower() in comment.body.lower():
					game.phrase_placed == True
					game.end_day = game.end_day = datetime.now() + timedelta(days=1)
					game.target_comment = comment
					game.puppet.message('Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body)
					game.master.message('Phrase identified', '[Comment](' + comment.permalink + '): ' + comment.body)
					
				elif comment.author != game.master and comment.author != game.puppet and comment.body.lower() == "!you're it" or commen.body.lower() == "!youre it":
					comment.reply("Incorrect. This comment does not contain the word/phrase. Keep trying bb")
					
			if game.phrase_placed == True:
				if relativedelta.relativedelta(game.end_day, datetime.now() == 0:
					game = game.endGame('puppet')
				
				elif comment.author != game.master and comment.author != game.puppet and (comment.body.lower() == "!you're it" or commen.body.lower() == "!youre it"):
					if game.target_comment == comment.parent()
						comment.reply('Correct! The next game shall being in 3...2...1...\n\n    COMMENCE START UP SEQUENCE')
						game = game.endGame('master')
					else:
						comment.reply("Incorrect. This comment does not contain the word/phrase. Keep trying bb")