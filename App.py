import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# 1. ACTUALIZACIÓN DE IMPORTACIONES: Cambiamos Shelf por Librero y añadimos VentaUsuario
from server.db import db, Usuario, Libro, Librero, Comentario, VentaUsuario 
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db_user = os.getenv('USER')
db_password = os.getenv('PASSWORD')
db_host = os.getenv('HOST')
db_name = os.getenv('DATABASE')

if db_user and db_name:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"
else:
    print("Credenciales MySQL no encontradas. Usando SQLite local para desarrollo.")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pesca_libros_local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin' # Actualizado al nombre real de ruta

@login_manager.user_loader
def load_user(user_id):
    # 2. ACTUALIZACIÓN: Se usa id_usuario en lugar de id
    return Usuario.query.get(int(user_id))

with app.app_context():
    db.create_all()
    
    if not Libro.query.first():
        print("Catalogo vacio. Insertando libros de prueba...")
        # 3. ACTUALIZACIÓN: Adaptado a las nuevas columnas obligatorias de Libro
        libro1 = Libro(
            nombre_libro="Clean Code: A Handbook of Agile Software Craftsmanship",
            autor="Robert C. Martin",
            publicacion_year=2008,
            genero_literario="Ingeniería",
            categoria="educativo",
            precio=450.00,
            stock=1,
            tiene_pasta_blanda=True,
            portada="https://images-na.ssl-images-amazon.com/images/I/41jEbK-jG+L._SX358_BO1,204,203,200_.jpg"
        )
        db.session.add(libro1)
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
    termino_busqueda = request.args.get('q', '')

    # 4. ACTUALIZACIÓN: Ya no existe "vendido", se busca que haya stock
    query = Libro.query.filter(Libro.stock > 0)

    if termino_busqueda:
        filtro = f"%{termino_busqueda}%"
        # 5. ACTUALIZACIÓN: titulo cambió a nombre_libro
        query = query.filter(
            db.or_(
                Libro.nombre_libro.ilike(filtro),
                Libro.autor.ilike(filtro),
                Libro.categoria.ilike(filtro)
            )
        )

    catalogo = query.all()
    return render_template('gallery.html', libros=catalogo, busqueda=termino_busqueda)

@app.route('/comprar/<int:libro_id>', methods=['POST'])
@login_required
def comprar_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    
    # 6. ACTUALIZACIÓN: Lógica de inventario por stock
    if libro.stock < 1:
        flash('Lo sentimos, este libro se ha agotado.')
        return redirect(url_for('mi_librero'))
        
    # Reduce stock y aumenta las ventas
    libro.stock -= 1
    libro.vendidos += 1
    
    # También actualizamos el estado en la tabla de Ventas_Usuarios P2P
    venta_relacionada = VentaUsuario.query.filter_by(id_libro=libro.id_libro, estado_venta='disponible').first()
    if venta_relacionada:
        venta_relacionada.estado_venta = 'vendido'
    
    # 7. ACTUALIZACIÓN: Limpiar de TODOS los carritos (Librero) usando id_libro
    Librero.query.filter_by(id_libro=libro.id_libro).delete()
    db.session.commit()
    
    flash(f'Has comprado "{libro.nombre_libro}". El vendedor se pondrá en contacto contigo.')
    return redirect(url_for('mi_librero'))

@app.route('/vender', methods=['GET', 'POST'])
@login_required
def vender_libro():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        anio_publicacion = request.form.get('anio_publicacion')
        precio = request.form.get('precio')
        calidad = request.form.get('calidad', 'Usado') 
        
        # Valores por defecto para mantener el formulario HTML simple por ahora
        categoria = 'entretenimiento'
        genero_literario = 'General'
        
        imagen = request.files.get('imagen_archivo')
        imagen_url = "" 
        
        if imagen and imagen.filename != '':
            nombre_archivo = secure_filename(imagen.filename)
            ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            imagen.save(ruta_guardado)
            imagen_url = f"/static/uploads/{nombre_archivo}"
        else:
            flash('Por favor, sube una imagen para tu libro.')
            return redirect(url_for('vender_libro'))

        if not titulo or not autor or not precio or not anio_publicacion:
            flash('Por favor, llena los campos obligatorios.')
            return redirect(url_for('vender_libro'))

        # 8. ACTUALIZACIÓN DUAL: Creamos el Libro en el catálogo general
        nuevo_libro = Libro(
            nombre_libro=titulo,
            autor=autor,
            publicacion_year=int(anio_publicacion),
            genero_literario=genero_literario,
            categoria=categoria,
            precio=float(precio),
            stock=1,
            portada=imagen_url
        )
        db.session.add(nuevo_libro)
        db.session.flush() # Obtenemos el ID del libro recién creado sin hacer commit final

        # ...Y registramos que ESTE usuario lo está vendiendo (P2P)
        nueva_venta = VentaUsuario(
            id_usuario=current_user.id_usuario,
            id_libro=nuevo_libro.id_libro,
            nombre_libro=titulo,
            autor=autor,
            tipo='pasta_blanda',
            descripcion_venta=f"Estado: {calidad}",
            precio=float(precio)
        )
        db.session.add(nueva_venta)
        db.session.commit()

        flash('¡Tu libro ha sido publicado para la venta exitosamente!')
        return redirect(url_for('gallery'))

    return render_template('Transaction.html')

