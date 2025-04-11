import os
import io
import json
import logging
import qrcode
import xlsxwriter
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify, send_file, Response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import Admin, Customer, Product, Order, OrderItem, BotMessage, Setting
from utils import generate_pdf_invoice
from sqlalchemy import func, desc

# Login routes
@app.route('/admin', methods=['GET'])
def admin_login_page():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = 'remember' in request.form
    
    admin = Admin.query.filter_by(username=username).first()
    
    if not admin or not check_password_hash(admin.password_hash, password):
        flash('Invalid username or password', 'danger')
        return redirect(url_for('admin_login_page'))
    
    login_user(admin, remember=remember)
    flash(f'Welcome back, {admin.name}!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login_page'))

# Dashboard routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Get counts for dashboard
    new_orders_count = Order.query.filter_by(status='new').count()
    total_orders_count = Order.query.count()
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get sales data for the last 7 days
    today = datetime.utcnow().date()
    date_from = today - timedelta(days=6)
    
    daily_sales = db.session.query(
        func.date(Order.created_at).label('date'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('total')
    ).filter(
        func.date(Order.created_at) >= date_from
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()
    
    # Format dates for chart
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    
    # Create a dictionary to lookup sales by date
    sales_by_date = {str(item.date): {'count': item.count, 'total': item.total or 0} for item in daily_sales}
    
    # Fill in missing dates
    chart_data = []
    for date in dates:
        if date in sales_by_date:
            chart_data.append({
                'date': date,
                'count': sales_by_date[date]['count'],
                'total': float(sales_by_date[date]['total'])
            })
        else:
            chart_data.append({
                'date': date,
                'count': 0,
                'total': 0.0
            })
    
    # Get top products
    top_products = db.session.query(
        Product.name,
        Product.name_ar,
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).group_by(
        Product.id
    ).order_by(
        desc('total_quantity')
    ).limit(5).all()
    
    return render_template(
        'dashboard.html',
        new_orders_count=new_orders_count,
        total_orders_count=total_orders_count,
        total_products=total_products,
        total_customers=total_customers,
        recent_orders=recent_orders,
        chart_data=json.dumps(chart_data),
        top_products=top_products
    )

# Order routes
@app.route('/admin/orders')
@login_required
def admin_orders():
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Base query
    query = Order.query.join(Customer)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    # Apply search if provided
    if search_query:
        query = query.filter(
            (Customer.full_name.ilike(f'%{search_query}%')) |
            (Customer.phone.ilike(f'%{search_query}%')) |
            (Order.id.cast(db.String).like(f'%{search_query}%'))
        )
    
    # Get orders with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get order statuses for filter
    statuses = [
        {'value': 'new', 'label': 'New'},
        {'value': 'processing', 'label': 'Processing'},
        {'value': 'shipped', 'label': 'Shipped'},
        {'value': 'delivered', 'label': 'Delivered'},
        {'value': 'cancelled', 'label': 'Cancelled'}
    ]
    
    return render_template(
        'orders.html',
        orders=orders,
        statuses=statuses,
        current_status=status_filter,
        search_query=search_query
    )

@app.route('/admin/orders/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    
    return render_template(
        'order_detail.html',
        order=order,
        customer=customer,
        items=order.items
    )

@app.route('/admin/orders/<int:order_id>/update', methods=['POST'])
@login_required
def admin_update_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes')
    
    if status:
        order.status = status
    
    if admin_notes is not None:
        order.admin_notes = admin_notes
    
    db.session.commit()
    flash('Order updated successfully', 'success')
    
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/orders/<int:order_id>/invoice')
@login_required
def admin_generate_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    customer = Customer.query.get(order.customer_id)
    
    # Get business info from settings
    business_name = Setting.get('business_name', 'My Business')
    business_address = Setting.get('business_address', '')
    business_phone = Setting.get('business_phone', '')
    business_email = Setting.get('business_email', '')
    
    # Generate PDF
    pdf_data = generate_pdf_invoice(
        order, customer, order.items,
        business_name, business_address, business_phone, business_email
    )
    
    # Return the PDF file
    return Response(
        pdf_data,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment;filename=invoice_{order.id}.pdf'}
    )

@app.route('/admin/orders/<int:order_id>/qrcode')
@login_required
def admin_generate_qrcode(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Generate the QR code for the order tracking URL
    tracking_url = url_for('order_status', order_id=order.id, _external=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tracking_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'order_{order.id}_qrcode.png'
    )

@app.route('/admin/orders/export')
@login_required
def admin_export_orders():
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Base query
    query = Order.query.join(Customer)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    # Apply search if provided
    if search_query:
        query = query.filter(
            (Customer.full_name.ilike(f'%{search_query}%')) |
            (Customer.phone.ilike(f'%{search_query}%')) |
            (Order.id.cast(db.String).like(f'%{search_query}%'))
        )
    
    # Get all orders matching the filter
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Create an Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Add headers
    headers = ['Order ID', 'Date', 'Customer', 'Phone', 'Products', 'Total', 'Status']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Add data
    for row, order in enumerate(orders, start=1):
        customer = Customer.query.get(order.customer_id)
        
        # Get product names
        products = []
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                products.append(f"{product.name} (x{item.quantity})")
        
        # Write data
        worksheet.write(row, 0, order.id)
        worksheet.write(row, 1, order.created_at.strftime('%Y-%m-%d %H:%M'))
        worksheet.write(row, 2, customer.full_name or customer.messenger_name)
        worksheet.write(row, 3, customer.phone or 'N/A')
        worksheet.write(row, 4, ", ".join(products))
        worksheet.write(row, 5, order.total_amount)
        worksheet.write(row, 6, order.status)
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'orders_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

# Product routes
@app.route('/admin/products')
@login_required
def admin_products():
    search_query = request.args.get('search', '')
    
    # Base query
    query = Product.query
    
    # Apply search if provided
    if search_query:
        query = query.filter(
            (Product.name.ilike(f'%{search_query}%')) |
            (Product.name_ar.ilike(f'%{search_query}%')) |
            (Product.category.ilike(f'%{search_query}%'))
        )
    
    # Get products with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    products = query.order_by(Product.name).paginate(page=page, per_page=per_page)
    
    return render_template(
        'products.html',
        products=products,
        search_query=search_query
    )

@app.route('/admin/products/new', methods=['GET', 'POST'])
@login_required
def admin_new_product():
    if request.method == 'POST':
        name = request.form.get('name')
        name_ar = request.form.get('name_ar')
        description = request.form.get('description')
        description_ar = request.form.get('description_ar')
        price = request.form.get('price')
        category = request.form.get('category')
        category_ar = request.form.get('category_ar')
        active = 'active' in request.form
        
        # Validate required fields
        if not name or not name_ar or not price or not category or not category_ar:
            flash('Please fill out all required fields', 'danger')
            return redirect(url_for('admin_new_product'))
        
        try:
            price = float(price)
        except ValueError:
            flash('Price must be a valid number', 'danger')
            return redirect(url_for('admin_new_product'))
        
        # Create product
        product = Product(
            name=name,
            name_ar=name_ar,
            description=description,
            description_ar=description_ar,
            price=price,
            category=category,
            category_ar=category_ar,
            active=active
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product created successfully', 'success')
        return redirect(url_for('admin_products'))
    
    # Get all categories for dropdown
    categories = db.session.query(Product.category, Product.category_ar).distinct().all()
    
    return render_template('product_form.html', categories=categories)

@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        name_ar = request.form.get('name_ar')
        description = request.form.get('description')
        description_ar = request.form.get('description_ar')
        price = request.form.get('price')
        category = request.form.get('category')
        category_ar = request.form.get('category_ar')
        active = 'active' in request.form
        
        # Validate required fields
        if not name or not name_ar or not price or not category or not category_ar:
            flash('Please fill out all required fields', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))
        
        try:
            price = float(price)
        except ValueError:
            flash('Price must be a valid number', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))
        
        # Update product
        product.name = name
        product.name_ar = name_ar
        product.description = description
        product.description_ar = description_ar
        product.price = price
        product.category = category
        product.category_ar = category_ar
        product.active = active
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin_products'))
    
    # Get all categories for dropdown
    categories = db.session.query(Product.category, Product.category_ar).distinct().all()
    
    return render_template('product_form.html', product=product, categories=categories)

@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is used in any orders
    order_items = OrderItem.query.filter_by(product_id=product_id).first()
    
    if order_items:
        flash('Cannot delete product as it is used in orders. Consider deactivating it instead.', 'danger')
        return redirect(url_for('admin_products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin_products'))

# Bot message routes
@app.route('/admin/bot-messages')
@login_required
def admin_bot_messages():
    messages = BotMessage.query.order_by(BotMessage.message_key).all()
    return render_template('bot_messages.html', messages=messages)

@app.route('/admin/bot-messages/<int:message_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_bot_message(message_id):
    message = BotMessage.query.get_or_404(message_id)
    
    if request.method == 'POST':
        message_text = request.form.get('message_text')
        message_text_ar = request.form.get('message_text_ar')
        
        if not message_text or not message_text_ar:
            flash('Both language versions are required', 'danger')
            return redirect(url_for('admin_edit_bot_message', message_id=message_id))
        
        message.message_text = message_text
        message.message_text_ar = message_text_ar
        message.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Bot message updated successfully', 'success')
        return redirect(url_for('admin_bot_messages'))
    
    return render_template('bot_message_form.html', message=message)

# Settings routes
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        # Business information
        business_name = request.form.get('business_name')
        business_address = request.form.get('business_address')
        business_phone = request.form.get('business_phone')
        business_email = request.form.get('business_email')
        
        # Save settings
        Setting.set('business_name', business_name)
        Setting.set('business_address', business_address)
        Setting.set('business_phone', business_phone)
        Setting.set('business_email', business_email)
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('admin_settings'))
    
    # Get current settings
    settings = {
        'business_name': Setting.get('business_name', ''),
        'business_address': Setting.get('business_address', ''),
        'business_phone': Setting.get('business_phone', ''),
        'business_email': Setting.get('business_email', '')
    }
    
    return render_template('settings.html', settings=settings)

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Update name and email
        if name and email:
            current_user.name = name
            current_user.email = email
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('admin_profile'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('admin_profile'))
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long', 'danger')
                return redirect(url_for('admin_profile'))
            
            current_user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('profile.html')

# Analytics routes
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    # Period filter
    period = request.args.get('period', 'week')
    
    today = datetime.utcnow().date()
    
    if period == 'week':
        date_from = today - timedelta(days=6)
        grouping = func.date(Order.created_at)
        format_str = '%Y-%m-%d'
    elif period == 'month':
        date_from = today.replace(day=1)
        grouping = func.date(Order.created_at)
        format_str = '%Y-%m-%d'
    elif period == 'year':
        date_from = today.replace(month=1, day=1)
        grouping = func.strftime('%Y-%m', Order.created_at)
        format_str = '%Y-%m'
    else:
        # Default to week
        date_from = today - timedelta(days=6)
        grouping = func.date(Order.created_at)
        format_str = '%Y-%m-%d'
    
    # Sales over time
    sales_over_time = db.session.query(
        grouping.label('date'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('total')
    ).filter(
        func.date(Order.created_at) >= date_from
    ).group_by(
        grouping
    ).order_by(
        grouping
    ).all()
    
    # Format for chart
    sales_data = [{
        'date': item.date.strftime(format_str) if hasattr(item.date, 'strftime') else item.date,
        'count': item.count,
        'total': float(item.total) if item.total else 0
    } for item in sales_over_time]
    
    # Top products
    top_products = db.session.query(
        Product.name,
        Product.name_ar,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).group_by(
        Product.id
    ).order_by(
        desc('total_quantity')
    ).limit(10).all()
    
    # Format for chart
    product_data = [{
        'name': item.name,
        'name_ar': item.name_ar,
        'quantity': item.total_quantity,
        'revenue': float(item.total_revenue) if item.total_revenue else 0
    } for item in top_products]
    
    # Order status breakdown
    status_breakdown = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(
        Order.status
    ).all()
    
    # Format for chart
    status_data = [{
        'status': item.status,
        'count': item.count
    } for item in status_breakdown]
    
    # Total metrics
    total_orders = Order.query.count()
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    total_customers = Customer.query.count()
    
    # Recent period metrics for comparison
    if period == 'week':
        prev_date_from = date_from - timedelta(days=7)
        prev_date_to = date_from - timedelta(days=1)
    elif period == 'month':
        prev_date_from = (date_from.replace(day=1) - timedelta(days=1)).replace(day=1)
        prev_date_to = date_from - timedelta(days=1)
    elif period == 'year':
        prev_date_from = date_from.replace(year=date_from.year-1)
        prev_date_to = today.replace(year=today.year-1)
    
    current_period_orders = Order.query.filter(func.date(Order.created_at) >= date_from).count()
    current_period_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(
        func.date(Order.created_at) >= date_from
    ).scalar() or 0
    
    prev_period_orders = Order.query.filter(
        func.date(Order.created_at) >= prev_date_from,
        func.date(Order.created_at) <= prev_date_to
    ).count()
    
    prev_period_revenue = db.session.query(
        func.sum(Order.total_amount)
    ).filter(
        func.date(Order.created_at) >= prev_date_from,
        func.date(Order.created_at) <= prev_date_to
    ).scalar() or 0
    
    # Calculate growth percentages
    order_growth = ((current_period_orders - prev_period_orders) / max(prev_period_orders, 1)) * 100 if prev_period_orders else 100
    revenue_growth = ((current_period_revenue - prev_period_revenue) / max(prev_period_revenue, 1)) * 100 if prev_period_revenue else 100
    
    return render_template(
        'analytics.html',
        period=period,
        sales_data=json.dumps(sales_data),
        product_data=json.dumps(product_data),
        status_data=json.dumps(status_data),
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_customers=total_customers,
        current_period_orders=current_period_orders,
        current_period_revenue=current_period_revenue,
        order_growth=order_growth,
        revenue_growth=revenue_growth
    )
