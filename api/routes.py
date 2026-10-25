
from flask import Blueprint, app, jsonify, request
from sqlalchemy.exc import IntegrityError

from api.extensions import db
from api.models import Category

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.order_by(Category.id).all()

    return jsonify([
        {
            "id": category.id,
            "category_name": category.category_name,
            "description": category.description
        }
        for category in categories
    ]), 200


@api_bp.route("/categories", methods=["POST"])
def create_category():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    category_name = data.get("category_name")

    if not isinstance(category_name, str) or not category_name.strip():
        return jsonify({"error": "category_name wajib diisi"}), 400

    category = Category(
        category_name=category_name.strip(),
        description=data.get("description")
    )

    try:
        db.session.add(category)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Nama kategori sudah digunakan"}), 409

    return jsonify({
        "message": "Kategori berhasil dibuat",
        "id": category.id,
        "category_name": category.category_name,
        "description": category.description
    }), 201


@api_bp.route("/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    category = db.session.get(Category, category_id)

    if category is None:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    if "category_name" in data:
        name = data["category_name"]

        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "category_name tidak boleh kosong"}), 400

        category.category_name = name.strip()

    if "description" in data:
        category.description = data["description"]

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Nama kategori sudah digunakan"}), 409

    return jsonify({
        "message": "Kategori berhasil diperbarui",
        "id": category.id,
        "category_name": category.category_name,
        "description": category.description
    }), 200


@api_bp.route("/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    category = db.session.get(Category, category_id)

    if category is None:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    try:
        db.session.delete(category)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Kategori tidak bisa dihapus karena masih digunakan transaksi atau anggaran"
        }), 409

    return jsonify({"message": "Kategori berhasil dihapus"}), 200


from decimal import Decimal, InvalidOperation

from api.models import Wallet, User, Transaction


def parse_money(value):
    """Validasi nominal uang agar berupa angka non-negatif."""
    if isinstance(value, bool) or value is None:
        return None

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None

    if not amount.is_finite() or amount < 0:
        return None

    if amount.as_tuple().exponent < -2:
        return None

    return amount


@api_bp.route("/wallets", methods=["GET"])
def get_wallets():
    wallets = Wallet.query.order_by(Wallet.id).all()

    return jsonify([
        {
            "id": wallet.id,
            "user_id": wallet.user_id,
            "wallet_name": wallet.wallet_name,
            "balance": str(wallet.balance)
        }
        for wallet in wallets
    ]), 200


@api_bp.route("/wallets", methods=["POST"])
def create_wallet():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    user_id = data.get("user_id")
    wallet_name = data.get("wallet_name")
    balance = parse_money(data.get("balance", 0))

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        return jsonify({"error": "user_id harus berupa bilangan bulat positif"}), 400

    if not isinstance(wallet_name, str) or not wallet_name.strip():
        return jsonify({"error": "wallet_name wajib diisi"}), 400

    if balance is None:
        return jsonify({"error": "balance harus berupa angka non-negatif dengan maksimal 2 angka desimal"}), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    wallet = Wallet(
        user_id=user_id,
        wallet_name=wallet_name.strip(),
        balance=balance
    )

    db.session.add(wallet)
    db.session.commit()

    return jsonify({
        "message": "Dompet berhasil dibuat",
        "id": wallet.id,
        "user_id": wallet.user_id,
        "wallet_name": wallet.wallet_name,
        "balance": str(wallet.balance)
    }), 201


@api_bp.route("/wallets/<int:wallet_id>", methods=["PUT"])
def update_wallet(wallet_id):
    wallet = db.session.get(Wallet, wallet_id)

    if wallet is None:
        return jsonify({"error": "Dompet tidak ditemukan"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    if "wallet_name" in data:
        name = data["wallet_name"]

        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "wallet_name tidak boleh kosong"}), 400

        wallet.wallet_name = name.strip()

    if "balance" in data:
        balance = parse_money(data["balance"])

        if balance is None:
            return jsonify({"error": "balance harus berupa angka non-negatif dengan maksimal 2 angka desimal"}), 400

        wallet.balance = balance

    db.session.commit()

    return jsonify({
        "message": "Dompet berhasil diperbarui",
        "id": wallet.id,
        "user_id": wallet.user_id,
        "wallet_name": wallet.wallet_name,
        "balance": str(wallet.balance)
    }), 200


