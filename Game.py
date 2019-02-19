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
		# Create initial Round object
		game.current_round = Round(game)
		game.current_master = game.current_round.master
		game.current_puppet = game.current_round.puppet
		game.runGame()

	def runGame(game):
		while(True):
			# Run round until completion and then get results
			results = game.current_round.runRound()

			# Get the new round and update Master/Puppet
			game.current_round = results[0]
			game.current_master = game.current_round.master
			game.current_puppet = game.current_round.puppet

			# Get the winner of the previous round
			round_winner = results[1]
			winner_role = results[2]

			# Get the user who tagged the comment (if one exists)
			tagger = results[3]