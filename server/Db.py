from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
import os

# Inicializar
db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    rol = db.Column(db.String(20), default='cliente') # cliente, vendedor, empleado
    
    # Relación con el "Librero" (Carrito)
    libros_en_shelf = db.relationship('Shelf', backref='propietario', lazy=True)

class Libro(db.Model):
    __tablename__ = 'libros'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    anio_publicacion = db.Column(db.Integer)
    precio = db.Column(db.Float, nullable=False)
    tipo_pasta = db.Column(db.String(50)) # Dura, Blanda
    calidad = db.Column(db.String(50))    # Nuevo, Usado
    imagen_url = db.Column(db.String(255)) # Para Google Cloud Storage
    categoria = db.Column(db.String(50))
    # Flag para checar que se vendio
    vendido = db.Column(db.Boolean, default=False)
    
    # Para saber quién lo puso a la venta (P2P)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    # Relacion con comentarios
    comentarios = db.relationship('Comentario', backref='libro', lazy=True, cascade="all, delete-orphan")

class Shelf(db.Model):
    """Modelo para el carrito/librero personal"""
    __tablename__ = 'shelf'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)

class Comentario(db.Model):
    """Modelo para el sistema de reseñas y opiniones"""
    __tablename__ = 'comentarios'
    
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # ForeignKeys para saber quién comentó y en qué libro
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    
    # Relacion para acceder a datos de autor
    autor = db.relationship('Usuario', backref='mis_comentarios')