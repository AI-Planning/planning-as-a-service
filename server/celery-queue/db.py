
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Integer, String
from sqlalchemy.dialects.mysql import BLOB
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

MYSQL_USER=os.environ.get('MYSQL_USER', 'user')
MYSQL_PASSWORD=os.environ.get('MYSQL_PASSWORD', 'password')
 
class MetaBasic(Base):
    __tablename__ = 'meta_basic'

    task_id = Column(String, primary_key=True)
    name = Column(String)
    duration = Column(Integer)

    def __init__(self, task_id, name, duration):
        self.task_id = task_id
        self.name = name
        self.duration = duration

class MetaAdvanced(Base):
    __tablename__ = 'meta_advanced'

    task_id = Column(String, primary_key=True)
    result = Column(BLOB)

    def __init__(self, task_id, result):
        self.task_id = task_id
        self.result = result


class MetaDB:
    def __init__(self):
        self.engine = create_engine(f'mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@mysql:3306/db', pool_recycle=500)
        

    def add_meta_basic(self,task_id,name,duration):
        Session = sessionmaker(bind=self.engine)
        with Session.begin() as session:
            meta_basic_record = MetaBasic(task_id=task_id, name=name, duration=duration)
            session.add(meta_basic_record)
            session.commit()
            session.close()

    def add_meta_advanced(self,task_id,result):
        Session = sessionmaker(bind=self.engine)
        with Session.begin() as session:
            meta_advanced_record = MetaAdvanced(task_id=task_id, result=result)
            session.add(meta_advanced_record)
            session.commit()
            session.close()





