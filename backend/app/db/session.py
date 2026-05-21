"""Database session placeholder.

TODO(db): teammate wires SQLAlchemy / SQLModel here.
Replace the stub generator below with a real async session factory.
"""
from typing import AsyncGenerator


async def get_db() -> AsyncGenerator[None, None]:
    """Stub DB session dependency.

    Yields None for now.  Every route that calls Depends(get_db)
    receives None and must guard all persistence operations with
    # TODO(db): comments so they are easy to find.
    """
    yield None  # TODO(db): yield real AsyncSession
