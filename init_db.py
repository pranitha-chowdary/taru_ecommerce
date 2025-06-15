"""
Database initialization and management script
"""
from app import create_app
from app.models import db, User, Category, Product, ProductImage

def init_db():
    """Initialize the database with tables"""
    app = create_app()
    with app.app_context():
        # Drop all tables (use with caution in production)
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")

def seed_data():
    """Seed the database with initial data"""
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@taruecommerce.com',
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("Admin user created!")
        else:
            print("Admin user already exists!")
        
        # Check and create sample categories
        category_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            {'name': 'Clothing', 'description': 'Mens and womens clothing'},
            {'name': 'Books', 'description': 'Books and educational materials'},
            {'name': 'Home & Garden', 'description': 'Home improvement and garden items'},
            {'name': 'Sports', 'description': 'Sports and fitness equipment'}
        ]
        
        categories_created = 0
        for cat_data in category_data:
            existing_category = Category.query.filter_by(name=cat_data['name']).first()
            if not existing_category:
                category = Category(name=cat_data['name'], description=cat_data['description'])
                db.session.add(category)
                categories_created += 1
        
        if categories_created > 0:
            print(f"Created {categories_created} new categories!")
        else:
            print("All categories already exist!")
        
        # Commit category changes before creating products
        db.session.commit()
        
        # Check and create sample products
        electronics_category = Category.query.filter_by(name='Electronics').first()
        clothing_category = Category.query.filter_by(name='Clothing').first()
        
        if electronics_category and clothing_category:
            product_data = [
                {
                    'name': 'Smartphone XYZ',
                    'description': 'Latest smartphone with advanced features',
                    'short_description': 'High-performance smartphone',
                    'sku': 'PHONE-XYZ-001',
                    'price': 25999.0,
                    'compare_price': 29999.0,
                    'stock_quantity': 50,
                    'category_id': electronics_category.id,
                    'is_featured': True
                },
                {
                    'name': 'Cotton T-Shirt',
                    'description': 'Comfortable cotton t-shirt for casual wear',
                    'short_description': '100% cotton comfortable t-shirt',
                    'sku': 'TSHIRT-COT-001',
                    'price': 599.0,
                    'compare_price': 799.0,
                    'stock_quantity': 100,
                    'category_id': clothing_category.id
                }
            ]
            
            products_created = 0
            for prod_data in product_data:
                existing_product = Product.query.filter_by(sku=prod_data['sku']).first()
                if not existing_product:
                    product = Product(**prod_data)
                    db.session.add(product)
                    products_created += 1
            
            if products_created > 0:
                db.session.commit()
                print(f"Created {products_created} new products!")
            else:
                print("All products already exist!")
        
        print("Sample data seeding completed!")

def reset_db():
    """Reset the database by dropping and recreating all tables"""
    app = create_app()
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Database reset successfully!")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_db()
        seed_data()
    else:
        init_db()
        seed_data()
