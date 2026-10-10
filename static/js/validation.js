document.addEventListener('DOMContentLoaded', () => {
	const forms = [
		{ form: document.getElementById('login-form'), errorBox: document.getElementById('login-errors'), mode: 'login' },
		{ form: document.getElementById('register-form'), errorBox: document.getElementById('register-errors'), mode: 'register' },
	];

	forms.forEach(({ form, errorBox, mode }) => {
		if (!form || !errorBox) {
			return;
		}

		form.addEventListener('submit', (event) => {
			errorBox.innerHTML = '';

			const username = form.querySelector('input[name="username"]');
			const password = form.querySelector('input[name="password"]');
			const errors = [];

			if (!username.value.trim()) {
				errors.push('Username is required.');
			}

			if (!password.value.trim()) {
				errors.push('Password is required.');
			}

			if (mode === 'register') {
				const confirmPassword = form.querySelector('input[name="confirm_password"]');
				if (!confirmPassword.value.trim()) {
					errors.push('Please confirm your password.');
				}
				if (password.value && confirmPassword.value && password.value !== confirmPassword.value) {
					errors.push('Passwords do not match.');
				}
				if (password.value.trim() && password.value.trim().length < 6) {
					errors.push('Password must be at least 6 characters.');
				}
			}

			if (errors.length > 0) {
				event.preventDefault();
				errorBox.innerHTML = errors.map((message) => `<p class="login-message error">${message}</p>`).join('');
			}
		});
	});
});
