from app.config import settings
from app.events.interface import EventPublisher
from app.events.noop import NoOpEventPublisher

_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    global _publisher
    if _publisher is not None:
        return _publisher

    if settings.FIREBASE_CREDENTIALS_PATH and settings.FIREBASE_PROJECT_ID:
        from app.events.firebase import FirebaseEventPublisher

        _publisher = FirebaseEventPublisher(
            settings.FIREBASE_CREDENTIALS_PATH,
            settings.FIREBASE_PROJECT_ID,
        )
    else:
        _publisher = NoOpEventPublisher()

    return _publisher
