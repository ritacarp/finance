from app import app, db
from app.models import Users, Orders


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Orders': Orders}