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
});
