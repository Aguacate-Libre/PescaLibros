create database PescaLibro;
use PescaLibro;
CREATE TABLE Usuarios (
	id_usuario	INT AUTO_INCREMENT PRIMARY KEY,
    foto_perfil	VARCHAR(500),
    nombre_usuario	VARCHAR(50) NOT NULL UNIQUE,
    correo	VARCHAR(100) NOT NULL UNIQUE,
    contrasena	VARCHAR(255) NOT NULL,
    edad	TINYINT UNSIGNED NOT NULL CHECK (edad >= 13),
    rol	ENUM('comprador', 'vendedor', 'admin') NOT NULL DEFAULT 'comprador',
    estado_cuenta	ENUM('activa', 'suspendida', 'baneada') NOT NULL DEFAULT 'activa',
    seguidores	INT UNSIGNED DEFAULT 0,
    fecha_registro	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE Libros (
	id_libro	INT AUTO_INCREMENT PRIMARY KEY,
    portada	VARCHAR(500),
    nombre_libro	VARCHAR(200) NOT NULL,
    autor	VARCHAR(150) NOT NULL,
    publicacion_year	YEAR NOT NULL,
    genero_literario	VARCHAR(100) NOT NULL,
    categoria	ENUM('entretenimiento', 'educativo') NOT NULL,
    clasificacion	ENUM('publico', 'mayores_18') NOT NULL DEFAULT 'publico',
    sinopsis	TEXT,
    tiene_pasta_blanda	BOOLEAN DEFAULT FALSE,
    tiene_pasta_dura	BOOLEAN DEFAULT FALSE,
    tiene_digital	BOOLEAN DEFAULT FALSE,
    precio	DECIMAL(10, 2) NOT NULL CHECK (precio >= 0),
    stock	INT UNSIGNED NOT NULL DEFAULT 0,
    favoritos	INT UNSIGNED DEFAULT 0,
    vendidos	INT UNSIGNED DEFAULT 0,
    editorial	VARCHAR(150),
    idioma	VARCHAR(50) NOT NULL DEFAULT 'Español',
    fecha_agregado	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Favoritos (
	id_favorito	INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario	INT NOT NULL,
    id_libro	INT NOT NULL,
    fecha_agregado  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fav_usuario FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_fav_libro FOREIGN KEY (id_libro) REFERENCES Libros(id_libro) ON DELETE CASCADE,
    CONSTRAINT uq_fav_usuario_libro UNIQUE (id_usuario, id_libro)
    );

CREATE TABLE Librero (
	id_orden	INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario	INT NOT NULL,
    id_libro	INT NOT NULL,
    cantidad	TINYINT UNSIGNED NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
    precio_unitario DECIMAL(10, 2) NOT NULL CHECK (precio_unitario >= 0),
    fecha_agregado  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado	ENUM('activo', 'guardado', 'procesado') NOT NULL DEFAULT 'activo',
    CONSTRAINT fk_carrito_usuario FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_carrito_libro FOREIGN KEY (id_libro) REFERENCES Libros(id_libro) ON DELETE CASCADE
    );
    
CREATE TABLE Pedido (
	id_pedido	INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario	INT NOT NULL,
    fecha_pedido	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_pedido	ENUM('pendiente', 'enviado', 'entregado', 'cancelado') NOT NULL DEFAULT 'pendiente',
    metodo_pago	ENUM('tarjeta', 'paypal', 'transferencia', 'efectivo') NOT NULL,
    direccion_envio	VARCHAR(300),
    tiempo_envio	VARCHAR(100),
    total_pedido	DECIMAL(10, 2) NOT NULL CHECK (total_pedido >= 0),
    CONSTRAINT fk_pedido_usuario FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE RESTRICT
    );
    
CREATE TABLE Detalle_Pedido (
	id_detalle	INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido	INT NOT NULL,
    id_libro	INT NOT NULL,
    cantidad	TINYINT UNSIGNED NOT NULL DEFAULT 1 CHECK (cantidad >= 1),
    precio_unitario DECIMAL(10, 2) NOT NULL CHECK (precio_unitario >= 0),
    CONSTRAINT fk_detalle_pedido FOREIGN KEY (id_pedido) REFERENCES Pedido(id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_libro  FOREIGN KEY (id_libro)  REFERENCES Libros(id_libro)  ON DELETE RESTRICT
    );
    
CREATE TABLE Contactanos (
	id_ayuda	INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario	INT,
    correo_contacto	VARCHAR(100),
    asunto	VARCHAR(200) NOT NULL,
    tipo_problema	ENUM('pago', 'envio', 'cuenta', 'libro', 'otro') NOT NULL,
    descripcion_problema TEXT NOT NULL,
    estado	ENUM('pendiente', 'en_revision', 'resuelto') NOT NULL DEFAULT 'pendiente',
    fecha_envio	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_contacto_usuario FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE SET NULL
    );

CREATE TABLE Ventas_Usuarios (
	id_venta	INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario	INT NOT NULL,
    id_libro	INT,
    nombre_libro	VARCHAR(200),
    autor	VARCHAR(150),
    tipo	ENUM('pasta_blanda', 'pasta_dura', 'digital') NOT NULL,
    descripcion_venta	TEXT NOT NULL,
    precio	DECIMAL(10, 2) NOT NULL CHECK (precio >= 0),
    estado_venta	ENUM('disponible', 'vendido', 'pausado') NOT NULL DEFAULT 'disponible',
    fecha_publicacion	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_venta_usuario FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_venta_libro   FOREIGN KEY (id_libro)   REFERENCES Libros(id_libro)    ON DELETE SET NULL
    );
    
CREATE TABLE Seguimientos (
	id_seguimiento	INT AUTO_INCREMENT PRIMARY KEY,
    id_seguidor	INT NOT NULL,
    id_seguido	INT NOT NULL,
    fecha_seguimiento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_seguidor FOREIGN KEY (id_seguidor) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_seguido  FOREIGN KEY (id_seguido)  REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT uq_seguimiento UNIQUE (id_seguidor, id_seguido)
    );

CREATE TABLE Comentarios (
	id_comentario	INT AUTO_INCREMENT PRIMARY KEY,
    id_libro	INT NOT NULL,
    id_usuario	INT NOT NULL,
    comentario	TEXT NOT NULL,
    calificacion	TINYINT UNSIGNED CHECK (calificacion BETWEEN 1 AND 5),
    fecha_comentario	DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comentario_libro FOREIGN KEY (id_libro) REFERENCES Libros(id_libro) ON DELETE CASCADE,
    CONSTRAINT fk_comentario_usuario FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE
    );
    