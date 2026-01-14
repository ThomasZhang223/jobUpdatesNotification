import json
from pathlib import Path
from flask import Flask, jsonify, request
from flask_mail import Mail, Message

from config import get_settings
from scraper import Listing, scrape_canadian_internships


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


def load_state() -> dict:
    """Load state from JSON file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


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


def format_no_changes_email(top_listing: Listing, repo_name: str) -> str:
    """Format email body when no new listings found."""
    body = f"No new listings found in {repo_name}.\n\n"
    body += "Current top listing:\n"
    body += f"Company: {top_listing.company}\n"
    body += f"Role: {top_listing.role}\n"
    body += f"Location: {top_listing.location}\n"
    body += f"Date Posted: {top_listing.date_posted}\n"
    body += f"Apply: {top_listing.apply_link}\n"

    return body


def send_notification(new_listings: list[Listing], repo_name: str, emails: list[str]) -> None:
    """Send email notification for new listings."""
    if not emails:
        return

    with app.app_context():
        msg = Message(
            subject=f"New Internship Listings - {repo_name}",
            sender=settings.mail_username,
            recipients=emails,
            body=format_email_body(new_listings, repo_name),
        )
        mail.send(msg)


def send_no_changes_notification(top_listing: Listing, repo_name: str, emails: list[str]) -> None:
    """Send email notification when no new listings found."""
    if not emails:
        return

    with app.app_context():
        msg = Message(
            subject=f"No New Listings - {repo_name}",
            sender=settings.mail_username,
            recipients=emails,
            body=format_no_changes_email(top_listing, repo_name),
        )
        mail.send(msg)


@app.route("/scrape", methods=["GET"])
def scrape():
    """Scrape repos and send notifications for new listings."""
    state = load_state()
    emails = state.get("emails", [])
    results = {}

    # Scrape Canadian Tech Internships
    try:
        listings = scrape_canadian_internships(settings.canadian_internships_url)

        if listings:
            stored_top = state.get("canadian_internships")
            new_listings = find_new_listings(listings, stored_top)

            if new_listings:
                send_notification(new_listings, "Canadian Tech Internships 2026", emails)
                results["canadian_internships"] = {
                    "status": "new_listings",
                    "count": len(new_listings),
                    "listings": [l.to_dict() for l in new_listings],
                }
            else:
                send_no_changes_notification(listings[0], "Canadian Tech Internships 2026", emails)
                results["canadian_internships"] = {
                    "status": "no_changes",
                    "top_listing": listings[0].to_dict(),
                }

            # Update state with new top listing
            state["canadian_internships"] = listings[0].to_dict()

    except Exception as e:
        results["canadian_internships"] = {"status": "error", "message": str(e)}

    save_state(state)
    return jsonify(results)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.route("/subscribe/<email>", methods=["POST"])
def subscribe(email: str):
    """Add a new email to the notification list."""
    email = email.strip()
    if not email:
        return jsonify({"error": "Email cannot be empty"}), 400

    state = load_state()
    emails = state.get("emails", [])

    if email in emails:
        return jsonify({"message": "Already subscribed", "email": email})

    emails.append(email)
    state["emails"] = emails
    save_state(state)

    return jsonify({"message": "Subscribed", "email": email})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
