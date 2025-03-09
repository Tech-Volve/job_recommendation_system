document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('loginForm').addEventListener('submit', async function(event) {
        event.preventDefault(); // Prevent the default form submission

        const password = document.getElementById('password').value;
        const email = document.getElementById('email').value;

        const talentData = {
            password: password,
            email: email,
        };

        try {
            const result = await loginTalent(talentData);
            console.log('Talent Logged in successfully:', result);
            window.location.href = 'dashboard.html';
        } catch (error) {
            console.error('Error logging in talent:', error);
        }
    });
});

async function loginTalent(talentData) {
    const url = 'http://127.0.0.1:5000/login/talent';

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(talentData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Login failed');
        }

        console.log('Talent logged in successfully:', data);
        return data;
    } catch (error) {
        console.error('Error logging in talent:', error);
        throw error;
    }
}