from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from datetime import datetime, timedelta

from database import (
    get_db,
    process_matured_investments
)


user_bp = Blueprint(
    "user",
    __name__
)


# =========================================
# USER AUTHENTICATION HELPER
# =========================================

def user_required():

    if "user_id" not in session:
        return False

    return True


# =========================================
# USER DASHBOARD
# =========================================

@user_bp.route("/dashboard")
def dashboard():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    process_matured_investments()

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    transactions = connection.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "dashboard.html",
        user=user,
        transactions=transactions
    )


# =========================================
# WALLET
# =========================================

@user_bp.route("/wallet")
def wallet():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    process_matured_investments()

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    pending_withdrawals = connection.execute("""
        SELECT *
        FROM withdrawal_requests
        WHERE user_id = ?
        AND status = ?
        ORDER BY created_at DESC
    """, (
        session["user_id"],
        "Pending"
    )).fetchall()

    pending_deposits = connection.execute("""
        SELECT *
        FROM deposit_requests
        WHERE user_id = ?
        AND status = ?
        ORDER BY created_at DESC
    """, (
        session["user_id"],
        "Pending"
    )).fetchall()

    transactions = connection.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    withdrawal_receipt = session.pop(
        "withdrawal_receipt",
        None
    )

    return render_template(
        "wallet.html",
        user=user,
        pending_withdrawals=pending_withdrawals,
        pending_deposits=pending_deposits,
        transactions=transactions,
        withdrawal_receipt=withdrawal_receipt
    )


# =========================================
# INVESTMENTS
# =========================================

@user_bp.route("/investments")
def investments():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    process_matured_investments()

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    investment_list = connection.execute("""
        SELECT *
        FROM investments
        WHERE user_id = ?
        ORDER BY start_date DESC
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    current_time = datetime.now()

    processed_investments = []

    for investment in investment_list:

        try:

            start_date = datetime.fromisoformat(
                investment["start_date"]
            )

            maturity_date = datetime.fromisoformat(
                investment["maturity_date"]
            )

        except (ValueError, TypeError):

            continue

        # =========================================
        # CALCULATE TOTAL AND ELAPSED TIME
        # =========================================

        total_seconds = (
            maturity_date - start_date
        ).total_seconds()

        elapsed_seconds = (
            current_time - start_date
        ).total_seconds()

        # =========================================
        # CALCULATE PROGRESS
        # =========================================

        if total_seconds > 0:

            progress = (
                elapsed_seconds /
                total_seconds
            ) * 100

        else:

            progress = 100

        progress = max(
            0,
            min(100, progress)
        )

        if investment["status"] == "Completed":

            progress = 100

        # =========================================
        # CALCULATE REMAINING TIME
        # =========================================

        remaining_seconds = (
            maturity_date - current_time
        ).total_seconds()

        if (
            investment["status"] == "Completed"
            or remaining_seconds <= 0
        ):

            days_remaining = 0

        else:

            days_remaining = int(
                (remaining_seconds + 86399) // 86400
            )

        # =========================================
        # COUNTDOWN
        # =========================================

        if investment["status"] == "Completed":

            countdown = "Completed"

        elif remaining_seconds <= 0:

            countdown = "Processing"

        else:

            remaining_days = int(
                remaining_seconds // 86400
            )

            remaining_hours = int(
                (remaining_seconds % 86400) // 3600
            )

            remaining_minutes = int(
                (remaining_seconds % 3600) // 60
            )

            if remaining_days > 0:

                countdown = (
                    f"{remaining_days}d "
                    f"{remaining_hours}h remaining"
                )

            elif remaining_hours > 0:

                countdown = (
                    f"{remaining_hours}h "
                    f"{remaining_minutes}m remaining"
                )

            else:

                countdown = (
                    f"{remaining_minutes}m remaining"
                )

        # =========================================
        # PREPARE INVESTMENT DATA
        # =========================================

        investment_data = dict(
            investment
        )

        investment_data["progress"] = round(
            progress,
            2
        )

        investment_data["days_remaining"] = (
            days_remaining
        )

        investment_data["countdown"] = (
            countdown
        )

        investment_data["maturity_display"] = (
            maturity_date.strftime(
                "%b %d, %Y %I:%M %p"
            )
        )

        # =========================================
        # RETURN RATE
        # =========================================

        investment_data["return_rate"] = 10

        # =========================================
        # MATURITY STATUS
        # =========================================

        if investment["status"] == "Completed":

            investment_data["maturity_status"] = (
                "Matured"
            )

        elif remaining_seconds <= 0:

            investment_data["maturity_status"] = (
                "Processing"
            )

        else:

            investment_data["maturity_status"] = (
                "Active"
            )

        processed_investments.append(
            investment_data
        )

    # =========================================
    # PORTFOLIO STATISTICS
    # =========================================

    total_invested = sum(
        investment["amount"]
        for investment in processed_investments
    )

    active_portfolio_value = sum(
        investment["expected_return"]
        for investment in processed_investments
        if investment["status"] == "Active"
    )

    completed_returns = sum(
        investment["expected_return"]
        for investment in processed_investments
        if investment["status"] == "Completed"
    )

    total_demo_profit = sum(
        investment["expected_return"]
        - investment["amount"]
        for investment in processed_investments
    )

    active_plans = sum(
        1
        for investment in processed_investments
        if investment["status"] == "Active"
    )

    return render_template(
        "investments.html",
        user=user,
        investments=processed_investments,
        total_invested=total_invested,
        portfolio_value=active_portfolio_value,
        completed_returns=completed_returns,
        demo_returns=total_demo_profit,
        active_plans=active_plans
    )


# =========================================
# CREATE INVESTMENT
# =========================================

@user_bp.route(
    "/create-investment",
    methods=["POST"]
)
def create_investment():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    try:

        amount = float(
            request.form["amount"]
        )

    except (ValueError, TypeError, KeyError):

        return redirect(
            url_for("user.investments")
        )

    if amount <= 0:

        return redirect(
            url_for("user.investments")
        )

    plan_name = request.form.get(
        "plan_name",
        "30-Day Growth Plan"
    ).strip()

    if not plan_name:

        plan_name = (
            "30-Day Growth Plan"
        )

    connection = get_db()

    user = connection.execute("""
        SELECT balance
        FROM users
        WHERE id = ?
        AND is_admin = 0
    """, (
        session["user_id"],
    )).fetchone()

    if not user:

        connection.close()

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    if amount > (user["balance"] or 0):

        connection.close()

        return redirect(
            url_for("user.investments")
        )

    duration_days = 30

    expected_return = (
        amount * 1.10
    )

    start_date = datetime.now()

    maturity_date = (
        start_date +
        timedelta(
            days=duration_days
        )
    )

    connection.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE id = ?
    """, (
        amount,
        session["user_id"]
    ))

    connection.execute("""
        INSERT INTO investments
        (
            user_id,
            plan_name,
            amount,
            expected_return,
            return_rate,
            duration_days,
            start_date,
            maturity_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        plan_name,
        amount,
        expected_return,
        10,
        duration_days,
        start_date.isoformat(),
        maturity_date.isoformat(),
        "Active"
    ))

    connection.execute("""
        INSERT INTO transactions
        (
            user_id,
            type,
            amount,
            status,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        "Investment",
        amount,
        "Completed",
        f"Investment created: {plan_name}"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for("user.investments")
    )


# =========================================
# TRANSACTIONS
# =========================================

@user_bp.route("/transactions")
def transactions():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    process_matured_investments()

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    transaction_list = connection.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "transactions.html",
        user=user,
        transactions=transaction_list
    )


