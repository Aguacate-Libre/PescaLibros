import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# 1. ACTUALIZACIÓN DE IMPORTACIONES: Cambiamos Shelf por Librero y añadimos VentaUsuario
# OTRA ACTUALIZACION:  LAS RUTAS FALTANTES
from server.db import db, Usuario, Libro, Librero, Comentario, VentaUsuario, Contacto, Pedido, DetallePedido, Favorito, Seguimiento
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

@app.route('/perfil')
@login_required
def mi_perfil():
    # Obtener los libros favoritos del usuario
    mis_favoritos = db.session.query(Libro).join(Favorito).filter(Favorito.id_usuario == current_user.id_usuario).all()
    
    # Obtener a los vendedores que este usuario sigue
    siguiendo_a = db.session.query(Usuario).join(Seguimiento, Seguimiento.id_seguido == Usuario.id_usuario)\
                  .filter(Seguimiento.id_seguidor == current_user.id_usuario).all()

    # Obtener los libros que yo estoy vendiendo
    mis_ventas = VentaUsuario.query.filter_by(id_usuario=current_user.id_usuario).all()

    return render_template('Account.html', favoritos=mis_favoritos, siguiendo=siguiendo_a, mis_ventas=mis_ventas)

@app.route('/store/<int:vendedor_id>')
def ver_tienda(vendedor_id):
    # Buscar al vendedor
    vendedor = Usuario.query.get_or_404(vendedor_id)
    
    # Buscar los libros que tiene a la venta (que esten disponibles)
    libros_venta = VentaUsuario.query.filter_by(id_usuario=vendedor_id, estado_venta='disponible').all()
    
    # Verificar si el usuario actual ya lo sigue 
    lo_sigue = False
    if current_user.is_authenticated:
        lo_sigue = Seguimiento.query.filter_by(id_seguidor=current_user.id_usuario, id_seguido=vendedor_id).first() is not None

    return render_template('store.html', vendedor=vendedor, libros=libros_venta, lo_sigue=lo_sigue)

# Follower stuff
@app.route('/seguir/<int:vendedor_id>', methods=['POST'])
@login_required
def toggle_seguir(vendedor_id):
    if vendedor_id == current_user.id_usuario:
        flash('No puedes seguirte a ti mismo.')
        return redirect(request.referrer or url_for('inicio'))

    vendedor = Usuario.query.get_or_404(vendedor_id)
    relacion = Seguimiento.query.filter_by(id_seguidor=current_user.id_usuario, id_seguido=vendedor_id).first()

    if relacion:
        # Ya lo sigue -> Lo dejamos de seguir
        db.session.delete(relacion)
        vendedor.seguidores -= 1 # Restamos al contador
        flash(f'Has dejado de seguir a {vendedor.nombre_usuario}.')
    else:
        # No lo sigue -> Lo empezamos a seguir
        nuevo_seguimiento = Seguimiento(id_seguidor=current_user.id_usuario, id_seguido=vendedor_id)
        db.session.add(nuevo_seguimiento)
        vendedor.seguidores += 1 # Sumamos al contador
        flash(f'Ahora sigues a {vendedor.nombre_usuario}.')

    db.session.commit()
    return redirect(request.referrer or url_for('ver_tienda', vendedor_id=vendedor_id))

@app.route('/favorito/<int:libro_id>', methods=['POST'])
@login_required
def toggle_favorito(libro_id):
    libro = Libro.query.get_or_404(libro_id)
    favorito_existente = Favorito.query.filter_by(id_usuario=current_user.id_usuario, id_libro=libro_id).first()

    if favorito_existente:
        # Ya es favorito -> Lo quitamos
        db.session.delete(favorito_existente)
        if libro.favoritos > 0:
            libro.favoritos -= 1
        flash('Libro eliminado de tus favoritos.')
    else:
        # No es favorito -> Lo agregamos
        nuevo_favorito = Favorito(id_usuario=current_user.id_usuario, id_libro=libro_id)
        db.session.add(nuevo_favorito)
        libro.favoritos += 1
        flash('Libro agregado a tus favoritos.')

    db.session.commit()
    return redirect(request.referrer or url_for('gallery'))

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
    comentarios = Comentario.query.filter_by(id_libro=libro_id).all()
    favorito = False

    if current_user.is_authenticated:
        favorito = Favorito.query.filter_by(
            id_usuario=current_user.id_usuario,
            id_libro=libro_id
        ).first() is not None
    return render_template('Book.html', libro=libro, comentarios=comentarios, favorito=favorito)


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

