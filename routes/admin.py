from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from database import (
    get_db,
    process_matured_investments
)


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# =========================================
# ADMIN AUTHENTICATION HELPER
# =========================================

def admin_required():

    if "admin_id" not in session:
        return False

    connection = get_db()

    admin = connection.execute("""
        SELECT is_admin
        FROM users
        WHERE id = ?
    """, (
        session["admin_id"],
    )).fetchone()

    connection.close()

    if not admin:
        return False

    return admin["is_admin"] == 1


# =========================================
# ADMIN DASHBOARD
# =========================================

@admin_bp.route("")
def admin_dashboard():

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    process_matured_investments()

    connection = get_db()

    admin = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        AND is_admin = 1
    """, (
        session["admin_id"],
    )).fetchone()

    total_users = connection.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE is_admin = 0
    """).fetchone()[0]

    total_balance = connection.execute("""
        SELECT COALESCE(SUM(balance), 0)
        FROM users
        WHERE is_admin = 0
    """).fetchone()[0]

    active_investments = connection.execute("""
        SELECT COUNT(*)
        FROM investments
        WHERE status = ?
    """, (
        "Active",
    )).fetchone()[0]

    total_invested = connection.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM investments
    """).fetchone()[0]

    pending_withdrawals = connection.execute("""
        SELECT COUNT(*)
        FROM withdrawal_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    pending_withdrawal_amount = connection.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM withdrawal_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    pending_deposits = connection.execute("""
        SELECT COUNT(*)
        FROM deposit_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    pending_deposit_amount = connection.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM deposit_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    withdrawal_requests = connection.execute("""
        SELECT
            withdrawal_requests.*,
            users.full_name,
            users.email
        FROM withdrawal_requests
        INNER JOIN users
        ON withdrawal_requests.user_id = users.id
        ORDER BY withdrawal_requests.created_at DESC
        LIMIT 20
    """).fetchall()

    deposit_requests = connection.execute("""
        SELECT
            deposit_requests.*,
            users.full_name,
            users.email
        FROM deposit_requests
        INNER JOIN users
        ON deposit_requests.user_id = users.id
        ORDER BY deposit_requests.created_at DESC
        LIMIT 20
    """).fetchall()

    recent_users = connection.execute("""
        SELECT *
        FROM users
        WHERE is_admin = 0
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        admin=admin,
        total_users=total_users,
        total_balance=total_balance,
        active_investments=active_investments,
        total_invested=total_invested,
        pending_withdrawals=pending_withdrawals,
        pending_withdrawal_amount=pending_withdrawal_amount,
        pending_deposits=pending_deposits,
        pending_deposit_amount=pending_deposit_amount,
        withdrawal_requests=withdrawal_requests,
        deposit_requests=deposit_requests,
        recent_users=recent_users
    )


# =========================================
# ADMIN USERS
# =========================================

@admin_bp.route("/users")
def admin_users():

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    users = connection.execute("""
        SELECT *
        FROM users
        WHERE is_admin = 0
        ORDER BY created_at DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        users=users,
        admin_section="users"
    )


# =========================================
# ADMIN USER ACCOUNT VIEW
# =========================================

@admin_bp.route(
    "/users/access/<int:user_id>"
)
def admin_access_user(user_id):

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        AND is_admin = 0
    """, (
        user_id,
    )).fetchone()

    if not user:

        connection.close()

        return redirect(
            url_for("admin.admin_users")
        )

    user_transactions = connection.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (
        user_id,
    )).fetchall()

    user_investments = connection.execute("""
        SELECT *
        FROM investments
        WHERE user_id = ?
        ORDER BY start_date DESC
    """, (
        user_id,
    )).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        user_account=user,
        user_transactions=user_transactions,
        user_investments=user_investments,
        admin_section="user_account"
    )


# =========================================
# ADMIN ADJUST USER BALANCE
# =========================================

