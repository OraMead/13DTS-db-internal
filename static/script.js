// On start logic
document.addEventListener('DOMContentLoaded', () => {
    bindRemoveTagButtons();
});


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

// Toggle tags
document.querySelectorAll('.tag-checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', () => {
        const noteId = checkbox.dataset.noteId;
        const tagId = checkbox.dataset.tagId;
        const checked = checkbox.checked;
        toggleTag(noteId, tagId, checked)
    });
});


function bindRemoveTagButtons() {
    document.querySelectorAll('.remove-tag-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const noteId = btn.dataset.noteId;
            const tagId = btn.dataset.tagId;
            toggleTag(noteId, tagId, false);
        });
    });
}


function toggleTag(noteId, tagId, checked) {
    fetch('/toggle', {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            note_id: noteId,
            tag_id: tagId,
            action: checked
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Server returned error');
        return response.json();
    })
    .then(data => {
        if (!data.success) throw new Error(data.error || 'Unknown error');

        refreshTagList(noteId);

        const modal = document.getElementById(`change-tags-modal-${noteId}`);
        const checkbox = modal.querySelector(`.tag-checkbox[data-tag-id="${tagId}"]`);
        if (checkbox) checkbox.checked = checked;
    })
    .catch(error => {
        alert('Failed to update tag: ' + error.message);
        checkbox.checked = !checked;
    });
}


function refreshTagList(noteId) {
    fetch(`/process-tags/${noteId}`)
        .then(response => response.text())
        .then(html => {
            const noteContainer = document.querySelector(`.note-box[data-note-id="${noteId}"]`);
            const tagListContainer = noteContainer.querySelector('.tag-list');
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newList = tempDiv.querySelector('.tag-list');
            tagListContainer.replaceWith(newList);
            bindRemoveTagButtons();
        })
        .catch(error => {
            console.error('Failed to refresh tag list:', error);
        });
}
