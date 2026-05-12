import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from server.db import db, Usuario, Libro, Shelf, Comentario 
from werkzeug.utils import secure_filename

# Cargar variables del .env
load_dotenv()

# Inicializar Flask y decirle dónde están las carpetas
app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuración de Seguridad
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuración de la Base de Datos
db_user = os.getenv('USER')
db_password = os.getenv('PASSWORD')
db_host = os.getenv('HOST')
db_name = os.getenv('DATABASE')

# Si hay datos en el .env usa MySQL, si no, usa SQLite local
if db_user and db_name:
    # Conexión oficial a MySQL (Esto es para ti Vinicio)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"
else:
    # Conexión temporal mientras hago pruebas sin el google cloud
    print("Credenciales MySQL no encontradas. Usando SQLite local para desarrollo.")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pesca_libros_local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Carpeta local para guardar fotos temporalmente 
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
# Asegurarnos de que la carpeta exista cuando arranque el servidor
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Vincular la base de datos con la aplicación Flask
db.init_app(app)

# Inicializar Bcrypt para cifrar contraseñas
bcrypt = Bcrypt(app)

# Configurar Flask-Login para manejar las sesiones
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Si alguien sin sesión intenta entrar a una ruta protegida, lo manda aquí

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Crear todas las tablas en la base de datos (basado en las clases de db.py) y carga de datos de prueba
with app.app_context():
    db.create_all()
    
    # Validamos si ya existen libros en la base de datos
    if not Libro.query.first():
        print("Catalogo vacio. Insertando libros de prueba...")
        libro1 = Libro(
            titulo="Clean Code: A Handbook of Agile Software Craftsmanship",
            autor="Robert C. Martin",
            anio_publicacion=2008,
            precio=450.00,
            tipo_pasta="Blanda",
            calidad="Nuevo",
            categoria="Programación",
            imagen_url="https://images-na.ssl-images-amazon.com/images/I/41jEbK-jG+L._SX358_BO1,204,203,200_.jpg"
        )
        libro2 = Libro(
            titulo="Cien años de soledad",
            autor="Gabriel García Márquez",
            anio_publicacion=1967,
            precio=280.50,
            tipo_pasta="Dura",
            calidad="Usado",
            categoria="Novela",
            imagen_url="https://m.media-amazon.com/images/I/71YoFJSz3LL._SL1500_.jpg"
        )
        db.session.add_all([libro1, libro2])
        db.session.commit()
        print("Libros de prueba insertados.")
    else:
        print("Base de datos lista.")

# --- RUTAS ---

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/gallery.html')
def gallery():
    # Capturar lo que el usuario escribio en la searchbar
    # Usamos request.args para peticiones GET
    termino_busqueda = request.args.get('q', '')

    # Consulta base: solo libros disponibles (no vendidos)
    query = Libro.query.filter_by(vendido=False)

    # Si el usuario busco algo, agregamos filtros
    if termino_busqueda:
        # Agregamos (%) para buscar la palabra en cualquier parte del texto
        filtro = f"%{termino_busqueda}%"
        
        # Filtramos buscando coincidencias en Titulo, Autor o Categoria
        query = query.filter(
            db.or_(
                Libro.titulo.ilike(filtro),
                Libro.autor.ilike(filtro),
                Libro.categoria.ilike(filtro)
            )
        )

    # Ejecutar la consulta para traer los resultados finales
    catalogo = query.all()

    # Mandar los libros y el termino de busqueda (por si Oscar quiere dejarlo escrito en la barra)
    return render_template('gallery.html', libros=catalogo, busqueda=termino_busqueda)

@app.route('/comprar/<int:libro_id>', methods=['POST'])
@login_required
def comprar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    
    # Verificamos que el libro no haya sido comprado por alguien mas
    if libro.vendido:
        flash('Lo sentimos, este libro acaba de ser vendido.')
        return redirect(url_for('ver_shelf'))
        
    # Marcar el libro como vendido
    libro.vendido = True
    
    # Eliminar este libro de TODOS los libreros (Shelf) para que nadie mas lo intente comprar
    Shelf.query.filter_by(libro_id=libro.id).delete()
    
    # Guardamos los cambios en la base de datos
    db.session.commit()
    
    flash(f'Has comprado "{libro.titulo}". El vendedor se pondrá en contacto contigo.')
    
    # Lo regresamos a su librero
    return redirect(url_for('mi_librero'))