@admin_bp.route(
    "/users/adjust-balance/<int:user_id>",
    methods=["POST"]
)
def admin_adjust_balance(user_id):

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    try:

        amount = float(
            request.form["amount"]
        )

    except (ValueError, TypeError):

        return redirect(
            url_for(
                "admin.admin_access_user",
                user_id=user_id
            )
        )

    if amount == 0:

        return redirect(
            url_for(
                "admin.admin_access_user",
                user_id=user_id
            )
        )

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        AND is_admin = 0
    """, (
        user_id,
    )).fetchone()

    if not user:

        connection.close()

        return redirect(
            url_for("admin.admin_users")
        )

    new_balance = user["balance"] + amount

    if new_balance < 0:

        connection.close()

        return redirect(
            url_for(
                "admin.admin_access_user",
                user_id=user_id
            )
        )

    connection.execute("""
        UPDATE users
        SET balance = ?
        WHERE id = ?
    """, (
        new_balance,
        user_id
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
        user_id,
        "Admin Adjustment",
        amount,
        "Completed",
        "Administrative balance adjustment"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for(
            "admin.admin_access_user",
            user_id=user_id
        )
    )


# =========================================
# ADMIN WITHDRAWALS
# =========================================

@admin_bp.route("/withdrawals")
def admin_withdrawals():

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    withdrawal_requests = connection.execute("""
        SELECT
            withdrawal_requests.*,
            users.full_name,
            users.email
        FROM withdrawal_requests
        INNER JOIN users
        ON withdrawal_requests.user_id = users.id
        ORDER BY withdrawal_requests.created_at DESC
    """).fetchall()

    pending_withdrawals = connection.execute("""
        SELECT COUNT(*)
        FROM withdrawal_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    connection.close()

    return render_template(
        "admin.html",
        withdrawal_requests=withdrawal_requests,
        pending_withdrawals=pending_withdrawals,
        admin_section="withdrawals"
    )


# =========================================
# ADMIN APPROVE WITHDRAWAL
# =========================================

