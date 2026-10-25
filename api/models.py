
from api.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    wallet_name = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )
    description = db.Column(db.Text)



class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(
        db.Integer,
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False
    )
    amount = db.Column(db.Numeric(15, 2), nullable=False)

    transaction_type = db.Column(
        db.String(10),
        nullable=False,
        default="expense"
    )

    description = db.Column(db.Text)
    transaction_date = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )




class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False
    )
    amount_limit = db.Column(db.Numeric(15, 2), nullable=False)
    current_spending = db.Column(db.Numeric(15, 2), default=0.00)
    budget_month = db.Column(
        db.Integer,
        db.CheckConstraint(
            "budget_month BETWEEN 1 AND 12",
            name="check_budget_month"
        ),
        nullable=False
    )
    budget_year = db.Column(db.Integer, nullable=False)