# =========================================
# MARKETS
# =========================================

@user_bp.route("/markets")
def markets():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    connection.close()

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "markets.html",
        user=user
    )


# =========================================
# DEPOSIT
# =========================================

@user_bp.route(
    "/deposit",
    methods=["POST"]
)
def deposit():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    # =========================================
    # GET FORM DATA
    # =========================================

    try:

        amount = float(
            request.form.get(
                "amount",
                0
            )
        )

    except (ValueError, TypeError):

        return redirect(
            url_for("user.wallet")
        )

    currency = (
        request.form.get(
            "currency",
            "BTC"
        )
        .strip()
        .upper()
    )

    network = (
        request.form.get(
            "network",
            "Bitcoin"
        )
        .strip()
    )

    reference = (
        request.form.get(
            "reference",
            ""
        )
        .strip()
    )

    # =========================================
    # BASIC VALIDATION
    # =========================================

    if amount <= 0:

        return redirect(
            url_for("user.wallet")
        )

    if not currency:

        return redirect(
            url_for("user.wallet")
        )

    if not network:

        return redirect(
            url_for("user.wallet")
        )

    # =========================================
    # PAYMENT ADDRESS
    #
    # THIS IS NOT A REAL PAYMENT ADDRESS.
    # =========================================

    demo_wallet_address = (
        "BTC-ADDRESS-FOR-REAL-FUNDS"
    )

    # =========================================
    # DATABASE
    # =========================================

    connection = get_db()

    user = connection.execute("""
        SELECT id
        FROM users
        WHERE id = ?
        AND is_admin = 0
    """, (
        session["user_id"],
    )).fetchone()

    if not user:

        connection.close()

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # =========================================
    # CREATE DEPOSIT REQUEST
    #
    # BALANCE IS NOT CREDITED HERE.
    # =========================================

    connection.execute("""
        INSERT INTO deposit_requests
        (
            user_id,
            amount,
            currency,
            network,
            wallet_address,
            reference,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        amount,
        currency,
        network,
        demo_wallet_address,
        reference,
        "Pending"
    ))

    # =========================================
    # CREATE PENDING TRANSACTION
    # =========================================

    connection.execute("""
        INSERT INTO transactions
        (
            user_id,
            type,
            amount,
            status,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        "Deposit",
        amount,
        "Pending",
        "Deposit submitted and awaiting admin verification"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for("user.wallet")
    )


# =========================================
# WITHDRAWAL
# =========================================

@user_bp.route(
    "/withdraw",
    methods=["POST"]
)
def withdraw():

    if not user_required():
        return redirect(
            url_for("auth.login")
        )

    # =========================================
    # GET WITHDRAWAL METHOD
    # =========================================

    withdrawal_method = (
        request.form.get(
            "withdrawal_method",
            ""
        )
        .strip()
        .lower()
    )

    if withdrawal_method not in (
        "bank",
        "crypto"
    ):

        return redirect(
            url_for("user.wallet")
        )

    # =========================================
    # GET AMOUNT
    # =========================================

    try:

        amount = float(
            request.form.get(
                "amount",
                0
            )
        )

    except (ValueError, TypeError):

        return redirect(
            url_for("user.wallet")
        )

    if amount <= 0:

        return redirect(
            url_for("user.wallet")
        )

    # =========================================
    # GET BANK DETAILS
    # =========================================

    bank_name = request.form.get(
        "bank_name",
        ""
    ).strip()

    account_name = request.form.get(
        "account_name",
        ""
    ).strip()

    account_number = request.form.get(
        "account_number",
        ""
    ).strip()

    # =========================================
    # GET CRYPTO DETAILS
    # =========================================

    crypto_currency = request.form.get(
        "crypto_currency",
        ""
    ).strip().upper()

    crypto_network = request.form.get(
        "crypto_network",
        ""
    ).strip()

    wallet_address = request.form.get(
        "wallet_address",
        ""
    ).strip()

    # =========================================
    # VALIDATE BANK WITHDRAWAL
    # =========================================

    if withdrawal_method == "bank":

        if not bank_name:

            return redirect(
                url_for("user.wallet")
            )

        if not account_name:

            return redirect(
                url_for("user.wallet")
            )

        if not account_number:

            return redirect(
                url_for("user.wallet")
            )

        # Clear crypto fields

        crypto_currency = None
        crypto_network = None
        wallet_address = None

    # =========================================
    # VALIDATE CRYPTO WITHDRAWAL
    # =========================================

    if withdrawal_method == "crypto":

        if not crypto_currency:

            return redirect(
                url_for("user.wallet")
            )

        if not crypto_network:

            return redirect(
                url_for("user.wallet")
            )

        if not wallet_address:

            return redirect(
                url_for("user.wallet")
            )

        # Clear bank fields

        bank_name = None
        account_name = None
        account_number = None

    # =========================================
    # DATABASE CONNECTION
    # =========================================

    connection = get_db()

    user = connection.execute("""
        SELECT
            id,
            balance
        FROM users
        WHERE id = ?
        AND is_admin = 0
    """, (
        session["user_id"],
    )).fetchone()

    if not user:

        connection.close()

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # =========================================
    # CHECK AVAILABLE BALANCE
    # =========================================

    current_balance = (
        user["balance"] or 0
    )

    if amount > current_balance:

        connection.close()

        return redirect(
            url_for("user.wallet")
        )

    # =========================================
    # RESERVE / DEDUCT BALANCE
    # =========================================

    connection.execute("""
        UPDATE users
        SET balance = balance - ?
        WHERE id = ?
    """, (
        amount,
        session["user_id"]
    ))

    # =========================================
    # CREATE WITHDRAWAL REQUEST
    # =========================================

    cursor = connection.execute("""
        INSERT INTO withdrawal_requests
        (
            user_id,
            amount,
            status,
            withdrawal_method,
            bank_name,
            account_name,
            account_number,
            crypto_currency,
            crypto_network,
            wallet_address
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        amount,
        "Completed",
        withdrawal_method,
        bank_name,
        account_name,
        account_number,
        crypto_currency,
        crypto_network,
        wallet_address
    ))

    withdrawal_id = cursor.lastrowid

    # =========================================
    # CREATE TRANSACTION RECORD
    # =========================================

    if withdrawal_method == "bank":

            description = (
            "Bank withdrawal recorded as completed "
            f"(reference #{withdrawal_id})"
        )
    else:


        description = (
            "Crypto withdrawal recorded as completed "
            f"(reference #{withdrawal_id})"
        )

    connection.execute("""
        INSERT INTO transactions
        (
            user_id,
            type,
            amount,
            status,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        "Withdrawal",
        amount,
        "Completed",
        description
    ))

    # =========================================
    # SAVE EVERYTHING
    # =========================================

    connection.commit()

    # =========================================
    # CREATE ONE-TIME WITHDRAWAL RECEIPT
    # =========================================

    completed_at = datetime.now()

    session["withdrawal_receipt"] = {
        "amount": amount,
        "date": completed_at.strftime("%d %B %Y"),
        "time": completed_at.strftime("%I:%M:%S %p")
    }

    connection.close()

    # =========================================
    # RETURN TO WALLET
    # =========================================

    return redirect(
        url_for("user.wallet")
    )
