"""Category repository with caching for performance.

Provides CRUD operations for Category model with in-memory caching.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.models.category import Category
from src.config.logging import get_logger

logger = get_logger(__name__)


class CategoryRepository:
    """Repository for Category model with caching."""

    # Class-level cache for categories (populated on first access)
    _categories_cache: Optional[list[Category]] = None
    _categories_by_id: Optional[dict[int, Category]] = None
    _categories_by_name: Optional[dict[str, Category]] = None

    def __init__(self, session: AsyncSession):
        """Initialize category repository.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def _load_cache(self) -> None:
        """Load categories into cache if not already loaded."""
        if CategoryRepository._categories_cache is not None:
            return

        result = await self.session.execute(
            select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order)
        )
        categories = list(result.scalars().all())

        CategoryRepository._categories_cache = categories
        CategoryRepository._categories_by_id = {c.category_id: c for c in categories}
        CategoryRepository._categories_by_name = {c.name: c for c in categories}

        logger.info(f"Categories cache loaded with {len(categories)} categories")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the categories cache.

        Call this after creating/updating/deleting categories.
        """
        cls._categories_cache = None
        cls._categories_by_id = None
        cls._categories_by_name = None
        logger.info("Categories cache cleared")

    async def get_all(self) -> list[Category]:
        """Get all active categories.

        Returns:
            List of Category instances ordered by sort_order
        """
        await self._load_cache()
        return CategoryRepository._categories_cache.copy()

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID from cache.

        Args:
            category_id: Category primary key

        Returns:
            Category instance if found, None otherwise
        """
        await self._load_cache()
        return CategoryRepository._categories_by_id.get(category_id)

    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name from cache.

        Args:
            name: Category name

        Returns:
            Category instance if found, None otherwise
        """
        await self._load_cache()
        return CategoryRepository._categories_by_name.get(name)

    async def get_by_type(self, category_type: str) -> list[Category]:
        """Get all categories of specific type.

        Args:
            category_type: Category type ('income' or 'expense')

        Returns:
            List of Category instances of the specified type
        """
        await self._load_cache()
        return [c for c in CategoryRepository._categories_cache if c.type == category_type]

    async def get_income_category(self) -> Optional[Category]:
        """Get the Income category.

        Returns:
            Income Category instance if found, None otherwise
        """
        return await self.get_by_name("Income")

    async def get_expense_categories(self) -> list[Category]:
        """Get all expense categories for keyboard display.

        Returns:
            List of expense Category instances ordered by sort_order
        """
        return await self.get_by_type("expense")

    async def create(
        self,
        name: str,
        category_type: str,
        emoji: Optional[str] = None,
        sort_order: Optional[int] = None,
    ) -> Category:
        """Create a new category.

        Args:
            name: Category name (unique)
            category_type: Category type ('income' or 'expense')
            emoji: Emoji representation (optional)
            sort_order: Display order (optional, auto-calculated if not provided)

        Returns:
            Created Category instance

        Raises:
            ValueError: If category_type is invalid
            IntegrityError: If name already exists
        """
        if category_type not in ("income", "expense"):
            raise ValueError(f"Invalid category_type: {category_type}")

        # Auto-calculate sort_order if not provided
        if sort_order is None:
            result = await self.session.execute(
                select(Category.sort_order).order_by(Category.sort_order.desc()).limit(1)
            )
            max_sort_order = result.scalar_one_or_none()
            sort_order = (max_sort_order or 0) + 1

        category = Category(
            name=name,
            type=category_type,
            emoji=emoji,
            sort_order=sort_order,
            is_active=True,
        )

        self.session.add(category)
        await self.session.flush()

        # Clear cache to reload on next access
        CategoryRepository.clear_cache()

        logger.info(
            "Category created",
            extra={
                "category_id": category.category_id,
                "name": name,
                "type": category_type,
            },
        )

        return category
