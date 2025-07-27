function validateLoginForm() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    if (username.length < 4) {
        alert('Username must be at least 4 characters long.');
        return false;
    }
    if (password.length < 6) {
        alert('Password must be at least 6 characters long.');
        return false;
    }
    return true;
}

function validateRegisterForm() {
    return validateLoginForm();
}