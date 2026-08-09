# Email System

## 1. What Is It?

The email system handles sending transactional emails — messages triggered by specific events in the application. These are not marketing emails; they're functional messages that users need to interact with the application.

---

## 2. Why Does It Matter?

Email is the primary out-of-band communication channel:
- Users can't verify their email without receiving an email
- Password reset doesn't work without email delivery
- Team invitations are sent via email
- Notifications keep users engaged

---

## DevFlow Transactional Emails

| Email | Trigger | Priority |
|---|---|---|
| Email verification | User registration | High |
| Password reset | Forgot password request | High |
| Password changed | Password updated | High |
| Team invitation | Admin invites member | Medium |
| Task assigned | Task assigned to user | Medium |
| Comment mention | User @mentioned in comment | Medium |
| Daily digest | Scheduled (daily) | Low |
| Account deactivated | Admin deactivates account | High |

---

## Implementation Approach

### Development: MailHog
MailHog captures all outgoing emails without actually sending them. Access the web UI to see emails, test formatting, and verify content.

### Production: SMTP / Email Service
Use a transactional email service:
- **SendGrid** — Reliable, good API
- **Amazon SES** — Cheap, integrates with AWS
- **Postmark** — Focused on transactional email
- **Resend** — Modern, developer-friendly

### Email Templates with Jinja2
Use HTML templates for professional-looking emails:
- Base template with header/footer
- Template variables for personalization
- Plain-text fallback for email clients that don't render HTML

### Async Sending
Always send emails via background tasks:
- Don't block the API response while waiting for SMTP
- Handle failures with retries
- Log delivery status

---

## What I Should Be Able to Do Afterward

- [ ] Set up MailHog for local email testing
- [ ] Create HTML email templates with Jinja2
- [ ] Send emails asynchronously via background tasks
- [ ] Handle email delivery failures with retries
- [ ] Configure SPF, DKIM, and DMARC records for production
