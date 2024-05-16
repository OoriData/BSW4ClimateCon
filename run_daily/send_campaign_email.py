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


def create_campaign(url, summary, action_items):
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
        file_path = "email_template.html"

        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()
            html_content = html_content.format(url=url, summary=summary, action_items=action_items)

        client.campaigns.set_content(campaign_id, body={"html": html_content})

        # Send the campaign
        client.campaigns.send(campaign_id)
        print("Campaign sent successfully!")

    except ApiClientError as error:
        print("Error creating/sending campaign:", error.text)
