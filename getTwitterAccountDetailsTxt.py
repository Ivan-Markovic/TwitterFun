# Contact: ivanm@security-net.biz
# Interesting analysis done with similar scripts:
# 1. https://security-net.biz/shared/bots/Analiza_neocekivanog_Twitter_statusa_IM_2022.pdf
# 2. https://security-net.biz/shared/bots/Analiza_neocekivanog_Twitter_statusa_IM_2022_v2.pdf

# Imports
import argparse
import re
import simplejson as simplejson
import tweepy
import time
import os

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
args = parser.parse_args()

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
            os.remove("./summary_data.csv")
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

print("")
print("// This (getTwitterAccountDetailsTxt.py) script will try to download Twitter account data from the account list file: ./acc_list.txt")
print("// And it will create summary in file: summary_data.csv, which you can open with Office applications.")

def make_csv(acc_name, acc_data):
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
    else:
        csv_data += "," + "ERROR"
    # Is verified
    output = re.search('verified\': (.*?), \'statuses_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        if output.group(1) == 'True':
            csv_data += "," + "True"
        else:
            csv_data += "," + "False"
    else:
        csv_data += "," + "False"
    # Is protected
    output = re.search('protected\': (.*?), \'followers_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        if output.group(1) == 'True':
            csv_data += "," + "True"
        else:
            csv_data += "," + "False"
    else:
        csv_data += "," + "False"
    # Followers
    output = re.search('followers_count\': (.*?), \'friends_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
    else:
        csv_data += ",0"
    # Following
    output = re.search('friends_count\': (.*?), \'listed_count', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
    else:
        csv_data += ",0"
    # Posts
    output = re.search('statuses_count\': (.*?), \'lang', acc_data, flags=re.IGNORECASE)
    if output is not None:
        csv_data += "," + output.group(1)
    else:
        csv_data += ",0"
    return csv_data

# Check files
if not os.path.exists("./acc_list.txt") or os.stat("./acc_list.txt").st_size == 0:
    with open("./acc_list.txt", mode='a'): pass
    print("\n= ERROR: Please enter Twitter account names into acc_list.txt file, separated by new line.\n")
    exit()

if not os.path.exists("./suspended.txt"):
    with open("./suspended.txt", mode='a'): pass

if not os.path.exists("processed.txt"):
    with open("processed.txt", mode='a'): pass

if not os.path.exists("./data"):
    os.mkdir("./data")

if not os.path.exists("summary_data.csv"):
    with open("summary_data.csv", "a") as myfile:
        myfile.write("Account,FullName,RegDate,Verified,Locked,Followers,Following,Posts\n")
    myfile.close()

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
    print('\nSuccessful Authentication to Twitter API.')
except:
    print('\nFailed authentication to Twitter API. Check your settings.')
    exit()

print("""
================================================.
     .-.   .-.     .--.                         |
    | 00| | 00|   / _.-' .-.   .-.  .-.    .-.  |
    | --| | --|   \  '-. '-'   '-'  '-'    '-'  |
    '^^^' '^^^'    '--'                         |
===============.       .================.  .-.  |
               |       |                |  '-'  |

// START WITH DATA COLLECTION
""")

csv_data = ""
for acc in screen_name_list:
    acc = acc.strip()

    if (None != acc and acc != "" and acc + "\n" not in screen_name_list_p):
        try:
            user = api.get_user(screen_name=acc)
            # print(user._json)

            with open("data/"+acc+".txt", "w") as myfile:
                myfile.write(simplejson.dumps(user._json, indent=4, sort_keys=True))
            myfile.close()

            csv_data += make_csv(acc, str(user._json)) + "\n"

            with open("processed.txt", "a") as myfile:
                myfile.write(str(acc) + "\n")
            myfile.close()

            print("New record inserted: ", acc)
        except Exception as e:
            print(" --- ")
            print(acc, str(e))
            print(" --- ")
            if ("user not found" in str(e).lower() or "duplicate" in str(e).lower()):
                pass
            elif ("suspended" in str(e).lower()): # If we detect suspended account it will be recorded in this file
                with open("suspended.txt", "a") as myfile:
                    myfile.write(acc + "\n")
                pass
            else:
                exit()

        # This value is sleep time between each request, you can put smaller value but watch about API limitations
        time.sleep(1)
    else:
        print("Skip: ", acc)


with open("summary_data.csv", "a") as myfile:
    myfile.write(csv_data)
myfile.close()

print("\nThat's all folks!")

print("""
-> In file ./suspended.txt you can find suspended accounts. 
-> You can open ./summary_data.csv file with Office applications. 
-> All other accounts data is in ./data/ folder as json.
""")