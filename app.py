from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from database.models import (
    init_db,
    get_session,
    User,
    Tool,
    UserManager,
    ToolManager,
    ConnectionManager,
)
from sqlalchemy import func
import logging
from functools import wraps
from logcfg import setup_logging
from utils import get_log_dir, load_env, envvarsenum
from tool_manager import get_tool_names


app = Flask(__name__)
envars = load_env()
app.secret_key = 'NaPnFO863yf6FQoi7XsO'

ADMIN_USERNAME = envars[envvarsenum.ADMIN_USER]
ADMIN_PASSWORD = envars[envvarsenum.ADMIN_PASSWORD]

# Initialize database
init_db()

# Configure logging
setup_logging(get_log_dir())
logger = logging.getLogger("App")

# Register tools
toolnames = get_tool_names()
for t in toolnames:
    logger.info(f"Registered tool function: {t}")
    ToolManager.register(t)

# ============= Authentication Decorator =============
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============= User Page Routes =============
@app.route("/")
def index():
    """Redirect to user page"""
    return redirect(url_for("user_page"))

@app.route("/get_premium", methods=["GET", "POST"])
def get_premium():
    """Get Premium Info Page"""
    if request.method == "POST":
        user_email = request.form.get("user_email", "").strip()
        if user_email and "@" in user_email and "." in user_email:
            # Save email to session only, not to database
            session['user_email'] = user_email
            flash("Email saved! You can now proceed with the premium upgrade.", "success")
        else:
            flash("Please enter a valid email address", "error")
        return redirect(url_for("get_premium"))
    
    return render_template("get_premium.html")

@app.route("/user")
def user_page():
    """User registration page"""
    session = get_session()
    users = []
    tools = []
    try:
        users = session.query(User).filter(User.user_enable == True).all()
        tools = session.query(Tool).filter(Tool.tool_enable == True).all()
    finally:
        session.close()
    
    return render_template("user.html", users=users, tools=tools)


@app.route("/user/register", methods=["POST"])
def register_user():
    """Register a new user URL"""
    user_url = request.form.get("user_url", "").strip()
    user_email = request.form.get("user_email", "").strip()
    if not user_url:
        flash("URL cannot be empty", "error")
        return redirect(url_for("user_page"))
    if not user_email:
        flash("Email cannot be empty", "error")
        return redirect(url_for("user_page"))
    # Validate email format (basic check)
    if "@" not in user_email or "." not in user_email:
        flash("Invalid email address", "error")
        return redirect(url_for("user_page"))
    # Validate URL format (basic check)
    if not (user_url.startswith("wss://")):
        flash("URL must start with wss://", "error")
        return redirect(url_for("user_page"))
    
    session = get_session()
    try:
        # Check if URL already exists
        existing_user = UserManager.get_by_url(user_url, session=session)
        if existing_user:
            flash(f"URL already registered with ID: {existing_user.user_id}", "warning")
        else:
            # Create new user
            new_user = UserManager.create(user_url, user_email=user_email, user_enable=True, session=session)
            # Save email in Flask session
            from flask import session as flask_session
            flask_session['user_email'] = user_email
            flask_session['user_id'] = new_user.user_id
            flash(f"Successfully registered! Your User ID is: {new_user.user_id}", "success")
            logger.info(f"New user registered: {new_user}")
    except Exception as e:
        flash(f"Error registering URL: {str(e)}", "error")
        logger.error(f"Error registering user: {e}")
    finally:
        session.close()
    
    return redirect(url_for("user_page"))


# ============= Admin Authentication Routes =============
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash("Successfully logged in", "success")
            logger.info(f"Admin logged in: {username}")
            return redirect(url_for("admin_page"))
        else:
            flash("Invalid credentials", "error")
            logger.warning(f"Failed login attempt: {username}")
    
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash("Successfully logged out", "success")
    logger.info("Admin logged out")
    return redirect(url_for("admin_login"))


