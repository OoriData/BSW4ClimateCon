import webbrowser
import tempfile

from utiloori.ansi_color import ansi_color

import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

from config import EMAIL_TEMPLATE, MAILCHIMP_API_KEY, MAILCHIMP_API_SERVER, MAILCHIMP_AUDIENCE_ID


# Set up Mailchimp API client
client = MailchimpMarketing.Client()
client.set_config({'api_key': MAILCHIMP_API_KEY, 'server': MAILCHIMP_API_SERVER})


def create_campaign(url, summary, action_items):
    print(ansi_color('\nCreating email campaign...', 'green'))
    try:
        response = client.campaigns.create(
            {
                'type': 'regular',
                'recipients': {'list_id': MAILCHIMP_AUDIENCE_ID},
                'settings': {
                    'subject_line': 'Your 10 minute climate digest',
                    'from_name': '10MinClimate',
                    'reply_to': 'info@10minclimate.org',
                },
            }
        )
        campaign_id = response['id']

        html_content = EMAIL_TEMPLATE.format(url=url, summary=summary, action_items=action_items)

        client.campaigns.set_content(campaign_id, body={'html': html_content})

        # Send the campaign
        client.campaigns.send(campaign_id)
        print(ansi_color('Campaign sent successfully!', 'green'))

    except ApiClientError as error:
        print(ansi_color(f'Error creating/sending campaign: {error.text}', 'red'))


def display_html_string(html_string):
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as temp_file:
        temp_file.write(html_string)
        temp_file_path = temp_file.name
    
    # Open the temporary HTML file in the default web browser
    print(ansi_color('Email HTML generated successfully! Opening in browser...', 'green'))
    webbrowser.open_new_tab('file://' + temp_file_path)


def test_campaign(url, summary, action_items):
    print(ansi_color('\nCreating test email...', 'green'))
    html_content = EMAIL_TEMPLATE.format(url=url, summary=summary, action_items=action_items)
    display_html_string(html_content)
    