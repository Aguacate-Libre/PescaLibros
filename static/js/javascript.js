// script 1 -----------------------------------------------------------------------------------

const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.settings-section');

navItems.forEach(item => {
  item.addEventListener('click', () => {
    // Activar nav
    navItems.forEach(n => n.classList.remove('active'));
    item.classList.add('active');

    // Mostrar sección correspondiente
    const target = item.dataset.section;
    sections.forEach(s => s.classList.remove('active'));
    document.getElementById(target).classList.add('active');
  });
});

// Feedback al guardar
document.querySelectorAll('.btn-save').forEach(btn => {
  btn.addEventListener('click', () => {
    const original = btn.textContent;
    btn.textContent = '✓ Guardado';
    btn.style.background = '#27ae60';
    setTimeout(() => {
      btn.textContent = original;
      btn.style.background = '';
    }, 2000);
  });
});

// Confirmación para eliminar cuenta
const btnEliminar = document.querySelector('.btn-danger');
if (btnEliminar) {
  btnEliminar.addEventListener('click', () => {
    const confirm = window.confirm('¿Estás seguro de que deseas eliminar tu cuenta? Esta acción no se puede deshacer.');
    if (confirm) alert('Cuenta eliminada (demo).');
  });
}

// script 2 -----------------------------------------------------------------------------------

// ── Datos de los libros ──
const books = [
  { id: 1, price: 299 },
  { id: 2, price: 450 },
  { id: 3, price: 149 },
];

const SHIPPING_COST = 80;

// Cantidades iniciales
const quantities = { 1: 1, 2: 2, 3: 1 };

// ── Actualizar totales ──
function updateTotals() {
  let subtotal = 0;
  books.forEach(book => {
    const qty = quantities[book.id] ?? 0;
    subtotal += book.price * qty;
  });

  document.getElementById('subtotal').textContent = `$${subtotal.toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
  document.getElementById('total').textContent = `$${(subtotal + SHIPPING_COST).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`;
}

// ── Actualizar contador de artículos ──
function updateItemCount() {
  const total = Object.values(quantities).reduce((a, b) => a + b, 0);
  const el = document.getElementById('item-count');
  if (el) el.textContent = `${total} artículo${total !== 1 ? 's' : ''}`;
}

// ── Eliminar libro ──
function removeBook(id) {
  const item = document.querySelector(`.book-item[data-id="${id}"]`);
  if (item) {
    item.style.opacity = '0';
    item.style.transform = 'translateX(16px)';
    item.style.transition = 'opacity 0.25s, transform 0.25s';
    setTimeout(() => {
      item.remove();
      delete quantities[id];
      updateTotals();
      updateItemCount();
      checkEmpty();
    }, 260);
  }
}

// ── Verificar carrito vacío ──
function checkEmpty() {
  const list = document.getElementById('book-list');
  const empty = document.getElementById('cart-empty');
  const footer = document.querySelector('.cart-footer');

  if (list && list.children.length === 0) {
    if (empty) empty.style.display = 'block';
    if (footer) footer.style.display = 'none';
  }
}

// ── Eventos de cantidad y eliminación ──
document.getElementById('book-list').addEventListener('click', (e) => {
  const id = parseInt(e.target.dataset.id);
  if (!id) return;

  if (e.target.classList.contains('plus')) {
    quantities[id] = (quantities[id] ?? 0) + 1;
    document.getElementById(`qty-${id}`).textContent = quantities[id];
    updateTotals();
    updateItemCount();
  }

  if (e.target.classList.contains('minus')) {
    if (quantities[id] > 1) {
      quantities[id]--;
      document.getElementById(`qty-${id}`).textContent = quantities[id];
      updateTotals();
      updateItemCount();
    }
  }

  if (e.target.classList.contains('btn-remove')) {
    removeBook(id);
  }
});

// ── Animación de la barra de progreso al cargar ──
window.addEventListener('DOMContentLoaded', () => {
  updateTotals();
  updateItemCount();

  // Animar barra de progreso
  const fill = document.getElementById('progress-fill');
  if (fill) {
    const target = fill.style.width;
    fill.style.width = '0%';
    setTimeout(() => { fill.style.width = target; }, 300);
  }
});

// script 3 -----------------------------------------------------------------------------------

// Feedback al agregar al carrito
document.querySelectorAll('.seller-card .btn-save').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.added) return;
    btn.dataset.added = true;
    btn.textContent = '✓ Agregado';
    btn.style.background = '#27ae60';
    setTimeout(() => {
      btn.textContent = 'Agregar al carrito';
      btn.style.background = '';
      delete btn.dataset.added;
    }, 2000);
  });
});