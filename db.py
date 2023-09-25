from typing import List
import enum
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, Enum, DateTime, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
	pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
	# LDAP/test account username
	id: Mapped[str] = mapped_column(String(30), primary_key=True)
	name: Mapped[str] = mapped_column(String(30))

	jobs: Mapped[List['Job']] = relationship(
		back_populates='user', cascade='all, delete-orphan'
	)

	def __repr__(self) -> str:
		return f"User(id={self.id!r}, name={self.name!r})"

class JobStatus(enum.Enum):
	queued = 1
	cancelled = 2
	finished = 3

class Job(db.Model):
	# uuidv4
	id: Mapped[str] = mapped_column(String(36), primary_key=True)

	filename: Mapped[str] = mapped_column(String(100))
	filesize_kb: Mapped[int] = mapped_column()
	copies: Mapped[int] = mapped_column()
	pages_printed: Mapped[int] = mapped_column()

	user_id: Mapped[str] = mapped_column(ForeignKey('user.id'))
	user: Mapped['User'] = relationship(back_populates='jobs')

	# job status comes from the newest update
	updates: Mapped[List['JobUpdate']] = relationship(
		back_populates='job', cascade='all, delete-orphan'
	)

	def __repr__(self) -> str:
		return f"Job(id={self.id!r}, filename={self.name!r}, filesize={self.filesize_kb!r}KB, copies={self.copies!r}, pages_printed={self.pages_printed!r})"

class JobUpdate(db.Model):
	__tablename__ = "job_update"

	# uuidv4
	id: Mapped[str] = mapped_column(String(36), primary_key=True)
	job_id: Mapped[str] = mapped_column(ForeignKey('job.id'))
	job: Mapped['Job'] = relationship(back_populates='updates')
	status: Mapped[JobStatus] = mapped_column(Enum(JobStatus))
	changed_at: Mapped[datetime] = mapped_column(DateTime())

	def __repr__(self) -> str:
		return f"JobUpdate(id={self.id!r}, status={self.status!r}, changed_at={self.changed_at!r})"
