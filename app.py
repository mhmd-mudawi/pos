from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

# Database setup
DB_PATH = 'pos_system.db'

def init_db():
    """Initialize the database with required tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        total_purchase_price REAL DEFAULT 0,
        unit_purchase_price REAL DEFAULT 0,
        unit_selling_price REAL DEFAULT 0,
        unit_profit REAL DEFAULT 0,
        expiry_date TEXT,
        location TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create sales table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_purchase_price REAL NOT NULL,
        unit_selling_price REAL NOT NULL,
        unit_profit REAL NOT NULL,
        total_selling_price REAL NOT NULL,
        discount REAL DEFAULT 0,
        final_selling_price REAL NOT NULL,
        total_profit REAL NOT NULL,
        customer_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    ''')
    
    # Create purchases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        supplier_id INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    )
    ''')
    
    # Create customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create suppliers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create notes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database on startup
@app.before_first_request
def before_first_request():
    init_db()

# Routes
@app.route('/')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')

@app.route('/inventory')
def inventory():
    """Render the inventory page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        p.id, 
        p.name, 
        p.quantity as total_quantity,
        p.total_purchase_price,
        p.unit_purchase_price,
        p.unit_selling_price,
        p.unit_profit,
        p.expiry_date,
        p.location,
        p.notes,
        COALESCE(SUM(s.quantity), 0) as sold_quantity,
        (p.quantity - COALESCE(SUM(s.quantity), 0)) as available_quantity,
        (p.quantity * p.unit_purchase_price) as inventory_purchase_value,
        (p.quantity * p.unit_selling_price) as inventory_selling_value,
        ((p.quantity * p.unit_selling_price) - (p.quantity * p.unit_purchase_price)) as inventory_profit,
        COALESCE(SUM(s.total_selling_price), 0) as total_sales,
        COALESCE(SUM(s.total_profit), 0) as total_profit_earned
    FROM 
        products p
    LEFT JOIN 
        sales s ON p.id = s.product_id
    GROUP BY 
        p.id
    ''')
    
    products = cursor.fetchall()
    conn.close()
    
    return render_template('inventory.html', products=products)

# API Routes for AJAX operations
@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product to inventory"""
    try:
        data = request.json
        name = data.get('name')
        quantity = int(data.get('quantity', 0))
        total_purchase_price = float(data.get('total_purchase_price', 0))
        unit_selling_price = float(data.get('unit_selling_price', 0))
        expiry_date = data.get('expiry_date', '')
        location = data.get('location', '')
        notes = data.get('notes', '')
        
        # Calculate unit purchase price and profit
        unit_purchase_price = total_purchase_price / quantity if quantity > 0 else 0
        unit_profit = unit_selling_price - unit_purchase_price
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO products 
        (name, quantity, total_purchase_price, unit_purchase_price, unit_selling_price, unit_profit, expiry_date, location, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, quantity, total_purchase_price, unit_purchase_price, unit_selling_price, unit_profit, expiry_date, location, notes))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'product_id': product_id, 'message': 'Product added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding product: {str(e)}'})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product"""
    try:
        data = request.json
        name = data.get('name')
        quantity = int(data.get('quantity', 0))
        total_purchase_price = float(data.get('total_purchase_price', 0))
        unit_selling_price = float(data.get('unit_selling_price', 0))
        expiry_date = data.get('expiry_date', '')
        location = data.get('location', '')
        notes = data.get('notes', '')
        
        # Calculate unit purchase price and profit
        unit_purchase_price = total_purchase_price / quantity if quantity > 0 else 0
        unit_profit = unit_selling_price - unit_purchase_price
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE products 
        SET name=?, quantity=?, total_purchase_price=?, unit_purchase_price=?, unit_selling_price=?, unit_profit=?, expiry_date=?, location=?, notes=?
        WHERE id=?
        ''', (name, quantity, total_purchase_price, unit_purchase_price, unit_selling_price, unit_profit, expiry_date, location, notes, product_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating product: {str(e)}'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if product has sales or purchases
        cursor.execute('SELECT COUNT(*) FROM sales WHERE product_id = ?', (product_id,))
        sales_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM purchases WHERE product_id = ?', (product_id,))
        purchases_count = cursor.fetchone()[0]
        
        if sales_count > 0 or purchases_count > 0:
            conn.close()
            return jsonify({
                'success': False, 
                'message': 'Cannot delete product with associated sales or purchases. Consider marking it as inactive instead.'
            })
        
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting product: {str(e)}'})

# Routes for sales
@app.route('/sales/new')
def new_sale():
    """Render the new sale page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM products WHERE (quantity - COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = products.id), 0)) > 0')
    products = cursor.fetchall()
    
    cursor.execute('SELECT id, name FROM customers')
    customers = cursor.fetchall()
    
    conn.close()
    
    return render_template('new_sale.html', products=products, customers=customers)

# Update the sales_records route in app.py to include customers for the edit modal

@app.route('/sales/records')
def sales_records():
    """Render the sales records page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all sales with related data
    cursor.execute('''
    SELECT 
        s.id, 
        s.date, 
        p.id as product_id,
        p.name as product_name, 
        s.quantity, 
        s.unit_purchase_price, 
        s.unit_selling_price, 
        s.unit_profit, 
        s.total_selling_price, 
        s.discount, 
        s.final_selling_price, 
        s.total_profit, 
        s.customer_id,
        c.name as customer_name, 
        s.notes
    FROM 
        sales s
    JOIN 
        products p ON s.product_id = p.id
    LEFT JOIN 
        customers c ON s.customer_id = c.id
    ORDER BY 
        s.date DESC
    ''')
    
    sales = cursor.fetchall()
    
    # Get all customers for the edit modal dropdown
    cursor.execute('SELECT id, name FROM customers')
    customers = cursor.fetchall()
    
    conn.close()
    
    return render_template('sales_records.html', sales=sales, customers=customers)
@app.route('/api/sales', methods=['POST'])
def add_sale():
    """Add a new sale"""
    try:
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity'))
        customer_id = data.get('customer_id')
        if customer_id:
            customer_id = int(customer_id)
        notes = data.get('notes', '')
        discount = float(data.get('discount', 0))
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get product details
        cursor.execute('SELECT unit_purchase_price, unit_selling_price, unit_profit FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found!'})
        
        unit_purchase_price = product['unit_purchase_price']
        unit_selling_price = product['unit_selling_price']
        unit_profit = product['unit_profit']
        
        # Calculate prices
        total_selling_price = unit_selling_price * quantity
        final_selling_price = total_selling_price - discount
        total_profit = (unit_profit * quantity) - discount
        
        # Check if enough inventory is available
        cursor.execute('''
        SELECT 
            p.quantity - COALESCE(SUM(s.quantity), 0) as available
        FROM 
            products p
        LEFT JOIN 
            sales s ON p.id = s.product_id
        WHERE 
            p.id = ?
        GROUP BY 
            p.id
        ''', (product_id,))
        
        available_result = cursor.fetchone()
        available = available_result['available'] if available_result else 0
        
        if available < quantity:
            conn.close()
            return jsonify({
                'success': False, 
                'message': f'Not enough inventory! Only {available} units available.'
            })
        
        # Add the sale
        cursor.execute('''
        INSERT INTO sales 
        (date, product_id, quantity, unit_purchase_price, unit_selling_price, unit_profit, 
        total_selling_price, discount, final_selling_price, total_profit, customer_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, product_id, quantity, unit_purchase_price, unit_selling_price, unit_profit, 
             total_selling_price, discount, final_selling_price, total_profit, customer_id, notes))
        
        sale_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'sale_id': sale_id, 'message': 'Sale recorded successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error recording sale: {str(e)}'})

# Routes for purchases
@app.route('/purchases/new')
def new_purchase():
    """Render the new purchase page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM products')
    products = cursor.fetchall()
    
    cursor.execute('SELECT id, name FROM suppliers')
    suppliers = cursor.fetchall()
    
    conn.close()
    
    return render_template('new_purchase.html', products=products, suppliers=suppliers)

@app.route('/purchases/records')
def purchases_records():
    """Render the purchases records page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        pur.id, 
        pur.date, 
        p.id as product_id,
        p.name as product_name, 
        pur.quantity, 
        pur.unit_price, 
        pur.total_price, 
        pur.supplier_id,
        s.name as supplier_name, 
        pur.notes
    FROM 
        purchases pur
    JOIN 
        products p ON pur.product_id = p.id
    LEFT JOIN 
        suppliers s ON pur.supplier_id = s.id
    ORDER BY 
        pur.date DESC
    ''')
    
    purchases = cursor.fetchall()
    
    # Get all suppliers for the edit modal dropdown
    cursor.execute('SELECT id, name FROM suppliers')
    suppliers = cursor.fetchall()
    
    conn.close()
    
    return render_template('purchases_records.html', purchases=purchases, suppliers=suppliers)