# ============= Admin Page Routes =============
@app.route("/admin")
@admin_required
def admin_page():
    """Admin dashboard"""
    db_session = get_session()
    try:
        users = db_session.query(User).order_by(User.user_id.desc()).all()
        tools = db_session.query(Tool).order_by(Tool.tool_id.desc()).all()
        
        # Get connection stats
        user_count = db_session.query(func.count(User.user_id)).scalar()
        tool_count = db_session.query(func.count(Tool.tool_id)).scalar()
        
        return render_template(
            "admin.html",
            users=users,
            tools=tools,
            user_count=user_count,
            tool_count=tool_count,
        )
    finally:
        db_session.close()


# ============= User Management Routes =============
@app.route("/admin/user/premium/<int:user_id>", methods=["POST"])
@admin_required
def make_user_premium(user_id):
    session = get_session()
    try:
        user = UserManager.get_by_id(user_id, session=session)
        if user:
            new_status = not user.is_premium
            UserManager.update(user_id, session=session, is_premium=new_status)
            ConnectionManager.autodisconnect(user, session=session)
            ConnectionManager.autoconnect(user, session=session)
            flash(f"User '{user.user_id}' marked as {'premium' if new_status else 'standard'}", "success")
        else:
            flash(f"User {user_id} not found", "error")
    except Exception as e:
        flash(f"Error updating user premium status: {str(e)}", "error")
        logger.error(f"Error updating user {user_id} premium status: {e}")
    finally:
        session.close()
    return redirect(url_for("admin_page"))
  
