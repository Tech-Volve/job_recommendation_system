document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const name = document.getElementById('orgname').value;
    const password = document.getElementById('orgpassword').value;
    const email = document.getElementById('orgemail').value;
    const phone = document.getElementById('orgphone').value;

    const talentData = {
        name: name,
        password: password,
        email: email,
        phone: phone,
    };

    try {
        const result = await registerTalent(talentData);
        console.log('Organization registered successfully:', result);
        window.location.href = './login_organization.html';
    } catch (error) {
        console.error('Error registering organization:', error);
    }
});

async function registerTalent(talentData) {
    const url = 'http://127.0.0.1:5000/register/organization';

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(talentData),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Registration failed');
        }

        console.log('Organization registered successfully:', data);
        return data;
    } catch (error) {
        console.error('Error registering organization:', error);
        throw error;
    }
}