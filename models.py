from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    items = db.relationship(
        'Item',
        backref='owner',
        lazy=True,
        cascade="all, delete-orphan"
    )


class Item(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=False)

    price = db.Column(db.Integer, nullable=False)

    category = db.Column(db.String(100), nullable=False)

    image = db.Column(db.String(300))

    auction_end = db.Column(db.String(50))

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )


class Bid(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    bidder_name = db.Column(db.String(100), nullable=False)

    amount = db.Column(db.Integer, nullable=False)

    item_id = db.Column(
        db.Integer,
        db.ForeignKey('item.id')
    )
class BarterRequest(db.Model):


 id = db.Column(db.Integer, primary_key=True)

requester_name = db.Column(
    db.String(100),
    nullable=False
)

offered_item = db.Column(
    db.String(200),
    nullable=False
)

item_id = db.Column(
    db.Integer,
    db.ForeignKey('item.id')
)

requester_user_id = db.Column(
    db.Integer,
    db.ForeignKey('user.id')
)

status = db.Column(
    db.String(50),
    default="Pending"
)
class Message(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey('item.id')
    )