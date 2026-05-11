#!/usr/bin/env python3
"""
Migration script to convert relative deadlines to actual dates.
Uses each meeting's created_at date as the base for conversion.
"""
import sqlite3
import re
from datetime import datetime, timedelta

DB_PATH = "data/teamai.db"


def convert_relative_deadline(deadline: str, meeting_date: datetime) -> str:
    """
    Convert relative deadline to actual date.
    """
    if not deadline:
        return deadline

    dl = deadline.lower().strip()

    # Already an actual date? Return as-is
    if re.search(r'\d{4}|\d{1,2}/\d{1,2}', dl):
        if not re.match(r'^(tomorrow|today|this|next|end)', dl, re.IGNORECASE):
            return deadline

    # Skip non-date values
    skip_values = ['tbd', 'not specified', 'ongoing', 'asap', 'as needed', 'n/a', '']
    if dl in skip_values:
        return deadline

    result_date = None

    # Today
    if 'today' in dl:
        result_date = meeting_date

    # Tomorrow
    elif 'tomorrow' in dl:
        result_date = meeting_date + timedelta(days=1)

    # Day of week (Monday, Tuesday, etc.)
    elif any(day in dl for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in dl:
                current_weekday = meeting_date.weekday()
                target_weekday = i
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Target day is today or already passed this week
                    days_ahead += 7
                result_date = meeting_date + timedelta(days=days_ahead)
                break

    # This week (assume Friday)
    elif 'this week' in dl:
        days_until_friday = (4 - meeting_date.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        result_date = meeting_date + timedelta(days=days_until_friday)

    # Next week (assume Monday)
    elif 'next week' in dl:
        days_until_monday = (7 - meeting_date.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        result_date = meeting_date + timedelta(days=days_until_monday)

    # End of month
    elif 'end of month' in dl or 'month end' in dl:
        if meeting_date.month == 12:
            result_date = datetime(meeting_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            result_date = datetime(meeting_date.year, meeting_date.month + 1, 1) - timedelta(days=1)

    if result_date:
        return result_date.strftime("%B %d, %Y")
    return deadline


def migrate_deadlines():
    """
    Migrate all tasks with relative deadlines to actual dates.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all tasks with relative deadlines
    cursor.execute("""
        SELECT t.id, t.deadline, t.meeting_id, m.created_at
        FROM tasks t
        JOIN meetings m ON t.meeting_id = m.id
        WHERE t.deadline LIKE '%tomorrow%'
           OR t.deadline LIKE '%Monday%'
           OR t.deadline LIKE '%Tuesday%'
           OR t.deadline LIKE '%Wednesday%'
           OR t.deadline LIKE '%Thursday%'
           OR t.deadline LIKE '%Friday%'
           OR t.deadline LIKE '%Saturday%'
           OR t.deadline LIKE '%Sunday%'
           OR t.deadline LIKE '%this week%'
           OR t.deadline LIKE '%next week%'
           OR t.deadline LIKE '%end of month%'
    """)

    tasks = cursor.fetchall()
    print(f"Found {len(tasks)} tasks with relative deadlines to migrate")

    updated = 0
    for task_id, deadline, meeting_id, meeting_created_at in tasks:
        # Parse meeting date
        meeting_date = datetime.fromisoformat(meeting_created_at.replace('Z', '+00:00').split('+')[0])

        # Convert deadline
        new_deadline = convert_relative_deadline(deadline, meeting_date)

        if new_deadline != deadline:
            cursor.execute(
                "UPDATE tasks SET deadline = ? WHERE id = ?",
                (new_deadline, task_id)
            )
            print(f"  {deadline} -> {new_deadline} (meeting: {meeting_date.strftime('%Y-%m-%d')})")
            updated += 1

    conn.commit()
    conn.close()

    print(f"\nMigration complete: {updated} tasks updated")


if __name__ == "__main__":
    migrate_deadlines()
