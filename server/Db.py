from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'Usuarios'
    
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    foto_perfil = db.Column(db.String(500)) # Aquí guardaremos la ruta del archivo subido
    nombre_usuario = db.Column(db.String(50), nullable=False, unique=True)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    contrasena = db.Column(db.String(255), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    rol = db.Column(db.Enum('comprador', 'vendedor', 'admin'), nullable=False, default='comprador')
    estado_cuenta = db.Column(db.Enum('activa', 'suspendida', 'baneada'), nullable=False, default='activa')
    seguidores = db.Column(db.Integer, default=0)
    fecha_registro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Flask-Login necesita esta función porque cambiamos 'id' por 'id_usuario'
    def get_id(self):
        return str(self.id_usuario)

class Libro(db.Model):
    __tablename__ = 'Libros'
    
    id_libro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    portada = db.Column(db.String(500)) # Archivo de imagen de la portada
    nombre_libro = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=False)
    publicacion_year = db.Column(db.Integer, nullable=False)
    genero_literario = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.Enum('entretenimiento', 'educativo'), nullable=False)
    clasificacion = db.Column(db.Enum('publico', 'mayores_18'), nullable=False, default='publico')
    sinopsis = db.Column(db.Text)
    tiene_pasta_blanda = db.Column(db.Boolean, default=False)
    tiene_pasta_dura = db.Column(db.Boolean, default=False)
    tiene_digital = db.Column(db.Boolean, default=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    favoritos = db.Column(db.Integer, default=0)
    vendidos = db.Column(db.Integer, default=0)
    editorial = db.Column(db.String(150))
    idioma = db.Column(db.String(50), nullable=False, default='Español')
    fecha_agregado = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Favorito(db.Model):
    __tablename__ = 'Favoritos'
    
    id_favorito = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('Libros.id_libro', ondelete='CASCADE'), nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Librero(db.Model):
    __tablename__ = 'Librero'
    
    id_orden = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('Libros.id_libro', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado = db.Column(db.Enum('activo', 'guardado', 'procesado'), nullable=False, default='activo')

class Pedido(db.Model):
    __tablename__ = 'Pedido'
    
    id_pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='RESTRICT'), nullable=False)
    fecha_pedido = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    estado_pedido = db.Column(db.Enum('pendiente', 'enviado', 'entregado', 'cancelado'), nullable=False, default='pendiente')
    metodo_pago = db.Column(db.Enum('tarjeta', 'paypal', 'transferencia', 'efectivo'), nullable=False)
    direccion_envio = db.Column(db.String(300))
    tiempo_envio = db.Column(db.String(100))
    total_pedido = db.Column(db.Numeric(10, 2), nullable=False)

class DetallePedido(db.Model):
    __tablename__ = 'Detalle_Pedido'
    
    id_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('Pedido.id_pedido', ondelete='CASCADE'), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('Libros.id_libro', ondelete='RESTRICT'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

class Contacto(db.Model):
    __tablename__ = 'Contactanos'
    
    id_ayuda = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='SET NULL'))
    correo_contacto = db.Column(db.String(100))
    asunto = db.Column(db.String(200), nullable=False)
    tipo_problema = db.Column(db.Enum('pago', 'envio', 'cuenta', 'libro', 'otro'), nullable=False)
    descripcion_problema = db.Column(db.Text, nullable=False)
    estado = db.Column(db.Enum('pendiente', 'en_revision', 'resuelto'), nullable=False, default='pendiente')
    fecha_envio = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class VentaUsuario(db.Model):
    __tablename__ = 'Ventas_Usuarios'
    
    id_venta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('Libros.id_libro', ondelete='SET NULL'))
    nombre_libro = db.Column(db.String(200))
    autor = db.Column(db.String(150))
    tipo = db.Column(db.Enum('pasta_blanda', 'pasta_dura', 'digital'), nullable=False)
    descripcion_venta = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    estado_venta = db.Column(db.Enum('disponible', 'vendido', 'pausado'), nullable=False, default='disponible')
    fecha_publicacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Seguimiento(db.Model):
    __tablename__ = 'Seguimientos'
    
    id_seguimiento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_seguidor = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    id_seguido = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    fecha_seguimiento = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Comentario(db.Model):
    __tablename__ = 'Comentarios'
    
    id_comentario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_libro = db.Column(db.Integer, db.ForeignKey('Libros.id_libro', ondelete='CASCADE'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    calificacion = db.Column(db.Integer)
    fecha_comentario = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
