"""
 __  __                     ___                     _             
|  \/  | ___ _ __ ___   ___|_ _|_ ____   _____  ___| |_ ___  _ __ 
| |\/| |/ _ \ '_ ` _ \ / _ \| || '_ \ \ / / _ \/ __| __/ _ \| '__|
| |  | |  __/ | | | | |  __/| || | | \ V /  __/\__ \ || (_) | |   
|_|  |_|\___|_| |_| |_|\___|___|_| |_|\_/ \___||___/\__\___/|_|   
                                                                  
"""

# Standard scripts
import time
from threading import Thread

# Third-party library
import praw

# Our own scripts and files
import config
from investor import *
import message
import utils

# Reddit instance initialization
reddit = praw.Reddit(client_id=config.client_id,
                     client_secret=config.client_secret,
                     username=config.username,
                     password=config.password,
                     user_agent=config.user_agent)

# Subreddit initialization
subreddit_name = "pewds_test"
subreddit = reddit.subreddit(subreddit_name)

# A list of available commands:
commands = ["!create", "!invest", "!balance", "!help", "!broke"]

# The amount of MemeCoins given by default
starter = 1000

# Data folder
data_folder = "./data/"

# File to store all investors
investors_file = "investors.txt"

# File to store all awaiting investments
awaiting_file = "awaiting.txt"

# File to store all done investments
done_file = "done.txt"

# File to store checked comments
checked_file = "checked_comments.txt"

# Dictionary of all the investors
users = utils.read_investors(data_folder + investors_file)

print(users)

# Array to store done and awaiting investments
done = utils.read_investments(data_folder + done_file)
awaiting = utils.read_investments(data_folder + awaiting_file)

# Array to store IDs of parsed comment, so we won't parse the same
# comment multiple times
checked_comments = utils.read_array(data_folder + checked_file)

def save_data():
    global users, awaiting, done
    utils.write_investors(data_folder + investors_file, users)
    utils.write_investments(data_folder + awaiting_file, awaiting)
    utils.write_investments(data_folder + done_file, done)
    utils.write_array(data_folder + checked_file, checked_comments)

def help(comment):
    comment.reply(message.help_org)

def create(comment, author):
    users[author] = Investor(author, starter)
    comment.reply(message.modify_create(author, users[author].get_balance()))
    
def invest(comment, author, text):
    post = reddit.submission(comment.submission)
    post_ID = post.id
    upvotes = post.ups
    investor = users[author]
    
    # If it can't extract the invest amount, abandon the operation
    try:
        investm = int(float(text.replace("!invest", "").replace(" ", "")))
    except ValueError as ve:
        return False

    if (investm < 100):
        comment.reply(message.min_invest_org)
        return
    
    is_enough = investor.enough(investm)
    
    if (is_enough):
        inv =investor.invest(post_ID, upvotes, investm)
        comment.reply(message.modify_invest(investm, investor.get_balance()))
        awaiting.append(inv)
        return True
    else:
        comment.reply(message.insuff_org)
        return True
        
def balance(comment, author):
    investor = users[author] 
    balance = investor.get_balance()
    comment.reply(message.modify_balance(balance))
    return True

def broke(comment, author):
    investor = users[author]
    balance = investor.get_balance()
    active = investor.get_active()

    if (balance < 100):
        if (active == 0):
            comment.reply(message.broke_org)
        else:
            comment.reply(message.modify_broke_active(active))
    else:
        comment.reply(message.modify_broke_money(balance))
    return True
            
def comment_thread():

    for comment in subreddit.stream.comments():
        author = comment.author.name.lower()

        # We don't serve your kind around here
        if ("_bot" in author):
            continue
        
        text = comment.body.lower()
        exist = author in list(users.keys())
        print("Author - {}\nText - {}\nExist? - {}\n\n".format(author, text, exist))

        if ("!help" in text):
            help(comment)
            continue
        
        # The !create command
        if (("!create" in text) and (not exist)):
            create(comment, author)
            save_data()
            continue

        if (not exist):
            comment.reply(message.no_account_org)
            continue

        # The !invest command
        if ("!invest" in text):
            invest(comment, author, text)
            save_data()
            continue
                
        if ("!balance" in text):
            balance(comment, author)
            save_data()
            continue

        if ("!broke" in text):
            broke(comment, author)
            save_data()
            continue
        
def check_investments():
    time.sleep(60)
    investment = awaiting[0]
    investor_id = investment.get_name()
    investor = users[investor_id]
    post = investment.get_ID()
    upvotes = reddit.submission(post).ups

    if (investment.check()):
        investor.calculate(investment, upvotes)
        done.append(awaiting.pop(0))

def threads():
    Thread(name="Comments", target=comment_thread).start()

if __name__ == "__main__":
    threads()