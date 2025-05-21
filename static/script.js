// Run setup when DOM content has fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // Modal text inputs - Add subject box
    // For each subject select dropdown with id starting "subject-select-"
    document.querySelectorAll('select[id^="subject-select-"]').forEach(select => {
        // Listen for change event to toggle "Add new subject" input visibility
        select.addEventListener('change', function () {
            const suffix = this.id.replace('subject-select-', '');
            const container = document.getElementById('new-subject-container-' + suffix);
            const input = document.getElementById('new-subject-' + suffix);

            if (container && input) {
                // Show input only if "Add new" option selected
                const showInput = this.value === 'add-new';
                container.style.display = showInput ? 'block' : 'none';
                input.required = showInput; // Make input required if visible
            }
        });
    });

    // Modal text inputs - Admin password box
    const roleSelect = document.getElementById('role');
    const adminPasswordGroup = document.getElementById('admin-password-group');

    if (roleSelect && adminPasswordGroup) {
        // Listen for role changes to toggle admin password field visibility & requirement
        roleSelect.addEventListener('change', function () {
            const isAdmin = this.value === '2'; // Role "2" is admin
            adminPasswordGroup.style.display = isAdmin ? 'block' : 'none';
            const input = adminPasswordGroup.querySelector('input');
            input.required = isAdmin;

            if (!isAdmin) input.value = ''; // Clear password if not admin role
        });
    }

    // Add tag button listeners
    // Attach click event listeners to all buttons with class "add-tag-btn"
    document.querySelectorAll('.add-tag-btn').forEach(button => {
        button.addEventListener('click', function () {
            const noteId = this.dataset.noteId;
            const input = document.getElementById(`new-tag-input-${noteId}`);
            const tagName = input.value.trim();

            if (!tagName) return; // Ignore empty inputs

            // Send POST request to add new tag for the note
            fetch('/add-tag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag_name: tagName, note_id: noteId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const { tag_id, tag_name } = data;

                    // For every open modal, add checkbox for new tag if not already present
                    document.querySelectorAll(`.modal`).forEach(modal => {
                        const tagContainer = modal.querySelector('[data-tag-container]');
                        if (!tagContainer) return;

                        // Skip if checkbox for this tag already exists
                        if (modal.querySelector(`.tag-checkbox[data-tag-id="${tag_id}"]`)) return;

                        // Create checkbox and label elements for the new tag
                        const label = document.createElement('label');
                        label.innerHTML = `
                            <input type="checkbox" class="tag-checkbox" data-tag-id="${tag_id}" data-note-id="${noteId}">
                            ${tag_name}
                        `;
                        tagContainer.appendChild(label);
                        tagContainer.appendChild(document.createElement('br'));
                    });

                    input.value = ''; // Clear input after adding tag
                } else {
                    alert(data.error || 'Failed to add tag.');
                }
            });
        });
    });

    // Hide sharing suggestions dropdown on blur
    document.querySelectorAll('.new-user-id').forEach(input => {
        input.addEventListener('blur', () => {
            // Delay hiding to allow click on suggestion items
            setTimeout(() => {
                const container = input.closest('.add-share-box');
                const suggestionsList = container.querySelector('.suggestions-list');
                suggestionsList.style.display = 'none';
            }, 200);
        });
    });

    // Navigate to note URL on note box click
    // Except when clicking buttons, tags, modals inside the box
    document.querySelectorAll('.note-box').forEach(box => {
        box.addEventListener('click', function (e) {
            if (e.target.closest('button') || e.target.closest('.tag-list') || e.target.closest('.open-modal-btn') || e.target.closest('.modal')) {
                return; // Ignore clicks on interactive children
            }
            const url = box.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        });
    });
});

// Modal popup open buttons
// Attach click listeners to open modals by id
document.querySelectorAll('.open-modal-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-modal');
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'block'; // Show modal
    });
});

// Modal close handler
// Close modal when clicking background or close button
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal') || e.target.classList.contains('close-btn')) {
            modal.style.display = 'none';
        }
    });
});

// Tag checkbox toggle (add/remove tag)
document.addEventListener('change', function (e) {
    if (e.target.classList.contains('tag-checkbox')) {
        const checkbox = e.target;
        const noteId = checkbox.dataset.noteId;
        const tagId = checkbox.dataset.tagId;
        toggleTag(noteId, tagId, checkbox.checked);
    }
});

// Remove tag button handler
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('remove-tag-btn')) {
        const noteId = e.target.dataset.noteId;
        const tagId = e.target.dataset.tagId;
        toggleTag(noteId, tagId, false);
    }
});

