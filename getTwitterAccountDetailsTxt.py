#!/usr/bin/python3
# Contact: ivanm@security-net.biz
# Interesting analysis done with similar scripts:
# 1. https://security-net.biz/shared/bots/Analiza_neocekivanog_Twitter_statusa_IM_2022.pdf
# 2. https://security-net.biz/shared/bots/Analiza_neocekivanog_Twitter_statusa_IM_2022_v2.pdf

# Imports
import argparse
import re, os, time, shutil
import sys
from datetime import datetime
import simplejson as simplejson
import tweepy

# Go to https://apps.twitter.com/ and create an app.
# The consumer key and secret will be generated for you after
api_key = "-CHANGE-ME-"  # UPDATE THIS PART WITH NEW VALUES !!!
api_secrets = "-CHANGE-ME-"  # UPDATE THIS PART WITH NEW VALUES !!!

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Create New App" section
access_token = "-CHANGE-ME-"  # UPDATE THIS PART WITH NEW VALUES !!!
access_secret = "-CHANGE-ME-"  # UPDATE THIS PART WITH NEW VALUES !!!

parser = argparse.ArgumentParser("")
parser.add_argument("-c", help="Delete all files and start from beginning.", action='store_true')
parser.add_argument("-i", help="Ignore processed file and download data again.", action='store_true')
parser.add_argument("-b", help="Backup all files.", action='store_true')
parser.add_argument("-s", help="Sleep between requests, default 1 second.", default=1)
parser.add_argument("-r", help="Save raw JSON too.", action='store_true')
args = parser.parse_args()

