from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Integer, default=200000)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(500), default='')
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    db.create_all()
    if Product.query.count() == 0:
        products = [
            Product(name='Intel Core i9-14900K', category='processors',
                    image_url='https://cdn.citilink.ru/Y7gbDkuUsRhitw8uBa6sw1N895tPabQdhyZTWeRRXtc/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/cdd6d99a-afb3-4ca8-93db-96912c640cc3.jpg',
                    price=58900, quantity=25, date_added='2025-11-15',
                    description='24 ядра / 32 потока, до 6.0 ГГц'),
            Product(name='AMD Ryzen 9 7950X', category='processors',
                    image_url='https://cdn.citilink.ru/bO01DmxnyAob-JluA5zthD2_LcQdHQyIfAn75DWWyq8/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/9b941533-2e82-49b7-bb16-e46e72fed6ff.jpg',
                    price=54900, quantity=18, date_added='2025-10-20',
                    description='16 ядер / 32 потока, до 5.7 ГГц'),
            Product(name='Intel Core i7-14700K', category='processors',
                    image_url='https://cdn.citilink.ru/FgGVt0SbbaLEVIYYF23pu03cNpaHTKDx6zQuC0Iqen0/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/ddbbf773-e717-4ddb-9415-67253991881c.jpg',
                    price=38900, quantity=40, date_added='2025-11-01',
                    description='20 ядер / 28 потоков, до 5.6 ГГц'),
            Product(name='NVIDIA GeForce RTX 4090', category='graphics-cards',
                    image_url='https://cdn.citilink.ru/xMFGTboOSUYe8rnInZasbHzW-skXaLPpfqBlYFSvWZk/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/6b43818c-aac7-4364-8485-9451e45a055e.jpg',
                    price=159900, quantity=8, date_added='2025-09-10',
                    description='24 ГБ GDDR6X, DLSS 3.5'),
            Product(name='NVIDIA GeForce RTX 4080 Super', category='graphics-cards',
                    image_url='https://cdn.citilink.ru/2fwaWdYiwMEl16oIjgR8E3kl9UkIqaGIFWbVyLPUXnU/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/4fceb3d2-f49c-445e-8f4f-1840f5c5ac56.jpg',
                    price=99900, quantity=15, date_added='2025-12-01',
                    description='16 ГБ GDDR6X, DLSS 3.5'),
            Product(name='AMD Radeon RX 7900 XTX', category='graphics-cards',
                    image_url='https://cdn.citilink.ru/pJqeqIZ4-2ug_8fbPKXAAygpATiRnN7qUiQEiHzkP8w/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/41d3dc3e-0ab2-45a0-899b-cf9dcf5451ac.jpg',
                    price=92900, quantity=12, date_added='2025-10-05',
                    description='24 ГБ GDDR6, FSR 3.0'),
            Product(name='NVIDIA GeForce RTX 4070 Ti', category='graphics-cards',
                    image_url='https://cdn.citilink.ru/XceL7vuewLBph0QWbjwKPqmfGjcGQTAHGETQP9BwzcM/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/2644ef97-3e30-4a4c-8e4b-cf5081d1e32c.jpg',
                    price=79900, quantity=22, date_added='2025-11-20',
                    description='12 ГБ GDDR6X, DLSS 3.5'),
            Product(name='ASUS ROG Maximus Z790 Hero', category='motherboards',
                    image_url='https://c.dns-shop.ru/thumb/st1/fit/500/500/85b292f5b1a5f87927fd5be67dab420f/6fa53afc841f1750ae7d07d58a9a59d7642a7e709ab5dc6d731e294859a7bd86.jpg.webp',
                    price=49900, quantity=10, date_added='2025-10-10',
                    description='LGA 1700, DDR5, PCIe 5.0'),
            Product(name='MSI MAG B650 Tomahawk WiFi', category='motherboards',
                    image_url='https://cdn.citilink.ru/60nk7EFU19MZ2WFn5sXGSFalFVSxj-xSHQjLS0YStq0/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/326a2182-e294-48f3-8d78-afeeb72480fc.jpg',
                    price=21900, quantity=30, date_added='2025-11-25',
                    description='AM5, DDR5, PCIe 4.0, Wi-Fi 6E'),
            Product(name='Corsair Vengeance 32GB DDR5', category='memory',
                    image_url='https://c.dns-shop.ru/thumb/st4/fit/500/500/d732dcef8463562d7a292291af472cdf/fa284d22054da8910f82c719320817e112a2f7214ff561e1e0f7d93c0803f50f.jpg.webp',
                    price=12900, quantity=50, date_added='2025-12-05',
                    description='2×16 ГБ, 6000 МГц, CL30'),
            Product(name='G.Skill Trident Z5 64GB DDR5', category='memory',
                    image_url='https://c.dns-shop.ru/thumb/st4/fit/500/500/4bbb1512a05f9bf440dd25c39379a6bb/d2012f480b477d44fc20f3aa62dbe57822463dc62efc5a89a81e4b352f5e9ba2.png.webp',
                    price=24900, quantity=20, date_added='2025-10-30',
                    description='2×32 ГБ, 6400 МГц, CL32'),
            Product(name='Samsung 990 Pro 2TB NVMe', category='storage',
                    image_url='https://cdn.citilink.ru/sOsaUn91aTySsBmZrH0aJ2-h0TJomwLs0Y5qkz3HUz8/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/304fbcd9-0341-4480-a0ab-6c48cec85400.jpg',
                    price=17900, quantity=35, date_added='2025-11-10',
                    description='M.2 NVMe, 7450/6900 МБ/с'),
            Product(name='WD Black SN850X 4TB NVMe', category='storage',
                    image_url='https://cdn.citilink.ru/QrbmVvsiABZ8Dwf0SRu2BjFOzb4omtf_x-v1jj-T34Y/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/52658bbb-6aef-4f87-b7a0-a416eae2fe36.jpg',
                    price=30900, quantity=14, date_added='2025-09-25',
                    description='M.2 NVMe, 7300/6600 МБ/с'),
            Product(name='Corsair RM1000x 1000W', category='power-supplies',
                    image_url='https://c.dns-shop.ru/thumb/st1/fit/500/500/bf64ded173e587e744662120e8e45b11/e86c81135135fb0c386fd402e7863e60a2514ec613c8471b41181b977ac02bb8.jpg.webp',
                    price=18900, quantity=28, date_added='2025-10-15',
                    description='80+ Gold, модульный, ATX 3.1'),
            Product(name='Seasonic Focus GX-850 850W', category='power-supplies',
                    image_url='https://cdn.citilink.ru/9YbVR4ZAqy5nfC3Fy2_jJXRjXRl5FUFRPkat_L09u38/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/829de3ff-7fd0-4c9f-a504-54b78fc51739.jpg',
                    price=14900, quantity=33, date_added='2025-11-05',
                    description='80+ Gold, модульный, ATX 3.0'),
            Product(name='ASUS ROG Swift PG27UQ 27"', category='monitors',
                    image_url='https://cdn.citilink.ru/rLgB1vy9BAj4XV5xtuqnXOAi4HQbD869EsalumRQC0A/resizing_type:fit/gravity:sm/width:400/height:400/plain/product-images/e16e3725-b0ec-4fb5-90c8-6457b8d3f902.jpg',
                    price=69900, quantity=6, date_added='2025-08-20',
                    description='4K UHD, 144 Гц, IPS, G-Sync'),
            Product(name='LG UltraGear 27GP850 27"', category='monitors',
                    image_url='https://c.dns-shop.ru/thumb/st1/fit/500/500/4aec5ca510295cc5ebf0061a1b998a5e/cfda853ff6c9064c8442e4565a6993407d931092a0ad5b2018d0e3248fffa32a.jpg.webp',
                    price=39900, quantity=19, date_added='2025-12-10',
                    description='QHD, 165 Гц, Nano IPS, 1 мс'),
            Product(name='Logitech G Pro X Superlight 2', category='peripherals',
                    image_url='https://c.dns-shop.ru/thumb/st1/fit/wm/0/0/cc709bcbf2f63d7903ee93905486f4f4/c4e6aaa511f96c2e5d6b44aceabebcd06f3ef1944078a0cd66ae06a1666c2c1b.jpg.webp',
                    price=12900, quantity=45, date_added='2025-11-30',
                    description='Беспроводная, 60 г, 32000 DPI'),
        ]
        db.session.add_all(products)
        db.session.commit()

