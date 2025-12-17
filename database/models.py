from datetime import datetime
from typing import List
from utils import get_persistent_data

from sqlalchemy import (
	Column,
	Integer,
	String,
	Boolean,
	DateTime,
	Table,
	ForeignKey,
	create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# association table for many-to-many relationship between users and tools
connection_table = Table(
	"connection",
	Base.metadata,
	Column("user_id", Integer, ForeignKey("users.user_id"), primary_key=True),
	Column("tool_id", Integer, ForeignKey("tools.tool_id"), primary_key=True),
)


class Tool(Base):
	__tablename__ = "tools"

	tool_id = Column(Integer, primary_key=True, autoincrement=True)
	tool_name = Column(String(255), nullable=False, unique=True)
	tool_enable = Column(Boolean, default=True, nullable=False)
	is_premium = Column(Boolean, default=False, nullable=False)
	last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	users = relationship("User", secondary=connection_table, back_populates="tools")

	def __repr__(self) -> str:
		return f"<Tool(id={self.tool_id} name={self.tool_name} enabled={self.tool_enable} premium={self.is_premium})>"


class User(Base):
	__tablename__ = "users"

	user_id = Column(Integer, primary_key=True, autoincrement=True)
	user_email = Column(String(255), nullable=False, unique=True)
	user_url = Column(String(500), nullable=False, unique=True)
	user_enable = Column(Boolean, default=True, nullable=False)
	is_premium = Column(Boolean, default=False, nullable=False)
	last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	tools = relationship("Tool", secondary=connection_table, back_populates="users")

	def __repr__(self) -> str:
		return f"<User(id={self.user_id}  email={self.user_email} url={self.user_url} enabled={self.user_enable} premium={self.is_premium})>"


# Database helpers
def get_engine(sqlite_url: str = "sqlite:///" + get_persistent_data("xiaozhi.db")):
	return create_engine(sqlite_url, future=True)


def init_db(engine=None):
	if engine is None:
		engine = get_engine()
	Base.metadata.create_all(engine)


def get_session(engine=None):
	if engine is None:
		engine = get_engine()
	Session = sessionmaker(bind=engine, autoflush=False, future=True)
	return Session()


# -------------------------
# Manager classes (static methods)
# -------------------------


class UserManager:
	@staticmethod
	def create(user_url: str, user_email: str, user_enable: bool = True, session=None) -> User:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = User(user_url=user_url, user_email=user_email, user_enable=user_enable, is_premium=False)
		session.add(user)
		session.commit()
		session.refresh(user)
		if close_session:
			session.close()
		return user

	@staticmethod
	def get_by_id(user_id: int, session=None) -> User | None:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_id=user_id).one_or_none()
		if close_session:
			session.close()
		return user

	@staticmethod
	def get_by_url(user_url: str, session=None) -> User | None:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_url=user_url).one_or_none()
		if close_session:
			session.close()
		return user

	@staticmethod
	def update(user_id: int, session=None, **kwargs) -> User | None:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_id=user_id).one_or_none()
		if user is None:
			if close_session:
				session.close()
			return None
		for k, v in kwargs.items():
			if hasattr(user, k):
				setattr(user, k, v)
		session.commit()
		session.refresh(user)
		if close_session:
			session.close()
		return user

	@staticmethod
	def delete(user_id: int, session=None) -> bool:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_id=user_id).one_or_none()
		if user is None:
			if close_session:
				session.close()
			return False
		session.delete(user)
		session.commit()
		if close_session:
			session.close()
		return True


class ToolManager:
	@staticmethod
	def register(tool_name: str):
		tool = ToolManager.get_by_name(tool_name)
		if tool is None:
			ToolManager.create(tool_name)

	@staticmethod
	def create(tool_name: str, tool_enable: bool = True, session=None) -> Tool:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		tool = Tool(tool_name=tool_name, tool_enable=tool_enable, is_premium=False)
		session.add(tool)
		session.commit()
		session.refresh(tool)
		if close_session:
			session.close()
		return tool

	@staticmethod
	def get_by_id(tool_id: int, session=None) -> Tool | None:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		tool = session.query(Tool).filter_by(tool_id=tool_id).one_or_none()
		if close_session:
			session.close()
		return tool

	@staticmethod
	def get_by_name(tool_name: str, session=None) -> Tool | None:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		tool = session.query(Tool).filter_by(tool_name=tool_name).one_or_none()
		if close_session:
			session.close()
		return tool

	@staticmethod
	def update(tool_id: int, session=None, **kwargs) -> Tool | None:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		tool = session.query(Tool).filter_by(tool_id=tool_id).one_or_none()
		if tool is None:
			if close_session:
				session.close()
			return None
		for k, v in kwargs.items():
			if hasattr(tool, k):
				setattr(tool, k, v)
		session.commit()
		session.refresh(tool)
		if close_session:
			session.close()
		return tool

	@staticmethod
	def delete(tool_id: int, session=None) -> bool:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		tool = session.query(Tool).filter_by(tool_id=tool_id).one_or_none()
		if tool is None:
			if close_session:
				session.close()
			return False
		session.delete(tool)
		session.commit()
		if close_session:
			session.close()
		return True


