import os, sqlite3, secrets, hashlib, hmac, json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, g

BASE=os.path.dirname(__file__)
DB=os.getenv('DATABASE_PATH',os.path.join(BASE,'data','shop.db'))
app=Flask(__name__,static_folder='static',static_url_path='')
ADMIN_EMAIL=os.getenv('ADMIN_EMAIL','admin@shopora.local').lower()
ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD','ChangeMe123!')

def conn():
    if 'db' not in g:
        os.makedirs(os.path.dirname(DB),exist_ok=True)
        g.db=sqlite3.connect(DB,timeout=15)
        g.db.row_factory=sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
        g.db.execute('PRAGMA journal_mode=WAL')
    return g.db

@app.teardown_appcontext
def close(err):
    db=g.pop('db',None)
    if db:db.close()

def passhash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),230000).hex()

def verify(password,hashed):
    try:return hmac.compare_digest(passhash(password,hashed.split(':')[0]),hashed)
    except:return False

def init():
    with app.app_context():
        d=conn()
        d.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'customer',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER NOT NULL,expires TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,title TEXT NOT NULL,category TEXT NOT NULL,price REAL NOT NULL,mrp REAL NOT NULL,stock INTEGER NOT NULL DEFAULT 0,rating REAL NOT NULL DEFAULT 4.4,description TEXT NOT NULL DEFAULT '',image TEXT NOT NULL DEFAULT '',badge TEXT DEFAULT '',featured INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,total REAL NOT NULL,status TEXT DEFAULT 'Placed',address TEXT NOT NULL,payment TEXT NOT NULL,phone TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY,order_id INTEGER NOT NULL,product_id INTEGER,title TEXT NOT NULL,qty INTEGER NOT NULL,price REAL NOT NULL,FOREIGN KEY(order_id) REFERENCES orders(id));''')
        if not d.execute('SELECT 1 FROM users WHERE email=?',(ADMIN_EMAIL,)).fetchone():
            d.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',('Store Administrator',ADMIN_EMAIL,passhash(ADMIN_PASSWORD),'admin'))
        if not d.execute('SELECT 1 FROM products').fetchone():
            demo=[
            ('Wireless Noise Cancelling Headphones','Electronics',1999,3999,42,4.6,'40-hour battery, deep bass, lightweight fit.','https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80','Bestseller',1),
            ('Premium Smart Watch with AMOLED Display','Electronics',2499,5999,29,4.7,'Fitness tracking, heart rate, sleek AMOLED screen.','https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80','Limited deal',1),
            ('Minimalist Everyday Backpack','Fashion',1199,2499,38,4.5,'Water-resistant modern daily carry with laptop pocket.','https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80','Top rated',1),
            ('Running Shoes for Everyday Comfort','Fashion',1799,3499,24,4.4,'Responsive sole and all-day walking comfort.','https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80','Deal',1),
            ('Modern Table Lamp','Home & Kitchen',899,1899,51,4.5,'Warm ambient bedside lighting for modern spaces.','https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80','',0),
            ('Stainless Steel Water Bottle','Home & Kitchen',649,1299,65,4.6,'Vacuum insulated bottle for hot and cold drinks.','https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=800&q=80','',0),
            ('Compact Digital Camera','Electronics',6499,9999,18,4.3,'Lightweight photography camera for travel.','https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=800&q=80','Popular',1),
            ('Wireless Bluetooth Speaker','Electronics',1299,2999,34,4.7,'Powerful portable sound with rich bass.','https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80','Bestseller',1),
            ('Cotton Casual T-Shirt','Fashion',599,1199,77,4.3,'Soft breathable cotton everyday wear.','https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80','',0),
            ('Coffee Maker for Home','Home & Kitchen',2999,5999,16,4.5,'Brew a fresh aromatic coffee every morning.','https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80','Deal',1),
            ('Skincare Essentials Set','Beauty',1599,3199,21,4.7,'Gentle self-care collection for a fresh glow.','https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=800&q=80','New',1),
            ('Classic Sunglasses','Fashion',799,1699,53,4.4,'Timeless everyday UV-protective shades.','https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=800&q=80','',0),
            ('Building Blocks Creative Toy Set','Toys & Games',1099,2299,31,4.8,'Imaginative building fun for little creators.','https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=800&q=80','Family pick',1),
            ('Yoga Mat for Home Workouts','Sports',799,1699,50,4.6,'Non-slip cushioned mat for stretching and yoga.','https://images.unsplash.com/photo-1599447421416-3414500d18a5?w=800&q=80','',0),
            ('Portable Laptop Stand','Electronics',849,1799,40,4.5,'Aluminium ergonomic stand for desk setups.','https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&q=80','',0),
            ('Hardcover Notebook Collection','Books & Stationery',449,899,88,4.6,'Elegant notebooks for planning, writing, journaling.','https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800&q=80','',0)]
            d.executemany('INSERT INTO products(title,category,price,mrp,stock,rating,description,image,badge,featured) VALUES(?,?,?,?,?,?,?,?,?,?)',demo)
        d.commit()
init()

def current_user():
    token=request.headers.get('Authorization','').removeprefix('Bearer ').strip()
    if not token:return None
    return conn().execute('SELECT u.id,u.name,u.email,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?',(token,datetime.utcnow().isoformat())).fetchone()

def auth(admin=False):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args,**kwargs):
            u=current_user()
            if not u:return jsonify(error='Please sign in first'),401
            if admin and u['role']!='admin':return jsonify(error='Admin access required'),403
            return fn(*args,**kwargs)
        return wrapped
    return deco

def data():return request.get_json(silent=True) or {}
def product_row(x):return dict(x)
def error(msg,status=400):return jsonify(error=msg),status

@app.get('/')
def home():return send_from_directory(app.static_folder,'index.html')

@app.get('/api/products')
def products():
    q=request.args.get('q','').strip();cat=request.args.get('category','').strip();sort=request.args.get('sort','popular')
    sql='SELECT * FROM products WHERE 1=1';a=[]
    if q:sql+=' AND (title LIKE ? OR description LIKE ? OR category LIKE ?)';a.extend(['%'+q+'%']*3)
    if cat and cat!='All':sql+=' AND category=?';a.append(cat)
    sql+=' ORDER BY '+{'price-low':'price ASC','price-high':'price DESC','newest':'id DESC','rating':'rating DESC'}.get(sort,'featured DESC,id DESC')
    return jsonify(products=[product_row(r) for r in conn().execute(sql,a).fetchall()])

@app.get('/api/categories')
def categories():return jsonify(categories=[x[0] for x in conn().execute('SELECT DISTINCT category FROM products ORDER BY category')])

@app.post('/api/register')
def register():
    x=data();name=str(x.get('name','')).strip();email=str(x.get('email','')).lower().strip();pw=str(x.get('password',''))
    if not name or '@' not in email or len(pw)<8:return error('Provide a name, valid email and password of at least 8 characters')
    try:
        d=conn();d.execute('INSERT INTO users(name,email,password) VALUES(?,?,?)',(name,email,passhash(pw)));d.commit()
    except sqlite3.IntegrityError:return error('Email is already registered',409)
    return login_user(email,pw)

def login_user(email,pw):
    d=conn();u=d.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
    if not u or not verify(pw,u['password']):return error('Invalid email or password',401)
    token=secrets.token_urlsafe(36)
    d.execute('INSERT INTO sessions(token,user_id,expires) VALUES(?,?,?)',(token,u['id'],(datetime.utcnow()+timedelta(days=7)).isoformat()));d.commit()
    return jsonify(token=token,user={k:u[k] for k in ('id','name','email','role')})

@app.post('/api/login')
def login():
    x=data();return login_user(str(x.get('email','')).strip().lower(),str(x.get('password','')))

@app.get('/api/me')
@auth()
def me():return jsonify(user=dict(current_user()))

@app.post('/api/logout')
@auth()
def logout():
    conn().execute('DELETE FROM sessions WHERE token=?',(request.headers['Authorization'].removeprefix('Bearer ').strip(),));conn().commit();return jsonify(ok=True)

@app.post('/api/orders')
@auth()
def place_order():
    x=data();items=x.get('items',[]);address=str(x.get('address','')).strip();phone=str(x.get('phone','')).strip();payment=x.get('payment','COD')
    if not isinstance(items,list) or not items or len(items)>100:return error('Cart cannot be empty')
    if len(address)<12 or len(phone)<8:return error('Enter a complete delivery address and phone number')
    if payment!='COD':return error('Only Cash on Delivery is enabled in this demo')
    d=conn()
    try:
        d.execute('BEGIN IMMEDIATE');picked=[];total=0
        for i in items:
            pid=int(i.get('id',0));qty=int(i.get('qty',0))
            if qty<1 or qty>20:raise ValueError('Quantity must be 1 to 20 per product')
            p=d.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone()
            if not p:raise ValueError('A product in your cart is no longer available')
            if p['stock']<qty:raise ValueError('Not enough stock for '+p['title'])
            picked.append((p,qty));total+=p['price']*qty
        u=current_user()
        c=d.execute('INSERT INTO orders(user_id,total,address,phone,payment) VALUES(?,?,?,?,?)',(u['id'],round(total,2),address,phone,payment));oid=c.lastrowid
        for p,qty in picked:
            d.execute('INSERT INTO order_items(order_id,product_id,title,qty,price) VALUES(?,?,?,?,?)',(oid,p['id'],p['title'],qty,p['price']))
            d.execute('UPDATE products SET stock=stock-? WHERE id=?',(qty,p['id']))
        d.commit();return jsonify(ok=True,order_id=oid,total=round(total,2))
    except (ValueError,TypeError) as ex:d.rollback();return error(str(ex))
    except Exception:d.rollback();return error('Could not place order',500)

@app.get('/api/orders')
@auth()
def my_orders():
    d=conn();u=current_user();rows=d.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC',(u['id'],)).fetchall()
    return jsonify(orders=[dict(r)|{'items':[dict(i) for i in d.execute('SELECT title,qty,price FROM order_items WHERE order_id=?',(r['id'],))]} for r in rows])

@app.get('/api/admin/summary')
@auth(admin=True)
def summary():
    d=conn();return jsonify(summary={'products':d.execute('SELECT COUNT(*) FROM products').fetchone()[0],'orders':d.execute('SELECT COUNT(*) FROM orders').fetchone()[0],'customers':d.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0],'revenue':d.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status!='Cancelled'").fetchone()[0]},orders=[dict(r) for r in d.execute('SELECT o.*,u.name customer FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC LIMIT 100')])

@app.post('/api/admin/products')
@auth(admin=True)
def add_product():
    x=data()
    try:
        title=str(x['title']).strip();category=str(x['category']).strip();price=float(x['price']);mrp=float(x['mrp']);stock=int(x['stock'])
        if not title or not category or price<0 or mrp<price or stock<0:raise ValueError()
    except (KeyError,ValueError,TypeError):return error('Invalid product details or pricing')
    d=conn();cur=d.execute('INSERT INTO products(title,category,price,mrp,stock,description,image,badge,featured) VALUES(?,?,?,?,?,?,?,?,?)',(title,category,price,mrp,stock,str(x.get('description','')),str(x.get('image','')),str(x.get('badge','')),int(bool(x.get('featured')))));d.commit();return jsonify(id=cur.lastrowid,ok=True)

@app.put('/api/admin/products/<int:pid>')
@auth(admin=True)
def update_product(pid):
    x=data()
    try:
        title=str(x['title']).strip();category=str(x['category']).strip();price=float(x['price']);mrp=float(x['mrp']);stock=int(x['stock'])
        if not title or not category or price<0 or mrp<price or stock<0:raise ValueError()
    except (KeyError,ValueError,TypeError):return error('Invalid product details')
    d=conn();cur=d.execute('UPDATE products SET title=?,category=?,price=?,mrp=?,stock=?,description=?,image=?,badge=?,featured=? WHERE id=?',(title,category,price,mrp,stock,str(x.get('description','')),str(x.get('image','')),str(x.get('badge','')),int(bool(x.get('featured'))),pid));d.commit()
    if not cur.rowcount:return error('Product not found',404)
    return jsonify(ok=True)

@app.delete('/api/admin/products/<int:pid>')
@auth(admin=True)
def delete_product(pid):
    d=conn();d.execute('DELETE FROM products WHERE id=?',(pid,));d.commit();return jsonify(ok=True)

@app.patch('/api/admin/orders/<int:oid>')
@auth(admin=True)
def update_order(oid):
    status=data().get('status')
    if status not in ('Placed','Processing','Shipped','Delivered','Cancelled'):return error('Invalid status')
    d=conn();cur=d.execute('UPDATE orders SET status=? WHERE id=?',(status,oid));d.commit()
    if not cur.rowcount:return error('Order not found',404)
    return jsonify(ok=True)

@app.get('/api/health')
def health():return jsonify(status='ok')

if __name__=='__main__':app.run(host='0.0.0.0',port=8000)