@admin_bp.route(
    "/withdrawal/approve/<int:request_id>",
    methods=["POST"]
)
def approve_withdrawal(request_id):

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    withdrawal = connection.execute("""
        SELECT *
        FROM withdrawal_requests
        WHERE id = ?
    """, (
        request_id,
    )).fetchone()

    if not withdrawal:

        connection.close()

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if withdrawal["status"] != "Pending":

        connection.close()

        return redirect(
            url_for("admin.admin_dashboard")
        )

    connection.execute("""
        UPDATE withdrawal_requests
        SET
            status = ?,
            processed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "Approved",
        request_id
    ))

    connection.execute("""
        UPDATE transactions
        SET
            status = ?,
            description = ?
        WHERE user_id = ?
        AND type = ?
        AND amount = ?
        AND status = ?
        AND description = ?
    """, (
        "Completed",
        "Withdrawal approved by administration",
        withdrawal["user_id"],
        "Withdrawal",
        withdrawal["amount"],
        "Pending",
        "Withdrawal request pending admin verification"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for("admin.admin_dashboard")
    )


# =========================================
# ADMIN REJECT WITHDRAWAL
# =========================================

@admin_bp.route(
    "/withdrawal/reject/<int:request_id>",
    methods=["POST"]
)
def reject_withdrawal(request_id):

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    withdrawal = connection.execute("""
        SELECT *
        FROM withdrawal_requests
        WHERE id = ?
    """, (
        request_id,
    )).fetchone()

    if not withdrawal:

        connection.close()

        return redirect(
            url_for("admin.admin_dashboard")
        )

    if withdrawal["status"] != "Pending":

        connection.close()

        return redirect(
            url_for("admin.admin_dashboard")
        )

    connection.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE id = ?
    """, (
        withdrawal["amount"],
        withdrawal["user_id"]
    ))

    connection.execute("""
        UPDATE withdrawal_requests
        SET
            status = ?,
            processed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "Rejected",
        request_id
    ))

    connection.execute("""
        UPDATE transactions
        SET
            status = ?,
            description = ?
        WHERE user_id = ?
        AND type = ?
        AND amount = ?
        AND status = ?
        AND description = ?
    """, (
        "Failed",
        "Withdrawal rejected and funds returned",
        withdrawal["user_id"],
        "Withdrawal",
        withdrawal["amount"],
        "Pending",
        "Withdrawal request pending admin verification"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for("admin.admin_dashboard")
    )


# =========================================
# ADMIN DEPOSITS
# =========================================

@admin_bp.route("/deposits")
def admin_deposits():

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    deposit_requests = connection.execute("""
        SELECT
            deposit_requests.*,
            users.full_name,
            users.email
        FROM deposit_requests
        INNER JOIN users
        ON deposit_requests.user_id = users.id
        ORDER BY deposit_requests.created_at DESC
    """).fetchall()

    pending_deposits = connection.execute("""
        SELECT COUNT(*)
        FROM deposit_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    pending_deposit_amount = connection.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM deposit_requests
        WHERE status = ?
    """, (
        "Pending",
    )).fetchone()[0]

    connection.close()

    return render_template(
        "admin.html",
        deposit_requests=deposit_requests,
        pending_deposits=pending_deposits,
        pending_deposit_amount=pending_deposit_amount,
        admin_section="deposits"
    )


# =========================================
# ADMIN APPROVE DEPOSIT
# =========================================

@admin_bp.route(
    "/deposit/approve/<int:request_id>",
    methods=["POST"]
)
def approve_deposit(request_id):

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    deposit = connection.execute("""
        SELECT *
        FROM deposit_requests
        WHERE id = ?
    """, (
        request_id,
    )).fetchone()

    if not deposit:

        connection.close()

        return redirect(
            url_for("admin.admin_deposits")
        )

    if deposit["status"] != "Pending":

        connection.close()

        return redirect(
            url_for("admin.admin_deposits")
        )

    connection.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE id = ?
    """, (
        deposit["amount"],
        deposit["user_id"]
    ))

    connection.execute("""
        UPDATE deposit_requests
        SET
            status = ?,
            processed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "Approved",
        request_id
    ))

    connection.execute("""
        UPDATE transactions
        SET
            status = ?,
            description = ?
        WHERE user_id = ?
        AND type = ?
        AND amount = ?
        AND status = ?
        AND description = ?
    """, (
        "Completed",
        "Deposit approved by administration",
        deposit["user_id"],
        "Deposit",
        deposit["amount"],
        "Pending",
        "Deposit submitted and awaiting admin verification"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for("admin.admin_deposits")
    )


# =========================================
# ADMIN REJECT DEPOSIT
# =========================================

@admin_bp.route(
    "/deposit/reject/<int:request_id>",
    methods=["POST"]
)
def reject_deposit(request_id):

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    deposit = connection.execute("""
        SELECT *
        FROM deposit_requests
        WHERE id = ?
    """, (
        request_id,
    )).fetchone()

    if not deposit:

        connection.close()

        return redirect(
            url_for("admin.admin_deposits")
        )

    if deposit["status"] != "Pending":

        connection.close()

        return redirect(
            url_for("admin.admin_deposits")
        )

    connection.execute("""
        UPDATE deposit_requests
        SET
            status = ?,
            processed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "Rejected",
        request_id
    ))

    connection.execute("""
        UPDATE transactions
        SET
            status = ?,
            description = ?
        WHERE user_id = ?
        AND type = ?
        AND amount = ?
        AND status = ?
        AND description = ?
    """, (
        "Failed",
        "Deposit rejected by administration",
        deposit["user_id"],
        "Deposit",
        deposit["amount"],
        "Pending",
        "Deposit submitted and awaiting admin verification"
    ))

    connection.commit()

    connection.close()

    return redirect(
        url_for("admin.admin_deposits")
    )


# =========================================
# ADMIN TRANSACTIONS
# =========================================

@admin_bp.route("/transactions")
def admin_transactions():

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    connection = get_db()

    transactions = connection.execute("""
        SELECT
            transactions.*,
            users.full_name,
            users.email
        FROM transactions
        INNER JOIN users
        ON transactions.user_id = users.id
        ORDER BY transactions.created_at DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        transactions=transactions,
        admin_section="transactions"
    )


# =========================================
# ADMIN INVESTMENTS
# =========================================

@admin_bp.route("/investments")
def admin_investments():

    if not admin_required():
        return redirect(
            url_for("auth.admin_login")
        )

    process_matured_investments()

    connection = get_db()

    investments = connection.execute("""
        SELECT
            investments.*,
            users.full_name,
            users.email
        FROM investments
        INNER JOIN users
        ON investments.user_id = users.id
        ORDER BY investments.start_date DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        investments=investments,
        admin_section="investments"
    )