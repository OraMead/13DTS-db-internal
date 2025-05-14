// On start logic
// document.addEventListener('DOMContentLoaded', () => {
//     bindRemoveTagButtons();
// });


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


document.addEventListener('click', function (e) {
    if (e.target.classList.contains('remove-tag-btn')) {
        const noteId = e.target.dataset.noteId;
        const tagId = e.target.dataset.tagId;
        toggleTag(noteId, tagId, false);
    }
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
document.querySelectorAll('.permission-select').forEach(select => {
    select.addEventListener('change', async (e) => {
        const shareBox = e.target.closest('.share-box');
        const userId = shareBox.dataset.userId;
        const noteId = e.target.closest('.share-list').dataset.noteId;
        const newPermission = e.target.value;

        if (newPermission === 'remove') {
            const res = await fetch(`/unshare`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note_id: noteId, user_id: userId })
            });
            if (res.ok) {
                shareBox.remove();
            }
        } else {
            await fetch(`/update-permission`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note_id: noteId, user_id: userId, permission: newPermission })
            });
        }
    });
});

document.querySelectorAll('.note-box').forEach(container => {
    const noteId = container.dataset.noteId;
    const addButton = container.querySelector('.add-share-btn');

    addButton.addEventListener('click', async () => {
        const userIdInput = container.querySelector('.new-user-id');
        const permissionSelect = container.querySelector('.new-user-permission');
        const userId = userIdInput.value.trim();
        const permission = permissionSelect.value;

        if (!userId) return alert("Please enter a username.");

        const res = await fetch('/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                note_id: noteId,
                user_id: userId,
                permission: permission
            })
        });

        // if (res.ok) {
        //     const data = await res.json();
        //     const shareList = container.querySelector('.share-list');

        //     const newDiv = document.createElement('div');
        //     newDiv.className = 'share-box';
        //     newDiv.dataset.userId = data.user_id;

        //     newDiv.innerHTML = `
        //         <span>${data.name}</span>
        //         <select class="permission-select">
        //             <option value="0"${permission === '0' ? ' selected' : ''}>Read</option>
        //             <option value="1"${permission === '1' ? ' selected' : ''}>Edit</option>
        //             <option value="2"${permission === '2' ? ' selected' : ''}>Manage</option>
        //             <option value="remove">Remove</option>
        //         </select>
        //     `;

        //     shareList.appendChild(newDiv);

        //     usernameInput.value = '';
        // } else {
        //     const error = await res.json();
        //     alert("Error: " + (error.message || error.error || 'Unknown error'));
        // }
    });
});
