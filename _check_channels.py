from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
load_dotenv()

yt = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))

# Handle channel
res1 = yt.channels().list(part='snippet', forHandle='@sakuraUM-777').execute()
for i in res1.get('items', []):
    print(f"@sakuraUM-777 -> {i['snippet']['title']}")

# ID channels
ids = ['UC0Nl4j7fv7J7PI4Sf55hXiA', 'UC5laEaxR5O1Fsx1VtcJfw4A', 'UCOE8QbYgjEKV_ikBuoI3pkw']
res2 = yt.channels().list(part='snippet', id=','.join(ids)).execute()
for i in res2.get('items', []):
    print(f"{i['id']} -> {i['snippet']['title']}")
