from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

BUSINESS_EMAIL = 'bristoeventcaterers@gmail.com'  # your business email

# ----------------------- Booking Functions -----------------------

def format_booking_email(data, booking_id):
    # if eventType == "other", use customEventType
    event_type = data.get("eventType")
    if event_type == "other":
        event_type = data.get("customEventType", "Other")

    return f"""
New Booking Received:

Booking ID: {booking_id}
Name: {data.get('name')}
Phone: {data.get('phone')}
Email: {data.get('email')}
Event Type: {event_type}
Event Date: {data.get('eventDate')}
Guests: {data.get('guests')}
Venue Location: {data.get('venueLocation')}
Budget: {data.get('budget')}
Special Requests: {data.get('specialRequests')}
"""


def format_confirmation_email(data, booking_id):
    event_type = data.get("eventType")
    if event_type == "other":
        event_type = data.get("customEventType", "Other")

    return f"""
Hi {data.get('name')},

Thank you for booking with Bristo Event Caterers.

Your Booking ID is {booking_id}.

Here are your booking details:
- Event Type: {event_type}
- Event Date: {data.get('eventDate')}
- Guests: {data.get('guests')}
- Venue Location: {data.get('venueLocation')}
- Budget: {data.get('budget')}
- Special Requests: {data.get('specialRequests')}

Our team will contact you shortly to confirm the booking and schedule.

Best regards,  
Bristo Event Caterers Team
"""


@app.route('/api/book', methods=['POST'])
def book_service():
    # works for both form-data and JSON
    data = request.get_json() or request.form.to_dict()
    try:
        booking_id = "BK" + str(uuid.uuid4())[:8].upper()

        # Send to business email
        msg_to_business = Message(
            subject=f"New Booking from {data.get('name')} (ID: {booking_id})",
            recipients=[BUSINESS_EMAIL],
            body=format_booking_email(data, booking_id)
        )
        mail.send(msg_to_business)

        # Confirmation to user
        user_email = data.get('email')
        if user_email:
            msg_to_user = Message(
                subject="Booking Confirmation - Bristo Event Caterers",
                recipients=[user_email],
                body=format_confirmation_email(data, booking_id)
            )
            mail.send(msg_to_user)

        return jsonify({
            "message": "Booking received and emails sent",
            "booking_id": booking_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------- Contact Functions (unchanged) -----------------------
@app.route('/api/contact', methods=['POST'])
def contact_us():
    data = request.get_json() or request.form.to_dict()
    try:
        msg_to_business = Message(
            subject=f"Contact Form Message - {data.get('subject')}",
            recipients=[BUSINESS_EMAIL],
            body=f"""
New Contact Message Received:

Full Name: {data.get('name')}
Email: {data.get('email')}
Phone Number: {data.get('phone')}
Preferred Contact Method: {data.get('preferredContact')}
Subject: {data.get('subject')}
Message:
{data.get('message')}
"""
        )
        mail.send(msg_to_business)

        user_email = data.get('email')
        if user_email:
            msg_to_user = Message(
                subject="We Received Your Message - Bristo Event Caterers",
                recipients=[user_email],
                body=f"""
Hi {data.get('name')},

Thank you for reaching out to Bristo Event Caterers. 

We have received your message and will get back to you shortly.

Here’s a summary of your message:
- Subject: {data.get('subject')}
- Message: {data.get('message')}
- Preferred Contact Method: {data.get('preferredContact')}

If you need to speak to us urgently, call us directly at +254 710 302 253.

Best regards,  
Bristo Event Caterers Team
"""
            )
            mail.send(msg_to_user)

        return jsonify({"message": "Message sent successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
