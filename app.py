import json
import re
import secrets
from functools import wraps
from pathlib import Path

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
from flask import Flask, jsonify, request
from flask_mail import Mail, Message

from config import get_settings
from scraper import Listing, scrape_canadian_internships, scrape_us_internships


app = Flask(__name__)
settings = get_settings()

# Configure Flask-Mail
app.config["MAIL_SERVER"] = settings.mail_server
app.config["MAIL_PORT"] = settings.mail_port
app.config["MAIL_USE_TLS"] = settings.mail_use_tls
app.config["MAIL_USERNAME"] = settings.mail_username
app.config["MAIL_PASSWORD"] = settings.mail_password

mail = Mail(app)

STATE_FILE = Path(__file__).parent / "state.json"


def require_api_key(f):
    """Decorator to require API key for protected endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("API-Key")
        if api_key != settings.api_key:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


DEFAULT_STATE = {
    "emails": {},
    "canadian_internships": {
        "company": "Genesys",
        "role": "Software Development Intern - Recording and QM",
        "location": "Toronto, ON",
        "apply_link": "https://genesys.wd1.myworkdayjobs.com/en-US/Genesys/job/Toronto-Flexible/Software-Development-Intern--Recording-and-QM--12-16mos-_JR109189",
        "date_posted": "Jan 9",
    },
    "us_internships": {
        "company": "Kinaxis",
        "role": "Intern/Co-op Software Developer - Core Algorithms",
        "location": "Ottawa, ON, Canada",
        "apply_link": "https://careers-kinaxis.icims.com/jobs/34146/job?mobile=true&needsRedirect=false&utm_source=Simplify&ref=Simplify",
        "date_posted": "0d",
    },
}


def load_state() -> dict:
    """Load state from JSON file, creating with defaults if not exists."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    # Create file with default state
    with open(STATE_FILE, "w") as f:
        json.dump(DEFAULT_STATE, f, indent=2)
    return DEFAULT_STATE.copy()


