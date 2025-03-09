document.addEventListener("DOMContentLoaded", () => {
    // State management
    const state = {
        query: 'web',
        place: '',
        jobType: '',
        isRemote: false,
        currentPage: 1,
        jobsPerPage: 100,
        isLoading: false,
        retryCount: 0,
        maxRetries: 3,
        retryDelay: 2000 // 2 seconds
    };

    // DOM Elements
    const elements = {
        searchInput: document.querySelector(".query_search"),
        locationBtn: document.querySelector(".loc_button"),
        jobTypeBtn: document.querySelector(".loc_button2"),
        placesDropdown: document.querySelector(".places"),
        typesDropdown: document.querySelector(".types"),
        remoteCheckbox: document.querySelector("#category"),
        searchButton: document.querySelector(".Submit_query"),
        jobContainer: document.querySelector(".jobs"),
        paginationContainer: document.querySelector(".pagination")
    };

    // Event Listeners setup
    setupEventListeners();

    function setupEventListeners() {
        elements.locationBtn?.addEventListener("click", toggleDropdown(elements.placesDropdown));
        elements.jobTypeBtn?.addEventListener("click", toggleDropdown(elements.typesDropdown));
        elements.searchButton?.addEventListener("click", handleSearch);
        elements.placesDropdown?.addEventListener("click", handlePlaceSelection);
        elements.typesDropdown?.addEventListener("click", handleTypeSelection);
        elements.remoteCheckbox?.addEventListener("change", handleRemoteToggle);

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filters')) {
                elements.placesDropdown.style.display = "none";
                elements.typesDropdown.style.display = "none";
            }
        });
    }

    // Toggle dropdown function
    function toggleDropdown(element) {
        return () => {
            if (!element) return;
            const isHidden = element.style.display === "none" || element.style.display === "";
            element.style.display = isHidden ? "block" : "none";
            
            // Close other dropdowns
            const dropdowns = [elements.placesDropdown, elements.typesDropdown];
            dropdowns.forEach(dropdown => {
                if (dropdown && dropdown !== element) {
                    dropdown.style.display = "none";
                }
            });
        };
    }

    // Event Handlers
    function handlePlaceSelection(e) {
        if (e.target.tagName === "DIV") return;
        state.place = e.target.textContent.trim();
        elements.locationBtn.textContent = state.place || "Location";
        elements.placesDropdown.style.display = "none";
    }

    function handleTypeSelection(e) {
        if (e.target.tagName === "DIV") return;
        state.jobType = e.target.textContent.trim();
        elements.jobTypeBtn.textContent = state.jobType || "Job Type";
        elements.typesDropdown.style.display = "none";
    }

    function handleRemoteToggle(e) {
        state.isRemote = e.target.checked;
    }

    function handleSearch() {
        if (state.isLoading) return;
        state.query = elements.searchInput?.value || 'web';
        state.currentPage = 1;
        state.retryCount = 0;
        fetchJobs();
    }

    // API Functions
    async function fetchJobs() {
        if (state.isLoading) return;
        
        state.isLoading = true;
        showLoadingState();
    
        try {
            const requestData = {
                search_term: state.query,
                location: state.place || 'mumbai',
                results_wanted: 60,
                site_name: [
                    'indeed',
                    'linkedin',
                    'zip_recruiter',
                    'glassdoor'
                ],
                distance: 50,
                job_type: state.jobType.toLowerCase().replace(' ', '') || 'fulltime',
                is_remote: state.isRemote,
                linkedin_fetch_description: false,
                hours_old: 300
            };
            
            // Fetch jobs from the external API
            const externalResponse = await fetch('https://jobs-search-api.p.rapidapi.com/getjobs', {
                method: 'POST',
                headers: {
                    'x-rapidapi-key': '8ec0ed2528mshdbc246edfb4c888p1d4a42jsn6450870c3cc0',
                    'x-rapidapi-host': 'jobs-search-api.p.rapidapi.com',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
    
            if (externalResponse.status === 429) {
                // Handle rate limiting
                await handleRateLimit();
                return;
            }
    
            if (!externalResponse.ok) {
                throw new Error(`HTTP error! status: ${externalResponse.status}`);
            }
    
            const externalData = await externalResponse.json();
            const jobs = externalData.jobs || [];
            
            // Store the jobs in the database
            await storeJobsInDatabase(jobs);
            
            // Display jobs as before
            displayJobs(jobs);
        } catch (error) {
            console.error('Error fetching jobs:', error);
            handleError(error);
        } finally {
            state.isLoading = false;
            hideLoadingState();
        }
    }

    async function handleRateLimit() {
        if (state.retryCount >= state.maxRetries) {
            showError('Rate limit exceeded. Please try again later.');
            return;
        }

        state.retryCount++;
        const waitTime = state.retryDelay * state.retryCount;
        
        showMessage(`Rate limit reached. Retrying in ${waitTime/1000} seconds...`);
        
        await new Promise(resolve => setTimeout(resolve, waitTime));
        await fetchJobs();
    }

    function handleError(error) {
        if (error.message.includes('429')) {
            showError('Rate limit exceeded. Please try again in a few minutes.');
        } else {
            showError('Failed to fetch jobs. Please try again later.');
        }
    }

    // UI Functions
    function showMessage(message) {
        if (!elements.jobContainer) return;
        elements.jobContainer.innerHTML = `
            <div class="text-center text-blue-600 p-4">
                <p>${sanitizeHTML(message)}</p>
            </div>
        `;
    }

    function displayJobs(jobs) {
        if (!elements.jobContainer) return;
        
        elements.jobContainer.innerHTML = '';
        
        if (jobs.length === 0) {
            showNoResults();
            return;
        }

        const startIndex = (state.currentPage - 1) * state.jobsPerPage;
        const endIndex = startIndex + state.jobsPerPage;
        const currentJobs = jobs.slice(startIndex, endIndex);

        const jobsContainer = document.createElement('div');
        jobsContainer.className = 'space-y-4';
        
        function formatJobDescription(description) {
            if (!description) return '';
        
            // Remove escape characters and convert markdown-style formatting
            let formatted = description
                .replace(/\\\*/g, '*')  // Unescape asterisks
                .replace(/\\\-/g, '-')  // Unescape hyphens
                .replace(/\\n/g, '<br>')  // Convert escaped newlines
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Convert bold text
                .replace(/\*(.*?)\*/g, '<em>$1</em>');  // Convert italic text
        
            // Split into sections
            const sections = formatted.split(/(?=\*\*[\w\s]+:\*\*)/);
        
            // Format each section
            return sections.map(section => {
                // Format lists
                section = section.replace(/\\-\s/g, '<br>• ');  // Convert escaped hyphens to bullets
                
                // Format benefits and other list items
                section = section.replace(/\*\s/g, '<br>• ');
        
                // Add proper spacing around headers
                section = section.replace(/(\*\*[\w\s]+:\*\*)/, '\n$1\n');
        
                return section;
            }).join('\n');
        }

        currentJobs.forEach(job => {
            const jobCard = document.createElement('div');
            jobCard.className = 'job-card bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200';
            
            jobCard.innerHTML = `
                <h3 class="text-xl font-bold text-gray-800 mb-2">${sanitizeHTML(job.title)}</h3>
                <div class="flex items-center mb-2">
                    <span class="text-gray-600 font-medium">${sanitizeHTML(job.company)}</span>
                    ${job.is_remote ? '<span class="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">Remote</span>' : ''}
                </div>
                <div class="text-gray-600 mb-3">
                    <i class="fas fa-map-marker-alt mr-2"></i>${sanitizeHTML(job.location)}
                </div>
                <h4 class="text-lg font-semibold text-gray-800 mb-2">Description</h4>
                <div class="description-container hidden overflow-y-auto max-h-32">
                    <p class="text-gray-700 mb-4 description">${(formatJobDescription(job.description || ''))}</p>
                </div>
                <div class="flex justify-between items-center">
                    <button onclick="window.open('${sanitizeHTML(job.job_url)}', '_blank')" 
                            class="bg-blue-600 hover text-white px-4 py-2 rounded transition-colors duration-200">
                        View Job
                    </button>
                    <button class="application">
                        Apply Job
                    </button>
                </div>
            `;
            
            jobsContainer.appendChild(jobCard);
            console.log(job);
        });
        elements.jobContainer.appendChild(jobsContainer);

        // Add event listeners for the info icons
        document.querySelectorAll('.info-icon').forEach(icon => {
            icon.addEventListener('click', () => {
                const descriptionContainer = icon.closest('.job-card').querySelector('.description-container');
                descriptionContainer.classList.toggle('hidden');
            });
        });

        if (jobs.length > state.jobsPerPage) {
            addPagination(jobs.length);
        }
    }

    function addPagination(totalJobs) {
        if (!elements.paginationContainer) return;

        elements.paginationContainer.innerHTML = '';

        const totalPages = Math.ceil(totalJobs / state.jobsPerPage);

        for (let i = 1; i <= totalPages; i++) {
            const pageButton = document.createElement('button');
            pageButton.textContent = i;
            pageButton.className = 'pagination-button';
            if (i === state.currentPage) {
                pageButton.classList.add('active');
            }
            pageButton.addEventListener('click', () => {
                state.currentPage = i;
                fetchJobs();
            });
            elements.paginationContainer.appendChild(pageButton);
        }
    }

    // Utility Functions
    function sanitizeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        }).format(date);
    }

    function showLoadingState() {
        if (!elements.jobContainer) return;
        elements.jobContainer.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
            </div>
        `;
    }

    function hideLoadingState() {
        // Loading state is automatically removed when new content is displayed
    }

    function showError(message) {
        if (!elements.jobContainer) return;
        elements.jobContainer.innerHTML = `
            <div class="text-center text-red-600 p-4">
                <p>${sanitizeHTML(message)}</p>
            </div>
        `;
    }

    function showNoResults() {
        if (!elements.jobContainer) return;
        elements.jobContainer.innerHTML = `
            <div class="text-center text-gray-600 p-4">
                <p>No jobs found matching your criteria. Try adjusting your search parameters.</p>
        `;
    }

    function toggleDescription(icon) {
        const descriptionContainer = icon.closest('.job-card').querySelector('.description-container');
        descriptionContainer.classList.toggle('hidden');
    }

    // Initialize with default search
    fetchJobs();
});


// Add this function to your existing JavaScript
async function storeJobsInDatabase(jobs) {
    try {
        console.log('Attempting to store jobs:', jobs.length);
        
        // Add source information to each job
        const jobsWithSource = jobs.map(job => ({
            ...job,
            source: job.source || 'external_api'  // Default source if not provided
        }));
        
        const response = await fetch('/api/store-jobs/', {  // Update with your actual API URL
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()  // Function to get Django CSRF token
            },
            body: JSON.stringify({ jobs: jobsWithSource })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Failed to store jobs: ${response.status}`);
        }
        
        const result = await response.json();
        console.log(`Successfully stored ${result.jobs?.length || 0} jobs in database`);
    } catch (error) {
        console.error('Error storing jobs in database:', error);
    }
}

// Function to get CSRF token from cookies
function getCsrfToken() {
    const name = 'csrftoken';
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

