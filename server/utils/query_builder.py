from typing import Optional
from datetime import datetime, UTC
from sqlalchemy import select, func, or_, Float, case
from sqlalchemy.sql import Select
from sqlalchemy.types import DateTime
from flask import current_app

class QueryBuilder:
    def __init__(self, model):
        self.model = model
        self.base_query = select(model)
        self.filters = []
        self.sort_column = None
        self.sort_direction = None
        self.page = None
        self.page_size = None
        self._joins = []
        
    def add_filter(self, condition):
        """Add a filter condition to the query"""
        current_app.logger.info(f"Adding filter condition: {condition}")
        self.filters.append(condition)
        return self
        
    def build(self) -> Select:
        """Build the main query with all filters"""
        current_app.logger.info("=== Query Build Debug ===")
        current_app.logger.info(f"Base query: {self.base_query}")
        current_app.logger.info(f"Number of filters: {len(self.filters)}")
        
        # Start with base query
        query = self.base_query
        
        # Apply joins first
        for join_target in self._joins:
            current_app.logger.info(f"Applying join for: {join_target}")
            query = query.join(join_target)
        
        # Apply filters
        for i, filter_condition in enumerate(self.filters):
            current_app.logger.info(f"Applying filter {i + 1}: {filter_condition}")
            query = query.where(filter_condition)
            current_app.logger.info(f"Query after filter {i + 1}: {query}")
        
        # Apply sorting
        if self.sort_column:
            current_app.logger.info(f"Applying sort: {self.sort_column} {self.sort_direction}")
            order_column = self.get_order_column()
            
            if order_column is not None:
                if self.sort_direction == 'desc':
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            else:
                current_app.logger.warning(f"Sort column {self.sort_column} not found, using id")
                query = query.order_by(self.model.id)
        else:
            current_app.logger.info("Applying default sort by id")
            query = query.order_by(self.model.id)
            
        # Apply pagination
        if self.page is not None and self.page_size is not None:
            offset = (self.page - 1) * self.page_size
            current_app.logger.info(f"Applying pagination: page={self.page}, page_size={self.page_size}, offset={offset}")
            query = query.offset(offset).limit(self.page_size)
            
        current_app.logger.info(f"Final query: {query}")
        return query
        
    def build_count(self) -> Select:
        """Build a count query using the same filters"""
        current_app.logger.info("=== Count Query Build Debug ===")
        
        # Start with base query
        query = self.base_query
        
        # Apply joins first
        for join_target in self._joins:
            current_app.logger.info(f"Applying join for count query: {join_target}")
            query = query.join(join_target)
        
        # Apply filters
        for filter_condition in self.filters:
            query = query.where(filter_condition)
        
        # Create subquery
        subquery = query.subquery()
        current_app.logger.info(f"Created subquery: {subquery}")
        
        # Build count query
        count_query = select(func.count()).select_from(subquery)
        current_app.logger.info(f"Final count query: {count_query}")
        
        return count_query

    def get_order_column(self):
        """Get the appropriate column or expression for sorting"""
        # Handle special cases first
        if self.sort_column == 'niche__name':
            from models.niche import Niche
            # Don't modify query here, just return the column
            return Niche.name
        elif self.sort_column == 'detection_rate':
            # Handle division by zero with CASE
            return case(
                (self.model.total_checks == 0, 0.0),
                else_=func.cast(self.model.total_detections, Float) * 100.0 / func.cast(self.model.total_checks, Float)
            )
        
        # Handle regular columns
        if hasattr(self.model, self.sort_column):
            column = getattr(self.model, self.sort_column)
            
            # Special handling for datetime columns
            if isinstance(column.type, DateTime):
                # Use COALESCE with timezone-aware values
                if self.sort_direction == 'desc':
                    return func.coalesce(column, datetime.min.replace(tzinfo=UTC))
                else:
                    return func.coalesce(column, datetime.max.replace(tzinfo=UTC))
            
            return column
            
        return None

class ProfileQueryBuilder(QueryBuilder):
    def with_niche_id(self, niche_id: Optional[str]) -> 'ProfileQueryBuilder':
        """Add niche_id filter if provided"""
        if niche_id:
            current_app.logger.info(f"Adding niche_id filter: {niche_id}")
            self.add_filter(self.model.niche_id == niche_id)
        return self

    def with_status(self, status: Optional[str]) -> 'ProfileQueryBuilder':
        """Add status filter if provided"""
        if status:
            current_app.logger.info(f"Adding status filter: {status}")
            self.add_filter(self.model.status == status)
        return self

    def with_search(self, search: Optional[str]) -> 'ProfileQueryBuilder':
        """Add search filter if provided"""
        if search:
            current_app.logger.info(f"Adding search filter: {search}")
            # Case-insensitive search on username
            search_pattern = f"%{search.lower()}%"
            self.add_filter(func.lower(self.model.username).like(search_pattern))
        return self

    def with_active_story(self, has_active_story: Optional[bool]) -> 'ProfileQueryBuilder':
        """Add active_story filter if provided"""
        if has_active_story is not None:
            current_app.logger.info(f"Adding active_story filter: {has_active_story}")
            self.add_filter(self.model.active_story == has_active_story)
        return self

    def with_pagination(self, page: int, page_size: int) -> 'ProfileQueryBuilder':
        """Store pagination parameters"""
        current_app.logger.info(f"Setting pagination: page={page}, page_size={page_size}")
        self.page = page
        self.page_size = page_size
        return self

    def with_sorting(self, sort_column: str, sort_direction: str = 'asc') -> 'ProfileQueryBuilder':
        """Store sorting parameters and set up any required joins"""
        current_app.logger.info(f"Setting sorting: column={sort_column}, direction={sort_direction}")
        self.sort_column = sort_column
        self.sort_direction = sort_direction

        # Set up joins needed for sorting
        if sort_column == 'niche__name':
            from models.niche import Niche
            if Niche not in self._joins:
                self._joins.append(Niche)
                current_app.logger.info(f"Added join for Niche model")

        return self