@app.context_processor
def inject_globals():
    cart_count = 0
    cart_total = 0
    if current_user.is_authenticated:
        items = CartItem.query.filter_by(user_id=current_user.id).all()
        cart_count = sum(i.quantity for i in items)
        cart_total = sum(i.product.price * i.quantity for i in items)
    return dict(cart_count=cart_count, cart_total=cart_total, current_user=current_user)

@app.route('/')
def index():
    category = request.args.get('category', '')
    max_price = request.args.get('max_price', 200000, type=int)
    sort = request.args.get('sort', 'default')
    query = Product.query
    if category:
        query = query.filter(Product.category == category)
    query = query.filter(Product.price <= max_price)
    if sort == 'price-asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price-desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'date-desc':
        query = query.order_by(Product.date_added.desc())
    elif sort == 'date-asc':
        query = query.order_by(Product.date_added.asc())
    elif sort == 'qty-desc':
        query = query.order_by(Product.quantity.desc())
    elif sort == 'qty-asc':
        query = query.order_by(Product.quantity.asc())
    elif sort == 'name-asc':
        query = query.order_by(Product.name.asc())
    elif sort == 'name-desc':
        query = query.order_by(Product.name.desc())
    else:
        query = query.order_by(Product.id.desc())
    products = query.all()
    categories = ['processors', 'graphics-cards', 'motherboards', 'memory', 'storage', 'power-supplies', 'monitors', 'peripherals']
    return render_template('index.html', products=products, categories=categories, selected_category=category, max_price=max_price, sort=sort)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if product.quantity < 1:
        return jsonify({'error': 'Нет в наличии'}), 400
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        if item.quantity + 1 > product.quantity:
            return jsonify({'error': 'Недостаточно на складе'}), 400
        item.quantity += 1
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/update-cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    data = request.get_json()
    qty = data.get('quantity', 1)
    item = CartItem.query.get_or_404(item_id)
    if qty <= 0:
        db.session.delete(item)
    else:
        item.quantity = min(qty, item.product.quantity)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/remove-cart/<int:item_id>', methods=['POST'])
