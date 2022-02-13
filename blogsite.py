import os
from app import create_app, db
from app.models import User, Role, Post
from flask_migrate import Migrate

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app,db)

def make_shell_context():
    return dict(db=db, User=User, Role=Role)