def save_state(state: dict) -> None:
    """Save state to JSON file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def find_new_listings(
    current_listings: list[Listing], stored_top: dict | None
) -> list[Listing]:
    """Find new listings by comparing with stored top listing."""
    if not stored_top:
        # First run - no stored state, return empty (just capture baseline)
        return []

    stored_top_listing = Listing.from_dict(stored_top)
    new_listings = []

    for listing in current_listings:
        if listing == stored_top_listing:
            # Hit the old top listing, stop
            break
        new_listings.append(listing)

    return new_listings


def format_email_body(new_listings: list[Listing], repo_name: str) -> str:
    """Format email body with new listings."""
    body = f"New internship listings found in {repo_name}:\n\n"

    for listing in new_listings:
        body += f"Company: {listing.company}\n"
        body += f"Role: {listing.role}\n"
        body += f"Location: {listing.location}\n"
        body += f"Date Posted: {listing.date_posted}\n"
        body += f"Apply: {listing.apply_link}\n"
        body += "=" * 20 + "\n\n"

    return body


def send_notification(new_listings: list[Listing], repo_name: str, emails: list[str]) -> None:
    """Send email notification for new listings."""
    if not emails:
        return

    with app.app_context():
        msg = Message(
            subject=f"New Internship Listings - {repo_name}",
            sender=settings.mail_username,
            bcc=emails,
            body=format_email_body(new_listings, repo_name),
        )
        mail.send(msg)


@app.route("/scrape", methods=["GET"])
@require_api_key
def scrape():
    """Scrape repos and send notifications for new listings."""
    print("[SCRAPE] Starting...", flush=True)
    state = load_state()
    emails_dict = state.get("emails", {})
    emails = list(emails_dict.keys())
    results = {}

    # Scrape Canadian Tech Internships
    try:
        print("[SCRAPE] Fetching Canadian internships...", flush=True)
        listings = scrape_canadian_internships(settings.canadian_internships_url)
        print(f"[SCRAPE] Got {len(listings)} Canadian listings", flush=True)

        if listings:
            stored_top = state.get("canadian_internships")
            new_listings = find_new_listings(listings, stored_top)

            if new_listings:
                print(f"[SCRAPE] Sending email for {len(new_listings)} new Canadian listings...", flush=True)
                send_notification(new_listings, "Canadian Tech Internships 2026", emails)
                print("[SCRAPE] Email sent for Canadian", flush=True)
                results["canadian_internships"] = {
                    "status": "new_listings",
                    "count": len(new_listings),
                    "listings": [l.to_dict() for l in new_listings],
                }
            else:
                results["canadian_internships"] = {
                    "status": "no_changes",
                }

            # Update state with new top listing
            state["canadian_internships"] = listings[0].to_dict()

    except Exception as e:
        results["canadian_internships"] = {"status": "error", "message": str(e)}

    # Scrape US Tech Internships
    try:
        print("[SCRAPE] Fetching US internships...", flush=True)
        listings = scrape_us_internships(settings.us_internships_url)
        print(f"[SCRAPE] Got {len(listings)} US listings", flush=True)

        if listings:
            stored_top = state.get("us_internships")
            new_listings = find_new_listings(listings, stored_top)

            if new_listings:
                print(f"[SCRAPE] Sending email for {len(new_listings)} new US listings...", flush=True)
                send_notification(new_listings, "US Summer 2026 Internships", emails)
                print("[SCRAPE] Email sent for US", flush=True)
                results["us_internships"] = {
                    "status": "new_listings",
                    "count": len(new_listings),
                    "listings": [l.to_dict() for l in new_listings],
                }
            else:
                results["us_internships"] = {
                    "status": "no_changes",
                }

            # Update state with new top listing
            state["us_internships"] = listings[0].to_dict()

    except Exception as e:
        results["us_internships"] = {"status": "error", "message": str(e)}

    save_state(state)
    print("[SCRAPE] Done!", flush=True)
    return jsonify(results)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.route("/emails", methods=["GET"])
@require_api_key
def get_emails():
    """Get all subscribed emails."""
    state = load_state()
    emails_dict = state.get("emails", {})
    return jsonify({"emails": list(emails_dict.keys())})


@app.route("/listings", methods=["GET"])
@require_api_key
def get_listings():
    """Get current top listings."""
    state = load_state()
    return jsonify({
        "canadian_internships": state.get("canadian_internships"),
        "us_internships": state.get("us_internships"),
    })


@app.route("/subscribe/<email>", methods=["POST"])
def subscribe(email: str):
    """Add a new email to the notification list. Returns private key for unsubscribing."""
    email = email.strip().lower()
    if not email:
        return jsonify({"error": "Email cannot be empty"}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email format"}), 400

    state = load_state()
    emails_dict = state.get("emails", {})

    if email in emails_dict:
        return jsonify({"message": "Already subscribed", "email": email})

    # Generate private key for this user
    private_key = secrets.token_hex(16)
    emails_dict[email] = private_key
    state["emails"] = emails_dict
    save_state(state)

    return jsonify({
        "message": "Subscribed",
        "email": email,
        "private_key": private_key,
        "note": "Save this key to unsubscribe later"
    })


@app.route("/unsubscribe/<email>/<key>", methods=["DELETE"])
def unsubscribe(email: str, key: str):
    """Public endpoint for users to unsubscribe using their private key."""
    email = email.strip()
    state = load_state()
    emails_dict = state.get("emails", {})

    if email not in emails_dict:
        return jsonify({"error": "Email not found"}), 404

    if emails_dict[email] != key:
        return jsonify({"error": "Invalid key"}), 403

    del emails_dict[email]
    state["emails"] = emails_dict
    save_state(state)

    return jsonify({"message": "Unsubscribed", "email": email})


@app.route("/admin/unsubscribe/<email>", methods=["DELETE"])
@require_api_key
def admin_unsubscribe(email: str):
    """Admin endpoint to remove any email."""
    email = email.strip()
    state = load_state()
    emails_dict = state.get("emails", {})

    if email not in emails_dict:
        return jsonify({"error": "Email not found"}), 404

    del emails_dict[email]
    state["emails"] = emails_dict
    save_state(state)

    return jsonify({"message": "Unsubscribed", "email": email})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
