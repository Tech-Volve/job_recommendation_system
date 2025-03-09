document.addEventListener("DOMContentLoaded", () => {
    const CLIENT_ID = 'YOUR_CLIENT_ID';
    const API_KEY = 'YOUR_API_KEY';
    const DISCOVERY_DOCS = ["https://www.googleapis.com/discovery/v1/apis/gmail/v1/rest"];
    const SCOPES = 'https://www.googleapis.com/auth/gmail.send';

    const authorizeButton = document.getElementById('authorize_button');
    const signoutButton = document.getElementById('signout_button');
    const sendEmailButton = document.getElementById('sendEmail');

    function handleClientLoad() {
        gapi.load('client:auth2', initClient);
    }

    function initClient() {
        gapi.client.init({
            apiKey: API_KEY,
            clientId: CLIENT_ID,
            discoveryDocs: DISCOVERY_DOCS,
            scope: SCOPES
        }).then(() => {
            gapi.auth2.getAuthInstance().isSignedIn.listen(updateSigninStatus);
            updateSigninStatus(gapi.auth2.getAuthInstance().isSignedIn.get());
            authorizeButton.onclick = handleAuthClick;
            signoutButton.onclick = handleSignoutClick;
        });
    }

    function updateSigninStatus(isSignedIn) {
        if (isSignedIn) {
            authorizeButton.style.display = 'none';
            signoutButton.style.display = 'block';
            sendEmailButton.style.display = 'block';
        } else {
            authorizeButton.style.display = 'block';
            signoutButton.style.display = 'none';
            sendEmailButton.style.display = 'none';
        }
    }

    function handleAuthClick(event) {
        gapi.auth2.getAuthInstance().signIn();
    }

    function handleSignoutClick(event) {
        gapi.auth2.getAuthInstance().signOut();
    }

    function sendEmail() {
        const names = document.getElementById('names').value;
        const email = document.getElementById('email').value;
        const message = document.getElementById('message').value;
        const attachment = document.getElementById('attachment').files;

        const emailContent = `
            From: ${email}
            To: "me"
            Subject: Message from ${names}
            Content-Type: multipart/mixed; boundary="boundary"

            --boundary
            Content-Type: text/plain; charset="UTF-8"

            ${message}

            --boundary
        `;

        const reader = new FileReader();
        reader.onload = function(e) {
            const fileContent = e.target.result.split(',')[1];
            const attachmentContent = `
                Content-Type: ${attachment[0].type}; name="${attachment[0].name}"
                Content-Disposition: attachment; filename="${attachment[0].name}"
                Content-Transfer-Encoding: base64

                ${fileContent}
                --boundary--
            `;

            const raw = btoa(emailContent + attachmentContent).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

            gapi.client.gmail.users.messages.send({
                'userId': 'me',
                'resource': {
                    'raw': raw
                }
            }).then(() => {
                alert('Email sent!');
            });
        };
        reader.readAsDataURL(attachment[0]);
    }

    sendEmailButton.addEventListener('click', sendEmail);
    handleClientLoad();
});