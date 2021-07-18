'''
Asks YouTube about the recent activity of a few channels and prints them.
Author: Mateen Kasim (2021)

'''

import os
import settings
import datetime
from pprint import pprint

import googleapiclient.discovery
import googleapiclient.errors

def main():
	# Disable OAuthlib's HTTPS verification when running locally.
	# *DO NOT* leave this option enabled in production.
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

	youtube = googleapiclient.discovery.build(
		settings.API_SERVICE_NAME, settings.API_VERSION, developerKey=settings.YOUTUBE_API_KEY)

	# For each channel we want to see
	for channel_name in settings.CHANNELS:
		# Get the week's activity by the channel
		channel_activity_request = youtube.activities().list(
			part='snippet,contentDetails',
			channelId=settings.CHANNELS[channel_name],
			publishedAfter=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
		)
		channel_activity_response = channel_activity_request.execute()

		# For each item in activity list
		for item in channel_activity_response['items']:
			# If the activity was a video upload
			if item['snippet']['type'] == 'upload':
				# Print the info! Maybe include thumbnails later?
				video_id = item['contentDetails']['upload']['videoId']

				print(f'New video by {channel_name}: "{item["snippet"]["title"]}"\n\tLink: https://www.youtube.com/watch?v={video_id}\n')

if __name__ == "__main__":
	main()