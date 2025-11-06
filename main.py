from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
import os
import requests
import json

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# -------------------- ZOHO MAIL API CONFIG --------------------
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
BUSINESS_EMAIL = "bristoeventcaterers@bristoevents.co.ke"
ZOHO_API_BASE = "https://mail.zoho.com/api/accounts"

def get_access_token():
    """Fetch a short-lived access token using refresh token."""
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    res = requests.post(url, data=data)
    res.raise_for_status()
    token_data = res.json()
    return token_data.get("access_token")

def get_primary_account_id(token):
    """Fetch the user's primary Zoho Mail account ID."""
    url = ZOHO_API_BASE
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    accounts = response.json().get("data", [])
    if not accounts:
        raise Exception("No Zoho Mail accounts found.")
    # Usually the first account is the primary
    return accounts[0].get("accountId")

def send_email_via_zoho(to_email, subject, content):
    """Send email using Zoho Mail API."""
    token = get_access_token()
    account_id = get_primary_account_id(token)  # You already have this helper

    url = f"{ZOHO_API_BASE}/{account_id}/messages"
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json"
    }

    # ✅ Here’s the important part:
    data = {
        "fromAddress": BUSINESS_EMAIL,
        "toAddress": to_email,
        "subject": subject,
        "mailFormat": "html",   # tells Zoho to render it as HTML
        "content": content      # directly pass HTML text (NOT nested in JSON)
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        print("Zoho Mail API error:", response.text)
    return response.json()


# ----------------------- Booking Functions -----------------------
def format_booking_email(data, booking_id):
    event_type = data.get("eventType")
    if event_type == "other":
        event_type = data.get("customEventType", "Other")

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #b22222; text-align:center;">🎉 New Booking Received</h2>
            <hr style="border: none; height: 2px; background-color: #b22222; width: 80px; margin: 10px auto 20px auto;">
            
            <p><strong>Booking ID:</strong> {booking_id}</p>
            <p><strong>Name:</strong> {data.get('name')}</p>
            <p><strong>Phone:</strong> <a href="tel:{data.get('phone')}" style="color:#b22222; text-decoration:none;">{data.get('phone')}</a></p>
            <p><strong>Email:</strong> <a href="mailto:{data.get('email')}" style="color:#b22222; text-decoration:none;">{data.get('email')}</a></p>

            <h3 style="color:#b22222; margin-top:25px;">Booking Details</h3>
            <table style="width:100%; border-collapse: collapse;">
                <tr><td style="padding:8px; border-bottom:1px solid #eee;"><strong>Event Type:</strong></td><td>{event_type}</td></tr>
                <tr><td style="padding:8px; border-bottom:1px solid #eee;"><strong>Event Date:</strong></td><td>{data.get('eventDate')}</td></tr>
                <tr><td style="padding:8px; border-bottom:1px solid #eee;"><strong>Guests:</strong></td><td>{data.get('guests')}</td></tr>
                <tr><td style="padding:8px; border-bottom:1px solid #eee;"><strong>Venue Location:</strong></td><td>{data.get('venueLocation')}</td></tr>
                <tr><td style="padding:8px; border-bottom:1px solid #eee;"><strong>Budget:</strong></td><td>{data.get('budget')}</td></tr>
                <tr><td style="padding:8px;"><strong>Special Requests:</strong></td><td>{data.get('specialRequests')}</td></tr>
            </table>

            <p style="margin-top:25px;">📞 <strong>Need to reach the client quickly?</strong><br>
            Call them directly at <a href="tel:{data.get('phone')}" style="color:#b22222; font-weight:bold;">{data.get('phone')}</a>.</p>

            <hr style="margin:25px 0; border:none; border-top:1px solid #eee;">
            <p style="font-size:13px; color:#888; text-align:center;">
                Bristo Event Caterers | <a href="tel:+254710302253" style="color:#b22222;">+254 710 302 253</a><br>
                <a href="https://www.bristoevents.co.ke" style="color:#b22222;">www.bristoevents.co.ke</a>
            </p>
        </div>
    </body>
    </html>
    """


def format_confirmation_email(data, booking_id):
    event_type = data.get("eventType")
    if event_type == "other":
        event_type = data.get("customEventType", "Other")

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #b22222;">Booking Confirmation - Bristo Event Caterers</h2>

        <p>Hi <strong>{data.get('name')}</strong>,</p>

        <p>Thank you for booking with <strong>Bristo Event Caterers</strong>.</p>

        <p>Your Booking ID is <strong>{booking_id}</strong>.</p>

        <h3>Here are your booking details:</h3>
        <ul>
            <li><strong>Event Type:</strong> {event_type}</li>
            <li><strong>Event Date:</strong> {data.get('eventDate')}</li>
            <li><strong>Guests:</strong> {data.get('guests')}</li>
            <li><strong>Venue Location:</strong> {data.get('venueLocation')}</li>
            <li><strong>Budget:</strong> {data.get('budget')}</li>
            <li><strong>Special Requests:</strong> {data.get('specialRequests')}</li>
        </ul>

        <p>Our team will contact you shortly to confirm your booking.</p>
        <p>If you need urgent assistance, please call us directly at 
        <a href="tel:+254710302253" style="color:#b22222; text-decoration:none; font-weight:bold;">+254 710 302 253</a>.</p>

        <p>Best regards,<br>
        <strong>Bristo Event Caterers Team</strong></p>
    </body>
    </html>
    """


@app.route("/api/book", methods=["POST"])
def book_service():
    data = request.get_json() or request.form.to_dict()
    try:
        booking_id = "BK" + str(uuid.uuid4())[:8].upper()

        # Send to business
        send_email_via_zoho(
            BUSINESS_EMAIL,
            f"New Booking from {data.get('name')} (ID: {booking_id})",
            format_booking_email(data, booking_id)
        )

        # Send confirmation to client
        user_email = data.get("email")
        if user_email:
            send_email_via_zoho(
                user_email,
                "Booking Confirmation - Bristo Event Caterers",
                format_confirmation_email(data, booking_id)
            )

        return jsonify({"message": "Booking received and emails sent", "booking_id": booking_id}), 200

    except Exception as e:
        print("Booking Error:", e)
        return jsonify({"error": str(e)}), 500

# ----------------------- Contact Functions -----------------------
# ----------------------- Contact Functions -----------------------

def format_contact_email(data):
    """HTML email sent to the business inbox."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #b22222;">New Contact Form Message</h2>

        <p><strong>Full Name:</strong> {data.get('name')}</p>
        <p><strong>Email:</strong> {data.get('email')}</p>
        <p><strong>Phone Number:</strong> {data.get('phone')}</p>
        <p><strong>Preferred Contact Method:</strong> {data.get('preferredContact')}</p>
        <p><strong>Subject:</strong> {data.get('subject')}</p>
        <p><strong>Message:</strong><br>{data.get('message')}</p>

        <hr>
        <p style="font-size: 14px; color: #777;">
            Sent via the Bristo Event Caterers website contact form.
        </p>
    </body>
    </html>
    """


def format_contact_confirmation_email(data):
    """HTML confirmation email sent to the client."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #b22222;">We Received Your Message - Bristo Event Caterers</h2>

        <p>Hi <strong>{data.get('name')}</strong>,</p>

        <p>Thank you for reaching out to <strong>Bristo Event Caterers</strong>.</p>
        <p>We’ve received your message and will get back to you as soon as possible.</p>

        <h3>Your Message Summary:</h3>
        <ul>
            <li><strong>Subject:</strong> {data.get('subject')}</li>
            <li><strong>Preferred Contact Method:</strong> {data.get('preferredContact')}</li>
            <li><strong>Message:</strong> {data.get('message')}</li>
        </ul>

        <p>If you need urgent assistance, please call us directly at 
        <a href="tel:+254710302253" style="color:#b22222; text-decoration:none; font-weight:bold;">+254 710 302 253</a>.</p>

        <p>Best regards,<br>
        <strong>Bristo Event Caterers Team</strong></p>
    </body>
    </html>
    """


@app.route("/api/contact", methods=["POST"])
def contact_us():
    data = request.get_json() or request.form.to_dict()
    try:
        # Send message to business
        send_email_via_zoho(
            BUSINESS_EMAIL,
            f"Contact Form Message - {data.get('subject')}",
            format_contact_email(data)
        )

        # Send confirmation to client
        user_email = data.get("email")
        if user_email:
            send_email_via_zoho(
                user_email,
                "We Received Your Message - Bristo Event Caterers",
                format_contact_confirmation_email(data)
            )

        return jsonify({"message": "Message sent successfully"}), 200

    except Exception as e:
        print("Contact Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
