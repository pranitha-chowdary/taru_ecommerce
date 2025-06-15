"""
Database utility functions
"""
from app.models import db, User, Product, Order, Category
from sqlalchemy import func
from datetime import datetime, timedelta

class DatabaseUtils:
    """Utility class for common database operations"""
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_product_by_sku(sku):
        """Get product by SKU"""
        return Product.query.filter_by(sku=sku).first()
    
    @staticmethod
    def get_featured_products(limit=10):
        """Get featured products"""
        return Product.query.filter_by(is_featured=True, is_active=True).limit(limit).all()
    
    @staticmethod
    def get_products_by_category(category_id, page=1, per_page=12):
        """Get products by category with pagination"""
        return Product.query.filter_by(
            category_id=category_id, 
            is_active=True
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    @staticmethod
    def search_products(query, page=1, per_page=12):
        """Search products by name or description"""
        search_query = f"%{query}%"
        return Product.query.filter(
            db.or_(
                Product.name.ilike(search_query),
                Product.description.ilike(search_query),
                Product.tags.ilike(search_query)
            ),
            Product.is_active == True
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def get_low_stock_products(threshold=None):
        """Get products with low stock"""
        if threshold is None:
            return Product.query.filter(
                Product.stock_quantity <= Product.min_stock_level
            ).all()
        else:
            return Product.query.filter(
                Product.stock_quantity <= threshold
            ).all()
    
    @staticmethod
    def get_user_cart_items(user_id):
        """Get all cart items for a user"""
        from app.models import CartItem
        return CartItem.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_user_orders(user_id, page=1, per_page=10):
        """Get user orders with pagination"""
        return Order.query.filter_by(user_id=user_id).order_by(
            Order.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    @staticmethod
    def get_order_by_number(order_number):
        """Get order by order number"""
        return Order.query.filter_by(order_number=order_number).first()
    
    @staticmethod
    def update_product_rating(product_id):
        """Update product rating based on reviews"""
        from app.models import Review
        
        reviews = Review.query.filter_by(
            product_id=product_id,
            is_approved=True
        ).all()
        
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews)
            
            product = Product.query.get(product_id)
            if product:
                product.rating_average = round(avg_rating, 2)
                product.rating_count = len(reviews)
                db.session.commit()
    
    @staticmethod
    def get_sales_stats(days=30):
        """Get sales statistics for the last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_revenue'),
            func.avg(Order.total_amount).label('avg_order_value')
        ).filter(
            Order.created_at >= start_date,
            Order.status.in_(['confirmed', 'processing', 'shipped', 'delivered'])
        ).first()
        
        return {
            'total_orders': stats.total_orders or 0,
            'total_revenue': float(stats.total_revenue or 0),
            'avg_order_value': float(stats.avg_order_value or 0),
            'period_days': days
        }
    
    @staticmethod
    def get_top_selling_products(limit=10, days=30):
        """Get top selling products"""
        from app.models import OrderItem
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            Product,
            func.sum(OrderItem.quantity).label('total_sold')
        ).join(
            OrderItem, Product.id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.created_at >= start_date,
            Order.status.in_(['confirmed', 'processing', 'shipped', 'delivered'])
        ).group_by(
            Product.id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_categories_with_product_count():
        """Get all categories with product count"""
        return db.session.query(
            Category,
            func.count(Product.id).label('product_count')
        ).outerjoin(
            Product, Category.id == Product.category_id
        ).filter(
            Category.is_active == True
        ).group_by(
            Category.id
        ).all()
    
    @staticmethod
    def create_order_number():
        """Generate unique order number"""
        import random
        import string
        
        while True:
            # Generate format: ORD-YYYYMMDD-XXXX
            date_part = datetime.utcnow().strftime('%Y%m%d')
            random_part = ''.join(random.choices(string.digits, k=4))
            order_number = f"ORD-{date_part}-{random_part}"
            
            # Check if order number already exists
            if not Order.query.filter_by(order_number=order_number).first():
                return order_number
    
    @staticmethod
    def bulk_update_inventory(updates):
        """Bulk update product inventory
        
        Args:
            updates: List of dictionaries with 'product_id' and 'quantity' keys
        """
        try:
            for update in updates:
                product = Product.query.get(update['product_id'])
                if product:
                    product.stock_quantity = max(0, update['quantity'])
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating inventory: {e}")
            return False