def make_csv(acc_name, acc_data):

    x_date = ""
    x_verified = 0
    x_locked = 0
    x_posts = 0
    x_followers = 0
    x_following = 0
    x_likes = 0
    x_last_rt = 0

    csv_data = acc_name
    # Full name
    output = re.search('name\': \'(.*?)\', \'screen_name', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + '"' + output.group(1) + '"'
    else:
        csv_data += "," + "ERROR"
    # Registration Date
    output = re.search('created_at\': (.*?), \'favourites_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
        x_date = output.group(1).split(" ")[-1].replace("'","")
    else:
        csv_data += "," + "ERROR"
    # Is verified
    output = re.search('verified\': (.*?), \'statuses_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        if output.group(1) == 'True':
            csv_data += "," + "True"
            x_verified = 1
        else:
            csv_data += "," + "False"
    else:
        csv_data += "," + "False"
    # Is protected
    output = re.search('protected\': (.*?), \'followers_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        if output.group(1) == 'True':
            csv_data += "," + "True"
            x_locked = 1
        else:
            csv_data += "," + "False"
    else:
        csv_data += "," + "False"
    # Followers
    output = re.search('followers_count\': (.*?), \'friends_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
        x_followers = output.group(1)
    else:
        csv_data += ",0"
    # Following
    output = re.search('friends_count\': (.*?), \'listed_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
        x_following = output.group(1)
    else:
        csv_data += ",0"
    # Posts
    output = re.search('statuses_count\': (.*?), \'lang', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
        x_posts = output.group(1)
    else:
        csv_data += ",0"
    # Likes
    output = re.search('favourites_count\': (.*?), \'utc_offset', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
        x_likes = output.group(1)
    else:
        csv_data += ",0"
    # Latest
    if "retweeted_status" in acc_data: # If Retweet
        x_last_rt = 1
        output = re.search('text\': \'RT (.*?)\', \'truncated', acc_data, flags=re.IGNORECASE)
        if output is not None:
            csv_data += ",True," + '"' + output.group(1).replace('"', "'") + '"'
        else:
            csv_data += ",True,EMPTY"
    else: # If Status
        output = re.search('text\': \'(.*?)\', \'truncated', acc_data, flags=re.IGNORECASE)
        if output is not None:
            csv_data += ",False," + '"' + output.group(1).replace('"', "'") + '"'
        else:
            csv_data += ",False,EMPTY"

    # Year,Accounts,Verified,Locked,NoPost,NoFollowers,NoFollowing,L5Posts,L100Posts,L5Following,L100Following,L5Followers,L100Followers,L50Likes,LastRT\
    # Account | Date, Verified, Locked, NoPosts, NoFollowers, NoFollowing, NoLikes, LastRT
    return [csv_data, x_date, x_verified, x_locked, x_posts, x_followers, x_following, x_likes, x_last_rt]

# Create Backup
if(args.b):
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y-%H-%M-%S")
    os.mkdir("backup/" + timestampStr)

    shutil.copy2("./acc_list.txt", "./backup/" + timestampStr + "/" + "acc_list.txt")
    shutil.copy2("./not_found.txt", "./backup/" + timestampStr + "/" + "not_found.txt")
    shutil.copy2("./processed.txt", "./backup/" + timestampStr + "/" + "processed.txt")
    shutil.copy2("./suspended.txt", "./backup/" + timestampStr + "/" + "suspended.txt")
    shutil.copy2("./summary_data.csv", "./backup/" + timestampStr + "/" + "summary_data.csv")
    shutil.copy2("./summary_data_per_year.csv", "./backup/" + timestampStr + "/" + "summary_data_per_year.csv")
    shutil.copytree("./data", "./backup/" + timestampStr + "/" + "data")

    print("Backup is created: ./backup/" + timestampStr)
    exit()

if(args.c):
    print("\nAre you sure you want to delete all files and start from the beginning?")
    answer = input("Enter yes or no: ")
    if answer == "yes":
        try:
            os.remove("./acc_list.txt")
        except:
            pass
        try:
            os.remove("./suspended.txt")
        except:
            pass
        try:
            os.remove("./processed.txt")
        except:
            pass
        try:
            os.remove("./not_found.txt")
        except:
            pass
        try:
            os.remove("./summary_data.csv")
        except:
            pass
        try:
            os.remove("./summary_data_per_year.csv")
        except:
            pass
        try:
            for i in os.listdir("./data"):
                os.remove("./data/" + i)
            os.rmdir("./data")
        except Exception as e:
            print(str(e))
            pass
        print("All files are deleted. You will have fresh start :)")
        exit()

# Check files
if not os.path.exists("./acc_list.txt") or os.stat("./acc_list.txt").st_size == 0:
    with open("./acc_list.txt", mode='a'): pass
    print("\n> Please enter Twitter account names into acc_list.txt file, separated by new line.\n")
    exit()

if not os.path.exists("./suspended.txt"):
    with open("./suspended.txt", mode='a'): pass

if not os.path.exists("processed.txt"):
    with open("processed.txt", mode='a'): pass

if not os.path.exists("not_found.txt"):
    with open("not_found.txt", mode='a'): pass

if not os.path.exists("./data"):
    os.mkdir("./data")

if not os.path.exists("./backup"):
    os.mkdir("./backup")

if not os.path.exists("summary_data.csv"):
    with open("summary_data.csv", "a") as myfile:
        myfile.write("Account,FullName,RegDate,Verified,Locked,Followers,Following,Posts,Likes,IsRT,LatestPost\n")
    myfile.close()

if not os.path.exists("summary_data_per_year.csv"):
    with open("summary_data_per_year.csv", "a") as myfile:
        myfile.write("Year,Accounts,Verified,Locked,NoPost,NoFollowers,NoFollowing,L5Posts,L100Posts,L5Following,L100Following,L5Followers,L100Followers,L50Likes,LastRT\n")
    myfile.close()

print("""
> You are running getTwitterAccountDetailsTxt.py script.
> This script will try to download Twitter account data, from the account list file: ./acc_list.txt. 
> And it will create summary in files: summary_data*.csv, which you can open with Office applications.
""")

# Load accounts list
txt_file = open("./acc_list.txt", "r")
screen_name_list = txt_file.readlines()

if (args.i):
    screen_name_list_p = []
else:
    txt_file_p = open("./processed.txt", "r")
    screen_name_list_p = txt_file_p.readlines()

# Authenticate to Twitter
auth = tweepy.OAuthHandler(api_key, api_secrets)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

try:
    api.verify_credentials()
    print('\n> Successful Authentication to Twitter API.')
except:
    print('\n> Failed authentication to Twitter API. Check your settings.')
    exit()

print("""
================================================.
     .-.   .-.     .--.                         |
    | 00| | 00|   / _.-' .-.   .-.  .-.    .-.  |
    | --| | --|   \  '-. '-'   '-'  '-'    '-'  |
    '^^^' '^^^'    '--'                         |
===============.       .================.  .-.  |
               |       |                |  '-'  |

> START WITH DATA COLLECTION:
""")

csv_data = ""
cvs_data_per_year = {}
for acc in screen_name_list:
    acc = acc.strip()

    if (None != acc and acc != "" and acc + "\n" not in screen_name_list_p):
        try:
            user = api.get_user(screen_name=acc)
            # print(user._json)

            #TODO: Bug, Case
            with open("data/"+acc+".txt", "w") as myfile:
                myfile.write(simplejson.dumps(user._json, indent=4, sort_keys=True))
            myfile.close()

            # TODO: Bug, Case
            if(args.r):
                with open("data/" + acc + "_raw.txt", "w") as myfile:
                    myfile.write(str(user._json))
                myfile.close()

            # Prepare CSV 1
            csv_data_temp = make_csv(acc, str(user._json))
            csv_data += csv_data_temp[0] + "\n"

            # Prepare CSV 2
            if csv_data_temp[1] not in cvs_data_per_year:
                cvs_data_per_year.update({csv_data_temp[1]: {"accounts": 0, "verified": 0, "locked": 0, "nopost": 0,
                                                             "nofollowers": 0, "nofollowing": 0, "l5posts": 0,
                                                             "l100posts": 0, "l5following": 0, "l100following": 0,
                                                             "l5followers": 0, "l100followers": 0, "l50likes": 0,
                                                             "lastrt": 0}})

            # Year,Accounts,Verified,Locked,NoPost,NoFollowers,NoFollowing,L5Posts,L100Posts,L5Following,L100Following,L5Followers,L100Followers,L50Likes,LastRT
            # return [csv_data, x_date, x_verified, x_locked, x_posts, x_followers, x_following, x_likes, x_last_rt]
            x_date = csv_data_temp[1]
            x_verified = int(csv_data_temp[2])
            x_locked = int(csv_data_temp[3])
            x_posts = int(csv_data_temp[4])
            x_followers = int(csv_data_temp[5])
            x_following = int(csv_data_temp[6])
            x_likes = int(csv_data_temp[7])
            x_last_rt = int(csv_data_temp[8])

            cvs_data_per_year[x_date]["accounts"] += 1
            if x_verified == 1:
                cvs_data_per_year[x_date]["verified"] += 1
            if x_locked == 1:
                cvs_data_per_year[x_date]["locked"] += 1
            if x_posts == 0:
                cvs_data_per_year[x_date]["nopost"] += 1
            if x_posts < 5:
                cvs_data_per_year[x_date]["l5posts"] += 1
            if x_posts < 100:
                cvs_data_per_year[x_date]["l100posts"] += 1
            if x_followers == 0:
                cvs_data_per_year[x_date]["nofollowers"] += 1
            if x_followers < 5:
                cvs_data_per_year[x_date]["l5followers"] += 1
            if x_followers < 100:
                cvs_data_per_year[x_date]["l100followers"] += 1
            if x_following == 0:
                cvs_data_per_year[x_date]["nofollowing"] += 1
            if x_following < 5:
                cvs_data_per_year[x_date]["l5following"] += 1
            if x_following < 100:
                cvs_data_per_year[x_date]["l100following"] += 1
            if x_likes < 50:
                cvs_data_per_year[x_date]["l50likes"] += 1
            if x_last_rt == 1:
                cvs_data_per_year[x_date]["lastrt"] += 1

            with open("processed.txt", "a") as myfile:
                myfile.write(str(acc) + "\n")
            myfile.close()

            print("New record inserted: ", acc)
        except Exception as e:
            print("---")
            print(acc, str(e))
            if ("user not found" in str(e).lower()):
                # If we detect not found / deleted account it will be recorded in this file
                # TODO: Remove duplicates.
                with open("not_found.txt", "a") as myfile:
                    myfile.write(acc + "\n")
                pass
            elif ("suspended" in str(e).lower()):
                # If we detect suspended account it will be recorded in this file
                # TODO: Remove duplicates.
                with open("suspended.txt", "a") as myfile:
                    myfile.write(acc + "\n")
                pass
            else:
                print("> Unhandled exception, please take screenshot (mask sensitive data), and contact the author: ivanm@security-net.biz.")
                exception_type, exception_object, exception_traceback = sys.exc_info()
                filename = exception_traceback.tb_frame.f_code.co_filename
                line_number = exception_traceback.tb_lineno
                print("> Exception type: ", exception_type)
                print("> File name: ", filename)
                print("> Line number: ", line_number)
                print("---")
                exit()
            print("---")

        # This value is sleep time between each request, you can put smaller value but watch about API limitations
        time.sleep(float(args.s))
    else:
        print("Skip: ", acc)

# Create summary_data.csv
# TODO: Save on every 100
with open("summary_data.csv", "a") as myfile:
    myfile.write(csv_data)
myfile.close()

# Create summary_data_per_year.csv
# print(simplejson.dumps(cvs_data_per_year, indent=4, sort_keys=True))
# Year,Accounts,Verified,Locked,NoPost,NoFollowers,NoFollowing,L5Posts,L100Posts,L5Following,L100Following,L5Followers,L100Followers,L50Likes,LastRT
# TODO: Save on every 100
t_accounts = 0
t_verified = 0
t_locked = 0
t_nopost = 0
t_nofollowers = 0
t_nofollowing = 0
t_l5posts = 0
t_l100posts = 0
t_l5following = 0
t_l100following = 0
t_l5followers = 0
t_l100followers = 0
t_l50likes = 0
t_lastrt = 0
with open("summary_data_per_year.csv", "a") as myfile2:
    for x in sorted(cvs_data_per_year):
        # TODO: Automatic Loop Concat
        t_accounts += cvs_data_per_year[x]["accounts"]
        t_verified += cvs_data_per_year[x]["verified"]
        t_locked += cvs_data_per_year[x]["locked"]
        t_nopost += cvs_data_per_year[x]["nopost"]
        t_nofollowers += cvs_data_per_year[x]["nofollowers"]
        t_nofollowing += cvs_data_per_year[x]["nofollowing"]
        t_l5posts += cvs_data_per_year[x]["l5posts"]
        t_l100posts += cvs_data_per_year[x]["l100posts"]
        t_l5following += cvs_data_per_year[x]["l5following"]
        t_l100following += cvs_data_per_year[x]["l100following"]
        t_l5followers += cvs_data_per_year[x]["l5followers"]
        t_l100followers += cvs_data_per_year[x]["l100followers"]
        t_l50likes += cvs_data_per_year[x]["l50likes"]
        t_lastrt += cvs_data_per_year[x]["lastrt"]

        myfile2.write(str(x)+","+str(cvs_data_per_year[x]["accounts"])+","+str(cvs_data_per_year[x]["verified"])+","+str(
            cvs_data_per_year[x]["locked"])+","+str(cvs_data_per_year[x]["nopost"])+","+str(
            cvs_data_per_year[x]["nofollowers"])+","+str(cvs_data_per_year[x]["nofollowing"])+","+str(
            cvs_data_per_year[x]["l5posts"])+","+str(cvs_data_per_year[x]["l100posts"])+","+str(
            cvs_data_per_year[x]["l5following"])+","+str(cvs_data_per_year[x]["l100following"])+","+str(
            cvs_data_per_year[x]["l5followers"])+","+str(cvs_data_per_year[x]["l100followers"])+","+str(
            cvs_data_per_year[x]["l50likes"])+","+str(cvs_data_per_year[x]["lastrt"])+"\n")

    myfile2.write("Total," + str(t_accounts) + "," + str(t_verified) + "," + str(t_locked) + "," + str(t_nopost) + "," + str(t_nofollowers) + "," + str(t_nofollowing) + "," + str(t_l5posts) + "," + str(t_l100posts) + "," + str(t_l5following) + "," + str(t_l100following) + "," + str(t_l5followers) + "," + str(t_l100followers) + "," + str(t_l50likes) + "," + str(t_lastrt) + "\n")
myfile2.close()


print("\nThat's all folks!")

print("""
> In file ./suspended.txt you can find suspended accounts.
> In file ./not_found.txt you can find deleted accounts.
> You can open ./summary_data*.csv file with Office applications. 
> All other accounts data is in ./data/ folder as JSON.
""")

