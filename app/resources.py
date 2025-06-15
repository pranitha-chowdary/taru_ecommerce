"""
API Resources for Taru E-Commerce
"""
from flask import request, jsonify
from flask_restful import Resource, Api
from functools import wraps
import secrets
from datetime import datetime, timedelta

from app.models import (
    db, User, Product, Category, Order, OrderItem, CartItem, 
    Address, Review, Coupon, Newsletter, ContactMessage,
    ProductImage, ProductVariant, Payment
)
from app.utils import DatabaseUtils

def token_required(f):
    """Decorator to require authentication token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        
        if not token:
            return {'error': 'Token is missing'}, 401
        
        current_user = User.verify_auth_token(token)
        if not current_user:
            return {'error': 'Invalid or expired token'}, 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return {'error': 'Admin privileges required'}, 403
        return f(current_user, *args, **kwargs)
    return decorated

# Authentication APIs
class RegisterAPI(Resource):
    def post(self):
        """User Registration"""
        try:
            data = request.get_json()
            
            # Validation
            required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
            for field in required_fields:
                if not data.get(field):
                    return {'error': f'{field} is required'}, 400
            
            # Check if user already exists
            if DatabaseUtils.get_user_by_email(data['email']):
                return {'error': 'Email already registered'}, 400
            
            if DatabaseUtils.get_user_by_username(data['username']):
                return {'error': 'Username already taken'}, 400
            
            # Create new user
            user = User(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone')
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class LoginAPI(Resource):
    def post(self):
        """User Login"""
        try:
            data = request.get_json()
            
            if not data.get('email') or not data.get('password'):
                return {'error': 'Email and password are required'}, 400
            
            user = DatabaseUtils.get_user_by_email(data['email'])
            
            if not user or not user.check_password(data['password']):
                return {'error': 'Invalid credentials'}, 401
            
            if not user.is_active:
                return {'error': 'Account is deactivated'}, 401
            
            # Generate tokens
            auth_token = user.generate_auth_token()
            refresh_token = user.generate_refresh_token()
            user.update_last_login()
            
            db.session.commit()
            
            return {
                'message': 'Login successful',
                'auth_token': auth_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_admin': user.is_admin
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

class LogoutAPI(Resource):
    @token_required
    def post(self, current_user):
        """User Logout"""
        try:
            current_user.revoke_tokens()
            db.session.commit()
            return {'message': 'Logout successful'}, 200
        except Exception as e:
            return {'error': str(e)}, 500

class RefreshTokenAPI(Resource):
    def post(self):
        """Refresh Authentication Token"""
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return {'error': 'Refresh token is required'}, 400
            
            user = User.query.filter_by(refresh_token=refresh_token).first()
            
            if not user or not user.is_refresh_token_valid():
                return {'error': 'Invalid or expired refresh token'}, 401
            
            # Generate new auth token
            new_auth_token = user.generate_auth_token()
            db.session.commit()
            
            return {
                'auth_token': new_auth_token,
                'message': 'Token refreshed successfully'
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

# User Profile APIs
class ProfileAPI(Resource):
    @token_required
    def get(self, current_user):
        """Get User Profile"""
        return {
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'phone': current_user.phone,
                'is_admin': current_user.is_admin,
                'last_login_at': current_user.last_login_at.isoformat() if current_user.last_login_at else None,
                'created_at': current_user.created_at.isoformat()
            }
        }, 200
    
    @token_required
    def put(self, current_user):
        """Update User Profile"""
        try:
            data = request.get_json()
            
            # Update allowed fields
            if 'first_name' in data:
                current_user.first_name = data['first_name']
            if 'last_name' in data:
                current_user.last_name = data['last_name']
            if 'phone' in data:
                current_user.phone = data['phone']
            
            db.session.commit()
            
            return {'message': 'Profile updated successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class ChangePasswordAPI(Resource):
    @token_required
    def post(self, current_user):
        """Change User Password"""
        try:
            data = request.get_json()
            
            if not data.get('current_password') or not data.get('new_password'):
                return {'error': 'Current password and new password are required'}, 400
            
            if not current_user.check_password(data['current_password']):
                return {'error': 'Current password is incorrect'}, 400
            
            current_user.set_password(data['new_password'])
            # Revoke all existing tokens for security
            current_user.revoke_tokens()
            
            db.session.commit()
            
            return {'message': 'Password changed successfully. Please login again.'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Product APIs
class ProductListAPI(Resource):
    def get(self):
        """Get Products List with Pagination and Filters"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 12, type=int)
            category_id = request.args.get('category_id', type=int)
            search = request.args.get('search')
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            sort_by = request.args.get('sort_by', 'created_at')
            sort_order = request.args.get('sort_order', 'desc')
            
            query = Product.query.filter_by(is_active=True)
            
            # Apply filters
            if category_id:
                query = query.filter_by(category_id=category_id)
            
            if search:
                search_query = f"%{search}%"
                query = query.filter(
                    db.or_(
                        Product.name.ilike(search_query),
                        Product.description.ilike(search_query),
                        Product.tags.ilike(search_query)
                    )
                )
            
            if min_price:
                query = query.filter(Product.price >= min_price)
            
            if max_price:
                query = query.filter(Product.price <= max_price)
            
            # Apply sorting
            if sort_by == 'price':
                query = query.order_by(Product.price.desc() if sort_order == 'desc' else Product.price.asc())
            elif sort_by == 'name':
                query = query.order_by(Product.name.desc() if sort_order == 'desc' else Product.name.asc())
            elif sort_by == 'rating':
                query = query.order_by(Product.rating_average.desc() if sort_order == 'desc' else Product.rating_average.asc())
            else:
                query = query.order_by(Product.created_at.desc() if sort_order == 'desc' else Product.created_at.asc())
            
            products = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'products': [{
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'short_description': product.short_description,
                    'sku': product.sku,
                    'price': product.price,
                    'compare_price': product.compare_price,
                    'discount_percentage': product.discount_percentage,
                    'stock_quantity': product.stock_quantity,
                    'is_in_stock': product.is_in_stock,
                    'is_featured': product.is_featured,
                    'rating_average': product.rating_average,
                    'rating_count': product.rating_count,
                    'category': {
                        'id': product.category.id,
                        'name': product.category.name
                    },
                    'images': [{'id': img.id, 'url': img.image_url, 'is_primary': img.is_primary} for img in product.images],
                    'created_at': product.created_at.isoformat()
                } for product in products.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': products.total,
                    'pages': products.pages,
                    'has_next': products.has_next,
                    'has_prev': products.has_prev
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

class ProductDetailAPI(Resource):
    def get(self, product_id):
        """Get Product Details"""
        try:
            product = Product.query.filter_by(id=product_id, is_active=True).first()
            
            if not product:
                return {'error': 'Product not found'}, 404
            
            # Increment view count
            product.view_count += 1
            db.session.commit()
            
            return {
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'short_description': product.short_description,
                    'sku': product.sku,
                    'price': product.price,
                    'compare_price': product.compare_price,
                    'discount_percentage': product.discount_percentage,
                    'stock_quantity': product.stock_quantity,
                    'is_in_stock': product.is_in_stock,
                    'is_featured': product.is_featured,
                    'weight': product.weight,
                    'dimensions': product.dimensions,
                    'tags': product.tags,
                    'rating_average': product.rating_average,
                    'rating_count': product.rating_count,
                    'view_count': product.view_count,
                    'sold_count': product.sold_count,
                    'category': {
                        'id': product.category.id,
                        'name': product.category.name,
                        'description': product.category.description
                    },
                    'images': [{
                        'id': img.id, 
                        'url': img.image_url, 
                        'alt_text': img.alt_text,
                        'is_primary': img.is_primary,
                        'sort_order': img.sort_order
                    } for img in product.images],
                    'variants': [{
                        'id': variant.id,
                        'name': variant.name,
                        'sku': variant.sku,
                        'price': variant.price,
                        'stock_quantity': variant.stock_quantity,
                        'attributes': variant.attributes
                    } for variant in product.variants if variant.is_active],
                    'reviews': [{
                        'id': review.id,
                        'rating': review.rating,
                        'title': review.title,
                        'comment': review.comment,
                        'user_name': review.user.first_name + ' ' + review.user.last_name,
                        'is_verified_purchase': review.is_verified_purchase,
                        'created_at': review.created_at.isoformat()
                    } for review in product.reviews if review.is_approved],
                    'created_at': product.created_at.isoformat()
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

# Category APIs
class CategoryListAPI(Resource):
    def get(self):
        """Get Categories List"""
        try:
            categories = Category.query.filter_by(is_active=True).all()
            
            return {
                'categories': [{
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'image_url': category.image_url,
                    'parent_id': category.parent_id,
                    'subcategories': [{
                        'id': sub.id,
                        'name': sub.name,
                        'description': sub.description
                    } for sub in category.subcategories if sub.is_active],
                    'product_count': len([p for p in category.products if p.is_active])
                } for category in categories]
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

class CategoryDetailAPI(Resource):
    def get(self, category_id):
        """Get Category Details with Products"""
        try:
            category = Category.query.filter_by(id=category_id, is_active=True).first()
            
            if not category:
                return {'error': 'Category not found'}, 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 12, type=int)
            
            products = DatabaseUtils.get_products_by_category(category_id, page, per_page)
            
            return {
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'image_url': category.image_url,
                    'parent_id': category.parent_id
                },
                'products': [{
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'compare_price': product.compare_price,
                    'discount_percentage': product.discount_percentage,
                    'rating_average': product.rating_average,
                    'is_in_stock': product.is_in_stock,
                    'images': [{'url': img.image_url, 'is_primary': img.is_primary} for img in product.images]
                } for product in products.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': products.total,
                    'pages': products.pages,
                    'has_next': products.has_next,
                    'has_prev': products.has_prev
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

# Cart APIs
class CartAPI(Resource):
    @token_required
    def get(self, current_user):
        """Get User Cart"""
        try:
            cart_items = DatabaseUtils.get_user_cart_items(current_user.id)
            
            total_amount = 0
            cart_data = []
            
            for item in cart_items:
                item_total = item.total_price
                total_amount += item_total
                
                cart_data.append({
                    'id': item.id,
                    'product': {
                        'id': item.product.id,
                        'name': item.product.name,
                        'price': item.product.price,
                        'sku': item.product.sku,
                        'images': [{'url': img.image_url, 'is_primary': img.is_primary} for img in item.product.images]
                    },
                    'variant': {
                        'id': item.product_variant.id,
                        'name': item.product_variant.name,
                        'price': item.product_variant.price,
                        'attributes': item.product_variant.attributes
                    } if item.product_variant else None,
                    'quantity': item.quantity,
                    'item_total': item_total,
                    'added_at': item.created_at.isoformat()
                })
            
            return {
                'cart_items': cart_data,
                'total_items': len(cart_items),
                'total_amount': total_amount
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def post(self, current_user):
        """Add Item to Cart"""
        try:
            data = request.get_json()
            
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            variant_id = data.get('variant_id')
            
            if not product_id:
                return {'error': 'Product ID is required'}, 400
            
            product = Product.query.filter_by(id=product_id, is_active=True).first()
            if not product:
                return {'error': 'Product not found'}, 404
            
            # Check if item already exists in cart
            existing_item = CartItem.query.filter_by(
                user_id=current_user.id,
                product_id=product_id,
                product_variant_id=variant_id
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                db.session.commit()
                return {'message': 'Cart updated successfully'}, 200
            else:
                cart_item = CartItem(
                    user_id=current_user.id,
                    product_id=product_id,
                    product_variant_id=variant_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
                db.session.commit()
                return {'message': 'Item added to cart successfully'}, 201
                
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class CartItemAPI(Resource):
    @token_required
    def put(self, current_user, item_id):
        """Update Cart Item Quantity"""
        try:
            data = request.get_json()
            quantity = data.get('quantity', 1)
            
            cart_item = CartItem.query.filter_by(
                id=item_id,
                user_id=current_user.id
            ).first()
            
            if not cart_item:
                return {'error': 'Cart item not found'}, 404
            
            if quantity <= 0:
                db.session.delete(cart_item)
                message = 'Item removed from cart'
            else:
                cart_item.quantity = quantity
                message = 'Cart item updated successfully'
            
            db.session.commit()
            return {'message': message}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500
    
    @token_required
    def delete(self, current_user, item_id):
        """Remove Item from Cart"""
        try:
            cart_item = CartItem.query.filter_by(
                id=item_id,
                user_id=current_user.id
            ).first()
            
            if not cart_item:
                return {'error': 'Cart item not found'}, 404
            
            db.session.delete(cart_item)
            db.session.commit()
            
            return {'message': 'Item removed from cart successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Order APIs
class OrderAPI(Resource):
    @token_required
    def get(self, current_user):
        """Get User Orders"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            orders = DatabaseUtils.get_user_orders(current_user.id, page, per_page)
            
            return {
                'orders': [{
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'total_amount': order.total_amount,
                    'subtotal': order.subtotal,
                    'tax_amount': order.tax_amount,
                    'shipping_amount': order.shipping_amount,
                    'discount_amount': order.discount_amount,
                    'item_count': len(order.order_items),
                    'created_at': order.created_at.isoformat(),
                    'confirmed_at': order.confirmed_at.isoformat() if order.confirmed_at else None,
                    'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
                    'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
                } for order in orders.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': orders.total,
                    'pages': orders.pages,
                    'has_next': orders.has_next,
                    'has_prev': orders.has_prev
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def post(self, current_user):
        """Create New Order"""
        try:
            data = request.get_json()
            
            # Get cart items
            cart_items = DatabaseUtils.get_user_cart_items(current_user.id)
            
            if not cart_items:
                return {'error': 'Cart is empty'}, 400
            
            # Calculate totals
            subtotal = sum(item.total_price for item in cart_items)
            tax_amount = data.get('tax_amount', 0)
            shipping_amount = data.get('shipping_amount', 0)
            discount_amount = data.get('discount_amount', 0)
            total_amount = subtotal + tax_amount + shipping_amount - discount_amount
            
            # Create order
            order = Order(
                order_number=DatabaseUtils.create_order_number(),
                user_id=current_user.id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                billing_address=data.get('billing_address'),
                shipping_address=data.get('shipping_address'),
                notes=data.get('notes')
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Create order items
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    product_variant_id=cart_item.product_variant_id,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku,
                    variant_name=cart_item.product_variant.name if cart_item.product_variant else None,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product_variant.price if cart_item.product_variant and cart_item.product_variant.price else cart_item.product.price,
                    total_price=cart_item.total_price
                )
                db.session.add(order_item)
            
            # Clear cart
            for cart_item in cart_items:
                db.session.delete(cart_item)
            
            db.session.commit()
            
            return {
                'message': 'Order created successfully',
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'total_amount': order.total_amount,
                    'status': order.status
                }
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class OrderDetailAPI(Resource):
    @token_required
    def get(self, current_user, order_id):
        """Get Order Details"""
        try:
            order = Order.query.filter_by(
                id=order_id,
                user_id=current_user.id
            ).first()
            
            if not order:
                return {'error': 'Order not found'}, 404
            
            return {
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'subtotal': order.subtotal,
                    'tax_amount': order.tax_amount,
                    'shipping_amount': order.shipping_amount,
                    'discount_amount': order.discount_amount,
                    'total_amount': order.total_amount,
                    'billing_address': order.billing_address,
                    'shipping_address': order.shipping_address,
                    'notes': order.notes,
                    'items': [{
                        'id': item.id,
                        'product_name': item.product_name,
                        'product_sku': item.product_sku,
                        'variant_name': item.variant_name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'total_price': item.total_price,
                        'product': {
                            'id': item.product.id,
                            'name': item.product.name,
                            'images': [{'url': img.image_url, 'is_primary': img.is_primary} for img in item.product.images]
                        } if item.product else None
                    } for item in order.order_items],
                    'payments': [{
                        'id': payment.id,
                        'payment_method': payment.payment_method,
                        'amount': payment.amount,
                        'status': payment.status,
                        'transaction_id': payment.transaction_id,
                        'created_at': payment.created_at.isoformat()
                    } for payment in order.payments],
                    'created_at': order.created_at.isoformat(),
                    'confirmed_at': order.confirmed_at.isoformat() if order.confirmed_at else None,
                    'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
                    'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

# Wishlist APIs
class WishlistAPI(Resource):
    @token_required
    def get(self, current_user):
        """Get User Wishlist"""
        try:
            return {
                'wishlist': [{
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'compare_price': product.compare_price,
                    'discount_percentage': product.discount_percentage,
                    'is_in_stock': product.is_in_stock,
                    'rating_average': product.rating_average,
                    'images': [{'url': img.image_url, 'is_primary': img.is_primary} for img in product.images]
                } for product in current_user.wishlist_products if product.is_active]
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def post(self, current_user):
        """Add Product to Wishlist"""
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            
            if not product_id:
                return {'error': 'Product ID is required'}, 400
            
            product = Product.query.filter_by(id=product_id, is_active=True).first()
            if not product:
                return {'error': 'Product not found'}, 404
            
            if product in current_user.wishlist_products:
                return {'error': 'Product already in wishlist'}, 400
            
            current_user.wishlist_products.append(product)
            db.session.commit()
            
            return {'message': 'Product added to wishlist successfully'}, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class WishlistItemAPI(Resource):
    @token_required
    def delete(self, current_user, product_id):
        """Remove Product from Wishlist"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return {'error': 'Product not found'}, 404
            
            if product not in current_user.wishlist_products:
                return {'error': 'Product not in wishlist'}, 400
            
            current_user.wishlist_products.remove(product)
            db.session.commit()
            
            return {'message': 'Product removed from wishlist successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Review APIs
class ReviewAPI(Resource):
    @token_required
    def post(self, current_user, product_id):
        """Add Product Review"""
        try:
            data = request.get_json()
            
            rating = data.get('rating')
            title = data.get('title')
            comment = data.get('comment')
            
            if not rating or rating not in range(1, 6):
                return {'error': 'Rating must be between 1 and 5'}, 400
            
            product = Product.query.filter_by(id=product_id, is_active=True).first()
            if not product:
                return {'error': 'Product not found'}, 404
            
            # Check if user already reviewed this product
            existing_review = Review.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()
            
            if existing_review:
                return {'error': 'You have already reviewed this product'}, 400
            
            # Check if user has purchased this product
            has_purchased = db.session.query(OrderItem).join(Order).filter(
                Order.user_id == current_user.id,
                OrderItem.product_id == product_id,
                Order.status.in_(['confirmed', 'processing', 'shipped', 'delivered'])
            ).first()
            
            review = Review(
                user_id=current_user.id,
                product_id=product_id,
                rating=rating,
                title=title,
                comment=comment,
                is_verified_purchase=bool(has_purchased)
            )
            
            db.session.add(review)
            db.session.commit()
            
            # Update product rating
            DatabaseUtils.update_product_rating(product_id)
            
            return {'message': 'Review added successfully'}, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Address APIs
class AddressAPI(Resource):
    @token_required
    def get(self, current_user):
        """Get User Addresses"""
        try:
            addresses = Address.query.filter_by(user_id=current_user.id).all()
            
            return {
                'addresses': [{
                    'id': address.id,
                    'type': address.type,
                    'first_name': address.first_name,
                    'last_name': address.last_name,
                    'company': address.company,
                    'address_line_1': address.address_line_1,
                    'address_line_2': address.address_line_2,
                    'city': address.city,
                    'state': address.state,
                    'postal_code': address.postal_code,
                    'country': address.country,
                    'phone': address.phone,
                    'is_default': address.is_default,
                    'created_at': address.created_at.isoformat()
                } for address in addresses]
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def post(self, current_user):
        """Add New Address"""
        try:
            data = request.get_json()
            
            required_fields = ['first_name', 'last_name', 'address_line_1', 'city', 'state', 'postal_code']
            for field in required_fields:
                if not data.get(field):
                    return {'error': f'{field} is required'}, 400
            
            # If this is set as default, unset other defaults
            if data.get('is_default'):
                Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
            
            address = Address(
                user_id=current_user.id,
                type=data.get('type', 'shipping'),
                first_name=data['first_name'],
                last_name=data['last_name'],
                company=data.get('company'),
                address_line_1=data['address_line_1'],
                address_line_2=data.get('address_line_2'),
                city=data['city'],
                state=data['state'],
                postal_code=data['postal_code'],
                country=data.get('country', 'India'),
                phone=data.get('phone'),
                is_default=data.get('is_default', False)
            )
            
            db.session.add(address)
            db.session.commit()
            
            return {'message': 'Address added successfully', 'address_id': address.id}, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class AddressDetailAPI(Resource):
    @token_required
    def put(self, current_user, address_id):
        """Update Address"""
        try:
            address = Address.query.filter_by(
                id=address_id,
                user_id=current_user.id
            ).first()
            
            if not address:
                return {'error': 'Address not found'}, 404
            
            data = request.get_json()
            
            # Update fields
            for field in ['first_name', 'last_name', 'company', 'address_line_1', 
                         'address_line_2', 'city', 'state', 'postal_code', 'country', 'phone']:
                if field in data:
                    setattr(address, field, data[field])
            
            # Handle default address
            if data.get('is_default'):
                Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
                address.is_default = True
            
            db.session.commit()
            
            return {'message': 'Address updated successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500
    
    @token_required
    def delete(self, current_user, address_id):
        """Delete Address"""
        try:
            address = Address.query.filter_by(
                id=address_id,
                user_id=current_user.id
            ).first()
            
            if not address:
                return {'error': 'Address not found'}, 404
            
            db.session.delete(address)
            db.session.commit()
            
            return {'message': 'Address deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Contact APIs
class ContactAPI(Resource):
    def post(self):
        """Submit Contact Form"""
        try:
            data = request.get_json()
            
            required_fields = ['name', 'email', 'subject', 'message']
            for field in required_fields:
                if not data.get(field):
                    return {'error': f'{field} is required'}, 400
            
            contact_message = ContactMessage(
                name=data['name'],
                email=data['email'],
                phone=data.get('phone'),
                subject=data['subject'],
                message=data['message']
            )
            
            db.session.add(contact_message)
            db.session.commit()
            
            return {'message': 'Contact message sent successfully'}, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class NewsletterAPI(Resource):
    def post(self):
        """Subscribe to Newsletter"""
        try:
            data = request.get_json()
            email = data.get('email')
            
            if not email:
                return {'error': 'Email is required'}, 400
            
            # Check if already subscribed
            existing = Newsletter.query.filter_by(email=email).first()
            if existing:
                if existing.is_active:
                    return {'error': 'Email already subscribed'}, 400
                else:
                    existing.is_active = True
                    db.session.commit()
                    return {'message': 'Newsletter subscription reactivated'}, 200
            
            newsletter = Newsletter(email=email)
            db.session.add(newsletter)
            db.session.commit()
            
            return {'message': 'Successfully subscribed to newsletter'}, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Admin APIs
class AdminDashboardAPI(Resource):
    @token_required
    @admin_required
    def get(self, current_user):
        """Get Admin Dashboard Stats"""
        try:
            stats = DatabaseUtils.get_sales_stats(30)
            
            # Additional stats
            total_users = User.query.count()
            total_products = Product.query.filter_by(is_active=True).count()
            total_categories = Category.query.filter_by(is_active=True).count()
            low_stock_products = len(DatabaseUtils.get_low_stock_products())
            
            recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
            
            return {
                'sales_stats': stats,
                'total_users': total_users,
                'total_products': total_products,
                'total_categories': total_categories,
                'low_stock_products': low_stock_products,
                'recent_orders': [{
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': f"{order.customer.first_name} {order.customer.last_name}",
                    'total_amount': order.total_amount,
                    'status': order.status,
                    'created_at': order.created_at.isoformat()
                } for order in recent_orders]
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

class AdminProductAPI(Resource):
    @token_required
    @admin_required
    def get(self, current_user):
        """Get All Products for Admin"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            products = Product.query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'products': [{
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'price': product.price,
                    'stock_quantity': product.stock_quantity,
                    'is_active': product.is_active,
                    'is_featured': product.is_featured,
                    'category_name': product.category.name,
                    'sold_count': product.sold_count,
                    'view_count': product.view_count,
                    'created_at': product.created_at.isoformat()
                } for product in products.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': products.total,
                    'pages': products.pages,
                    'has_next': products.has_next,
                    'has_prev': products.has_prev
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    @admin_required
    def post(self, current_user):
        """Create New Product"""
        try:
            data = request.get_json()
            
            required_fields = ['name', 'sku', 'price', 'category_id']
            for field in required_fields:
                if not data.get(field):
                    return {'error': f'{field} is required'}, 400
            
            # Check if SKU already exists
            if DatabaseUtils.get_product_by_sku(data['sku']):
                return {'error': 'SKU already exists'}, 400
            
            product = Product(
                name=data['name'],
                description=data.get('description'),
                short_description=data.get('short_description'),
                sku=data['sku'],
                price=data['price'],
                compare_price=data.get('compare_price'),
                cost_price=data.get('cost_price'),
                stock_quantity=data.get('stock_quantity', 0),
                min_stock_level=data.get('min_stock_level', 5),
                weight=data.get('weight'),
                dimensions=data.get('dimensions'),
                category_id=data['category_id'],
                is_active=data.get('is_active', True),
                is_featured=data.get('is_featured', False),
                is_digital=data.get('is_digital', False),
                requires_shipping=data.get('requires_shipping', True),
                tags=data.get('tags')
            )
            
            db.session.add(product)
            db.session.commit()
            
            return {
                'message': 'Product created successfully',
                'product_id': product.id
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class AdminProductDetailAPI(Resource):
    @token_required
    @admin_required
    def put(self, current_user, product_id):
        """Update Product"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return {'error': 'Product not found'}, 404
            
            data = request.get_json()
            
            # Update fields
            for field in ['name', 'description', 'short_description', 'price', 'compare_price',
                         'cost_price', 'stock_quantity', 'min_stock_level', 'weight', 'dimensions',
                         'category_id', 'is_active', 'is_featured', 'is_digital', 'requires_shipping', 'tags']:
                if field in data:
                    setattr(product, field, data[field])
            
            db.session.commit()
            
            return {'message': 'Product updated successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500
    
    @token_required
    @admin_required
    def delete(self, current_user, product_id):
        """Delete Product"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return {'error': 'Product not found'}, 404
            
            # Soft delete - just set as inactive
            product.is_active = False
            db.session.commit()
            
            return {'message': 'Product deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class AdminOrderAPI(Resource):
    @token_required
    @admin_required
    def get(self, current_user):
        """Get All Orders for Admin"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status')
            
            query = Order.query
            if status:
                query = query.filter_by(status=status)
            
            orders = query.order_by(Order.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'orders': [{
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer': {
                        'id': order.customer.id,
                        'name': f"{order.customer.first_name} {order.customer.last_name}",
                        'email': order.customer.email
                    },
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'total_amount': order.total_amount,
                    'item_count': len(order.order_items),
                    'created_at': order.created_at.isoformat()
                } for order in orders.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': orders.total,
                    'pages': orders.pages,
                    'has_next': orders.has_next,
                    'has_prev': orders.has_prev
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500

class AdminOrderDetailAPI(Resource):
    @token_required
    @admin_required
    def put(self, current_user, order_id):
        """Update Order Status"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return {'error': 'Order not found'}, 404
            
            data = request.get_json()
            new_status = data.get('status')
            
            if new_status not in ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']:
                return {'error': 'Invalid status'}, 400
            
            order.status = new_status
            
            # Update timestamps based on status
            if new_status == 'confirmed' and not order.confirmed_at:
                order.confirmed_at = datetime.utcnow()
            elif new_status == 'shipped' and not order.shipped_at:
                order.shipped_at = datetime.utcnow()
            elif new_status == 'delivered' and not order.delivered_at:
                order.delivered_at = datetime.utcnow()
            
            db.session.commit()
            
            return {'message': 'Order status updated successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

# Search API
class SearchAPI(Resource):
    def get(self):
        """Global Search for Products"""
        try:
            query = request.args.get('q', '')
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 12, type=int)
            
            if not query:
                return {'error': 'Search query is required'}, 400
            
            products = DatabaseUtils.search_products(query, page, per_page)
            
            return {
                'query': query,
                'products': [{
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'compare_price': product.compare_price,
                    'discount_percentage': product.discount_percentage,
                    'rating_average': product.rating_average,
                    'is_in_stock': product.is_in_stock,
                    'category_name': product.category.name,
                    'images': [{'url': img.image_url, 'is_primary': img.is_primary} for img in product.images]
                } for product in products.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': products.total,
                    'pages': products.pages,
                    'has_next': products.has_next,
                    'has_prev': products.has_prev
                }
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
