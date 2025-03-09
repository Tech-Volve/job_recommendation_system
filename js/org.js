document.addEventListener("DOMContentLoaded", () => {
    const elements = {
        locationBtn: document.querySelector(".loc_button"),
        jobTypeBtn: document.querySelector(".loc_button2"),
        placesDropdown: document.querySelector(".places"),
        typesDropdown: document.querySelector(".types"),
        remoteCheckbox: document.querySelector("#category"),
        jobForm: document.querySelector("#jobForm"),
        titleInput: document.querySelector("#title"),
        descriptionContainer: document.querySelector("#description") // Updated to descriptionContainer
    };

    const state = {
        place: "",
        jobType: "",
        isRemote: false, // Initialize as false
        title: "",
        description: ""
    };

    const ColorClass = Quill.import('attributors/class/color');
    const SizeStyle = Quill.import('attributors/style/size');
    Quill.register(ColorClass, true);
    Quill.register(SizeStyle, true);
    const quill = new Quill('#description', { theme: 'snow' });

    setupEventListeners();

    function setupEventListeners() {
        elements.locationBtn?.addEventListener("click", toggleDropdown(elements.placesDropdown));
        elements.jobTypeBtn?.addEventListener("click", toggleDropdown(elements.typesDropdown));
        elements.placesDropdown?.addEventListener("click", handlePlaceSelection);
        elements.typesDropdown?.addEventListener("click", handleTypeSelection);
        elements.remoteCheckbox?.addEventListener("change", handleRemoteToggle);
        elements.jobForm?.addEventListener("submit", handleFormSubmit);

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

    async function handleFormSubmit(e) {
        e.preventDefault();
        state.title = elements.titleInput.value.trim();
        state.description = quill.root.innerHTML.trim(); // Get HTML content from Quill

        try {
            const result = await postJobs(state);
            console.log('Jobs posted successfully:', result);
            window.location.href = 'org-dashboard.html';
        } catch (error) {
            console.error('Error posting jobs:', error);
        }
    }

    async function postJobs(state) {
        const url = 'http://127.0.0.1:5000/post/job';
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(state),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Vacancy posting failed');
            }

            console.log('Vacancy posted successfully', data);
            return data;
        } catch (error) {
            console.error('Error in posting vacancy:', error);
            throw error;
        }
    }
});