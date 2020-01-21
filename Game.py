import praw
from tinydb import TinyDB, Query
from Round import Round

# PRAW instance
reddit = praw.Reddit('Tag')

# TinyDB Querry object
find_stuff = Query()

# Automated message footer
message_footer = ("\n\n**This is an automated message**" +
                 "\n\n-----\n\n" +
                 "[View the rules here](https://www.reddit.com/r/edefinition/comments/ejll1f/tag_rules/)" +
                 " | [How to opt-in/out](https://www.reddit.com/r/edefinition/comments/ejll1f/tag_rules/" +
                 "fcyqizq?utm_source=share&utm_medium=web2x)" +
                 " | [Scoreboard](https://www.reddit.com/r/edefinition/comments/ejlnhv/tag_scoreboard/)")


# noinspection PyMethodParameters
class Game:
    def __init__(game):
        # Read current scoreboard
        game.scoreboardDB = TinyDB("player_data.json")
        game.scoreboard = game.read_score()
        game.scoreboard_post = reddit.submission(id="ejlnhv")
        
        # Count master consecutive wins
        game.master_wins = 0
        
        # Create initial Round object
        game.current_round = Round(game)
        game.current_master = game.current_round.master
        game.current_puppet = game.current_round.puppet
        game.run_game()
    
    # Continuously run rounds
    def run_game(game):
        while True:
            # Run round until completion and then get results
            winner = game.current_round.runRound()
            results = game.end_round(winner)
            hold_master = results[0]  # New master
            hold_puppet = results[1]  # New puppet
            winner = results[2]  # Round winner
            winner_role = results[3]  # Winner's role
            tagger = results[4]  # User who tagged comment
            
            # Increment consecutive master wins counter
            if winner_role == "master":
                game.master_wins += 1
            
            # Update the scoreboard
            game.update_score(winner, winner_role, tagger)
            
            # Format end-of-round report
            report = game.get_report(winner, winner_role, tagger)
            
            # Distribute the report
            report_comment = game.send_report(report)
            
            # Update scoreboard with permalink to report
            game.scoreboard[str(winner)]['last_round'] = report_comment.permalink
            game.scoreboardDB.update({'last_round': report_comment.permalink}, find_stuff.username == str(winner))
            
            # Remake the scoreboard with new info
            game.make_score(report_comment, winner)
            
            # Create next round
            if game.master_wins > 2:
                game.current_round = Round(game, puppet=hold_puppet)
                game.master_wins = 0
            else:
                game.current_round = Round(game, hold_master, hold_puppet)
    
    # Get points for consecutive master wins
    def get_increment(game):
        if game.master_wins == 1:
            return 25
        elif game.master_wins == 2:
            return 50
        else:
            return 100
    
    # Notify all users about the results of the round and initialize the next round
    def end_round(game, winner):
        # Round results
        newRound = None
        winner_user = None
        tagger = game.current_round.tagger
        
        # Hold users for next round
        hold_master = None
        hold_puppet = None
        
        # Master won
        if winner == 'master':
            winner_user = game.current_round.master
            print('Winner: ' + str(game.current_round.master) + '\tRole: Master')
            
            game.current_round.master.message('You win!', 'Congrats! You are victorious and will remain the Master for '
                                                          'another round' + message_footer)
            game.current_round.puppet.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo' +
                                              message_footer)
            
            # If the Master wins, they remain the master and a new Puppet is selected
            hold_master = game.current_round.master
            hold_puppet = game.current_round.getRandomUser('puppet')
            
            while str(hold_puppet) == str(hold_master):
                hold_puppet = game.current_round.getRandomUser('puppet')
        
        # Puppet won
        if winner == 'puppet':
            winner_user = game.current_round.puppet
            print('Winner: ' + str(game.current_round.puppet) + '\tRole: Puppet')
            
            game.current_round.puppet.message('You win!',
                                              'Congrats! You are victorious and will become the Master for the next '
                                              'round' + message_footer)
            game.current_round.master.message('You lost :(', 'Too bad, so sad. Better luck next time kiddo' +
                                              message_footer)
            
            # If the Puppet wins, they become the Master for the next round and a new Puppet is selected
            hold_master = game.current_round.puppet
            hold_puppet = game.current_round.getRandomUser('puppet')
            
            while str(hold_puppet) == str(hold_master):
                hold_puppet = game.current_round.getRandomUser('puppet')
        
        # Return round results
        return [hold_master, hold_puppet, winner_user, winner, tagger]
    
    # Format end-of-round report
    def get_report(game, winner, winner_role, tagger):
        # If the phrase was never set change it to display that info
        if game.current_round.phrase is None:
            game.current_round.phrase = " - Phrase not placed bt Master"
        
        elif game.current_round.phrase_permalink is None:
            game.current_round.phrase += " - Phrase not palced by Puppet"
        
        else:
            game.current_round.phrase = '[' + game.current_round.phrase + '](' + \
                                        game.current_round.phrase_permalink + ')'
        
        mess_subj = ""
        mess_body = ""
        
        # Puppet won
        if winner_role == "puppet":
            mess_subj += str(game.current_round.puppet) + ' has won this round as Puppet'
            mess_body += ("Phrase: " + game.current_round.phrase +
                          "\n\nMaster: " + str(game.current_round.master) +
                          "\n\nPoints Awarded to Puppet: 100" +
                          "\n\nThe Puppet will become the master for the next round. A new Puppet will be selected now" +
                          message_footer)
        
        # Master won
        if winner_role == "master":
            mess_subj += str(game.current_round.master) + ' has won this round as Master'
            mess_body += ('Phrase: ' + game.current_round.phrase +
                          '\n\nPuppet: ' + str(game.current_round.puppet))
            
            # Add info if comment was tagged
            if tagger is not None:
                mess_body += ("\n\nTagger: " + tagger +
                              "\n\nPoints awarded to Tagger: 50")
            
            mess_body += ("\n\nPoints awarded to Master: " + str(game.get_increment()))
            
            # Add info about master term limit
            if game.master_wins < 3:
                mess_body += "\n\nThe Master will remain in their role for the next round. " \
                             "A new Puppet will be selected now"
            else:
                mess_body += ("\n\nThe Master has won 3 consecutive rounds and will now be replaced. " +
                              "A new Master and Puppet will be selected now")
            
            mess_body += message_footer
        
        return [mess_subj, mess_body]
    
    # Distribute report
    def send_report(game, report):
        subj = report[0]
        body = report[1]
        game.current_round.notifyUsers(subj, body)
        
        # Return the comment object for the report
        return game.scoreboard_post.reply(subj + "\n\n" + body)
    
    # Read the scoreboard db
    def read_score(game):
        hold_board = {}
        for username in game.scoreboardDB:
            hold_board[username["username"]] = {"last_round": username['last_round'],
                                                "score": username['score']}
        return hold_board
    
    # Update the scoreboard
    def update_score(game, winner, role, tagger):
        # Re-read scoreboard
        game.scoreboard = game.read_score()
        
        # Master wins
        if role == "master":
            # Get score increment based on number of consecutive wins
            score_increment = game.get_increment()
            
            # Update the dict and DB
            old_score = game.scoreboard[str(winner)]['score']
            new_score = old_score + score_increment
            
            game.scoreboard[str(winner)]['score'] = new_score
            game.scoreboardDB.update({'score': new_score}, find_stuff.username == str(winner))
        
        elif role == "puppet":
            old_score = game.scoreboard[str(winner)]['score']
            new_score = old_score + 100
            
            game.scoreboard[str(winner)]['score'] = new_score
            game.scoreboardDB.update({'score': new_score}, find_stuff.username == str(winner))
        
        if tagger is not None:
            old_score = game.scoreboard[tagger]['score']
            new_score = old_score + 50
            
            game.scoreboard[tagger]['score'] = new_score
            game.scoreboardDB.update({'score': new_score}, find_stuff.username == tagger)
    
    # Remake the scoreboard with new info
    def make_score(game, comment, winner):
        permalink = comment.permalink
        post_header = "#[Most recent round](" + permalink + ")" + "\n\n#Current Leader - "
        table_header = "|Username|Last Round Victory|Score|\n|:-|:-|:-|\n"
        table_body = ""
        leader = ""
        top_score = 0
        
        # Create a row for each user
        for username in game.scoreboard:
            # Username
            row = "|"
            row += username + "|"
            
            # Last Round Victory
            if username == str(winner):
                row += ("[Link](" + permalink + ") |")
            else:
                row += (game.scoreboard[username]["last_round"] + "|")
            
            # Score
            score = game.scoreboard[username]['score']
            if score > top_score:
                top_score = score
                leader = username
            row += str(score) + "|"
            
            # Append table
            table_body += (row + "\n")
        
        # Combine parts and post
        new_board = ""
        post_header += leader
        new_board += post_header
        new_board += "\n\n ____\n\n"
        new_board += table_header
        new_board += table_body
        game.scoreboard_post.edit(new_board)
