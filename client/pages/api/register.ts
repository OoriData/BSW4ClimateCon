// import dotenv from 'dotenv';

import axios from "axios";

export default async function handler(req: any, res: any) {
    // dotenv.config();
   if (req.method === 'POST') {
    try {
        const { email } = req.body;
        const response = await addSubscriberToList(email);
        res.status(200).json({ success: true });
    } catch (error) {
        res.status(500).json({ error: 'Internal Server Error' });
    }
  } else {
    res.status(405).json({ error: 'Method Not Allowed' });
  }
}

async function addSubscriberToList(email: string) {
        // Generate params for api call
        const apiKey = process.env.MAILCHIMP_API_KEY;
        const datacenter = process.env.MAILCHIMP_API_SERVER;
        const audienceId = process.env.MAILCHIMP_AUDIENCE_ID;
        const url = `https://${datacenter}.api.mailchimp.com/3.0/lists/${audienceId}/members`;
        const body = JSON.stringify({
            'email_address': email,
            'status': 'subscribed',
        });
        const base64ApiKey = Buffer.from(`anystring:${apiKey}`).toString('base64');
        const headers = {
            "Content-Type": "application/json",
            Authorization: `Basic ${base64ApiKey}`,
        }

        await axios.post(url, body, { headers });
}