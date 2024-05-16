from dotenv import load_dotenv
import os
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

load_dotenv()

MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_API_SERVER = os.getenv("MAILCHIMP_API_SERVER")
MAILCHIMP_AUDIENCE_ID = os.getenv("MAILCHIMP_AUDIENCE_ID")

# Set up Mailchimp API client
client = MailchimpMarketing.Client()
client.set_config({"api_key": MAILCHIMP_API_KEY, "server": MAILCHIMP_API_SERVER})

# Create a new campaign
try:
    response = client.campaigns.create(
        {
            "type": "regular",
            "recipients": {"list_id": MAILCHIMP_AUDIENCE_ID},
            "settings": {
                "subject_line": "Your 10 minute climate digest",
                "from_name": "10MinClimate",
                "reply_to": "info@10minclimate.org",
            },
        }
    )
    campaign_id = response["id"]

    # Set campaign data (email body)
    content_data = {
        "html": "<p>The FitnessGram™ Pacer Test is a multistage aerobic capacity test that progressively gets more difficult as it continues. The 20 meter pacer test will begin in 30 seconds. Line up at the start. The running speed starts slowly, but gets faster each minute after you hear this signal. [beep] A single lap should be completed each time you hear this sound. [ding] Remember to run in a straight line, and run as long as possible. The second time you fail to complete a lap before the sound, your test is over. The test will begin on the word start. On your mark, get ready, start.</p>"
    }

    client.campaigns.set_content(campaign_id, body=content_data)

    # Send the campaign
    client.campaigns.send(campaign_id)
    print("Campaign sent successfully!")

except ApiClientError as error:
    print("Error creating/sending campaign:", error.text)
