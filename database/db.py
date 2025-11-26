from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User, Channel, Movie
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_user(self, user_id):
        session = self.Session()
        try:
            if not session.query(User).filter_by(user_id=user_id).first():
                user = User(user_id=user_id)
                session.add(user)
                session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_all_channels(self):
        session = self.Session()
        try:
            channels = session.query(Channel).all()
            return [channel.channel_id for channel in channels]
        finally:
            session.close()
    
    def add_channel(self, channel_id):
        session = self.Session()
        try:
            channel = Channel(channel_id=channel_id)
            session.add(channel)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    def remove_channel(self, channel_id):
        session = self.Session()
        try:
            channel = session.query(Channel).filter_by(channel_id=channel_id).first()
            if channel:
                session.delete(channel)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    def add_movie(self, code, channel_id, message_id, caption):
        session = self.Session()
        try:
            movie = Movie(
                code=code,
                channel_id=channel_id,
                message_id=message_id,
                caption=caption
            )
            session.add(movie)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_movie_by_code(self, code):
        session = self.Session()
        try:
            movie = session.query(Movie).filter_by(code=code).first()
            return movie
        finally:
            session.close()
    
    def get_all_users(self):
        session = self.Session()
        try:
            users = session.query(User).all()
            return [user.user_id for user in users]
        finally:
            session.close()
    
    def get_stats(self):
        session = self.Session()
        try:
            user_count = session.query(User).count()
            channel_count = session.query(Channel).count()
            movie_count = session.query(Movie).count()
            return {
                'users': user_count,
                'channels': channel_count,
                'movies': movie_count
            }
        finally:
            session.close()

# Global database instance
db = Database()