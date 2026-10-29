"""SQLite persistence using SQLAlchemy ORM."""
from datetime import datetime
from sqlalchemy import create_engine, String, Float, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from .config import DB_PATH

class Base(DeclarativeBase): pass

class Design(Base):
    __tablename__ = "designs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="Unclassified")
    image_path: Mapped[str] = mapped_column(Text, default="")
    designer: Mapped[str] = mapped_column(String(100), default="Studio team")
    collection: Mapped[str] = mapped_column(String(100), default="")
    season: Mapped[str] = mapped_column(String(40), default="")
    material: Mapped[str] = mapped_column(String(120), default="")
    color: Mapped[str] = mapped_column(String(60), default="")
    status: Mapped[str] = mapped_column(String(30), default="Concept")
    prediction: Mapped[str] = mapped_column(String(80), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    score: Mapped[float] = mapped_column(Float, default=0)
    sku: Mapped[str] = mapped_column(String(50), default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tasks: Mapped[list["Task"]] = relationship(back_populates="design", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship(back_populates="design", cascade="all, delete-orphan")
    sustainability: Mapped["Sustainability"] = relationship(back_populates="design", cascade="all, delete-orphan", uselist=False)

class Sustainability(Base):
    __tablename__ = "sustainability"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id"), unique=True)
    source: Mapped[str] = mapped_column(String(120), default="")
    recycled: Mapped[float] = mapped_column(Float, default=0)
    organic: Mapped[float] = mapped_column(Float, default=0)
    water: Mapped[float] = mapped_column(Float, default=0)
    energy: Mapped[float] = mapped_column(Float, default=0)
    packaging: Mapped[str] = mapped_column(String(100), default="")
    recyclable: Mapped[float] = mapped_column(Float, default=0)
    transport: Mapped[str] = mapped_column(String(80), default="")
    lifetime: Mapped[float] = mapped_column(Float, default=1)
    score: Mapped[float] = mapped_column(Float, default=0)
    design: Mapped[Design] = relationship(back_populates="sustainability")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="To do")
    assignee: Mapped[str] = mapped_column(String(100), default="Studio team")
    due_date: Mapped[str] = mapped_column(String(20), default="")
    design_id: Mapped[int | None] = mapped_column(ForeignKey("designs.id"), nullable=True)
    design: Mapped[Design | None] = relationship(back_populates="tasks")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id"))
    title: Mapped[str] = mapped_column(String(180))
    sku: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    inventory: Mapped[int] = mapped_column(Integer, default=0)
    platform_id: Mapped[str] = mapped_column(String(80), default="")
    design: Mapped[Design] = relationship(back_populates="products")

class Activity(Base):
    __tablename__ = "activity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine, expire_on_commit=False)
def initialize():
    Base.metadata.create_all(engine)
    with Session() as s:
        if s.query(Design).count() == 0:
            rows = [
                ("Eco Denim Jacket", "Jacket", "Organic cotton denim", "Indigo", "Approved", 88),
                ("Sustainable Summer Dress", "Dress", "Linen / TENCEL™", "Natural", "Designing", 92),
                ("Recycled Knit Hoodie", "Outerwear", "Recycled cotton", "Oat", "Production", 84),
                ("Organic Poplin Shirt", "Shirt", "Organic cotton", "Cloud", "Review", 90),
                ("Reworked Denim Skirt", "Skirt", "Upcycled denim", "Washed blue", "Concept", 94),
            ]
            for n,c,m,col,st,score in rows:
                d=Design(name=n,category=c,material=m,color=col,status=st,score=score,collection="Form & Fibre",season="Spring 2027",designer="Mira Sen")
                s.add(d); s.flush(); s.add(Sustainability(design_id=d.id,source="Certified supplier",recycled=35,organic=65,water=120,energy=18,packaging="Recycled paper",recyclable=90,transport="Rail",lifetime=5,score=score))
            s.add_all([Task(title="Approve final trims",status="In progress",assignee="Mira Sen",design_id=1),Task(title="Prepare production tech pack",status="To do",assignee="Studio team",design_id=3)])
            s.add(Activity(message="Demo collection added to your studio")); s.commit()
