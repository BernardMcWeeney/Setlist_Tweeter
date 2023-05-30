import json
import requests
import tweepy
import re
from decouple import config
import os
from datetime import datetime, timedelta

TWITTER_MAX_CHAR = 280
TEST_MODE = False

# Set up Twitter API authentication
bearer_token = config('bearer_token')
consumer_key = config('consumer_key')
consumer_secret = config('consumer_secret')
access_token = config('access_token')
access_token_secret = config('access_token_secret')

client = tweepy.Client(bearer_token,consumer_key,consumer_secret,access_token,access_token_secret)

# Set the API key
API_KEY = config('api_key')

# Setlist.fm API endpoint
URL = "https://api.setlist.fm/rest/1.0/"

# Function to retrieve all setlists for The Cure
def get_the_cure_setlists():
    headers = {
        "Accept": "application/json",
        "x-api-key": API_KEY
    }

    # Send a GET request to search for The Cure's setlists
    response = requests.get(URL + "artist/69ee3720-a7cb-4402-b48d-a02c366f2bcf/setlists", headers=headers)

    if response.status_code == 200:
        #print(response.json())  # print the response to check its structure
        return response.json()
    else:
        return None

# Function to tweet
def tweet(message, reply_to=None):
    if len(message) <= TWITTER_MAX_CHAR:
        if TEST_MODE:
            print(message)
        else:
            response = client.create_tweet(text=message, in_reply_to_tweet_id=reply_to)
            return response.data['id']
    else:
        split_position = message.rfind('\n', 0, TWITTER_MAX_CHAR)
        if split_position == -1:  # no newline character found
            split_position = message.rfind(' ', 0, TWITTER_MAX_CHAR)
        first_part = message[:split_position]
        remaining_part = message[split_position:].lstrip()
        if TEST_MODE:
            print(first_part)
            reply_to = tweet(remaining_part, reply_to)
        else:
            response = client.create_tweet(text=first_part, in_reply_to_tweet_id=reply_to)
            reply_to = response.data['id']
            tweet(remaining_part, reply_to)
    return reply_to


# Function to parse and tweet setlists
def parse_and_tweet_setlists(setlists):
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    last_tweet_id = None

    for setlist in setlists:
        event_date = datetime.strptime(setlist['eventDate'], "%d-%m-%Y")
        venue = setlist['venue']['name']
        city = setlist['venue']['city']['name']
        country = setlist['venue']['city']['country']['name']
        tour = setlist['tour']['name']
        
        if event_date.date() == yesterday.date():
            message = f"Yesterday's ({yesterday.date()}), The Cure's {tour} gig at the {venue}, {city}, {country} setlist:\n\n"
            for section in setlist['sets']['set']:
                if 'encore' in section:
                    message += f"Encore {section['encore']}:\n"
                else:
                    message += "Main Set:\n"
                for song in section['song']:
                    song_name = song['name']
                    song_info = song.get('info', '')
                    if song_info:
                        message += f"{song_name} -- ({song_info})\n"
                    else:
                        message += f"{song_name}\n"
                message += "\n"
            message += f"Community Sourced - SetlistFm\n"
            last_setlist_url = setlist['url']
            message += f"{last_setlist_url}\n"
            tourhashtag = tour.replace(" ", "")
            venuehashtag = venue.replace(" ", "")
            message += f"#TheCure #RobertSmith #{tourhashtag} #{venuehashtag} #Cureation"
            
            last_tweet_id = tweet(message, last_tweet_id)

# Main function
def main():
    setlists_response = get_the_cure_setlists()
    if setlists_response:
        setlists = setlists_response['setlist']  # Here's the change
        parse_and_tweet_setlists(setlists)
    else:
        print("Failed to fetch setlists.")

if __name__ == "__main__":
    main()
