# Taru E-Commerce API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
Most endpoints require authentication. Include the auth token in the Authorization header:
```
Authorization: Bearer <your_auth_token>
```

## API Endpoints

### Authentication APIs

#### 1. User Registration
- **POST** `/auth/register`
- **Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string (optional)"
}
```

#### 2. User Login
- **POST** `/auth/login`
- **Body**:
```json
{
  "email": "string",
  "password": "string"
}
```

#### 3. User Logout
- **POST** `/auth/logout`
- **Headers**: `Authorization: Bearer <token>`

#### 4. Refresh Token
- **POST** `/auth/refresh`
- **Body**:
```json
{
  "refresh_token": "string"
}
```

### User Profile APIs

#### 5. Get Profile
- **GET** `/profile`
- **Headers**: `Authorization: Bearer <token>`

#### 6. Update Profile
- **PUT** `/profile`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "first_name": "string",
  "last_name": "string",
  "phone": "string"
}
```

#### 7. Change Password
- **POST** `/profile/change-password`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

### Product APIs

#### 8. Get Products List
- **GET** `/products`
- **Query Parameters**:
  - `page`: Page number (default: 1)
  - `per_page`: Items per page (default: 12)
  - `category_id`: Filter by category
  - `search`: Search query
  - `min_price`: Minimum price filter
  - `max_price`: Maximum price filter
  - `sort_by`: Sort field (name, price, rating, created_at)
  - `sort_order`: Sort order (asc, desc)

#### 9. Get Product Details
- **GET** `/products/<product_id>`

### Category APIs

#### 10. Get Categories List
- **GET** `/categories`

#### 11. Get Category Details
- **GET** `/categories/<category_id>`
- **Query Parameters**:
  - `page`: Page number
  - `per_page`: Items per page

### Shopping Cart APIs

#### 12. Get Cart
- **GET** `/cart`
- **Headers**: `Authorization: Bearer <token>`

#### 13. Add to Cart
- **POST** `/cart`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "product_id": "integer",
  "quantity": "integer",
  "variant_id": "integer (optional)"
}
```

#### 14. Update Cart Item
- **PUT** `/cart/<item_id>`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "quantity": "integer"
}
```

#### 15. Remove Cart Item
- **DELETE** `/cart/<item_id>`
- **Headers**: `Authorization: Bearer <token>`

### Order APIs

#### 16. Get Orders
- **GET** `/orders`
- **Headers**: `Authorization: Bearer <token>`
- **Query Parameters**:
  - `page`: Page number
  - `per_page`: Items per page

#### 17. Create Order
- **POST** `/orders`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "billing_address": "object",
  "shipping_address": "object",
  "tax_amount": "float",
  "shipping_amount": "float",
  "discount_amount": "float",
  "notes": "string"
}
```

#### 18. Get Order Details
- **GET** `/orders/<order_id>`
- **Headers**: `Authorization: Bearer <token>`

### Wishlist APIs

#### 19. Get Wishlist
- **GET** `/wishlist`
- **Headers**: `Authorization: Bearer <token>`

#### 20. Add to Wishlist
- **POST** `/wishlist`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "product_id": "integer"
}
```

#### 21. Remove from Wishlist
- **DELETE** `/wishlist/<product_id>`
- **Headers**: `Authorization: Bearer <token>`

### Review APIs

#### 22. Add Product Review
- **POST** `/products/<product_id>/reviews`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "rating": "integer (1-5)",
  "title": "string",
  "comment": "string"
}
```

### Address APIs

#### 23. Get Addresses
- **GET** `/addresses`
- **Headers**: `Authorization: Bearer <token>`

#### 24. Add Address
- **POST** `/addresses`
- **Headers**: `Authorization: Bearer <token>`
- **Body**:
```json
{
  "type": "string (shipping/billing)",
  "first_name": "string",
  "last_name": "string",
  "company": "string",
  "address_line_1": "string",
  "address_line_2": "string",
  "city": "string",
  "state": "string",
  "postal_code": "string",
  "country": "string",
  "phone": "string",
  "is_default": "boolean"
}
```

#### 25. Update Address
- **PUT** `/addresses/<address_id>`
- **Headers**: `Authorization: Bearer <token>`

#### 26. Delete Address
- **DELETE** `/addresses/<address_id>`
- **Headers**: `Authorization: Bearer <token>`

### Contact APIs

#### 27. Contact Form
- **POST** `/contact`
- **Body**:
```json
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "subject": "string",
  "message": "string"
}
```

#### 28. Newsletter Subscription
- **POST** `/newsletter`
- **Body**:
```json
{
  "email": "string"
}
```

### Search API

#### 29. Global Search
- **GET** `/search`
- **Query Parameters**:
  - `q`: Search query (required)
  - `page`: Page number
  - `per_page`: Items per page

### Admin APIs (Requires Admin Role)

#### 30. Admin Dashboard
- **GET** `/admin/dashboard`
- **Headers**: `Authorization: Bearer <admin_token>`

#### 31. Get All Products (Admin)
- **GET** `/admin/products`
- **Headers**: `Authorization: Bearer <admin_token>`

#### 32. Create Product (Admin)
- **POST** `/admin/products`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Body**:
```json
{
  "name": "string",
  "description": "string",
  "short_description": "string",
  "sku": "string",
  "price": "float",
  "compare_price": "float",
  "cost_price": "float",
  "stock_quantity": "integer",
  "category_id": "integer",
  "is_active": "boolean",
  "is_featured": "boolean",
  "tags": "string"
}
```

#### 33. Update Product (Admin)
- **PUT** `/admin/products/<product_id>`
- **Headers**: `Authorization: Bearer <admin_token>`

#### 34. Delete Product (Admin)
- **DELETE** `/admin/products/<product_id>`
- **Headers**: `Authorization: Bearer <admin_token>`

#### 35. Get All Orders (Admin)
- **GET** `/admin/orders`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Query Parameters**:
  - `status`: Filter by order status
  - `page`: Page number
  - `per_page`: Items per page

#### 36. Update Order Status (Admin)
- **PUT** `/admin/orders/<order_id>`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Body**:
```json
{
  "status": "string (pending/confirmed/processing/shipped/delivered/cancelled)"
}
```

## Response Format

### Success Response
```json
{
  "message": "Success message",
  "data": {},
  "pagination": {} // (for paginated responses)
}
```

### Error Response
```json
{
  "error": "Error message"
}
```

## Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Authentication Flow
1. Register a new user or login with existing credentials
2. Store the `auth_token` and `refresh_token` from the response
3. Include the `auth_token` in the Authorization header for protected endpoints
4. Use the `refresh_token` to get a new `auth_token` when it expires
5. Logout to revoke all tokens

## Admin Access
To access admin endpoints:
1. Login with an admin account
2. The response will include `"is_admin": true`
3. Use the admin token for admin endpoints

## Sample Usage

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@taruecommerce.com", "password": "admin123"}'
```

### Get Products
```bash
curl -X GET "http://localhost:5000/api/products?page=1&per_page=10&category_id=1"
```

### Add to Cart
```bash
curl -X POST http://localhost:5000/api/cart \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"product_id": 1, "quantity": 2}'
```