@app.route('/vender', methods=['GET', 'POST'])
@login_required
def vender_libro():
    if request.method == 'POST':
        # Capturamos los datos enviados por el formulario HTML
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        anio_publicacion = request.form.get('anio_publicacion')
        precio = request.form.get('precio')
        tipo_pasta = request.form.get('tipo_pasta')
        calidad = request.form.get('calidad')
        categoria = request.form.get('categoria')
        
        # Capturamos el archivo fisico del formulario
        imagen = request.files.get('imagen_archivo')
        imagen_url = "" # Variable vacía por defecto
        
        # Valida que una foto se haya subido
        if imagen and imagen.filename != '':
            # Limpia el nombre del archivo (ej. "mi foto.jpg" a "mi_foto.jpg")
            nombre_archivo = secure_filename(imagen.filename)
            
            # Construir ruta donde se guardara en la computadora
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            
            # Se guarda el archivo en la carpeta local temporal (esto debe ser reemplazado para la db despues...)
            imagen.save(ruta_guardado)
            
            # Guardamos en la base de datos la ruta relativa para que HTML la pueda leer
            imagen_url = f"/static/uploads/{nombre_archivo}"
        else:
            flash('Por favor, sube una imagen para tu libro.')
            return redirect(url_for('vender_libro'))

        # Validacion básica para evitar que suban libros vacios
        if not titulo or not autor or not precio:
            flash('Por favor, llena los campos obligatorios (Título, Autor, Precio).')
            return redirect(url_for('vender_libro'))

        # Construir objeto
        nuevo_libro = Libro(
            titulo=titulo,
            autor=autor,
            anio_publicacion=anio_publicacion,
            precio=float(precio),
            tipo_pasta=tipo_pasta,
            calidad=calidad,
            categoria=categoria,
            imagen_url=imagen_url,
            vendedor_id=current_user.id  # El libro se asocia al usuario actual
        )

        # Guardamos en la base de datos MySQL / SQLite
        db.session.add(nuevo_libro)
        db.session.commit()

        flash('¡Tu libro ha sido publicado para la venta exitosamente!')
        
        # Redirigir a la galeria para que el usuario vea su libro publicado
        return redirect(url_for('gallery'))

    # Si la peticion es GET, solo mostramos la pagina con el formulario
    # Oscar preparara un archivo para esto (tal vez sea transaction o el de vender)
    return render_template('Transaction.html')

@app.route('/book.html/<int:libro_id>')
def detalle_libro(libro_id):
    # Buscar libro por su id
    libro = Libro.query.get_or_404(libro_id)
    return render_template('Book.html', libro=libro)

@app.route('/comentar/<int:libro_id>', methods=['POST'])
@login_required
def agregar_comentario(libro_id):
    texto = request.form.get('contenido')
    
    if texto and texto.strip(): # Validar que no se envie un comentario vacio
        nuevo_comentario = Comentario(
            contenido=texto,
            usuario_id=current_user.id,
            libro_id=libro_id
        )
        db.session.add(nuevo_comentario)
        db.session.commit()
        flash('Tu comentario ha sido publicado.')
    else:
        flash('El comentario no puede estar vacío.')
        
    # Lo regresamos a la pagina del libro para que vea su comentario publicado
    return redirect(url_for('detalle_libro', libro_id=libro_id))

@app.route('/add_to_shelf/<int:libro_id>')
@login_required
def agregar_al_librero(libro_id):
    # Validacion de existencia (Evita errores si el ID del libro no existe)
    libro = Libro.query.get_or_404(libro_id)
    
    # Verificar si ya esta en el librero para no duplicar
    existe = Shelf.query.filter_by(usuario_id=current_user.id, libro_id=libro.id).first()
    
    if not existe:
        nueva_entrada = Shelf(usuario_id=current_user.id, libro_id=libro.id)
        db.session.add(nueva_entrada)
        db.session.commit()
        flash(f'"{libro.titulo}" se agregó a tu librero personal.')
    else:
        flash(f'"{libro.titulo}" ya está en tu colección.')
        
    # request.referrer devuelve al usuario 
    # a la pagina exacta donde estaba (sea la galeria o los detalles del libro)
    return redirect(request.referrer or url_for('gallery'))

@app.route('/shelf.html')
@login_required
def mi_librero():
    # Optimizacion de consulta (JOIN)
    # En lugar de hacer un "for" que pregunte a la base de datos multiples veces,
    # cruzamos las tablas Libro y Shelf.
    mis_libros = Libro.query.join(Shelf).filter(Shelf.usuario_id == current_user.id).all()
    
    return render_template('Shelf.html', libros=mis_libros)


# Funcionalidad: Eliminar
@app.route('/remove_from_shelf/<int:libro_id>')
@login_required
def eliminar_del_librero(libro_id):
    # Buscar el registro exacto que une a este usuario con este libro
    item = Shelf.query.filter_by(usuario_id=current_user.id, libro_id=libro_id).first()
    
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('El libro fue removido de tu librero.')
        
    # Regresar a que vean su librero
    return redirect(url_for('mi_librero'))

@app.route('/signup.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Capturar los datos del formulario HTML
        fname = request.form.get('fname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verificar si el correo ya existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este correo ya está registrado.')
            return redirect(url_for('signup.html'))
            
        # Cifrar la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Crear el nuevo usuario y guardarlo en la base de datos
        nuevo_usuario = Usuario(fname=fname, lastname=lastname, email=email, password=hashed_password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Registro exitoso. Ahora puedes iniciar sesión.')
        return redirect(url_for('signin.html'))
        
    # Si es GET, solo mostramos la página
    return render_template('signin.html')

@app.route('/signin.html', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Buscar al usuario por su correo
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verificar que el usuario exista y la contraseña coincida
        if usuario and bcrypt.check_password_hash(usuario.password, password):
            login_user(usuario)
            return redirect(url_for('inicio')) # Lo mandamos a la página principal
        else:
            flash('Correo o contraseña incorrectos.')
            
    return render_template('signin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)