// Toggle tag association on the server for a note.
function toggleTag(noteId, tagId, checked) {
    fetch('/toggle', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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

        // Refresh tag list UI after successful update
        refreshTagList(noteId);

        // Sync checkbox state inside the modal
        const modal = document.getElementById(`change-tags-modal-${noteId}`);
        const checkbox = modal.querySelector(`.tag-checkbox[data-tag-id="${tagId}"]`);
        if (checkbox) checkbox.checked = checked;
    })
    .catch(error => {
        alert('Failed to update tag: ' + error.message);

        // Revert checkbox state if update failed
        const modal = document.getElementById(`change-tags-modal-${noteId}`);
        const checkbox = modal.querySelector(`.tag-checkbox[data-tag-id="${tagId}"]`);
        if (checkbox) checkbox.checked = !checked;
    });
}

// Refresh the displayed tag list for a note by fetching updated HTML.
function refreshTagList(noteId) {
    fetch(`/process-tags/${noteId}`)
        .then(response => response.text())
        .then(html => {
            const noteContainer = document.querySelector(`.note-box[data-note-id="${noteId}"]`);
            const tagListContainer = noteContainer.querySelector('.tag-list');

            // Parse returned HTML and replace existing tag list
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newList = tempDiv.querySelector('.tag-list');
            tagListContainer.replaceWith(newList);
        })
        .catch(error => {
            console.error('Failed to refresh tag list:', error);
        });
}

// Modify sharing permissions or share/unshare a note with a user.
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
            // Refresh shared user list after successful update
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

// Refresh the displayed shared users list for a note.
function refreshSharedList(noteId) {
    fetch(`/process-shared/${noteId}`)
        .then(response => response.text())
        .then(html => {
            const noteContainer = document.querySelector(`.note-box[data-note-id="${noteId}"]`);
            const shareListContainer = noteContainer.querySelector('.share-list');

            // Replace existing shared list with updated HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newList = tempDiv.querySelector('.share-list');
            shareListContainer.replaceWith(newList);
        })
        .catch(error => {
            console.error('Failed to refresh shared list:', error);
        });
}

// Change permission select dropdown handler
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

// Add share button and suggestion item click handler
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('add-share-btn')) {
        const container = e.target.closest('.note-box');
        const noteId = container.dataset.noteId;
        const userIdInput = container.querySelector('.new-user-id');
        const permissionSelect = container.querySelector('.new-user-permission');
        const userId = container.querySelector('.new-user-selected-id').value.trim();
        const permission = permissionSelect.value;

        // If no user has been selected (e.g., no suggestion clicked)
        if (!userId) {
            alert("Please enter a valid user ID.");
            return;
        }

        // Call modifyShare() to share the note with the selected user and permission
        // After successful share, clear the visible input box
        modifyShare('share', noteId, userId, permission)
            .then(() => {
                userIdInput.value = '';
            });

    // If the clicked element is one of the suggested users
    } else if (e.target.classList.contains('suggestion-item')) {
        const item = e.target;
        const container = item.closest('.input-with-suggestions');
        const input = container.querySelector('.new-user-id');
        const hiddenInput = container.querySelector('.new-user-selected-id');

        // Fill input box with the suggestion text (e.g., username or email)
        input.value = item.textContent;
        // Store the selected user ID in the hidden input
        hiddenInput.value = item.dataset.userId;

        // Clear and hide the suggestions dropdown
        container.querySelector('.suggestions-list').innerHTML = '';
        container.querySelector('.suggestions-list').style.display = 'none';
    }
});

// Handle typing into the user input box to show suggestions
document.addEventListener('input', async (e) => {
    // If user is typing in a user ID or name input field
    if (e.target.classList.contains('new-user-id')) {
        const input = e.target;
        const query = input.value.trim();

        const container = input.closest('.input-with-suggestions');
        const suggestionsList = container.querySelector('.suggestions-list');
        const hiddenInput = container.querySelector('.new-user-selected-id');
        // If query is empty, hide suggestions and clear stored user ID
        if (query.length < 1) {
            suggestionsList.innerHTML = '';
            suggestionsList.style.display = 'none';
            hiddenInput.value = '';
            return;
        }

        try {
            // Fetch matching user suggestions from the server
            const res = await fetch(`/search-users?q=${encodeURIComponent(query)}`);
            const suggestions = await res.json(); // Expecting an array of user objects: { id, label }

            suggestionsList.innerHTML = '';

            // If no suggestions were returned, hide the dropdown
            if (suggestions.length === 0) {
                suggestionsList.style.display = 'none';
                hiddenInput.value = '';
                return;
            }

            // Render each suggestion as a clickable div with user ID stored in data attribute
            suggestions.forEach(user => {
                const item = document.createElement('div');
                item.textContent = user.label; // Display label (e.g., name or email)
                item.classList.add('suggestion-item');
                item.dataset.userId = user.id;

                suggestionsList.appendChild(item); // Add to dropdown
            });
            suggestionsList.style.display = 'block';
        } catch (err) {
            console.error('Failed to fetch user suggestions:', err);
        }
    }
});
