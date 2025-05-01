// Modal popup boxes
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

// Add new subject modal
document.getElementById('subject-select').addEventListener('change', function () {
    const showInput = this.value === 'add-new';
    document.getElementById('new-subject-container').style.display = showInput ? 'block' : 'none';
    document.getElementById('new-subject').required = showInput;
});