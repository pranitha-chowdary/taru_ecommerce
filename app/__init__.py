from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
import os

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from app.models import db
    db.init_app(app)
    
    # Initialize Flask-RESTful
    api = Api(app)
    
    # Import and register API resources
    from app.resources import (
        # Authentication APIs
        RegisterAPI, LoginAPI, LogoutAPI, RefreshTokenAPI,
        # Profile APIs
        ProfileAPI, ChangePasswordAPI,
        # Product APIs
        ProductListAPI, ProductDetailAPI,
        # Category APIs
        CategoryListAPI, CategoryDetailAPI,
        # Cart APIs
        CartAPI, CartItemAPI,
        # Order APIs
        OrderAPI, OrderDetailAPI,
        # Wishlist APIs
        WishlistAPI, WishlistItemAPI,
        # Review APIs
        ReviewAPI,
        # Address APIs
        AddressAPI, AddressDetailAPI,
        # Contact APIs
        ContactAPI, NewsletterAPI,
        # Admin APIs
        AdminDashboardAPI, AdminProductAPI, AdminProductDetailAPI,
        AdminOrderAPI, AdminOrderDetailAPI,
        # Search API
        SearchAPI
    )
    
    # Register API routes
    # Authentication routes
    api.add_resource(RegisterAPI, '/api/auth/register')
    api.add_resource(LoginAPI, '/api/auth/login')
    api.add_resource(LogoutAPI, '/api/auth/logout')
    api.add_resource(RefreshTokenAPI, '/api/auth/refresh')
    
    # Profile routes
    api.add_resource(ProfileAPI, '/api/profile')
    api.add_resource(ChangePasswordAPI, '/api/profile/change-password')
    
    # Product routes
    api.add_resource(ProductListAPI, '/api/products')
    api.add_resource(ProductDetailAPI, '/api/products/<int:product_id>')
    
    # Category routes
    api.add_resource(CategoryListAPI, '/api/categories')
    api.add_resource(CategoryDetailAPI, '/api/categories/<int:category_id>')
    
    # Cart routes
    api.add_resource(CartAPI, '/api/cart')
    api.add_resource(CartItemAPI, '/api/cart/<int:item_id>')
    
    # Order routes
    api.add_resource(OrderAPI, '/api/orders')
    api.add_resource(OrderDetailAPI, '/api/orders/<int:order_id>')
    
    # Wishlist routes
    api.add_resource(WishlistAPI, '/api/wishlist')
    api.add_resource(WishlistItemAPI, '/api/wishlist/<int:product_id>')
    
    # Review routes
    api.add_resource(ReviewAPI, '/api/products/<int:product_id>/reviews')
    
    # Address routes
    api.add_resource(AddressAPI, '/api/addresses')
    api.add_resource(AddressDetailAPI, '/api/addresses/<int:address_id>')
    
    # Contact routes
    api.add_resource(ContactAPI, '/api/contact')
    api.add_resource(NewsletterAPI, '/api/newsletter')
    
    # Admin routes
    api.add_resource(AdminDashboardAPI, '/api/admin/dashboard')
    api.add_resource(AdminProductAPI, '/api/admin/products')
    api.add_resource(AdminProductDetailAPI, '/api/admin/products/<int:product_id>')
    api.add_resource(AdminOrderAPI, '/api/admin/orders')
    api.add_resource(AdminOrderDetailAPI, '/api/admin/orders/<int:order_id>')
    
    # Search route
    api.add_resource(SearchAPI, '/api/search')
    
    # Create tables
    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return jsonify({
            "message": "Welcome to Taru E-Commerce API",
            "version": "1.0.0",
            "endpoints": {
                "authentication": "/api/auth/",
                "products": "/api/products/",
                "categories": "/api/categories/",
                "cart": "/api/cart/",
                "orders": "/api/orders/",
                "profile": "/api/profile/",
                "admin": "/api/admin/",
                "search": "/api/search/"
            }
        })
    
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy", "message": "Taru E-Commerce API is running"})

    return app
