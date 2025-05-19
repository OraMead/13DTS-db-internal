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

// Modal text inputs
document.addEventListener('DOMContentLoaded', function () {
    // Add subject box
    document.querySelectorAll('select[id^="subject-select-"]').forEach(select => {
        select.addEventListener('change', function () {
            const suffix = this.id.replace('subject-select-', '');
            const container = document.getElementById('new-subject-container-' + suffix);
            const input = document.getElementById('new-subject-' + suffix);

            if (container && input) {
                const showInput = this.value === 'add-new';
                container.style.display = showInput ? 'block' : 'none';
                input.required = showInput;
            }
        });
    });

    // Admin password box
    const roleSelect = document.getElementById('role');
    const adminPasswordGroup = document.getElementById('admin-password-group');

    if (roleSelect && adminPasswordGroup) {
        roleSelect.addEventListener('change', function () {
            const isAdmin = this.value === '2';
            adminPasswordGroup.style.display = isAdmin ? 'block' : 'none';
            const input = adminPasswordGroup.querySelector('input');
            input.required = isAdmin;
            if (!isAdmin) input.value = '';
        });
    }
});


// Toggle tags
document.addEventListener('change', function (e) {
    if (e.target.classList.contains('tag-checkbox')) {
        const checkbox = e.target;
        const noteId = checkbox.dataset.noteId;
        const tagId = checkbox.dataset.tagId;
        toggleTag(noteId, tagId, checkbox.checked);
    }
});

document.addEventListener('click', function (e) {
    if (e.target.classList.contains('remove-tag-btn')) { // Tags
        const noteId = e.target.dataset.noteId;
        const tagId = e.target.dataset.tagId;
        toggleTag(noteId, tagId, false);
    }
});

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.add-tag-btn').forEach(button => {
        button.addEventListener('click', function () {
            const noteId = this.dataset.noteId;
            const input = document.getElementById(`new-tag-input-${noteId}`);
            const tagName = input.value.trim();
            if (!tagName) return;

            fetch('/add-tag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag_name: tagName, note_id: noteId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const { tag_id, tag_name } = data;

                    document.querySelectorAll(`.modal`).forEach(modal => {
                        const tagContainer = modal.querySelector('[data-tag-container]');
                        if (!tagContainer) return;

                        if (modal.querySelector(`.tag-checkbox[data-tag-id="${tag_id}"]`)) return;

                        const label = document.createElement('label');
                        label.innerHTML = `
                            <input type="checkbox" class="tag-checkbox" data-tag-id="${tag_id}" data-note-id="${noteId}">
                            ${tag_name}
                        `;
                        tagContainer.appendChild(label);
                        tagContainer.appendChild(document.createElement('br'));
                    });

                    input.value = '';
                } else {
                    alert(data.error || 'Failed to add tag.');
                }
            });
        });
    });
});

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
        })
        .catch(error => {
            console.error('Failed to refresh tag list:', error);
        });
}

// Sharing
async function modifyShare(action, noteId, userId, permission = null) {
    const payload = { action, note_id: noteId, user_id: userId };
    if (permission !== null) payload.permission = permission;

    try {
        const res = await fetch('/modify-share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            refreshSharedList(noteId);
        } else {
            const error = await res.json();
            alert("Error: " + (error.message || error.error || 'Unknown error'));
        }
    } catch (err) {
        console.error("Sharing error:", err);
        alert("An error occurred while sharing.");
    }
}

function refreshSharedList(noteId) {
    fetch(`/process-shared/${noteId}`)
        .then(response => response.text())
        .then(html => {
            const noteContainer = document.querySelector(`.note-box[data-note-id="${noteId}"]`);
            const shareListContainer = noteContainer.querySelector('.share-list');
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newList = tempDiv.querySelector('.share-list');
            shareListContainer.replaceWith(newList);
        })
        .catch(error => {
            console.error('Failed to refresh shared list:', error);
        });
}

document.addEventListener('change', (e) => {
    if (e.target.classList.contains('permission-select')) {
        const shareBox = e.target.closest('.share-box');
        const userId = shareBox.dataset.userId;
        const noteId = e.target.closest('.share-list').dataset.noteId;
        const permission = e.target.value;

        if (permission === 'remove') {
            modifyShare('unshare', noteId, userId);
        } else {
            modifyShare('update', noteId, userId, permission);
        }
    }
});

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('add-share-btn')) {
        const container = e.target.closest('.note-box');
        const noteId = container.dataset.noteId;
        const userIdInput = container.querySelector('.new-user-id');
        const permissionSelect = container.querySelector('.new-user-permission');

        const userId = container.querySelector('.new-user-selected-id').value.trim();
        const permission = permissionSelect.value;

        if (!userId) {
            alert("Please enter a valid user ID.");
            return;
        }

        modifyShare('share', noteId, userId, permission)
            .then(() => {
                userIdInput.value = '';
            });
    } else if (e.target.classList.contains('suggestion-item')) {
        const item = e.target;
        const container = item.closest('.input-with-suggestions');
        const input = container.querySelector('.new-user-id');
        const hiddenInput = container.querySelector('.new-user-selected-id');

        input.value = item.textContent;
        hiddenInput.value = item.dataset.userId;

        container.querySelector('.suggestions-list').innerHTML = '';
        container.querySelector('.suggestions-list').style.display = 'none';
    }
});

document.addEventListener('input', async (e) => {
    if (e.target.classList.contains('new-user-id')) {
        const input = e.target;
        const query = input.value.trim();
        const container = input.closest('.input-with-suggestions');
        const suggestionsList = container.querySelector('.suggestions-list');
        const hiddenInput = container.querySelector('.new-user-selected-id');

        if (query.length < 1) {
            suggestionsList.innerHTML = '';
            suggestionsList.style.display = 'none';
            hiddenInput.value = '';
            return;
        }

        try {
            const res = await fetch(`/search-users?q=${encodeURIComponent(query)}`);
            const suggestions = await res.json();

            suggestionsList.innerHTML = '';
            if (suggestions.length === 0) {
                suggestionsList.style.display = 'none';
                hiddenInput.value = '';
                return;
            }

            suggestions.forEach(user => {
                const item = document.createElement('div');
                item.textContent = user.label;
                item.classList.add('suggestion-item');
                item.dataset.userId = user.id;
                suggestionsList.appendChild(item);
            });
            suggestionsList.style.display = 'block';
        } catch (err) {
            console.error('Failed to fetch user suggestions:', err);
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.new-user-id').forEach(input => {
        input.addEventListener('blur', () => {
            setTimeout(() => {
                const container = input.closest('.add-share-box');
                const suggestionsList = container.querySelector('.suggestions-list');
                suggestionsList.style.display = 'none';
            }, 200);
        });
    });
});

// Note box link
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.note-box').forEach(box => {
        box.addEventListener('click', function (e) {
            // Prevent navigation if a button or interactive child is clicked
            if (e.target.closest('button') || e.target.closest('.tag-list') || e.target.closest('.open-modal-btn')) {
                return;
            }
            const url = box.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        });
    });
});