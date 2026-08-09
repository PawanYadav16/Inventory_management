import os
import unittest
from sqlalchemy.pool import StaticPool
from flask_login import current_user
from app import create_app, db
from app.models import User, Item, StockTransaction
from config import Config


class TestConfig(Config):
    """Testing configuration override."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False}
    }
    WTF_CSRF_ENABLED = False


class InventorySystemTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test application and in-memory database context."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        """Clean up database and close engine connections after each test."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def register_and_login(self, username='user1', email='user1@example.com', password='password123'):
        """Helper method to register and log in a test user."""
        self.client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)

        res_login = self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
        return res_login

    def test_public_home_page(self):
        """Test public landing home page accessibility."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Inventory Management System', response.data)
        self.assertIn(b'Get Started', response.data)
        self.assertIn(b'Login', response.data)

    def test_registration_and_login_flow(self):
        """Test registration, duplicate validation, and login."""
        # 1. Register User 1
        res = self.client.post('/register', data={
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Registration successful!', res.data)

        # 2. Duplicate registration attempt
        res_dup = self.client.post('/register', data={
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertIn(b'already taken', res_dup.data)

        # 3. Login User 1
        res_login = self.client.post('/login', data={
            'email': 'user1@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Welcome back, user1!', res_login.data)

    def test_item_crud_and_stock_status_logic(self):
        """Test item addition, automatic stock status, and per-user SKU rules."""
        self.register_and_login(username='user1', email='user1@example.com', password='password123')

        # Add Item 1 (In Stock: qty 15 > min 5)
        res_add1 = self.client.post('/items/add', data={
            'name': 'Wireless Keyboard',
            'description': 'RGB keyboard',
            'category': 'Electronics',
            'quantity': 15,
            'minimum_quantity': 5,
            'price': 49.99,
            'supplier': 'TechSupply',
            'sku': 'KBD-100',
            'location': 'Shelf A'
        }, follow_redirects=True)
        self.assertEqual(res_add1.status_code, 200)
        item1 = Item.query.filter_by(sku='KBD-100').first()
        self.assertIsNotNone(item1)
        self.assertEqual(item1.stock_status, 'In Stock')

        # Add Item 2 (Low Stock: 0 < qty 3 <= min 5)
        self.client.post('/items/add', data={
            'name': 'Office Desk',
            'category': 'Furniture',
            'quantity': 3,
            'minimum_quantity': 5,
            'price': 150.00,
            'sku': 'DSK-200'
        })
        item2 = Item.query.filter_by(sku='DSK-200').first()
        self.assertIsNotNone(item2)
        self.assertEqual(item2.stock_status, 'Low Stock')

        # Add Item 3 (Out of Stock: qty 0)
        self.client.post('/items/add', data={
            'name': 'Printer Toner',
            'category': 'Stationery',
            'quantity': 0,
            'minimum_quantity': 5,
            'price': 25.00,
            'sku': 'TNR-300'
        })
        item3 = Item.query.filter_by(sku='TNR-300').first()
        self.assertIsNotNone(item3)
        self.assertEqual(item3.stock_status, 'Out of Stock')

        # Duplicate SKU for user1 should fail
        res_dup_sku = self.client.post('/items/add', data={
            'name': 'Duplicate SKU Item',
            'category': 'Electronics',
            'quantity': 10,
            'minimum_quantity': 5,
            'price': 20.00,
            'sku': 'KBD-100'
        })
        self.assertIn(b'SKUs must be unique within your inventory', res_dup_sku.data)

    def test_per_user_sku_uniqueness(self):
        """Verify that two different users can use the same SKU."""
        # Register user1 & add SKU 'TEST-SKU'
        self.register_and_login(username='u1', email='u1@test.com', password='password123')
        self.client.post('/items/add', data={'name': 'Item U1', 'category': 'Electronics', 'quantity': 10, 'minimum_quantity': 5, 'price': 10.0, 'sku': 'TEST-SKU'})
        self.client.get('/logout')

        # Register user2 & add same SKU 'TEST-SKU' -> must succeed!
        self.register_and_login(username='u2', email='u2@test.com', password='password123')
        res = self.client.post('/items/add', data={'name': 'Item U2', 'category': 'Electronics', 'quantity': 5, 'minimum_quantity': 2, 'price': 20.0, 'sku': 'TEST-SKU'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        # Verify both items exist in database under different users
        items_sku = Item.query.filter_by(sku='TEST-SKU').all()
        self.assertEqual(len(items_sku), 2)

    def test_edit_manual_stock_transaction_and_quantity_controls(self):
        """Test edit item stock transaction logging and +/- quantity buttons."""
        self.register_and_login(username='u1', email='u1@test.com', password='password123')
        
        # Create item with qty 20
        self.client.post('/items/add', data={'name': 'Monitor', 'category': 'Electronics', 'quantity': 20, 'minimum_quantity': 5, 'price': 200.0, 'sku': 'MON-1'})
        item = Item.query.filter_by(sku='MON-1').first()
        self.assertIsNotNone(item)

        # 1. Edit quantity from 20 -> 35 (difference +15)
        self.client.post(f'/items/{item.id}/edit', data={
            'name': 'Monitor Ultra',
            'category': 'Electronics',
            'quantity': 35,
            'minimum_quantity': 5,
            'price': 220.0,
            'sku': 'MON-1'
        })
        
        # Check StockTransaction was logged for manual edit
        tx_edit = StockTransaction.query.filter_by(item_id=item.id, transaction_type='Manual Adjustment').first()
        self.assertIsNotNone(tx_edit)
        self.assertEqual(tx_edit.change, 15)

        # 2. Increase quantity using + button
        self.client.post(f'/items/{item.id}/adjust-quantity', data={'action': 'increase'})
        item_updated = Item.query.get(item.id)
        self.assertEqual(item_updated.quantity, 36)

        # 3. Decrease quantity using - button
        self.client.post(f'/items/{item.id}/adjust-quantity', data={'action': 'decrease'})
        item_updated2 = Item.query.get(item.id)
        self.assertEqual(item_updated2.quantity, 35)

    def test_strict_user_authorization_isolation(self):
        """Verify user A cannot view, edit, delete, or adjust user B's inventory."""
        # Create User A with item
        self.register_and_login(username='userA', email='userA@test.com', password='password123')
        self.client.post('/items/add', data={'name': 'UserA Private Item', 'category': 'Other', 'quantity': 10, 'minimum_quantity': 2, 'price': 99.0, 'sku': 'PRIV-01'})
        item_a = Item.query.filter_by(sku='PRIV-01').first()
        self.assertIsNotNone(item_a)
        self.client.get('/logout')

        # Create User B
        self.register_and_login(username='userB', email='userB@test.com', password='password123')

        # User B attempts unauthorized access to User A's item
        res_view = self.client.get(f'/items/{item_a.id}')
        self.assertEqual(res_view.status_code, 403)

        res_edit = self.client.get(f'/items/{item_a.id}/edit')
        self.assertEqual(res_edit.status_code, 403)

        res_delete = self.client.post(f'/items/{item_a.id}/delete')
        self.assertEqual(res_delete.status_code, 404)

        res_adjust = self.client.post(f'/items/{item_a.id}/adjust-quantity', data={'action': 'increase'})
        self.assertEqual(res_adjust.status_code, 403)

        res_history = self.client.get(f'/items/{item_a.id}/history')
        self.assertEqual(res_history.status_code, 403)

    def test_search_filtering_and_analytics(self):
        """Test search by name/SKU, category filter, and analytics page calculations."""
        self.register_and_login(username='user1', email='u1@test.com', password='password123')
        
        self.client.post('/items/add', data={'name': 'Gaming Mouse', 'category': 'Electronics', 'quantity': 10, 'minimum_quantity': 5, 'price': 50.0, 'sku': 'MS-01'})
        self.client.post('/items/add', data={'name': 'Standing Desk', 'category': 'Furniture', 'quantity': 2, 'minimum_quantity': 5, 'price': 300.0, 'sku': 'DSK-02'})

        # Clear setup flash messages before search assertions
        self.client.get('/dashboard')

        # Search test
        res_search = self.client.get('/dashboard?search=Mouse')
        self.assertIn(b'Gaming Mouse', res_search.data)
        self.assertNotIn(b'Standing Desk', res_search.data)

        # Category filter test
        res_cat = self.client.get('/dashboard?category=Furniture')
        self.assertIn(b'Standing Desk', res_cat.data)
        self.assertNotIn(b'Gaming Mouse', res_cat.data)

        # Analytics page test
        res_analytics = self.client.get('/analytics')
        self.assertEqual(res_analytics.status_code, 200)
        self.assertIn(b'Inventory Analytics', res_analytics.data)
        self.assertIn(b'1,100.00', res_analytics.data)

    def test_currency_preference_and_display(self):
        """Test user currency preference selection and formatting without DB price mutation."""
        self.register_and_login(username='u_curr', email='curr@test.com', password='password123')

        # Add item priced at 19.53
        self.client.post('/items/add', data={'name': 'Sample Item', 'category': 'Other', 'quantity': 5, 'minimum_quantity': 2, 'price': 19.53, 'sku': 'CURR-01'})
        item = Item.query.filter_by(sku='CURR-01').first()
        self.assertEqual(item.price, 19.53)

        # Default currency should be INR (₹)
        res_dash_inr = self.client.get('/dashboard')
        self.assertIn('₹19.53'.encode('utf-8'), res_dash_inr.data)

        # Change currency to USD ($)
        self.client.post('/profile', data={'form_type': 'currency', 'currency': 'USD'}, follow_redirects=True)
        res_dash_usd = self.client.get('/dashboard')
        self.assertIn(b'$19.53', res_dash_usd.data)
        # Verify DB price was NOT mutated
        item_db = Item.query.get(item.id)
        self.assertEqual(item_db.price, 19.53)

        # Change currency to EUR (€)
        self.client.post('/profile', data={'form_type': 'currency', 'currency': 'EUR'}, follow_redirects=True)
        res_dash_eur = self.client.get('/dashboard')
        self.assertIn('€19.53'.encode('utf-8'), res_dash_eur.data)

    def test_delete_item_workflow(self):
        """Test deleting an item from Dashboard removes record and associated transactions from database."""
        self.register_and_login(username='u_del', email='del@test.com', password='password123')
        self.client.post('/items/add', data={'name': 'Item To Delete', 'category': 'Other', 'quantity': 10, 'minimum_quantity': 2, 'price': 15.0, 'sku': 'DEL-101'})
        item = Item.query.filter_by(sku='DEL-101').first()
        self.assertIsNotNone(item)

        # Delete item via POST
        res_del = self.client.post(f'/items/{item.id}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIn(b'has been deleted from your inventory', res_del.data)

        # Verify item and transactions are removed from database
        deleted_item = Item.query.get(item.id)
        self.assertIsNone(deleted_item)
        tx_count = StockTransaction.query.filter_by(item_id=item.id).count()
        self.assertEqual(tx_count, 0)

    def test_delete_item_from_product_details_flow(self):
        """Test deleting an item from Product Details page removes record and redirects to dashboard."""
        self.register_and_login(username='u_del_det', email='del_det@test.com', password='password123')
        self.client.post('/items/add', data={'name': 'Detail Item Delete', 'category': 'Stationery', 'quantity': 5, 'minimum_quantity': 1, 'price': 12.50, 'sku': 'DEL-DET-99'})
        item = Item.query.filter_by(sku='DEL-DET-99').first()
        self.assertIsNotNone(item)

        # View detail page first
        res_view = self.client.get(f'/items/{item.id}')
        self.assertEqual(res_view.status_code, 200)
        self.assertIn(b'Detail Item Delete', res_view.data)

        # Execute POST delete from details page button
        res_del = self.client.post(f'/items/{item.id}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIn(b'has been deleted from your inventory', res_del.data)

        # Verify item is completely gone from DB and 404 on detail page
        self.assertIsNone(Item.query.get(item.id))
        res_view_after = self.client.get(f'/items/{item.id}')
        self.assertEqual(res_view_after.status_code, 404)

    def test_search_no_results_message(self):
        """Test searching for non-existent items renders 'No products found' banner."""
        self.register_and_login(username='u_srch', email='srch@test.com', password='password123')
        res_no_match = self.client.get('/dashboard?search=xyz-does-not-exist')
        self.assertEqual(res_no_match.status_code, 200)
        self.assertIn(b'No products found', res_no_match.data)
        self.assertIn(b'No inventory items match your search or selected filters', res_no_match.data)

    def test_logged_out_redirects_and_no_cache_headers(self):
        """Verify protected routes redirect logged-out users and send anti-caching headers when authenticated."""
        # 1. Logged-out user access attempt to protected routes
        for protected_url in ['/dashboard', '/analytics', '/profile', '/items/add', '/items/1', '/items/1/edit', '/items/1/history']:
            res = self.client.get(protected_url)
            self.assertEqual(res.status_code, 302)
            self.assertIn('/login', res.location)

        # 2. Login user and verify anti-caching headers on protected response
        self.register_and_login(username='u_cache', email='cache@test.com', password='password123')
        res_auth = self.client.get('/dashboard')
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn('no-store', res_auth.headers.get('Cache-Control', ''))
        self.assertIn('no-cache', res_auth.headers.get('Cache-Control', ''))

        # 3. Logout user and verify session destruction & authentication revocation
        self.client.get('/logout')
        self.assertFalse(current_user.is_authenticated)
        res_post_logout = self.client.get('/dashboard')
        self.assertEqual(res_post_logout.status_code, 302)


if __name__ == '__main__':
    unittest.main()
