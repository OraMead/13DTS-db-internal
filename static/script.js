document.querySelectorAll('.open-modal-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-modal');
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'block';
    });
});

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal') || e.target.classList.contains('close-btn')) {
            modal.style.display = 'none';
        }
    });
});

document.getElementById('subject-select').addEventListener('change', function() {
    var value = this.value;
    if (value === 'add-new') {
        document.getElementById('new-subject-container').style.display = 'block';
    } else {
        document.getElementById('new-subject-container').style.display = 'none';
    }
});