@app.route("/admin/user/toggle/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user(user_id):
    """Enable/disable a user"""
    session = get_session()
    try:
        user = UserManager.get_by_id(user_id, session=session)
        if user:
            new_status = not user.user_enable
            if new_status:
                ConnectionManager.autodisconnect(user, session=session)
                ConnectionManager.autoconnect(user, session=session)
            UserManager.update(user_id, session=session, user_enable=new_status)
            flash(f"User {user_id} {'enabled' if new_status else 'disabled'}", "success")
        else:
            flash(f"User {user_id} not found", "error")
    except Exception as e:
        flash(f"Error toggling user: {str(e)}", "error")
        logger.error(f"Error toggling user {user_id}: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))


@app.route("/admin/user/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    session = get_session()
    try:
        if UserManager.delete(user_id, session=session):
            flash(f"User {user_id} deleted successfully", "success")
        else:
            flash(f"User {user_id} not found", "error")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "error")
        logger.error(f"Error deleting user {user_id}: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))


# ============= Tool Management Routes =============
@app.route("/admin/tool/create", methods=["POST"])
@admin_required
def create_tool():
    """Register a new tool"""
    tool_name = request.form.get("tool_name", "").strip()
    
    if not tool_name:
        flash("Tool name cannot be empty", "error")
        return redirect(url_for("admin_page"))
    
    session = get_session()
    try:
        # Check if tool already exists
        existing_tool = ToolManager.get_by_name(tool_name, session=session)
        if existing_tool:
            flash(f"Tool '{tool_name}' already exists", "warning")
        else:
            # Create new tool
            new_tool = ToolManager.create(tool_name, tool_enable=True, session=session)
            ConnectionManager.broadcast_tool_change(new_tool, session=session)
            flash(f"Tool '{tool_name}' created successfully", "success")
            logger.info(f"New tool created: {new_tool}")
    except Exception as e:
        flash(f"Error creating tool: {str(e)}", "error")
        logger.error(f"Error creating tool: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))

@app.route("/admin/tool/premium/<int:tool_id>", methods=["POST"])
@admin_required
def make_premium(tool_id):
    """Toggle tool premium status"""
    session = get_session()
    try:
        tool = ToolManager.get_by_id(tool_id, session=session)
        if tool:
            new_status = not tool.is_premium
            ToolManager.update(tool_id, session=session, is_premium=new_status)
            ConnectionManager.broadcast_tool_change(tool, session=session)
            flash(f"Tool '{tool.tool_name}' marked as {'premium' if new_status else 'standard'}", "success")
        else:
            flash(f"Tool {tool_id} not found", "error")
    except Exception as e:
        flash(f"Error updating tool premium status: {str(e)}", "error")
        logger.error(f"Error updating tool {tool_id} premium status: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))

@app.route("/admin/tool/toggle/<int:tool_id>", methods=["POST"])
@admin_required
def toggle_tool(tool_id):
    """Enable/disable a tool"""
    session = get_session()
    try:
        tool = ToolManager.get_by_id(tool_id, session=session)
        if tool:
            new_status = not tool.tool_enable
            ToolManager.update(tool_id, session=session, tool_enable=new_status)
            flash(f"Tool '{tool.tool_name}' {'enabled' if new_status else 'disabled'}", "success")
        else:
            flash(f"Tool {tool_id} not found", "error")
    except Exception as e:
        flash(f"Error toggling tool: {str(e)}", "error")
        logger.error(f"Error toggling tool {tool_id}: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))


@app.route("/admin/tool/delete/<int:tool_id>", methods=["POST"])
@admin_required
def delete_tool(tool_id):
    """Delete a tool"""
    session = get_session()
    try:
        if ToolManager.delete(tool_id, session=session):
            flash(f"Tool {tool_id} deleted successfully", "success")
        else:
            flash(f"Tool {tool_id} not found", "error")
    except Exception as e:
        flash(f"Error deleting tool: {str(e)}", "error")
        logger.error(f"Error deleting tool {tool_id}: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))


# ============= User-Tool Association Routes =============
@app.route("/admin/connection/add", methods=["POST"])
@admin_required
def add_connection():
    """Associate a tool with a user"""
    user_id = request.form.get("user_id", type=int)
    tool_id = request.form.get("tool_id", type=int)
    
    if not user_id or not tool_id:
        flash("Both User ID and Tool ID are required", "error")
        return redirect(url_for("admin_page"))
    
    session = get_session()
    try:
        if ConnectionManager.connect(user_id, tool_id, session=session):
            flash(f"Tool {tool_id} associated with User {user_id}", "success")
        else:
            flash("Error: User or Tool not found", "error")
    except Exception as e:
        flash(f"Error adding connection: {str(e)}", "error")
        logger.error(f"Error adding connection: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))


@app.route("/admin/connection/remove", methods=["POST"])
@admin_required
def remove_connection():
    """Remove tool association from a user"""
    user_id = request.form.get("user_id", type=int)
    tool_id = request.form.get("tool_id", type=int)
    
    if not user_id or not tool_id:
        flash("Both User ID and Tool ID are required", "error")
        return redirect(url_for("admin_page"))
    
    session = get_session()
    try:
        if ConnectionManager.disconnect(user_id, tool_id, session=session):
            flash(f"Tool {tool_id} removed from User {user_id}", "success")
        else:
            flash("Error: Connection not found", "error")
    except Exception as e:
        flash(f"Error removing connection: {str(e)}", "error")
        logger.error(f"Error removing connection: {e}")
    finally:
        session.close()
    
    return redirect(url_for("admin_page"))


# ============= API Routes for AJAX =============
@app.route("/api/user/<int:user_id>/tools")
@admin_required
def get_user_tools(user_id):
    """Get tools associated with a user (JSON)"""
    session = get_session()
    try:
        tools = ConnectionManager.list_user_tools(user_id, session=session)
        return jsonify({
            "user_id": user_id,
            "tools": [{"id": t.tool_id, "name": t.tool_name, "enabled": t.tool_enable} for t in tools]
        })
    finally:
        session.close()
    
    

@app.route("/api/tool/<int:tool_id>/users")
@admin_required
def get_tool_users(tool_id):
    """Get users associated with a tool (JSON)"""
    session = get_session()
    try:
        users = ConnectionManager.list_tool_users(tool_id, session=session)
        return jsonify({
            "tool_id": tool_id,
            "users": [{"id": u.user_id, "url": u.user_url, "enabled": u.user_enable} for u in users]
        })
    finally:
        session.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
