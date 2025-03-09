async function getJobTitles() {
    try {
        const response = await fetch('http://127.0.0.1:5000/organization/applications');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const jsondata = await response.json(); // Await the JSON parsing
        console.log(jsondata);
        const titles = jsondata.map((job) => job.job_title);
        return titles;
    } catch (error) {
        console.error('Error fetching job titles:', error);
        return [];
    }
}

async function displayJobTitles() {
    const titles = await getJobTitles(); // Await the asynchronous function
    const titleList = document.querySelector('.aside');
    titles.forEach((title) => {
        const li = document.createElement('li');
        li.textContent = title;
        titleList.appendChild(li);
    });
}

// Call the function to display job titles
displayJobTitles();