@app.route('/book.html/<int:libro_id>')
def detalle_libro(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    return render_template('Book.html', libro=libro)

@app.route('/comentar/<int:libro_id>', methods=['POST'])
@login_required
def agregar_comentario(libro_id):
    texto = request.form.get('contenido')
    
    if texto and texto.strip(): 
        nuevo_comentario = Comentario(
            comentario=texto, # 9. ACTUALIZACIÓN: contenido -> comentario
            id_usuario=current_user.id_usuario,
            id_libro=libro_id
        )
        db.session.add(nuevo_comentario)
        db.session.commit()
        flash('Tu comentario ha sido publicado.')
    else:
        flash('El comentario no puede estar vacío.')
        
    return redirect(url_for('detalle_libro', libro_id=libro_id))

@app.route('/add_to_shelf/<int:libro_id>')
@login_required
def agregar_al_librero(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    
    # 10. ACTUALIZACIÓN: Shelf cambió a Librero y los IDs tienen nuevos nombres
    existe = Librero.query.filter_by(id_usuario=current_user.id_usuario, id_libro=libro.id_libro).first()
    
    if not existe:
        nueva_entrada = Librero(
            id_usuario=current_user.id_usuario, 
            id_libro=libro.id_libro,
            precio_unitario=libro.precio,
            cantidad=1
        )
        db.session.add(nueva_entrada)
        db.session.commit()
        flash(f'"{libro.nombre_libro}" se agregó a tu librero personal.')
    else:
        flash(f'"{libro.nombre_libro}" ya está en tu colección.')
        
    return redirect(request.referrer or url_for('gallery'))

@app.route('/shelf.html')
@login_required
def mi_librero():
    # 11. ACTUALIZACIÓN: JOIN con Librero
    mis_libros = Libro.query.join(Librero).filter(Librero.id_usuario == current_user.id_usuario).all()
    return render_template('Shelf.html', libros=mis_libros)

@app.route('/remove_from_shelf/<int:libro_id>', methods=['POST'])
@login_required
def eliminar_del_librero(libro_id):
    # Ya está usando POST como acordamos para mayor seguridad
    item = Librero.query.filter_by(id_usuario=current_user.id_usuario, id_libro=libro_id).first()
    
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('El libro fue removido de tu librero.')
        
    return redirect(url_for('mi_librero'))

@app.route('/signup.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # 12. ACTUALIZACIÓN: Los campos ahora deben coincidir con la tabla Usuarios
        nombre_usuario = request.form.get('nombre_usuario') 
        email = request.form.get('email')
        password = request.form.get('password')
        edad = request.form.get('edad')
        
        if not nombre_usuario or not email or not password or not edad:
            flash('Por favor, llena todos los campos.')
            return redirect(url_for('signup'))
            
        try:
            edad = int(edad)
            if edad < 13:
                flash('Debes tener al menos 13 años.')
                return redirect(url_for('signup'))
        except ValueError:
            flash('Edad inválida.')
            return redirect(url_for('signup'))

        usuario_existente = Usuario.query.filter_by(correo=email).first()
        if usuario_existente:
            flash('Este correo ya está registrado.')
            return redirect(url_for('signup'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        nuevo_usuario = Usuario(
            nombre_usuario=nombre_usuario, 
            correo=email, 
            contrasena=hashed_password,
            edad=edad
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Registro exitoso. Ahora puedes iniciar sesión.')
        return redirect(url_for('signin'))
        
    return render_template('signup.html')

@app.route('/signin.html', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 13. ACTUALIZACIÓN: 'email' -> 'correo' y 'password' -> 'contrasena'
        usuario = Usuario.query.filter_by(correo=email).first()
        
        if usuario and bcrypt.check_password_hash(usuario.contrasena, password):
            login_user(usuario)
            return redirect(url_for('inicio')) 
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
