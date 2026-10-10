document.addEventListener('DOMContentLoaded', () => {
  // Confirm before submitting remove forms for wishlist or collection
  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;

    const action = (form.getAttribute('action') || '').toLowerCase();
    const isWishlistRemove = action.includes('/wishlist/remove');
    const isCollectionRemove = action.includes('/collection/remove');

    // Also catch forms that use icon-remove buttons
    const hasIconRemove = form.querySelector('.icon-remove') !== null;

    if (isWishlistRemove || isCollectionRemove || hasIconRemove) {
      const confirmMsg = isWishlistRemove ? 'Remove this item from your wishlist?'
                        : isCollectionRemove ? 'Remove this item from your collection?'
                        : 'Remove this item?';
      if (!window.confirm(confirmMsg)) {
        event.preventDefault();
      }
    }
  }, true);

  // Wishlist/collection add/remove: submit with fetch so the page doesn't reload and jump to the top
  const listActionPattern = /\/(wishlist|collection)\/(add|remove)\/\d+$/;

  let toastTimer = null;
  const showToast = (message) => {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast';
      toast.className = 'toast';
      toast.setAttribute('role', 'status');
      toast.setAttribute('aria-live', 'polite');
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 2500);
  };

  const updateListForm = (form, button, inList) => {
    // Toggle buttons (homepage and search results) switch between add and remove
    if (button && button.dataset.labelAdd) {
      const action = form.getAttribute('action');
      form.setAttribute('action', action.replace(/\/(add|remove)\//, inList ? '/remove/' : '/add/'));
      button.textContent = inList ? button.dataset.labelRemove : button.dataset.labelAdd;
      return;
    }

    // Profile tables: remove the row of a removed record
    const row = form.closest('tr');
    if (!inList && row) {
      const tableWrap = row.closest('.table-wrap');
      const tbody = row.parentElement;
      row.remove();

      // Last row removed: show the same empty message as the server-rendered page
      if (tableWrap && tbody && !tbody.querySelector('tr') && tableWrap.dataset.emptyMessage) {
        const emptyMessage = document.createElement('p');
        emptyMessage.className = 'subtle';
        emptyMessage.textContent = tableWrap.dataset.emptyMessage;
        tableWrap.replaceWith(emptyMessage);
      }
    }
  };

  document.addEventListener('submit', async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented) return;

    const action = form.getAttribute('action') || '';
    if (!listActionPattern.test(action)) return;

    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;

    try {
      const response = await fetch(action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' },
        credentials: 'same-origin',
      });

      // Session expired: send the user to login and back to this page afterwards
      if (response.status === 401) {
        window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
        return;
      }
      if (!response.ok) throw new Error('Request failed');

      const data = await response.json();
      updateListForm(form, button, data.in_list);
      showToast(data.message);
    } catch (error) {
      showToast('Something went wrong. Please try again.');
    } finally {
      if (button) button.disabled = false;
    }
  });
});
