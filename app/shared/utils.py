import uuid
import uuid_utils


def generate_uuidv7() -> uuid.UUID:
    # uuid_utils.uuid7 возвращает свой тип -
    # конвертируем в стандартный uuid.UUID
    return uuid.UUID(str(uuid_utils.uuid7()))