@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    """Add a new purchase"""
    try:
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity'))
        unit_price = float(data.get('unit_price'))
        supplier_id = data.get('supplier_id')
        if supplier_id:
            supplier_id = int(supplier_id)
        notes = data.get('notes', '')
        
        total_price = unit_price * quantity
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT id, name, quantity, total_purchase_price, unit_selling_price FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        
        if product:
            # Update existing product
            current_quantity = product[2]
            current_total_purchase = product[3]
            current_unit_selling = product[4]
            
            new_quantity = current_quantity + quantity
            new_total_purchase = current_total_purchase + total_price
            new_unit_purchase = new_total_purchase / new_quantity if new_quantity > 0 else 0
            new_unit_profit = current_unit_selling - new_unit_purchase
            
            cursor.execute('''
            UPDATE products 
            SET quantity = ?, total_purchase_price = ?, unit_purchase_price = ?, unit_profit = ?
            WHERE id = ?
            ''', (new_quantity, new_total_purchase, new_unit_purchase, new_unit_profit, product_id))
        else:
            return jsonify({'success': False, 'message': 'Product not found!'})
        
        # Add the purchase
        cursor.execute('''
        INSERT INTO purchases 
        (date, product_id, quantity, unit_price, total_price, supplier_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, product_id, quantity, unit_price, total_price, supplier_id, notes))
        
        purchase_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'purchase_id': purchase_id, 'message': 'Purchase recorded successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error recording purchase: {str(e)}'})

# Routes for customers
@app.route('/customers')
def customers():
    """Render the customers page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM customers ORDER BY name')
    customers_list = cursor.fetchall()
    conn.close()
    
    return render_template('customers.html', customers=customers_list)

# Routes for suppliers
@app.route('/suppliers')
def suppliers():
    """Render the suppliers page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM suppliers ORDER BY name')
    suppliers_list = cursor.fetchall()
    conn.close()
    
    return render_template('suppliers.html', suppliers=suppliers_list)

# Routes for reports
@app.route('/reports')
def reports():
    """Render the reports page"""
    return render_template('reports.html')

# Routes for notes
@app.route('/notes')
def notes():
    """Render the notes page"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM notes ORDER BY created_at DESC')
    notes_list = cursor.fetchall()
    conn.close()
    
    return render_template('notes.html', notes=notes_list)

# Dashboard API endpoints
@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total sales
        cursor.execute('''
        SELECT 
            COALESCE(SUM(final_selling_price), 0) as total_sales,
            COALESCE(SUM(total_profit), 0) as total_profits,
            COUNT(*) as sales_count
        FROM sales
        ''')
        sales_stats = cursor.fetchone()
        
        # Get products count
        cursor.execute('SELECT COUNT(*) as count FROM products')
        products_count = cursor.fetchone()['count']
        
        # Get low stock count (less than 5 items)
        cursor.execute('''
        SELECT COUNT(*) as count
        FROM products p
        WHERE (p.quantity - COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = p.id), 0)) < 5
        AND (p.quantity - COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = p.id), 0)) > 0
        ''')
        low_stock_count = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_sales': sales_stats['total_sales'] or 0,
            'total_profits': sales_stats['total_profits'] or 0,
            'sales_count': sales_stats['sales_count'] or 0,
            'products_count': products_count,
            'low_stock_count': low_stock_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching dashboard stats: {str(e)}'})

@app.route('/api/dashboard/recent-sales')
def dashboard_recent_sales():
    """Get recent sales for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            s.id, 
            s.date, 
            p.name as product_name, 
            s.quantity, 
            s.final_selling_price
        FROM 
            sales s
        JOIN 
            products p ON s.product_id = p.id
        ORDER BY 
            s.date DESC
        LIMIT 5
        ''')
        
        sales = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(sales)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching recent sales: {str(e)}'})

