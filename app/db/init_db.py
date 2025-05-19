from sqlalchemy.orm import Session
from app.db.models import Base, YukiAdministration
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """Initialize the database with required data."""
    try:
        # Create tables
        Base.metadata.create_all(bind=db.get_bind())
        
        # Add default Yuki administration if none exists
        if not db.query(YukiAdministration).first():
            settings = get_settings()
            admin = YukiAdministration(
                administration_id="default",
                name="Default Administration",
                api_username=settings.YUKI_USERNAME,
                api_password=settings.YUKI_PASSWORD,
                api_url=settings.YUKI_API_URL
            )
            db.add(admin)
            db.commit()
            logger.info("Created default Yuki administration")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 