@login_required
def remove_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return jsonify({'error': 'Корзина пуста'}), 400
    total = 0
    for item in items:
        if item.quantity > item.product.quantity:
            return jsonify({'error': f'Недостаточно {item.product.name}'}), 400
        total += item.product.price * item.quantity
    if total > current_user.balance:
        return jsonify({'error': 'Недостаточно средств'}), 400
    current_user.balance -= total
    order = Order(user_id=current_user.id, total=total)
    db.session.add(order)
    for item in items:
        item.product.quantity -= item.quantity
        oi = OrderItem(order=order, product_name=item.product.name, price=item.product.price, quantity=item.quantity)
        db.session.add(oi)
        db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'order_id': order.id})

@app.route('/cart')
@login_required
def cart_view():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', items=items)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'].strip().lower()).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username'].strip().lower()
        if User.query.filter_by(username=u).first():
            flash('Пользователь уже существует')
        elif len(request.form['password']) < 4:
            flash('Пароль минимум 4 символа')
        else:
            user = User(username=u, email=request.form['email'], password_hash=generate_password_hash(request.form['password']), balance=200000)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        init_db()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', email='admin@test.ru', password_hash=generate_password_hash('admin123'), balance=500000))
        if not User.query.filter_by(username='test').first():
            db.session.add(User(username='test', email='test@test.ru', password_hash=generate_password_hash('test123'), balance=150000))
        db.session.commit()
    app.run(debug=True)