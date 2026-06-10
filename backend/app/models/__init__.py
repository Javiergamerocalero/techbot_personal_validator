"""SQLAlchemy ORM models. Importar acá para que Alembic los detecte."""
from app.models.employee import (  # noqa: F401
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    VALID_STATUSES,
    DocumentType,
    Employee,
)
from app.models.validation_log import (  # noqa: F401
    IdentifierType,
    ValidationLog,
    ValidationResult,
)
