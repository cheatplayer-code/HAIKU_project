"""In-memory demo repository with seeded demand pools."""

from app.domain.enums import IntentCategory, PoolStatus
from app.domain.models import DemandPoolDto, ProfileIntent
from app.services.pricing import (
    get_category_savings_benchmark,
    estimate_savings_percent,
    estimate_group_price_kzt,
)


def _create_demo_pool(
    id: str,
    city: str,
    category: IntentCategory,
    title: str,
    localized_title: str,
    current_intent_count: int,
    moq: int,
    estimated_retail_price_kzt: int,
) -> DemandPoolDto:
    """Helper to create a demo pool with calculated prices."""
    savings_interval = get_category_savings_benchmark(category)
    estimated_savings = estimate_savings_percent(category)
    estimated_group_price = estimate_group_price_kzt(estimated_retail_price_kzt, category)
    missing_to_moq = max(moq - current_intent_count, 0)
    
    return DemandPoolDto(
        id=id,
        city=city,
        category=category,
        title=title,
        localized_title=localized_title,
        status=PoolStatus.forming,
        current_intent_count=current_intent_count,
        moq=moq,
        missing_to_moq=missing_to_moq,
        estimated_retail_price_kzt=estimated_retail_price_kzt,
        estimated_group_price_kzt=estimated_group_price,
        estimated_savings_percent=estimated_savings,
        savings_interval_percent=savings_interval,
        benchmark_source="demo_category_benchmark",
        is_demo_data=True,
    )


class DemoRepository:
    """In-memory demo repository for demand pools and user intents."""
    
    def __init__(self) -> None:
        """Initialize the repository with seeded demo pools."""
        self.pools: dict[str, DemandPoolDto] = {}
        self.user_intents: dict[str, list[ProfileIntent]] = {}
        
        # Seed demo pools
        self._seed_pools()
    
    def _seed_pools(self) -> None:
        """Seed the repository with demo demand pools."""
        # Required killer demo pool: wireless headphones in Almaty
        headphones_pool = _create_demo_pool(
            id="pool-almaty-headphones",
            city="Almaty",
            category=IntentCategory.electronics,
            title="wireless headphones",
            localized_title="Беспроводные наушники",
            current_intent_count=24,
            moq=25,
            estimated_retail_price_kzt=22000,
        )
        self.pools[headphones_pool.id] = headphones_pool
        
        # Home humidifier in Almaty
        humidifier_pool = _create_demo_pool(
            id="pool-almaty-humidifier",
            city="Almaty",
            category=IntentCategory.home,
            title="home humidifier",
            localized_title="Домашний увлажнитель",
            current_intent_count=18,
            moq=20,
            estimated_retail_price_kzt=15000,
        )
        self.pools[humidifier_pool.id] = humidifier_pool
        
        # Portable projector in Almaty
        projector_pool = _create_demo_pool(
            id="pool-almaty-projector",
            city="Almaty",
            category=IntentCategory.electronics,
            title="portable projector",
            localized_title="Портативный проектор",
            current_intent_count=12,
            moq=15,
            estimated_retail_price_kzt=45000,
        )
        self.pools[projector_pool.id] = projector_pool
        
        # Fashion jacket in Almaty
        jacket_pool = _create_demo_pool(
            id="pool-almaty-jacket",
            city="Almaty",
            category=IntentCategory.fashion,
            title="winter jacket",
            localized_title="Зимняя куртка",
            current_intent_count=30,
            moq=35,
            estimated_retail_price_kzt=25000,
        )
        self.pools[jacket_pool.id] = jacket_pool
        
        # Basketball shoes in Almaty
        shoes_pool = _create_demo_pool(
            id="pool-almaty-basketball-shoes",
            city="Almaty",
            category=IntentCategory.sports,
            title="basketball shoes",
            localized_title="Баскетбольные кроссовки",
            current_intent_count=20,
            moq=25,
            estimated_retail_price_kzt=35000,
        )
        self.pools[shoes_pool.id] = shoes_pool
        
        # Kids toy in Astana
        toy_pool = _create_demo_pool(
            id="pool-astana-toy",
            city="Astana",
            category=IntentCategory.kids,
            title="educational toy set",
            localized_title="Набор образовательных игрушек",
            current_intent_count=15,
            moq=20,
            estimated_retail_price_kzt=12000,
        )
        self.pools[toy_pool.id] = toy_pool
        
        # Car accessory in Almaty
        car_accessory_pool = _create_demo_pool(
            id="pool-almaty-car-accessory",
            city="Almaty",
            category=IntentCategory.auto,
            title="car phone holder",
            localized_title="Автомобильный держатель для телефона",
            current_intent_count=40,
            moq=50,
            estimated_retail_price_kzt=8000,
        )
        self.pools[car_accessory_pool.id] = car_accessory_pool
        
        # Books in Almaty
        books_pool = _create_demo_pool(
            id="pool-almaty-books",
            city="Almaty",
            category=IntentCategory.books,
            title="programming book collection",
            localized_title="Коллекция книг по программированию",
            current_intent_count=8,
            moq=10,
            estimated_retail_price_kzt=18000,
        )
        self.pools[books_pool.id] = books_pool
    
    def list_pools(
        self,
        city: str,
        category: IntentCategory | None = None,
        limit: int = 20,
    ) -> list[DemandPoolDto]:
        """List demand pools filtered by city and optionally category.
        
        Args:
            city: City filter (case-insensitive).
            category: Optional category filter.
            limit: Maximum number of pools to return.
            
        Returns:
            List of DemandPoolDto sorted by:
            1. Pools closer to MOQ first
            2. Higher current_intent_count
            3. Stable ordering by id
        """
        city_lower = city.lower()
        
        filtered_pools = [
            pool for pool in self.pools.values()
            if pool.city.lower() == city_lower
            and (category is None or pool.category == category)
        ]
        
        # Sort by: missing_to_moq (asc), current_intent_count (desc), id (asc)
        sorted_pools = sorted(
            filtered_pools,
            key=lambda p: (p.missing_to_moq, -p.current_intent_count, p.id),
        )
        
        return sorted_pools[:limit]
    
    def get_pool(self, pool_id: str) -> DemandPoolDto | None:
        """Get a single pool by ID.
        
        Args:
            pool_id: The pool ID.
            
        Returns:
            DemandPoolDto if found, None otherwise.
        """
        return self.pools.get(pool_id)
    
    def update_pool(self, pool: DemandPoolDto) -> None:
        """Update a pool in the repository.
        
        Args:
            pool: The updated DemandPoolDto.
        """
        self.pools[pool.id] = pool
    
    def add_user_intent(self, esim_profile_id: str, intent_record: ProfileIntent) -> None:
        """Add a user intent record.
        
        Args:
            esim_profile_id: The eSIM profile ID.
            intent_record: The ProfileIntent to store.
        """
        if esim_profile_id not in self.user_intents:
            self.user_intents[esim_profile_id] = []
        self.user_intents[esim_profile_id].append(intent_record)
    
    def list_user_intents(self, esim_profile_id: str) -> list[ProfileIntent]:
        """List user intents for an eSIM profile.
        
        Args:
            esim_profile_id: The eSIM profile ID.
            
        Returns:
            List of ProfileIntent records, empty list if none exist.
        """
        return self.user_intents.get(esim_profile_id, [])
