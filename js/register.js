document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const password = document.getElementById('password').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const resumeInput = document.getElementById('resume');
    const resumeFile = resumeInput.files[0];

    if (!resumeFile) {
        alert('Please upload a resume file.');
        return;
    }

    const reader = new FileReader();
    reader.onload = async function(e) {
        const resumeContent = e.target.result;

        // Encode the resume content to Base64
        const base64Resume = arrayBufferToBase64(resumeContent);

        const talentData = {
            name: name,
            password: password,
            email: email,
            phone: phone,
            resume: base64Resume
        };

        try {
            const result = await registerTalent(talentData);
            console.log('Talent registered successfully:', result);
            window.location.href = 'login.html';
        } catch (error) {
            console.error('Error registering talent:', error);
        }
    };

    reader.readAsArrayBuffer(resumeFile);
});

function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

async function registerTalent(talentData) {
    const url = 'http://127.0.0.1:5000/register/talent';

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
            throw new Error(data.error || 'Registration failed');
        }

        console.log('Talent registered successfully', data);
        return data;
    } catch (error) {
        console.error('Error registering talent:', error);
        throw error;
    }
}