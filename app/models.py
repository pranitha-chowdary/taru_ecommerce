from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for many-to-many relationship between users and products (wishlist)
wishlist = db.Table('wishlist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

# Association table for many-to-many relationship between orders and products
order_products = db.Table('order_products',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('quantity', db.Integer, default=1),
    db.Column('price', db.Float)  # Price at the time of order
)

class User(db.Model):
    """User model for customer accounts"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Authentication tokens
    auth_token = db.Column(db.String(500), unique=True)  # Current active token
    token_expires_at = db.Column(db.DateTime)  # Token expiration time
    refresh_token = db.Column(db.String(500), unique=True)  # Refresh token for token renewal
    refresh_token_expires_at = db.Column(db.DateTime)  # Refresh token expiration
    last_login_at = db.Column(db.DateTime)  # Track last login time
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
      # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    wishlist_products = db.relationship('Product', secondary=wishlist, lazy='subquery',
                                      backref=db.backref('wishlisted_by', lazy=True))
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, expires_in=3600):
        """Generate authentication token (expires in 1 hour by default)"""
        import secrets
        self.auth_token = secrets.token_urlsafe(32)
        self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        return self.auth_token
    
    def generate_refresh_token(self, expires_in=604800):
        """Generate refresh token (expires in 7 days by default)"""
        import secrets
        self.refresh_token = secrets.token_urlsafe(32)
        self.refresh_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        return self.refresh_token
    
    def is_token_valid(self):
        """Check if current auth token is valid and not expired"""
        if not self.auth_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at
    
    def is_refresh_token_valid(self):
        """Check if refresh token is valid and not expired"""
        if not self.refresh_token or not self.refresh_token_expires_at:
            return False
        return datetime.utcnow() < self.refresh_token_expires_at
    
    def revoke_tokens(self):
        """Revoke all tokens (logout)"""
        self.auth_token = None
        self.token_expires_at = None
        self.refresh_token = None
        self.refresh_token_expires_at = None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
    
    @staticmethod
    def verify_auth_token(token):
        """Verify auth token and return user if valid"""
        if not token:
            return None
        
        user = User.query.filter_by(auth_token=token).first()
        if user and user.is_token_valid() and user.is_active:
            return user
        return None
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """Product category model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subcategories
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Product(db.Model):
    """Product model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(500))
    sku = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    compare_price = db.Column(db.Float)  # Original price for discount display
    cost_price = db.Column(db.Float)  # Cost for profit calculation
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=5)
    weight = db.Column(db.Float)
    dimensions = db.Column(db.String(100))  # e.g., "10x5x3 cm"
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_digital = db.Column(db.Boolean, default=False)
    requires_shipping = db.Column(db.Boolean, default=True)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(500))
    tags = db.Column(db.String(500))  # Comma-separated tags
    rating_average = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    sold_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.compare_price and self.compare_price > self.price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100, 2)
        return 0
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductImage(db.Model):
    """Product image model"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(200))
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.image_url}>'

class ProductVariant(db.Model):
    """Product variant model (for size, color, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Red - Large"
    sku = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float)  # If different from base product price
    stock_quantity = db.Column(db.Integer, default=0)
    weight = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    
    # Variant attributes (color, size, etc.)
    attributes = db.Column(db.JSON)  # Store as JSON: {"color": "red", "size": "large"}
    
    def __repr__(self):
        return f'<ProductVariant {self.name}>'

class Address(db.Model):
    """User address model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), default='shipping')  # shipping, billing
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    address_line_1 = db.Column(db.String(200), nullable=False)
    address_line_2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(100), nullable=False, default='India')
    phone = db.Column(db.String(20))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Address {self.first_name} {self.last_name}, {self.city}>'

class Order(db.Model):
    """Order model"""
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Order status
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, processing, shipped, delivered, cancelled
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    
    # Pricing
    subtotal = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0)
    shipping_amount = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Addresses (stored as JSON to preserve order-time data)
    billing_address = db.Column(db.JSON)
    shipping_address = db.Column(db.JSON)
    
    # Order details
    notes = db.Column(db.Text)
    currency = db.Column(db.String(20), default='INR')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    """Order item model"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'))
    
    # Product details at time of order (to preserve data even if product changes)
    product_name = db.Column(db.String(200), nullable=False)
    product_sku = db.Column(db.String(100), nullable=False)
    variant_name = db.Column(db.String(100))
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='order_items')
    product_variant = db.relationship('ProductVariant', backref='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.product_name} x{self.quantity}>'

class CartItem(db.Model):
    """Shopping cart item model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'))
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product_variant = db.relationship('ProductVariant', backref='cart_items')
    
    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        if self.product_variant and self.product_variant.price:
            return self.quantity * self.product_variant.price
        return self.quantity * self.product.price
    
    def __repr__(self):
        return f'<CartItem {self.product.name} x{self.quantity}>'

class Payment(db.Model):
    """Payment model"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)  # credit_card, debit_card, upi, wallet, cod
    payment_gateway = db.Column(db.String(100))  # razorpay, stripe, paytm, etc.
    transaction_id = db.Column(db.String(200))
    gateway_transaction_id = db.Column(db.String(200))
    
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(20), default='INR')
    status = db.Column(db.String(50), default='pending')  # pending, success, failed, refunded
    
    # Payment details
    gateway_response = db.Column(db.JSON)  # Store gateway response for debugging
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'

class Review(db.Model):
    """Product review model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.rating}★ for {self.product.name}>'

class Coupon(db.Model):
    """Coupon/Discount code model"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    
    # Discount details
    discount_type = db.Column(db.String(50), nullable=False)  # percentage, fixed_amount
    discount_value = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0)
    max_discount_amount = db.Column(db.Float)  # For percentage discounts
    
    # Usage limits
    usage_limit = db.Column(db.Integer)  # Total usage limit
    usage_limit_per_user = db.Column(db.Integer, default=1)
    used_count = db.Column(db.Integer, default=0)
    
    # Validity
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self):
        """Check if coupon is valid"""
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True
    
    def __repr__(self):
        return f'<Coupon {self.code}>'

class Newsletter(db.Model):
    """Newsletter subscription model"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Newsletter {self.email}>'

class ContactMessage(db.Model):
    """Contact form message model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_replied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ContactMessage from {self.email}>'