@api_bp.route("/wallets/<int:wallet_id>", methods=["DELETE"])
def delete_wallet(wallet_id):
    wallet = db.session.get(Wallet, wallet_id)

    if wallet is None:
        return jsonify({"error": "Dompet tidak ditemukan"}), 404

    if Transaction.query.filter_by(wallet_id=wallet_id).first():
        return jsonify({
            "error": "Dompet tidak bisa dihapus karena masih memiliki transaksi"
        }), 409

    db.session.delete(wallet)
    db.session.commit()

    return jsonify({"message": "Dompet berhasil dihapus"}), 200



from werkzeug.security import generate_password_hash


@api_bp.route("/users", methods=["GET"])
def get_users():
    users = User.query.order_by(User.id).all()

    return jsonify([
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at else None
            )
        }
        for user in users
    ]), 200


@api_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "Username wajib diisi"}), 400

    if not isinstance(email, str) or not email.strip() or "@" not in email:
        return jsonify({"error": "Email tidak valid"}), 400

    if not isinstance(password, str) or len(password) < 8:
        return jsonify({
            "error": "Password wajib minimal 8 karakter"
        }), 400

    user = User(
        username=username.strip(),
        email=email.strip().lower(),
        password_hash=generate_password_hash(password)
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Username atau email sudah digunakan"
        }), 409

    return jsonify({
        "message": "Pengguna berhasil dibuat",
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 201


@api_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    if "username" in data:
        username = data["username"]

        if not isinstance(username, str) or not username.strip():
            return jsonify({"error": "Username tidak boleh kosong"}), 400

        user.username = username.strip()

    if "email" in data:
        email = data["email"]

        if not isinstance(email, str) or not email.strip() or "@" not in email:
            return jsonify({"error": "Email tidak valid"}), 400

        user.email = email.strip().lower()

    if "password" in data:
        password = data["password"]

        if not isinstance(password, str) or len(password) < 8:
            return jsonify({
                "error": "Password wajib minimal 8 karakter"
            }), 400

        user.password_hash = generate_password_hash(password)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Username atau email sudah digunakan"
        }), 409

    return jsonify({
        "message": "Pengguna berhasil diperbarui",
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200


@api_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": "Pengguna berhasil dihapus"
    }), 200


from api.models import Transaction, Wallet, Category


def transaction_json(transaction):
    return {
        "id": transaction.id,
        "wallet_id": transaction.wallet_id,
        "category_id": transaction.category_id,
        "amount": str(transaction.amount),
        "transaction_type": transaction.transaction_type,
        "description": transaction.description,
        "transaction_date": (
            transaction.transaction_date.isoformat()
            if transaction.transaction_date else None
        )
    }


def apply_balance(wallet, amount, transaction_type, reverse=False):
    # Membalik transaksi lama ketika transaksi diedit atau dihapus.
    is_income = transaction_type == "income"

    if reverse:
        is_income = not is_income

    if is_income:
        wallet.balance = (wallet.balance or Decimal("0")) + amount
    else:
        wallet.balance = (wallet.balance or Decimal("0")) - amount


@api_bp.route("/transactions", methods=["GET"])
def get_transactions():
    transactions = Transaction.query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.id.desc()
    ).all()

    return jsonify([
        transaction_json(transaction)
        for transaction in transactions
    ]), 200




