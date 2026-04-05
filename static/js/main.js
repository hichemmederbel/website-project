//main.js – Validation côté client + interactivité


function validateField(input, errorEl, message) {
  if (!input.value.trim()) {
    input.classList.add('error');
    errorEl.textContent = message;
    errorEl.classList.add('show');
    return false;
  }
  input.classList.remove('error');
  errorEl.classList.remove('show');
  return true;
}

// Formulaire de connexion
function initLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    const nameInput = document.getElementById('login-name');
    const nameError = document.getElementById('login-name-error');
    const pwInput = document.getElementById('login-password');
    const pwError = document.getElementById('login-password-error');

    let valid = true;
    valid = validateField(nameInput, nameError, "Le nom d'utilisateur est requis.") && valid;
    valid = validateField(pwInput, pwError, "Le mot de passe est requis.") && valid;

    if (!valid) e.preventDefault();
  });
}

// Formulaire d'inscription
function initRegisterForm() {
  const form = document.getElementById('register-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    const nameInput = document.getElementById('reg-name');
    const nameError = document.getElementById('reg-name-error');
    const pwInput = document.getElementById('reg-password');
    const pwError = document.getElementById('reg-password-error');
    const cfmInput = document.getElementById('reg-confirm');
    const cfmError = document.getElementById('reg-confirm-error');

    let valid = true;
    valid = validateField(nameInput, nameError, "Le nom d'utilisateur est requis.") && valid;
    valid = validateField(pwInput, pwError, "Le mot de passe est requis.") && valid;
    valid = validateField(cfmInput, cfmError, "La confirmation est requise.") && valid;

    if (valid && pwInput.value !== cfmInput.value) {
      cfmInput.classList.add('error');
      cfmError.textContent = "Les mots de passe ne correspondent pas.";
      cfmError.classList.add('show');
      e.preventDefault();
    }
  });
}

// Formulaire d'ajout de tâche (admin)
function initAddTaskForm() {
  const form = document.getElementById('add-task-form');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    const titleInput = document.getElementById('task-title');
    const titleError = document.getElementById('task-title-error');
    const startInput = document.getElementById('task-start');
    const startError = document.getElementById('task-start-error');
    const endInput = document.getElementById('task-end');
    const endError = document.getElementById('task-end-error');

    let valid = true;
    valid = validateField(titleInput, titleError, "Le titre de la tâche est requis.") && valid;
    valid = validateField(startInput, startError, "L'heure de début est requise.") && valid;
    valid = validateField(endInput, endError, "L'heure de fin est requise.") && valid;

    if (valid && startInput.value >= endInput.value) {
      endInput.classList.add('error');
      endError.textContent = "L'heure de fin doit être après l'heure de début.";
      endError.classList.add('show');
      e.preventDefault();
    }
  });
}

// Filtre des tâches

function initTaskFilters() {
  const buttons = document.querySelectorAll('.filter-btn[data-filter]');
  const cards = document.querySelectorAll('.task-card[data-status]');
  if (!buttons.length) return;

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;
      cards.forEach(card => {
        const show = filter === 'all' || card.dataset.status === filter;
        card.style.display = show ? '' : 'none';
      });
    });
  });
}

//Auto-dismiss des flash messages

function initFlashMessages() {
  const messages = document.querySelectorAll('.flash');
  messages.forEach(msg => {
    setTimeout(() => {
      msg.style.transition = 'opacity 0.4s, transform 0.4s';
      msg.style.opacity = '0';
      msg.style.transform = 'translateY(-8px)';
      setTimeout(() => msg.remove(), 400);
    }, 4000);
  });
}

//Init

document.addEventListener('DOMContentLoaded', () => {
  initLoginForm();
  initRegisterForm();
  initAddTaskForm();
  initTaskFilters();
  initFlashMessages();
});
