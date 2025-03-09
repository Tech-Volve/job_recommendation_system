document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('loginForm').addEventListener('submit', async function(event) {
        event.preventDefault();

        const password = document.getElementById('password').value;
        const email = document.getElementById('email').value;
        const transcriptInput = document.getElementById('transcript');
        const transcriptFile = transcriptInput.files[0];

        let talentData = {
            password: password,
            email: email,
        };

        // If transcript file is provided, read it
        if (transcriptFile) {
            try {
                // Convert file to base64 for sending to backend
                const base64Content = await readFileAsBase64(transcriptFile);
                talentData.transcript = {
                    content: base64Content,
                    filename: transcriptFile.name,
                    fileType: transcriptFile.type
                };
            } catch (error) {
                console.error('Error reading transcript file:', error);
                alert('Error reading transcript file. Please make sure it\'s a valid PDF document.');
                return;
            }
        }

        try {
            const result = await loginTalent(talentData);
            console.log('Talent Logged in successfully:', result);
            window.location.href = 'dashboard.html';
        } catch (error) {
            console.error('Error logging in talent:', error);
            alert(error.message || 'Error during login');
        }
    });
});

// Function to read file as base64
function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = (event) => {
            // Remove the data URL prefix (e.g., "data:application/pdf;base64,")
            const base64Content = event.target.result.split(',')[1];
            resolve(base64Content);
        };
        
        reader.onerror = (error) => {
            reject(error);
        };

        if (!file.type.includes('pdf')) {
            alert('Please upload a PDF document.');
            reject(new Error('Only PDF files are supported'));
            return;
        }

        reader.readAsDataURL(file);
    });
}

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

        return data;
    } catch (error) {
        console.error('Error logging in talent:', error);
        throw error;
    }
}