@api_bp.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    def parse_positive_id(value):
        if isinstance(value, bool):
            return None

        try:
            parsed = int(value)
        except (ValueError, TypeError, OverflowError):
            return None

        if parsed <= 0 or str(value).strip() != str(parsed):
            return None

        return parsed

    wallet_id = parse_positive_id(data.get("wallet_id"))
    category_id = parse_positive_id(data.get("category_id"))
    amount = parse_money(data.get("amount"))
    transaction_type = data.get("transaction_type")
    description = data.get("description")

    if wallet_id is None:
        return jsonify({
            "error": "wallet_id harus berupa bilangan bulat positif"
        }), 400

    if category_id is None:
        return jsonify({
            "error": "category_id harus berupa bilangan bulat positif"
        }), 400

    if amount is None or amount <= 0:
        return jsonify({
            "error": "amount harus berupa angka positif dengan maksimal 2 desimal"
        }), 400

    if transaction_type not in ("income", "expense"):
        return jsonify({
            "error": "transaction_type harus income atau expense"
        }), 400

    if description is not None and not isinstance(description, str):
        return jsonify({"error": "description harus berupa teks"}), 400

    wallet = db.session.get(Wallet, wallet_id)
    if wallet is None:
        return jsonify({"error": "Dompet tidak ditemukan"}), 404

    category = db.session.get(Category, category_id)
    if category is None:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    if (
        transaction_type == "expense"
        and amount > Decimal(str(wallet.balance or 0))
    ):
        return jsonify({"error": "Saldo dompet tidak mencukupi"}), 400

    transaction = Transaction(
        wallet_id=wallet_id,
        category_id=category_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description
    )

    apply_balance(wallet, amount, transaction_type)

    try:
        db.session.add(transaction)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Gagal menyimpan transaksi")
        return jsonify({"error": "Transaksi gagal disimpan"}), 500

    return jsonify({
        "message": "Transaksi berhasil dibuat",
        "transaction": transaction_json(transaction),
        "new_balance": str(wallet.balance)
    }), 201



@api_bp.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)

    if transaction is None:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body harus berupa JSON"}), 400

    amount = parse_money(data.get("amount", transaction.amount))
    transaction_type = data.get(
        "transaction_type", transaction.transaction_type
    )
    wallet_id = data.get("wallet_id", transaction.wallet_id)
    category_id = data.get("category_id", transaction.category_id)
    description = data.get("description", transaction.description)

    if amount is None or amount <= 0:
        return jsonify({"error": "amount harus berupa angka positif"}), 400

    if transaction_type not in ("income", "expense"):
        return jsonify({"error": "Jenis transaksi tidak valid"}), 400

    if not isinstance(wallet_id, int) or isinstance(wallet_id, bool) or wallet_id <= 0:
        return jsonify({"error": "wallet_id tidak valid"}), 400

    if not isinstance(category_id, int) or isinstance(category_id, bool) or category_id <= 0:
        return jsonify({"error": "category_id tidak valid"}), 400

    if description is not None and not isinstance(description, str):
        return jsonify({"error": "description harus berupa teks"}), 400

    old_wallet = db.session.get(Wallet, transaction.wallet_id)
    new_wallet = db.session.get(Wallet, wallet_id)
    category = db.session.get(Category, category_id)

    if old_wallet is None or new_wallet is None:
        return jsonify({"error": "Dompet tidak ditemukan"}), 404

    if category is None:
        return jsonify({"error": "Kategori tidak ditemukan"}), 404

    # Kembalikan efek transaksi lama ke saldo.
    apply_balance(
        old_wallet,
        Decimal(str(transaction.amount)),
        transaction.transaction_type,
        reverse=True
    )

    # Periksa apakah saldo cukup setelah perubahan.
    if (
        transaction_type == "expense"
        and amount > Decimal(str(new_wallet.balance or 0))
    ):
        db.session.rollback()
        return jsonify({"error": "Saldo dompet tidak mencukupi"}), 400

    transaction.wallet_id = wallet_id
    transaction.category_id = category_id
    transaction.amount = amount
    transaction.transaction_type = transaction_type
    transaction.description = description

    apply_balance(new_wallet, amount, transaction_type)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Gagal memperbarui transaksi")
        return jsonify({"error": "Transaksi gagal diperbarui"}), 500

    return jsonify({
        "message": "Transaksi berhasil diperbarui",
        "transaction": transaction_json(transaction),
        "new_balance": str(new_wallet.balance)
    }), 200


@api_bp.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)

    if transaction is None:
        return jsonify({"error": "Transaksi tidak ditemukan"}), 404

    wallet = db.session.get(Wallet, transaction.wallet_id)

    if wallet is None:
        return jsonify({"error": "Dompet tidak ditemukan"}), 404

    apply_balance(
        wallet,
        Decimal(str(transaction.amount)),
        transaction.transaction_type,
        reverse=True
    )

    try:
        db.session.delete(transaction)
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception("Gagal menghapus transaksi")
        return jsonify({"error": "Transaksi gagal dihapus"}), 500

    return jsonify({
        "message": "Transaksi berhasil dihapus",
        "new_balance": str(wallet.balance)
    }), 200