class ConnectionManager:
	@staticmethod
	def broadcast_tool_change(tool: Tool, session=None) -> bool:
		if session is None:
			session = get_session()
		users = session.query(User).filter_by(user_enable=True).all()
		for u in users:
			if tool.is_premium and not u.is_premium:
				if tool in u.tools:
					u.tools.remove(tool)
				else:
					continue
				
			if tool not in u.tools:
				u.tools.append(tool)
		session.commit()
		return True

	@staticmethod
	def autoconnect(user: User, session = None) -> bool:
		if session is None:
			session = get_session()
		user_type = "premium" if user.is_premium else "standard"
		if user_type == "standard":
			tools = session.query(Tool).filter_by(tool_enable=True, is_premium=False).all()
		else:
			tools = session.query(Tool).filter_by(tool_enable=True).all()
		for t in tools:
			if t not in user.tools:
				user.tools.append(t)
		session.commit()
		return True
	
	@staticmethod
	def autodisconnect(user: User, session = None) -> bool:
		if session is None:
			session = get_session()
		# Just remove all tools
		user.tools = []
		session.commit()
		return True

	@staticmethod
	def connect(user_id: int, tool_id: int, session=None) -> bool:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_id=user_id).one_or_none()
		tool = session.query(Tool).filter_by(tool_id=tool_id).one_or_none()
		if user is None or tool is None:
			if close_session:
				session.close()
			return False
		if tool not in user.tools:
			user.tools.append(tool)
			session.commit()
		if close_session:
			session.close()
		return True

	@staticmethod
	def disconnect(user_id: int, tool_id: int, session=None) -> bool:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_id=user_id).one_or_none()
		tool = session.query(Tool).filter_by(tool_id=tool_id).one_or_none()
		if user is None or tool is None:
			if close_session:
				session.close()
			return False
		if tool in user.tools:
			user.tools.remove(tool)
			session.commit()
		if close_session:
			session.close()
		return True

	@staticmethod
	def list_user_tools(user_id: int, session=None) -> List[Tool]:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		user = session.query(User).filter_by(user_id=user_id).one_or_none()
		tools = user.tools[:] if user is not None else []
		if close_session:
			session.close()
		return tools

	@staticmethod
	def list_tool_users(tool_id: int, session=None) -> List[User]:
		close_session = False
		if session is None:
			session = get_session()
			close_session = True
		tool = session.query(Tool).filter_by(tool_id=tool_id).one_or_none()
		users = tool.users[:] if tool is not None else []
		if close_session:
			session.close()
		return users


# Backwards compatible aliases (function names kept)
def create_user(user_url: str, user_enable: bool = True, session=None) -> User:
	return UserManager.create(user_url, user_enable, session=session)


def get_user_by_id(user_id: int, session=None) -> User | None:
	return UserManager.get_by_id(user_id, session=session)


def get_user_by_url(user_url: str, session=None) -> User | None:
	return UserManager.get_by_url(user_url, session=session)


def update_user(user_id: int, **kwargs) -> User | None:
	return UserManager.update(user_id, **kwargs)


def delete_user(user_id: int) -> bool:
	return UserManager.delete(user_id)


def create_tool(tool_name: str, tool_enable: bool = True, session=None) -> Tool:
	return ToolManager.create(tool_name, tool_enable, session=session)


def get_tool_by_id(tool_id: int, session=None) -> Tool | None:
	return ToolManager.get_by_id(tool_id, session=session)


def get_tool_by_name(tool_name: str, session=None) -> Tool | None:
	return ToolManager.get_by_name(tool_name, session=session)


def update_tool(tool_id: int, **kwargs) -> Tool | None:
	return ToolManager.update(tool_id, **kwargs)


def delete_tool(tool_id: int) -> bool:
	return ToolManager.delete(tool_id)


def connect_user_tool(user_id: int, tool_id: int, session=None) -> bool:
	return ConnectionManager.connect(user_id, tool_id, session=session)


def disconnect_user_tool(user_id: int, tool_id: int) -> bool:
	return ConnectionManager.disconnect(user_id, tool_id)


def list_user_tools(user_id: int, session=None) -> List[Tool]:
	return ConnectionManager.list_user_tools(user_id, session=session)


def list_tool_users(tool_id: int, session=None) -> List[User]:
	return ConnectionManager.list_tool_users(tool_id, session=session)


# small example of CRUD usage
# end of models


