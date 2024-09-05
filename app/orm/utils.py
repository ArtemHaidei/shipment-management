from ulid import ULID


def make_uuid():
    """
    Returns a UUID V4 representation for ULID postgres based models
    """
    return ULID().to_uuid4()
