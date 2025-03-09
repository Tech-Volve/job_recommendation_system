// Function to search jobs with pagination
async function searchJobs(query = '', jobType = '', location = '', page = 1) {
    try {
        const params = new URLSearchParams({
            q: query,
            type: jobType,
            location: location,
            page: page,
            per_page: 10
        });

        const response = await fetch(`http://127.0.0.1:5000/search/jobs?${params}`, {
            method: 'GET',
            credentials: 'include'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to search jobs');
        }

        displayJobs(data.jobs);
        displayPagination(data);
        updateSearchStats(data.total_count);

    } catch (error) {
        console.error('Error searching jobs:', error);
        alert(error.message || 'Error searching jobs');
    }
}

// Function to display jobs
function displayJobs(jobs) {
    const jobsContainer = document.getElementById('jobsContainer');
    jobsContainer.innerHTML = '';

    if (jobs.length === 0) {
        jobsContainer.innerHTML = '<p>No jobs found matching your criteria.</p>';
        return;
    }

    jobs.forEach(job => {
        const jobElement = createJobElement(job);
        jobsContainer.appendChild(jobElement);
    });
}

// Function to create job element
function createJobElement(job) {
    const jobDiv = document.createElement('div');
    jobDiv.className = 'job-card';
    
    const sourceTag = job.source === 'created' ? 
        '<span class="source-tag internal">Internal</span>' : 
        '<span class="source-tag external">External</span>';
    
    const timeAgo = formatTimeAgo(new Date(job.created_at));
    
    jobDiv.innerHTML = `
        <div class="job-header">
            <h3>${job.job_title}</h3>
            ${sourceTag}
        </div>
        <p class="company">${job.org_names}</p>
        <p class="location">${job.job_location} ${job.is_remote ? '(Remote)' : ''}</p>
        <p class="type">${job.job_type}</p>
        <div class="description">${job.job_description}</div>
        <div class="job-footer">
            <span class="time-ago">${timeAgo}</span>
            <button onclick="applyForJob(${job.id})">Apply Now</button>
            ${job.job_url ? `<a href="${job.job_url}" target="_blank" class="original-post">View Original Post</a>` : ''}
        </div>
    `;
    
    return jobDiv;
}

// Function to display pagination
function displayPagination(data) {
    const paginationContainer = document.getElementById('pagination');
    if (!paginationContainer) return;

    const { page, total_pages } = data;
    
    let paginationHTML = '';
    
    if (page > 1) {
        paginationHTML += `<button onclick="searchJobs(undefined, undefined, undefined, ${page - 1})">Previous</button>`;
    }
    
    for (let i = Math.max(1, page - 2); i <= Math.min(total_pages, page + 2); i++) {
        paginationHTML += `
            <button class="${i === page ? 'active' : ''}" 
                    onclick="searchJobs(undefined, undefined, undefined, ${i})">${i}</button>
        `;
    }
    
    if (page < total_pages) {
        paginationHTML += `<button onclick="searchJobs(undefined, undefined, undefined, ${page + 1})">Next</button>`;
    }
    
    paginationContainer.innerHTML = paginationHTML;
}

// Helper function to format time ago
function formatTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval > 1) return interval + ' years ago';
    if (interval === 1) return 'a year ago';
    
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) return interval + ' months ago';
    if (interval === 1) return 'a month ago';
    
    interval = Math.floor(seconds / 86400);
    if (interval > 1) return interval + ' days ago';
    if (interval === 1) return 'yesterday';
    
    interval = Math.floor(seconds / 3600);
    if (interval > 1) return interval + ' hours ago';
    if (interval === 1) return 'an hour ago';
    
    interval = Math.floor(seconds / 60);
    if (interval > 1) return interval + ' minutes ago';
    if (interval === 1) return 'a minute ago';
    
    return 'just now';
}

// Function to update search statistics
function updateSearchStats(count) {
    const statsElement = document.getElementById('searchStats');
    if (statsElement) {
        statsElement.textContent = `Found ${count} job${count !== 1 ? 's' : ''}`;
    }
}

// Function to load search history
async function loadSearchHistory() {
    try {
        const response = await fetch('http://127.0.0.1:5000/get/search-history', {
            method: 'GET',
            credentials: 'include'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to load search history');
        }

        displaySearchHistory(data.searches);

    } catch (error) {
        console.error('Error loading search history:', error);
    }
}

// Function to display search history
function displaySearchHistory(searches) {
    const historyContainer = document.getElementById('searchHistory');
    if (!historyContainer) return;

    historyContainer.innerHTML = '';

    searches.forEach(search => {
        const searchElement = document.createElement('div');
        searchElement.className = 'search-history-item';
        searchElement.innerHTML = `
            <span class="query">${search.query}</span>
            <span class="count">${search.result_count} results</span>
            <span class="date">${new Date(search.search_date).toLocaleDateString()}</span>
            <button onclick="repeatSearch('${search.query}')">Search Again</button>
        `;
        historyContainer.appendChild(searchElement);
    });
}

// Function to repeat a previous search
function repeatSearch(query) {
    document.getElementById('searchInput').value = query;
    searchJobs(query);
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Load initial jobs
    searchJobs();
    
    // Load search history
    loadSearchHistory();

    // Set up search form
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = document.getElementById('searchInput').value;
            const jobType = document.getElementById('jobTypeSelect').value;
            const location = document.getElementById('locationInput').value;
            searchJobs(query, jobType, location);
        });
    }
}); 