@app.route('/checkout', methods=['POST'])
@login_required
def procesar_pago():
    # Obtener los productos actuales en el carrito del usuario
    items_carrito = Librero.query.filter_by(id_usuario=current_user.id_usuario, estado='activo').all()

    if not items_carrito:
        flash('Tu librero está vacío.')
        return redirect(url_for('mi_librero'))

    # Calcular el total y capturar datos del formulario de pago
    total = sum(item.precio_unitario * item.cantidad for item in items_carrito)
    metodo = request.form.get('metodo_pago') # tarjeta, paypal, etc.
    direccion = request.form.get('direccion')

    # Crear el registro del pedido
    nuevo_pedido = Pedido(
        id_usuario=current_user.id_usuario,
        metodo_pago=metodo,
        direccion_envio=direccion,
        total_pedido=total,
        estado_pedido='pendiente'
    )
    
    try:
        db.session.add(nuevo_pedido)
        db.session.flush() # Obtenemos el id_pedido sin cerrar la transaccion

        # Mover cada item del carrito a Detalle_Pedido y actualizar stock
        for item in items_carrito:
            # Se crea el detalle historico
            detalle = DetallePedido(
                id_pedido=nuevo_pedido.id_pedido,
                id_libro=item.id_libro,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario
            )
            db.session.add(detalle)

            # Actualizar el inventario del libro
            libro = Libro.query.get(item.id_libro)
            if libro.stock >= item.cantidad:
                libro.stock -= item.cantidad
                libro.vendidos += item.cantidad
            else:
                db.session.rollback()
                flash(f'Lo sentimos, ya no hay suficiente stock de "{libro.nombre_libro}".')
                return redirect(url_for('mi_librero'))

        # Limpiar el librero del usuario
        Librero.query.filter_by(id_usuario=current_user.id_usuario).delete()

        db.session.commit()
        flash('¡Compra realizada con éxito!')
        return redirect(url_for('ver_recibo', pedido_id=nuevo_pedido.id_pedido))

    except Exception as e:
        db.session.rollback()
        print(f"Error en checkout: {e}")
        flash('Hubo un problema al procesar tu pago.')
        return redirect(url_for('mi_librero'))

@app.route('/recibo/<int:pedido_id>')
@login_required
def ver_recibo(pedido_id):
    # Buscar pedido, que pertenezca al usuario actual
    pedido = Pedido.query.filter_by(id_pedido=pedido_id, id_usuario=current_user.id_usuario).first_or_404()
    
    # Obtenemos los detalles haciendo un JOIN con libros para tener los nombres
    detalles = db.session.query(DetallePedido, Libro).\
               join(Libro, DetallePedido.id_libro == Libro.id_libro).\
               filter(DetallePedido.id_pedido == pedido_id).all()

    return render_template('Receipt.html', pedido=pedido, detalles=detalles)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        # Capturar los datos del formulario HTML
        correo = request.form.get('correo')
        asunto = request.form.get('asunto')
        tipo_problema = request.form.get('tipo_problema')
        descripcion = request.form.get('descripcion')

        # Validacion
        if not asunto or not tipo_problema or not descripcion:
            flash('Por favor, llena los campos obligatorios del formulario.')
            return redirect(url_for('contacto'))

        # Logica para el ID de usuario
        # Si el usuario tiene sesion iniciada, guardamos su ID. Si es un visitante guest, guardamos None.
        usuario_id = current_user.id_usuario if current_user.is_authenticated else None
        
        # Si el usuario está logueado pero no escribio correo, usamos el de su cuenta
        if current_user.is_authenticated and not correo:
            correo = current_user.correo

        # Objeto para la base de datos
        nuevo_ticket = Contacto(
            id_usuario=usuario_id,
            correo_contacto=correo,
            asunto=asunto,
            tipo_problema=tipo_problema,
            descripcion_problema=descripcion
            # 'estado' y 'fecha_envio' se llenan solos gracias a los valores default en db.py
        )

        # 5. Guardamos en MySQL/SQLite
        db.session.add(nuevo_ticket)
        db.session.commit()

        flash('Tu mensaje ha sido enviado al equipo de soporte. Te contactaremos pronto.')
        return redirect(url_for('inicio'))

    # Si es GET, mostramos el diseño de Oscar
    return render_template('Contact.html')

@app.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    if request.method == 'POST':
        # Aquí programarás la lógica para actualizar perfil o contraseña después
        flash('Configuración actualizada.')
        return redirect(url_for('mi_perfil'))
        
    return render_template('Settings.html')

@app.route('/about')
def sobre_nosotros():
    # Renderiza la pagina informativa del proyecto y el equipo
    return render_template('About.html')

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

@app.route('/auth', methods=['GET', 'POST'])
def portal_autenticacion():
    # Si el usuario ya tiene sesion iniciada, no tiene sentido que este aqui
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        # Aquí entraría la logica futura de "Olvide mi contraseña" 
        # Este CAMBIA si si hacemos esto
        flash('La función de recuperación de cuenta está en construcción.')
        return redirect(url_for('signin'))
        
    return render_template('Auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)
