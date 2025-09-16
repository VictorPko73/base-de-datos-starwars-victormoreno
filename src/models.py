from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
import datetime

db = SQLAlchemy()


class Usuario(db.Model):
    
    __tablename__ = 'usuarios'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_suscripcion: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    favoritos: Mapped[list["Favorito"]] = relationship(back_populates="usuario")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "fecha_suscripcion": self.fecha_suscripcion.isoformat()
        }
    
class Planeta(db.Model):
    
    __tablename__ = 'planetas'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    clima: Mapped[str] = mapped_column(String(100))
    poblacion: Mapped[int] = mapped_column(Integer)
    favoritos: Mapped[list["Favorito"]] = relationship(back_populates="planeta")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "clima": self.clima,
            "poblacion": self.poblacion
        }

class Personaje(db.Model):
    
    __tablename__ = 'personajes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    genero: Mapped[Optional[str]] = mapped_column(String(20))
    nacimiento: Mapped[Optional[str]] = mapped_column(String(20))
    favoritos: Mapped[list["Favorito"]] = relationship(back_populates="personaje")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "genero": self.genero,
            "nacimiento": self.nacimiento
        }

class Favorito(db.Model):
    
    __tablename__ = 'favoritos'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey('usuarios.id'), nullable=False)
    planeta_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('planetas.id'), nullable=True)
    personaje_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('personajes.id'), nullable=True)
    usuario: Mapped["Usuario"] = relationship(back_populates="favoritos")
    planeta: Mapped[Optional["Planeta"]] = relationship(back_populates="favoritos")
    personaje: Mapped[Optional["Personaje"]] = relationship(back_populates="favoritos")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "planeta_id": self.planeta_id,
            "personaje_id": self.personaje_id
        }