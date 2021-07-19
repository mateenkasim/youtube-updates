'''
Asks YouTube about the recent activity of a few channels and prints them.
Author: Mateen Kasim (2021)
'''

# Generic
import os
import settings
import datetime
from functools import reduce

# YouTube
import googleapiclient.discovery
import googleapiclient.errors

# Email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_TEMPLATE = '''
<html>
	<head>
		<style>
			{html_style}
		</style>
	</head>
	<body>
		<h1 id="banner">Your Weekly Rundown</h1>
		{html_inner}
	</body>
</html>
'''
EMAIL_STYLE = '''
			body {
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
				color: #964A53;
			}
			.activity-thumbnail {
				width: 50%;
			}
'''

def main():
	# Disable OAuthlib's HTTPS verification when running locally.
	# *DO NOT* leave this option enabled in production.
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

	activity = get_activity()
	send_email(activity)
	

def get_activity():
	result = []
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
				# Save the info
				video_id = item['contentDetails']['upload']['videoId']
				date = datetime.datetime.strptime(item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%S%z").strftime("%D")

				result.append([channel_name, date, item["snippet"]["title"], video_id])

	# Return list of activity info
	return result


def send_email(activity):

	# msg = MIMEMultipart('alternative')
	# msg['Subject'] = "Weekly Video Update"
	# msg['From'] = settings.EMAIL_USER
	# msg['To'] = settings.EMAIL_USER

	text = ''
	html_inner = ''
	for a in activity:
		channel_name = a[0]
		date = a[1]
		title = a[2]
		video_id = a[3]

		text += f'New video by {channel_name} on {date}: "{title}"\n\tLink: https://www.youtube.com/watch?v={video_id}\n'
		html_inner += '''
		<div class="activity">
			<h3 class="activity-text">{title}</h3>
			<a target="_blank" href="https://www.youtube.com/watch?v={video_id}">
				<img class="activity-thumbnail" src="https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg">
			</a>
			<p class="activity-text">New Video by <strong class="activity-channel">{channel_name}</strong> on {date}</p>
		</div>
		'''.format(channel_name=channel_name, date=date, title=title, video_id=video_id)

	html = EMAIL_TEMPLATE.format(html_style=EMAIL_STYLE, html_inner=html_inner)

	print(text)
	print(html)

	# # Record the MIME types of both parts - text/plain and text/html.
	# part1 = MIMEText(text, 'plain')
	# part2 = MIMEText(html, 'html')

	# # Attach parts into message container.
	# # According to RFC 2046, the last part of a multipart message, in this case
	# # the HTML message, is best and preferred.
	# msg.attach(part1)
	# msg.attach(part2)

	# # Send the message via local SMTP server.
	# s = smtplib.SMTP_SSL(settings.SMTP_EMAIL_HOST,465)
	# s.login(settings.EMAIL_USER, settings.EMAIL_PASS)
	# # sendmail function takes 3 arguments: sender's address, recipient's address
	# # and message to send - here it is sent as one string.
	# s.sendmail(settings.EMAIL_USER, settings.EMAIL_USER, msg.as_string())
	# s.quit()

if __name__ == "__main__":
	main()


