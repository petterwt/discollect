document.addEventListener('DOMContentLoaded', () => {
	// Header search: copy query into the main stock search and show results
	const headerSearchForm = document.querySelector('.search-form');
	const headerSearchInput = headerSearchForm ? headerSearchForm.querySelector('input[type="search"]') : null;
	const featuredSort = document.getElementById('featured-sort');
	const featuredGrid = document.querySelector('#featured .product-grid');
	const storageKey = 'featured-sort-mode';

	const sortFeaturedRecords = (mode) => {
		if (!featuredGrid) {
			return;
		}

		const cards = Array.from(featuredGrid.querySelectorAll('.record-card'));
		const sortedCards = [...cards];

		sortedCards.sort((left, right) => {
			if (mode === 'price') {
				return Number(left.dataset.price || 0) - Number(right.dataset.price || 0);
			}

			if (mode === 'year') {
				return Number(right.dataset.releaseYear || 0) - Number(left.dataset.releaseYear || 0);
			}

			if (mode === 'title') {
				return (left.dataset.recordName || '').localeCompare(right.dataset.recordName || '');
			}

			return 0;
		});

		sortedCards.forEach((card) => featuredGrid.appendChild(card));
	};

	if (featuredSort && featuredGrid) {
		const savedMode = localStorage.getItem(storageKey) || 'featured';
		featuredSort.value = savedMode;
		sortFeaturedRecords(savedMode);

		featuredSort.addEventListener('change', () => {
			localStorage.setItem(storageKey, featuredSort.value);
			sortFeaturedRecords(featuredSort.value);
		});
	}

	const form = document.getElementById('stock-search-form');
	const input = document.getElementById('stock-search-input');
	const statusBox = document.getElementById('stock-search-status');
	const resultsBox = document.getElementById('stock-search-results');

	// Simple HTML escaper for text content inserted via templates
	const escapeHtml = (unsafe) => {
		if (unsafe === null || unsafe === undefined) return '';
		return String(unsafe)
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#039;');
	};

	const renderRecordGrid = (records, resultsBox, emptyMessage) => {
		if (!resultsBox) {
			return;
		}

		if (!records.length) {
			resultsBox.innerHTML = '';
			return emptyMessage;
		}

		resultsBox.innerHTML = records.map((record) => `
			<article class="product-card record-card search-result-card">
				<div class="media-frame">
					<img src="${escapeHtml(record.cover_url || record.image_url) || '/static/img/coverart/placeholder.png'}" alt="${escapeHtml(record.record_name || record.title)} cover art">
				</div>
				<h3><strong>${escapeHtml(record.record_name || record.title)}</strong></h3>
				<p class="meta">${escapeHtml(record.artist_name || record.artist)}</p>
				<p class="meta-year">Released: ${escapeHtml(record.release_year_only || record.release_year || 'N/A')}</p>
				<p class="subtle">${escapeHtml(record.description || 'Matched from the database.')}</p>
			</article>
		`).join('');

		return '';
	};

	const renderStockSearch = (results) => {
		if (!resultsBox || !statusBox) {
			return;
		}

		if (!results.length) {
			resultsBox.innerHTML = '';
			statusBox.textContent = 'No matches found.';
			return;
		}

		resultsBox.innerHTML = results.map((record) => `
			<article class="product-card record-card search-result-card">
				<div class="media-frame">
					<img src="${escapeHtml(record.cover_url) || '/static/img/coverart/placeholder.png'}" alt="${escapeHtml(record.record_name)} cover art">
				</div>
				<h3><strong>${escapeHtml(record.record_name)}</strong></h3>
				<p class="meta">${escapeHtml(record.artist_name)}</p>
				<p class="meta-year">Released: ${escapeHtml(record.release_year_only || 'N/A')}</p>
				<p class="subtle">${escapeHtml(record.description || 'In stock in the database.')}</p>
				<div class="record-actions record-actions-search">
					<form method="post" action="/wishlist/add/${encodeURIComponent(record.record_id)}">
						<input type="hidden" name="redirect_to" value="${escapeHtml(window.location.pathname)}">
						<button class="button wishlist-button button-small" type="submit">+ Wishlist</button>
					</form>
					<form method="post" action="/collection/add/${encodeURIComponent(record.record_id)}">
						<input type="hidden" name="redirect_to" value="${escapeHtml(window.location.pathname)}">
						<button class="button secondary button-small" type="submit">+ Collection</button>
					</form>
				</div>
			</article>
		`).join('');

		statusBox.textContent = `Showing ${results.length} result${results.length === 1 ? '' : 's'}.`;
	}

	const searchStock = async (searchForm, searchInput, searchStatus, searchResultsBox, searchUrl, renderer) => {
		const query = searchInput.value.trim();
		if (!query) {
			searchResultsBox.innerHTML = '';
			return;
		}

		searchStatus.textContent = 'Searching...';
		searchResultsBox.innerHTML = '';

		try {
			const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
			const data = await response.json();

			if (!response.ok) {
				throw new Error(data.error || 'Search request failed.');
			}

			renderer(data);
		} catch (error) {
			searchStatus.textContent = error.message;
		}
	};

	if (form && input && statusBox && resultsBox) {
		form.addEventListener('submit', (event) => {
			event.preventDefault();
			searchStock(form, input, statusBox, resultsBox, form.action, (data) => renderStockSearch(data.results || []));
		});

		input.addEventListener('search', () => {
			if (!input.value.trim()) {
				resultsBox.innerHTML = '';
			}
		});
	}

	// If a header search is used, forward it to the stock search and scroll to results
	if (headerSearchForm && headerSearchInput && form && input && resultsBox && statusBox) {
		headerSearchForm.addEventListener('submit', (event) => {
			event.preventDefault();
			const q = headerSearchInput.value.trim();
			if (!q) return;
			// populate the stock search input and run the same search
			input.value = q;
			// perform the search and when it completes, scroll to the first album card
			searchStock(form, input, statusBox, resultsBox, form.action, (data) => renderStockSearch(data.results || []))
				.then(() => {
					const firstCard = resultsBox.querySelector('.record-card');
					if (firstCard) {
						firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
					} else {
						resultsBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
					}
				})
				.catch(() => {
					// On error, fallback to showing the results section
					resultsBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
				});
		});
	}

	// Admin DB catalog search (shows full DB matches and allows stock edits)
	const adminDbForm = document.getElementById('admin-db-search-form');
	const adminDbInput = document.getElementById('admin-db-search-input');
	const adminDbStatus = document.getElementById('admin-db-search-status');
	const adminDbResults = document.getElementById('admin-db-search-results');

	const renderAdminSearchResults = (records) => {
		if (!adminDbResults || !adminDbStatus) return;
		if (!records.length) {
			adminDbResults.innerHTML = '';
			adminDbStatus.textContent = 'No matches found.';
			return;
		}

		// Render as a compact table list
		let rows = records.map((r) => `
			<tr data-record-id="${escapeHtml(r.record_id)}">
				<td>${escapeHtml(r.record_name || '')}</td>
				<td>${escapeHtml(r.artist_name || '')}</td>
				<td>${escapeHtml(r.genre_name || '')}</td>
				<td class="stock-qty">${escapeHtml(r.stock_qty || 0)}</td>
				<td>
					<div class="stock-controls">
						<button class="btn-decrement" data-id="${escapeHtml(r.record_id)}" title="Decrement">−</button>
						<button class="btn-increment" data-id="${escapeHtml(r.record_id)}" title="Increment">+</button>
						<input class="stock-input" data-id="${escapeHtml(r.record_id)}" type="number" value="${escapeHtml(r.stock_qty || 0)}" min="0">
						<button class="btn-set" data-id="${escapeHtml(r.record_id)}">Set</button>
					</div>
				</td>
			</tr>
		`).join('');

		adminDbResults.innerHTML = `
			<div class="table-wrap">
				<table class="compact-table">
					<thead>
						<tr><th>Record</th><th>Artist</th><th>Genre</th><th>Stock</th><th>Action</th></tr>
					</thead>
					<tbody>
						${rows}
					</tbody>
				</table>
			</div>
		`;

		adminDbStatus.textContent = `Showing ${records.length} result${records.length === 1 ? '' : 's'}.`;
	}

	if (adminDbForm && adminDbInput && adminDbStatus && adminDbResults) {
		let lastAdminQuery = '';
		adminDbForm.addEventListener('submit', (e) => {
			e.preventDefault();
			const q = adminDbInput.value.trim();
			if (!q) return;
			lastAdminQuery = q;
			adminDbStatus.textContent = 'Searching...';
			fetch(`/api/search?q=${encodeURIComponent(q)}`)
				.then((res) => res.json())
				.then((data) => renderAdminSearchResults(data.results || []))
				.catch((err) => { adminDbStatus.textContent = 'Search failed.'; });
		});

		// Handle clicks on increment/decrement/set via event delegation and AJAX
		adminDbResults.addEventListener('click', async (ev) => {
			const target = ev.target;
			if (target.matches('.btn-decrement') || target.matches('.btn-increment')) {
				ev.preventDefault();
				const id = target.dataset.id;
				const delta = target.matches('.btn-decrement') ? -1 : 1;
				const row = adminDbResults.querySelector(`tr[data-record-id="${id}"]`);
				if (!row) return;
				const stockCell = row.querySelector('.stock-qty');
				const current = parseInt(stockCell.textContent || '0', 10) || 0;
				const newQty = Math.max(0, current + delta);
				try {
					const form = new FormData();
					form.append('delta', String(delta));
					form.append('redirect_to', window.location.pathname + window.location.search);
					const res = await fetch(`/admin/change-stock/${id}`, { method: 'POST', body: form, credentials: 'same-origin' });
					if (!res.ok) throw new Error('Request failed');
					stockCell.textContent = String(newQty);
					const input = row.querySelector('.stock-input'); if (input) input.value = String(newQty);
				} catch (err) {
					adminDbStatus.textContent = 'Update failed.';
				}
				return;
			}

			if (target.matches('.btn-set')) {
				ev.preventDefault();
				const id = target.dataset.id;
				const row = adminDbResults.querySelector(`tr[data-record-id="${id}"]`);
				if (!row) return;
				const input = row.querySelector('.stock-input');
				let qty = parseInt(input.value || '0', 10) || 0;
				qty = Math.max(0, qty);
				try {
					const form = new FormData();
					form.append('stock_qty', String(qty));
					form.append('redirect_to', window.location.pathname + window.location.search);
					const res = await fetch(`/admin/set-stock/${id}`, { method: 'POST', body: form, credentials: 'same-origin' });
					if (!res.ok) throw new Error('Request failed');
					const stockCell = row.querySelector('.stock-qty');
					stockCell.textContent = String(qty);
					input.value = String(qty);
				} catch (err) {
					adminDbStatus.textContent = 'Set failed.';
				}
				return;
			}
		});
	}

	// Category search on the index page
	const categoryForm = document.getElementById('category-search-form');
	const categorySelect = document.getElementById('category-search-select');
	const categoryButton = document.getElementById('category-search-button');

	if (categoryForm && categorySelect && categoryButton && resultsBox && statusBox) {
		categoryForm.addEventListener('submit', (e) => { e.preventDefault(); categoryButton.click(); });
		categoryButton.addEventListener('click', (e) => {
			e.preventDefault();
			const gid = categorySelect.value;
			if (!gid) return;
			statusBox.textContent = 'Searching category...';
			resultsBox.innerHTML = '';
			fetch(`/api/search_by_genre?genre_id=${encodeURIComponent(gid)}`)
				.then((res) => res.json())
				.then((data) => {
					renderStockSearch(data.results || []);
					// scroll to first
					const firstCard = resultsBox.querySelector('.record-card');
					if (firstCard) firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
				})
				.catch(() => { statusBox.textContent = 'Category search failed.'; });
		});
	}

	// Profile: Spotify search to add to collection or wishlist
	const profileSpotifyForm    = document.getElementById('profile-spotify-form');
	const profileSpotifyInput   = document.getElementById('profile-spotify-input');
	const profileSpotifyStatus  = document.getElementById('profile-spotify-status');
	const profileSpotifyResults = document.getElementById('profile-spotify-results');

	if (profileSpotifyForm && profileSpotifyInput) {
		profileSpotifyForm.addEventListener('submit', (e) => {
			e.preventDefault();
			const q = profileSpotifyInput.value.trim();
			if (!q) return;
			profileSpotifyStatus.textContent = 'Searching Spotify...';
			profileSpotifyResults.innerHTML = '';
			fetch(`/api/spotify-search?q=${encodeURIComponent(q)}`)
				.then((res) => res.json())
				.then((data) => {
					const items = data.results || [];
					if (!items.length) {
						profileSpotifyStatus.textContent = 'No results found.';
						return;
					}
					profileSpotifyStatus.textContent = `${items.length} result${items.length === 1 ? '' : 's'} from Spotify.`;
					profileSpotifyResults.innerHTML = items.map((a) => `
						<article class="product-card record-card">
							<div class="media-frame">
								<img src="${escapeHtml(a.cover_url) || '/static/img/coverart/placeholder.png'}" alt="${escapeHtml(a.title)} cover">
							</div>
							<h3><strong>${escapeHtml(a.title)}</strong></h3>
							<p class="meta">${escapeHtml(a.artist)}</p>
							<p class="meta-year">${escapeHtml(a.release_date)}</p>
							<div class="record-actions record-actions-search" style="gap:.4rem;flex-direction:column;">
								<form method="post" action="/user/add-from-spotify">
									<input type="hidden" name="title"        value="${escapeHtml(a.title)}">
									<input type="hidden" name="artist"       value="${escapeHtml(a.artist)}">
									<input type="hidden" name="cover_url"    value="${escapeHtml(a.cover_url)}">
									<input type="hidden" name="release_date" value="${escapeHtml(a.release_date)}">
									<input type="hidden" name="list_type"    value="collection">
									<button class="button secondary button-small" type="submit">+ Collection</button>
								</form>
								<form method="post" action="/user/add-from-spotify">
									<input type="hidden" name="title"        value="${escapeHtml(a.title)}">
									<input type="hidden" name="artist"       value="${escapeHtml(a.artist)}">
									<input type="hidden" name="cover_url"    value="${escapeHtml(a.cover_url)}">
									<input type="hidden" name="release_date" value="${escapeHtml(a.release_date)}">
									<input type="hidden" name="list_type"    value="wishlist">
									<button class="button wishlist-button button-small" type="submit">+ Wishlist</button>
								</form>
							</div>
						</article>
					`).join('');
				})
				.catch(() => { profileSpotifyStatus.textContent = 'Search failed.'; });
		});
	}

	// Admin: Spotify search — add album to catalog with stock qty
	const adminSpotifyForm    = document.getElementById('admin-spotify-form');
	const adminSpotifyInput   = document.getElementById('admin-spotify-input');
	const adminSpotifyStatus  = document.getElementById('admin-spotify-status');
	const adminSpotifyResults = document.getElementById('admin-spotify-results');

	if (adminSpotifyForm && adminSpotifyInput) {
		adminSpotifyForm.addEventListener('submit', (e) => {
			e.preventDefault();
			const q = adminSpotifyInput.value.trim();
			if (!q) return;
			adminSpotifyStatus.textContent = 'Searching Spotify...';
			adminSpotifyResults.innerHTML = '';
			fetch(`/api/spotify-search?q=${encodeURIComponent(q)}`)
				.then((res) => res.json())
				.then((data) => {
					const items = data.results || [];
					if (!items.length) {
						adminSpotifyStatus.textContent = 'No results found.';
						return;
					}
					adminSpotifyStatus.textContent = `${items.length} result${items.length === 1 ? '' : 's'} from Spotify.`;
					adminSpotifyResults.innerHTML = items.map((a) => `
						<article class="product-card record-card">
							<div class="media-frame">
								<img src="${escapeHtml(a.cover_url) || '/static/img/coverart/placeholder.png'}" alt="${escapeHtml(a.title)} cover">
							</div>
							<h3><strong>${escapeHtml(a.title)}</strong></h3>
							<p class="meta">${escapeHtml(a.artist)}</p>
							<p class="meta-year">${escapeHtml(a.release_date)}</p>
							<form method="post" action="/admin/add-from-spotify" style="margin-top:.75rem;display:flex;gap:.4rem;align-items:center;flex-wrap:wrap;">
								<input type="hidden" name="title"        value="${escapeHtml(a.title)}">
								<input type="hidden" name="artist"       value="${escapeHtml(a.artist)}">
								<input type="hidden" name="cover_url"    value="${escapeHtml(a.cover_url)}">
								<input type="hidden" name="release_date" value="${escapeHtml(a.release_date)}">
								<input type="number" name="stock_qty" value="1" min="0" style="width:4.5rem;padding:.25rem;border:1px solid var(--border);border-radius:6px;text-align:center;background:var(--surface);color:var(--text);">
								<button class="button primary button-small" type="submit">Add to catalog</button>
							</form>
						</article>
					`).join('');
				})
				.catch(() => { adminSpotifyStatus.textContent = 'Search failed.'; });
		});
	}

});