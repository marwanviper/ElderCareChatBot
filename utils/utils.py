from datetime import UTC, datetime


def _utcnow():
    """Get the current UTC time."""
    return datetime.now(UTC)


if __name__ == "__main__":
    print("Current UTC time:", _utcnow())
