"""Create local development tables. Production uses Alembic migration."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db.database import Base, engine
Base.metadata.create_all(engine)
print("Database schema created")
