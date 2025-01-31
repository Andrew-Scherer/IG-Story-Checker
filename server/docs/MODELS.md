# Database Models Guide

## Core Principles

1. **Consistent Model Configuration**
   - Clear table naming
   - Proper constraint definition
   - Consistent option handling

2. **Clean Architecture**
   - Models only define structure and relationships
   - Business logic belongs in services
   - No circular dependencies

3. **Type Safety**
   - Explicit column types
   - Clear nullable flags
   - Proper default values

## Model Definition

### Basic Model Structure

All models inherit from BaseModel which provides:
- Automatic table naming (pluralized model name)
- Timestamp tracking (created_at, updated_at)
- extend_existing=True configuration
- Basic CRUD operations

```python
from server.extensions import db
from .base import BaseModel

class User(BaseModel):
    """User model for authentication and profile"""
    # No need to specify __tablename__ or __table_args__
    # BaseModel handles these automatically
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Required Fields
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Optional Fields
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
```

### Model with Constraints

```python
class Order(BaseModel):
    """Order model with constraints"""
    __tablename__ = 'orders'
    __table_args__ = (
        # Constraints first
        db.UniqueConstraint('order_number', name='uq_order_number'),
        db.CheckConstraint('amount >= 0', name='ck_positive_amount'),
        # Options last as dictionary
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
```

## Relationships

### One-to-Many Relationship

```python
class Post(BaseModel):
    # No need to specify __tablename__ or __table_args__
    # BaseModel handles these automatically
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship definition
    user = db.relationship('User', back_populates='posts')

class User(BaseModel):
    # No need to specify __tablename__ or __table_args__
    # BaseModel handles these automatically
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationship definition
    posts = db.relationship('Post', back_populates='user')
```

### Many-to-Many Relationship

```python
# Association table
tag_post = db.Table('tag_post',
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    {'extend_existing': True}
)

class Tag(BaseModel):
    __tablename__ = 'tags'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    # Many-to-many relationship
    posts = db.relationship('Post', secondary=tag_post, back_populates='tags')

class Post(BaseModel):
    __tablename__ = 'posts'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Many-to-many relationship
    tags = db.relationship('Tag', secondary=tag_post, back_populates='posts')
```

## Model Configuration

### Table Arguments

BaseModel automatically provides `extend_existing=True` configuration for all models. You only need to specify `__table_args__` when adding constraints to your model:

```python
class Order(BaseModel):
    """Order model with constraints"""
    __table_args__ = (
        # Add your constraints here
        db.UniqueConstraint('order_number', name='uq_order_number'),
        db.CheckConstraint('amount >= 0', name='ck_positive_amount')
        # No need to add extend_existing=True - BaseModel handles this
    )
```

Key Points:
- Only specify __table_args__ when adding constraints
- Use descriptive constraint names (e.g., uq_ prefix for unique constraints)
- No need to add extend_existing=True - it's inherited from BaseModel
- Follow SQLAlchemy naming conventions for constraints

### Column Configuration

```python
class Product(BaseModel):
    # No need to specify __tablename__ or __table_args__
    # BaseModel handles these automatically
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # String with length limit
    name = db.Column(db.String(100), nullable=False)
    
    # Numeric with precision
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Enum field
    status = db.Column(
        db.Enum('draft', 'published', name='product_status'),
        nullable=False,
        default='draft'
    )
    
    # Boolean with default
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Timestamp with timezone
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
```

## Common Patterns

### Soft Delete

```python
class SoftDeleteMixin:
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def soft_delete(self):
        self.deleted_at = datetime.now(UTC)
        db.session.commit()
    
    @classmethod
    def not_deleted(cls):
        return cls.query.filter_by(deleted_at=None)

class User(BaseModel, SoftDeleteMixin):
    # No need to specify __tablename__ or __table_args__
    # BaseModel handles these automatically
    pass
```

### Timestamps

```python
class TimestampMixin:
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

class User(BaseModel, TimestampMixin):
    # No need to specify __tablename__ or __table_args__
    # BaseModel handles these automatically
    pass
```

## Testing Models

### Unit Tests

```python
@pytest.mark.real_db
def test_user_creation(db_session):
    user = User(name="Test", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.created_at is not None

@pytest.mark.real_db
def test_unique_constraint(db_session):
    User(name="Test", email="test@example.com").save()
    
    with pytest.raises(IntegrityError):
        User(name="Test2", email="test@example.com").save()
```

### Relationship Tests

```python
@pytest.mark.real_db
def test_post_user_relationship(db_session):
    user = User(name="Test").save()
    post = Post(user=user, title="Test Post").save()
    
    assert post.user_id == user.id
    assert user.posts[0] == post
```

## Common Issues

### SQLAlchemy Instance Errors

1. **"A 'SQLAlchemy' instance has already been registered on this Flask app"**
   - Cause: Multiple calls to db.init_app() on the same Flask app
   - Solution: Only initialize SQLAlchemy once per Flask app
   ```python
   # In app.py
   def create_app():
       app = Flask(__name__)
       db.init_app(app)  # Initialize once here
       return app
   
   # In tests, don't call init_app again
   app = create_app()
   ```

2. **"The current Flask app is not registered with this 'SQLAlchemy' instance"**
   - Cause: Using db outside of Flask app context or before initialization
   - Solution: Ensure proper app context and initialization order
   ```python
   # Correct order
   app = create_app()
   with app.app_context():
       db.create_all()
   ```

### Table Already Defined

If you see "Table Already Defined" errors:
1. Verify your model inherits from BaseModel
2. Check for duplicate model imports
3. Ensure you're not creating multiple Flask applications
4. Verify table names are unique across your models

Common causes:
- Model not inheriting from BaseModel (missing extend_existing=True)
- Importing models through different paths (e.g., 'from models' vs 'from server.models')
- Creating multiple Flask app instances in tests
- Using the same table name in different models

### Constraint Violations

If you see integrity errors:
1. Check constraint definitions
2. Verify data meets constraints
3. Check for proper cascade settings

### Relationship Issues

If relationships aren't working:
1. Check back_populates matches
2. Verify foreign key columns
3. Check lazy loading settings

## Best Practices

1. **Clear Documentation**
```python
class User(BaseModel):
    """User model for authentication and profiles.
    
    Attributes:
        email: Primary email address, must be unique
        name: Display name
        role: User role (admin, user, etc)
    
    Relationships:
        posts: One-to-many with Post model
        groups: Many-to-many with Group model
    """
```

2. **Consistent Naming**
```python
# Table names: plural, lowercase
__tablename__ = 'users'

# Constraint names: prefix with type
db.UniqueConstraint('email', name='uq_user_email')
db.CheckConstraint('age >= 18', name='ck_user_adult')

# Index names: prefix with idx
db.Index('idx_user_email', 'email')
```

3. **Type Safety**
```python
# Good
age = db.Column(db.Integer, nullable=False)
name = db.Column(db.String(100), nullable=False)

# Bad
age = db.Column(db.Integer)  # Nullable not specified
name = db.Column(db.String)  # No length limit
```

4. **Proper Defaults**
```python
# Good
status = db.Column(db.String(20), nullable=False, default='active')
created_at = db.Column(db.DateTime(timezone=True), 
                      nullable=False,
                      default=lambda: datetime.now(UTC))

# Bad
status = db.Column(db.String(20))  # No default
created_at = db.Column(db.DateTime)  # No timezone