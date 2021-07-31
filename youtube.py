'''
Asks YouTube about the recent activity of a few channels and emails them to myself.
Author: Mateen Kasim (2021)
'''

# Generic
import os
import settings
import datetime
import base64

# YouTube
import googleapiclient.discovery
import googleapiclient.errors

# Gmail Auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


EMAIL_TEMPLATE = '''
<!DOCTYPE html>
<html>
	<head>
		<title>Monthly Rundown</title>
		<style>
			{html_style}
		</style>
	</head>
	<body>
		<div id="wrapper">
			<h1 id="banner">Your Monthly Rundown</h1>
			{html_inner}
		</div>
	</body>
</html>
'''
EMAIL_STYLE = '''
			#wrapper {
				height: auto;
				width: auto;
				text-align: center;
				font-family: 'Monaco';
				border: solid rgba(0, 0, 0, 0.2);
				background-color: #FFFEF9;
			}
			#banner {
				border-bottom: 1px solid #7293E5;
				display: inline-block;
				padding: 30px;
				width: 60%;
			}
			.activity {
				color: #0E1A36;
				margin: 0px 0px 30px 0px;
			}
			.activity-text {
				margin: 5px;
			}
			.activity-channel {
				color: #964A53 !important;
			}
			.activity-thumbnail {
				width: 60%;
			}
'''
EMAIL_INNER = '''
			<div class="activity">
				<h3 class="activity-text">{title}</h3>
				<a target="_blank" href="https://www.youtube.com/watch?v={video_id}">
					<img class="activity-thumbnail" src="https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg">
				</a>
				<p class="activity-text">
					New Video by 
					<strong>
						<a class="activity-channel" target="_blank" href="https://www.youtube.com/channel/{channel_id}">{channel_name}</a>
					</strong> on {date}
				</p>
			</div>
'''

def main():
	# Disable OAuthlib's HTTPS verification when running locally.
	# *DO NOT* leave this option enabled in production.
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

	creds = get_credentials()
	activity = get_activity()

	if creds and activity:
		send_email(creds, activity)

def get_credentials():

	creds = None
	if os.path.exists('.credentials'):
		creds = Credentials.from_authorized_user_file('.credentials', settings.SCOPES)
	# If there are no (valid) credentials available, let the user log in.
	try:
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					settings.CLIENT_SECRET, settings.SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open('.credentials', 'w') as token:
				token.write(creds.to_json())
	except Exception as e:
		print('Failed to generate credentials:', e)

	return creds
	

def get_activity():
	try:
		result = []
		today = datetime.datetime.today()
		# Last month calculation accounts for the fact that Jan is month 1, not month 0
		# i.e. can't do (today.month - 1) % 12
		last_month_first = datetime.datetime(today.year, (today.month - 2) % 12 + 1, 1).strftime("%Y-%m-%dT%H:%M:%SZ")
		youtube = googleapiclient.discovery.build(
			settings.API_SERVICE_NAME, settings.API_VERSION, developerKey=settings.YOUTUBE_API_KEY)

		# For each channel we want to see
		for channel_name in settings.CHANNELS:
			# Get the month's activity by the channel
			channel_activity_request = youtube.activities().list(
				part='snippet,contentDetails',
				channelId=settings.CHANNELS[channel_name],
				publishedAfter=last_month_first
			)
			channel_activity_response = channel_activity_request.execute()

			# For each item in activity list
			for item in channel_activity_response['items']:
				# If the activity was a video upload
				if item['snippet']['type'] == 'upload':
					# Save the info
					video_id = item['contentDetails']['upload']['videoId']
					date = datetime.datetime.strptime(item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%S%z").strftime("%D")
					vid = {
						'channel_name': channel_name, 
						'date': date, 
						'title': item["snippet"]["title"], 
						'video_id': video_id
						}
					result.append(vid)

		# Return list of activity info
		return sorted(result, key=lambda x : x['date'] if 'date' in x else 0)

	except Exception as error:
		print('Problem with YouTube API:', error)

def send_email(creds, activity):
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Monthly YouTube Update"
	msg['From'] = settings.EMAIL_USER
	msg['To'] = settings.EMAIL_USER

	text = ''
	html_inner = ''
	for a in activity:

		text += f'New video by {a["channel_name"]} on {a["date"]}: "{a["title"]}"\n\tLink: https://www.youtube.com/watch?v={a["video_id"]}\n'
		html_inner += EMAIL_INNER.format(channel_name=a['channel_name'], channel_id=settings.CHANNELS[a['channel_name']], \
					date=a['date'], title=a['title'], video_id=a['video_id'])

	html = EMAIL_TEMPLATE.format(html_style=EMAIL_STYLE, html_inner=html_inner)

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part1)
	msg.attach(part2)

	# Send message with Gmail API.
	service = build('gmail', 'v1', credentials=creds)
	msg_json = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}

	try:
		message = (service.users().messages().send(userId='me', body=msg_json).execute())
		return message
	except Exception as error:
		print('An error occurred: %s' % error)

if __name__ == "__main__":
	main()


