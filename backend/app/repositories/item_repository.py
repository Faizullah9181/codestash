"""
Item repository — data access for the Item model.

Add any custom queries here (e.g. full-text search, aggregations).
Standard CRUD comes from BaseRepository.
"""

from app.db.models import Item
from app.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    model = Item


# Singleton instance — import this in services
item_repository = ItemRepository()