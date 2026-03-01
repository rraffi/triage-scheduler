# Phase 5 — Notifications

## Scope

Notify assignees and the team when the weekly schedule is published. Two channels:
email and Microsoft Teams chat.

## Depends On

Phase 4 (Schedule Dashboard — provides the published schedule to link to).

## Trigger

Notifications fire when:
1. **Weekly schedule is published** (automatic or manual trigger).
2. **Assignment changes** (admin override or approved swap).
3. **Reminder** (optional: day-of reminder for the assigned member).

## Channels

### Email
| Event | Recipients | Content |
|-------|-----------|---------|
| Schedule published | All assignees for the week | Your assignment (app, week), link to dashboard |
| Assignment changed | Affected member(s) | Old → new assignment, reason, link to dashboard |
| Reminder (optional) | Assignee | "You are on triage for App X today" |

### Microsoft Teams
| Event | Target | Content |
|-------|--------|---------|
| Schedule published | Team channel | Summary card: all assignments for the week, link to dashboard |
| Assignment changed | Team channel | Update card: what changed and why |

## Notification Preferences (per member)

| Preference | Options | Default |
|------------|---------|---------|
| Email notifications | on / off | on |
| Teams notifications | on / off | on |
| Reminder | on / off | off |
| Reminder timing | day-before / day-of | day-of |

## Integration Details

### Email
- Use SMTP or a transactional email service (SendGrid, SES, etc.).
- HTML template with plain-text fallback.
- Include deep link to the dashboard for the relevant week.

### Microsoft Teams
- Use Teams incoming webhook or Graph API.
- Adaptive Card format for rich display.
- Include @mentions for assigned members.

## Acceptance Criteria

1. Assignees receive email within 5 minutes of schedule publish.
2. Teams channel receives a summary card within 5 minutes of schedule publish.
3. Members can opt out of individual channels without affecting others.
4. Failed notifications are retried with backoff and logged.

## Out of Scope

- Slack integration (can be added as a parallel channel later).
- SMS notifications.
- Notification for vacation reminders (that's member self-service in Phase 3).
