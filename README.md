# Job Updates Notification

Get email notifications when new internship listings are posted to popular GitHub repositories.

## Tracked Repositories

- [Canadian Tech Internships 2026](https://github.com/negarprh/Canadian-Tech-Internships-2026)
- [US Summer 2026 Internships](https://github.com/SimplifyJobs/Summer2026-Internships)

## How It Works

The service periodically checks for new internship listings. When new positions are posted, subscribers receive an email with job details including company, role, location, and apply link.

## Subscribe

To receive notifications, send a POST request:

```bash
curl -X POST https://your-app-url.com/subscribe/your-email@example.com
```

**Response:**
```json
{
  "message": "Subscribed",
  "email": "your-email@example.com",
  "private_key": "abc123...",
  "note": "Save this key to unsubscribe later"
}
```

**Important:** Save your `private_key` - you'll need it to unsubscribe.

## Unsubscribe

To stop receiving notifications:

```bash
curl -X DELETE https://your-app-url.com/unsubscribe/your-email@example.com/your-private-key
```

## Privacy

- Your email is stored securely and only used for job notifications
- Email addresses are hidden from other subscribers (BCC)
- No data is shared with third parties
