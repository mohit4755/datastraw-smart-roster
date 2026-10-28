"""Transactional persistent state with row locking and optimistic roster revisions.
Postgres is required on Vercel; SQLite is for local development and tests only.
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, JSON, select
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import NullPool

class Base(DeclarativeBase): pass
class Workspace(Base):
    __tablename__ = 'roster_workspace'
    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)

def make_engine(url=None):
    url = url or os.getenv('DATABASE_URL')
    if not url:
        if os.getenv('VERCEL'): raise RuntimeError('DATABASE_URL is required on Vercel')
        url = 'sqlite:///./roster.db'
    if url.startswith('postgres://'): url = url.replace('postgres://','postgresql+psycopg://',1)
    if url.startswith('postgresql://'): url = url.replace('postgresql://','postgresql+psycopg://',1)
    return create_engine(url, **({'connect_args':{'check_same_thread':False}} if url.startswith('sqlite') else {'poolclass':NullPool,'connect_args':{'connect_timeout':10}}))
_engine = None

def engine():
    global _engine
    if _engine is None: _engine = make_engine()
    return _engine

def initialize():
    Base.metadata.create_all(engine())
    with Session(engine()) as s, s.begin():
        if s.get(Workspace,1) is None:
            s.add(Workspace(id=1,data={**{k:[] for k in ['employees','pods','processes','brands','demands','leaves','holidays']},'rosters':{}}))

@contextmanager
def transaction():
    with Session(engine()) as s, s.begin():
        row = s.scalar(select(Workspace).where(Workspace.id==1).with_for_update())
        if row is None: raise RuntimeError('Database not initialized; run python -m app.seed')
        import copy
        data = copy.deepcopy(row.data)
        yield data
        row.data = data
