from flask import Flask, render_template, request, session, redirect, url_for
from models import db, User, Item, Bid, BarterRequest, Message
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
import os

app = Flask(__name__)

# ✅ SECRET KEY (ONLY ONE WAY)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "bidmate_secret_key")

# DB CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bidmate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# UPLOAD FOLDER
app.config['UPLOAD_FOLDER'] = os.path.join(
    app.root_path,
    'static',
    'uploads'
)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def home():

    search = request.args.get('search')

    if search:
        items = Item.query.filter(
            Item.title.contains(search)
        ).all()
    else:
        items = Item.query.all()

    return render_template(
        'index.html',
        items=items
    )

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(
            name=name,
            email=email,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:

            session['user_id'] = user.id
            session['user_name'] = user.name

            return redirect(url_for('dashboard'))

        return "Invalid Email or Password"

    return render_template('login.html')


@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template(
        'dashboard.html',
        user_name=session['user_name']
    )

@app.route('/upload-item', methods=['GET', 'POST'])
def upload_item():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        category = request.form['category']
        auction_end = request.form['auction_end']

        image_file = request.files['image']

        filename = ""

        if image_file and image_file.filename:

            filename = secure_filename(
                image_file.filename
            )

            image_path = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )

            image_file.save(image_path)

        item = Item(
            title=title,
            description=description,
            price=price,
            category=category,
            image=filename,
            auction_end=auction_end,
            user_id=session['user_id']
        )

        db.session.add(item)
        db.session.commit()

        return redirect(url_for('my_items'))

    return render_template('upload_item.html')

@app.route('/item/<int:item_id>', methods=['GET', 'POST'])
def item_details(item_id):

    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':

        bidder_name = request.form['bidder_name']
        amount = request.form['amount']

        highest_bid = Bid.query.filter_by(
            item_id=item.id
        ).order_by(
            Bid.amount.desc()
        ).first()

        if highest_bid and int(amount) <= highest_bid.amount:
            return "Bid must be higher than the current highest bid!"

        new_bid = Bid(
            bidder_name=bidder_name,
            amount=int(amount),
            item_id=item.id
        )

        db.session.add(new_bid)
        db.session.commit()

    bids = Bid.query.filter_by(
        item_id=item.id
    ).order_by(
        Bid.amount.desc()
    ).all()

    seller = User.query.get(item.user_id)

    return render_template(
        'item_details.html',
        item=item,
        bids=bids,
        seller=seller
    )


@app.route('/my-items')
def my_items():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    items = Item.query.filter_by(
        user_id=session['user_id']
    ).all()

    return render_template(
        'my_items.html',
        items=items
    )
@app.route('/edit-item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = Item.query.get_or_404(item_id)

    if item.user_id != session['user_id']:
        return "Unauthorized"

    if request.method == 'POST':

        item.title = request.form['title']
        item.description = request.form['description']
        item.price = request.form['price']
        item.category = request.form['category']

        db.session.commit()

        return redirect(url_for('my_items'))

    return render_template('edit_item.html', item=item)
@app.route('/delete-item/<int:item_id>')
def delete_item(item_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = Item.query.get_or_404(item_id)

    if item.user_id != session['user_id']:
        return "Unauthorized"

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('my_items'))


@app.route('/admin')
def admin():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if user.email != "admin@bidmate.com":
        return "Access Denied"

    users = User.query.all()
    items = Item.query.all()
    bids = Bid.query.all()

    return render_template(
        'admin.html',
        users=users,
        items=items,
        bids=bids
    )
@app.route('/admin-delete-item/<int:item_id>')
def admin_delete_item(item_id):

    item = Item.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('admin'))
@app.route('/admin-delete-user/<int:user_id>')
def admin_delete_user(user_id):

    user = User.query.get_or_404(user_id)

    Item.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('admin'))
@app.route('/barter/<int:item_id>', methods=['GET', 'POST'])
def barter(item_id):

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        requester_name = request.form.get('requester_name')
        offered_item = request.form.get('offered_item')

        new_request = BarterRequest(
            requester_name=requester_name,
            offered_item=offered_item,
            item_id=item.id,
            requester_user_id=user_id
        )

        db.session.add(new_request)
        db.session.commit()

        return redirect(url_for('my_barter_offers'))

    return render_template('barter.html', item=item)


# ----------------------------
# MY BARTER REQUESTS
# ----------------------------
@app.route('/my-barter-requests')
def my_barter_requests():

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    my_items = Item.query.filter_by(user_id=user_id).all()

    item_ids = [item.id for item in my_items]

    # ✅ SAFE FIX (prevents crash)
    if item_ids:
        requests = BarterRequest.query.filter(
            BarterRequest.item_id.in_(item_ids)
        ).all()
    else:
        requests = []

    return render_template(
        'my_barter_requests.html',
        requests=requests
    )


# ----------------------------
# MY BARTER OFFERS
# ----------------------------
@app.route('/my-barter-offers')
def my_barter_offers():

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    offers = BarterRequest.query.filter_by(
        requester_user_id=user_id
    ).all()

    return render_template(
        'my_barter_offers.html',
        offers=offers
    )


# ----------------------------
# ACCEPT BARTER
# ----------------------------
@app.route('/accept-barter/<int:request_id>')
def accept_barter(request_id):

    barter = BarterRequest.query.get_or_404(request_id)

    barter.status = "Accepted"
    db.session.commit()

    return redirect(url_for('my_barter_requests'))


# ----------------------------
# REJECT BARTER
# ----------------------------
@app.route('/reject-barter/<int:request_id>')
def reject_barter(request_id):

    barter = BarterRequest.query.get_or_404(request_id)

    barter.status = "Rejected"
    db.session.commit()

    return redirect(url_for('my_barter_requests'))
@app.route('/chat/<int:item_id>', methods=['GET', 'POST'])
def chat(item_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = Item.query.get_or_404(item_id)

    seller_id = item.user_id
    current_user = session['user_id']

    if request.method == 'POST':

        new_message = Message(
            sender_id=current_user,
            receiver_id=seller_id,
            message=request.form['message'],
            item_id=item.id
        )

        db.session.add(new_message)
        db.session.commit()

    messages = Message.query.filter(
        Message.item_id == item.id
    ).all()

    return render_template(
        'chat.html',
        item=item,
        messages=messages
    )
with app.app_context():
    db.create_all()
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)