@app.route('/api/dashboard/recent-purchases')
def dashboard_recent_purchases():
    """Get recent purchases for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            pur.id, 
            pur.date, 
            p.name as product_name, 
            pur.quantity, 
            pur.total_price
        FROM 
            purchases pur
        JOIN 
            products p ON pur.product_id = p.id
        ORDER BY 
            pur.date DESC
        LIMIT 5
        ''')
        
        purchases = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(purchases)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching recent purchases: {str(e)}'})

@app.route('/api/dashboard/low-stock')
def dashboard_low_stock():
    """Get low stock products for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            p.id, 
            p.name, 
            (p.quantity - COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = p.id), 0)) as available_quantity
        FROM 
            products p
        WHERE 
            (p.quantity - COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = p.id), 0)) < 5
            AND (p.quantity - COALESCE((SELECT SUM(quantity) FROM sales WHERE product_id = p.id), 0)) > 0
        ORDER BY 
            available_quantity ASC
        LIMIT 5
        ''')
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'id': row['id'],
                'name': row['name'],
                'available_quantity': row['available_quantity'],
                'purchase_url': url_for('new_purchase')
            })
        
        conn.close()
        
        return jsonify(products)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching low stock products: {str(e)}'})

# Products API endpoints
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM products WHERE id = ?
        ''', (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        conn.close()
        
        return jsonify({
            'success': True,
            'product': dict(product)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching product: {str(e)}'})

# Batch Sales API
@app.route('/api/sales/batch', methods=['POST'])
def add_batch_sales():
    """Add multiple sales at once"""
    try:
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        customer_id = data.get('customer_id')
        if customer_id:
            customer_id = int(customer_id)
        notes = data.get('notes', '')
        discount = float(data.get('discount', 0))
        items = data.get('items', [])
        
        if not items:
            return jsonify({'success': False, 'message': 'No items provided'})
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Process each sale item
        sale_ids = []
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            
            # Get product details
            cursor.execute('SELECT unit_purchase_price, unit_selling_price, unit_profit FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            
            if not product:
                conn.close()
                return jsonify({'success': False, 'message': f'Product with ID {product_id} not found'})
            
            unit_purchase_price = product['unit_purchase_price']
            unit_selling_price = product['unit_selling_price']
            unit_profit = product['unit_profit']
            
            # Calculate prices
            total_selling_price = unit_selling_price * quantity
            
            # For simplicity, divide the discount equally among all items
            item_discount = discount / len(items) if len(items) > 0 else 0
            
            final_selling_price = total_selling_price - item_discount
            total_profit = (unit_profit * quantity) - item_discount
            
            # Check if enough inventory is available
            cursor.execute('''
            SELECT 
                p.quantity - COALESCE(SUM(s.quantity), 0) as available
            FROM 
                products p
            LEFT JOIN 
                sales s ON p.id = s.product_id
            WHERE 
                p.id = ?
            GROUP BY 
                p.id
            ''', (product_id,))
            
            available_result = cursor.fetchone()
            available = available_result['available'] if available_result else 0
            
            if available < quantity:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'Not enough inventory for product ID {product_id}! Only {available} units available.'
                })
            
            # Add the sale
            cursor.execute('''
            INSERT INTO sales 
            (date, product_id, quantity, unit_purchase_price, unit_selling_price, unit_profit, 
            total_selling_price, discount, final_selling_price, total_profit, customer_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, product_id, quantity, unit_purchase_price, unit_selling_price, unit_profit, 
                 total_selling_price, item_discount, final_selling_price, total_profit, customer_id, notes))
            
            sale_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'sale_ids': sale_ids, 'message': 'Sales recorded successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error recording sales: {str(e)}'})

# Batch Purchases API
@app.route('/api/purchases/batch', methods=['POST'])
def add_batch_purchases():
    """Add multiple purchases at once"""
    try:
        data = request.json
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        supplier_id = data.get('supplier_id')
        if supplier_id:
            supplier_id = int(supplier_id)
        notes = data.get('notes', '')
        items = data.get('items', [])
        
        if not items:
            return jsonify({'success': False, 'message': 'No items provided'})
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Process each purchase item
        purchase_ids = []
        for item in items:
            product_id = item.get('product_id')
            product_name = item.get('product_name')
            quantity = int(item.get('quantity'))
            unit_price = float(item.get('unit_price'))
            selling_price = item.get('selling_price')
            expiry_date = item.get('expiry_date')
            location = item.get('location')
            
            total_price = unit_price * quantity
            
            # If it's a new product
            if not product_id and product_name:
                # Create new product
                if not selling_price:
                    conn.close()
                    return jsonify({'success': False, 'message': 'Selling price is required for new products'})
                
                selling_price = float(selling_price)
                unit_profit = selling_price - unit_price
                
                cursor.execute('''
                INSERT INTO products 
                (name, quantity, total_purchase_price, unit_purchase_price, unit_selling_price, unit_profit, expiry_date, location, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (product_name, quantity, total_price, unit_price, selling_price, unit_profit, expiry_date, location, notes))
                
                product_id = cursor.lastrowid
            
            # Add the purchase
            cursor.execute('''
            INSERT INTO purchases
            (date, product_id, quantity, unit_price, total_price, supplier_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date, product_id, quantity, unit_price, total_price, supplier_id, notes))
            
            purchase_ids.append(cursor.lastrowid)
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'purchase_ids': purchase_ids, 'message': 'Purchases recorded successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error recording purchases: {str(e)}'})

@app.route('/api/sales/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    """Delete a sale record"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First, check if the sale exists
        cursor.execute('SELECT * FROM sales WHERE id = ?', (sale_id,))
        sale = cursor.fetchone()
        
        if not sale:
            conn.close()
            return jsonify({'success': False, 'message': 'Sale record not found'})
        
        # Delete the sale
        cursor.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Sale record deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting sale record: {str(e)}'})

@app.route('/api/purchases/<int:purchase_id>', methods=['DELETE'])
def delete_purchase(purchase_id):
    """Delete a purchase record"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First, check if the purchase exists
        cursor.execute('SELECT * FROM purchases WHERE id = ?', (purchase_id,))
        purchase = cursor.fetchone()
        
        if not purchase:
            conn.close()
            return jsonify({'success': False, 'message': 'Purchase record not found'})
        
        # Get purchase details for updating product quantities
        cursor.execute('''
        SELECT product_id, quantity, unit_price, total_price
        FROM purchases
        WHERE id = ?
        ''', (purchase_id,))
        purchase_data = cursor.fetchone()
        
        if purchase_data:
            product_id, quantity, unit_price, total_price = purchase_data
            
            # Update product quantity and total purchase price
            cursor.execute('''
            SELECT quantity, total_purchase_price, unit_selling_price
            FROM products
            WHERE id = ?
            ''', (product_id,))
            product_data = cursor.fetchone()
            
            if product_data:
                current_quantity, current_total_purchase, unit_selling_price = product_data
                
                # Calculate new values
                new_quantity = max(0, current_quantity - quantity)  # Prevent negative quantities
                new_total_purchase = max(0, current_total_purchase - total_price)  # Prevent negative values
                new_unit_purchase = new_total_purchase / new_quantity if new_quantity > 0 else 0
                new_unit_profit = unit_selling_price - new_unit_purchase if new_unit_purchase <= unit_selling_price else 0
                
                # Update product
                cursor.execute('''
                UPDATE products
                SET quantity = ?, total_purchase_price = ?, unit_purchase_price = ?, unit_profit = ?
                WHERE id = ?
                ''', (new_quantity, new_total_purchase, new_unit_purchase, new_unit_profit, product_id))
        
        # Delete the purchase
        cursor.execute('DELETE FROM purchases WHERE id = ?', (purchase_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Purchase record deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting purchase record: {str(e)}'})

@app.route('/api/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    """Update an existing sale record"""
    try:
        data = request.json
        date = data.get('date')
        quantity = int(data.get('quantity', 0))
        discount = float(data.get('discount', 0))
        customer_id = data.get('customer_id')
        if customer_id:
            customer_id = int(customer_id)
        notes = data.get('notes', '')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get current sale data
        cursor.execute('''
        SELECT 
            s.product_id,
            s.quantity as original_quantity,
            p.unit_purchase_price,
            p.unit_selling_price,
            p.unit_profit
        FROM 
            sales s
        JOIN 
            products p ON s.product_id = p.id
        WHERE 
            s.id = ?
        ''', (sale_id,))
        
        sale_data = cursor.fetchone()
        
        if not sale_data:
            conn.close()
            return jsonify({'success': False, 'message': 'Sale record not found'})
        
        product_id = sale_data['product_id']
        original_quantity = sale_data['original_quantity']
        unit_purchase_price = sale_data['unit_purchase_price']
        unit_selling_price = sale_data['unit_selling_price']
        unit_profit = sale_data['unit_profit']
        
        # Check if there is enough inventory for new quantity
        if quantity > original_quantity:
            # Need to check if there's enough additional inventory
            additional_needed = quantity - original_quantity
            
            cursor.execute('''
            SELECT 
                (p.quantity - COALESCE(SUM(s.quantity), 0) + ?) as available
            FROM 
                products p
            LEFT JOIN 
                sales s ON p.id = s.product_id
            WHERE 
                p.id = ?
            GROUP BY 
                p.id
            ''', (original_quantity, product_id))
            
            available_result = cursor.fetchone()
            available = available_result['available'] if available_result else 0
            
            if available < quantity:
                conn.close()
                return jsonify({
                    'success': False, 
                    'message': f'Not enough inventory! Only {available} units available for this product.'
                })
        
        # Calculate prices
        total_selling_price = unit_selling_price * quantity
        final_selling_price = total_selling_price - discount
        total_profit = (unit_profit * quantity) - discount
        
        # Update the sale
        cursor.execute('''
        UPDATE sales 
        SET date = ?, quantity = ?, discount = ?, total_selling_price = ?, 
            final_selling_price = ?, total_profit = ?, customer_id = ?, notes = ?
        WHERE id = ?
        ''', (date, quantity, discount, total_selling_price, 
             final_selling_price, total_profit, customer_id, notes, sale_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Sale record updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating sale record: {str(e)}'})

@app.route('/api/purchases/<int:purchase_id>', methods=['PUT'])
def update_purchase(purchase_id):
    """Update an existing purchase record"""
    try:
        data = request.json
        date = data.get('date')
        quantity = int(data.get('quantity', 0))
        unit_price = float(data.get('unit_price', 0))
        supplier_id = data.get('supplier_id')
        if supplier_id:
            supplier_id = int(supplier_id)
        notes = data.get('notes', '')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get current purchase data
        cursor.execute('''
        SELECT 
            product_id,
            quantity as original_quantity,
            unit_price as original_unit_price,
            total_price as original_total_price
        FROM 
            purchases
        WHERE 
            id = ?
        ''', (purchase_id,))
        
        purchase_data = cursor.fetchone()
        
        if not purchase_data:
            conn.close()
            return jsonify({'success': False, 'message': 'Purchase record not found'})
        
        product_id = purchase_data['product_id']
        original_quantity = purchase_data['original_quantity']
        original_unit_price = purchase_data['original_unit_price']
        original_total_price = purchase_data['original_total_price']
        
        # Calculate new total price
        total_price = quantity * unit_price
        
        # Update product inventory based on change in quantity
        cursor.execute('''
        SELECT quantity, total_purchase_price, unit_selling_price
        FROM products
        WHERE id = ?
        ''', (product_id,))
        
        product_data = cursor.fetchone()
        
        if product_data:
            current_quantity = product_data['quantity']
            current_total_purchase = product_data['total_purchase_price']
            current_unit_selling = product_data['unit_selling_price']
            
            # Adjust for quantity and purchase price changes
            quantity_change = quantity - original_quantity
            
            # Update current quantity
            new_quantity = current_quantity + quantity_change
            
            # Remove original purchase price from the total
            adjusted_total_purchase = current_total_purchase - original_total_price
            
            # Add new purchase price to the total
            new_total_purchase = adjusted_total_purchase + total_price
            
            # Calculate new unit purchase price and profit
            new_unit_purchase = new_total_purchase / new_quantity if new_quantity > 0 else 0
            new_unit_profit = current_unit_selling - new_unit_purchase
            
            # Update product data
            cursor.execute('''
            UPDATE products 
            SET quantity = ?, total_purchase_price = ?, unit_purchase_price = ?, unit_profit = ?
            WHERE id = ?
            ''', (new_quantity, new_total_purchase, new_unit_purchase, new_unit_profit, product_id))
        
        # Update the purchase record
        cursor.execute('''
        UPDATE purchases 
        SET date = ?, quantity = ?, unit_price = ?, total_price = ?, supplier_id = ?, notes = ?
        WHERE id = ?
        ''', (date, quantity, unit_price, total_price, supplier_id, notes, purchase_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Purchase record updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating purchase record: {str(e)}'})
    
if __name__ == '__main__':
    app.run(debug=True)