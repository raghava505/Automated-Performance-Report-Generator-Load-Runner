let sprint_run_mappings = {};
let fieldCounter = 0;
let available_sprints = [];
let publishing_already_in_progress = false;
let report_generating_already_in_progress = false;

// window.onload = function() {
//     const data = localStorage.getItem('publishing_already_in_progress');
//     if (data) {
//         console.log("Restored data: ", data);
//         publishing_already_in_progress = data;
//     }
// };


// Fetch databases and collections from the server
document.addEventListener('DOMContentLoaded', () => {
    fetch('/get_databases')
        .then(response => response.json())
        .then(data => populateLoadTypeDropdown(data.databases))
        .catch(error => console.error('Error fetching databases:', error));
});
addSprintRunFields();
addSprintRunFields();

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
window.addEventListener('load', scrollToTop);

function populateLoadTypeDropdown(databases) {
    const loadtypeSelect = document.getElementById('loadtype');
    databases.forEach(db => {
        const option = document.createElement('option');
        option.value = db;
        option.textContent = db;
        loadtypeSelect.appendChild(option);
    });
    loadtypeSelect.addEventListener('change', (event) => {
        const selectedDB = event.target.value;
        fetch(`/get_collections?database=${selectedDB}`)
            .then(response => response.json())
            .then(data => populateLoadNameDropdown(data.collections))
            .catch(error => console.error('Error fetching collections:', error));
    });
}

function populateLoadNameDropdown(collections) {
    const loadnameSelect = document.getElementById('loadname');
    loadnameSelect.innerHTML = '<option value="">Select Load Name</option>'; // Reset options
    collections.forEach(coll => {
        const option = document.createElement('option');
        option.value = coll;
        option.textContent = coll;
        loadnameSelect.appendChild(option);
    });

    loadnameSelect.addEventListener('change', (event) => {
        const selectedDB = document.getElementById('loadtype').value;
        const selectedColl = event.target.value;
        if (selectedDB && selectedColl) {
            fetch(`/get_ids?database=${selectedDB}&collection=${selectedColl}`)
                .then(response => response.json())
                .then(data => {sprint_run_mappings = data.dictionary;available_sprints=data.sprints;populateSprintDropdowns(null)})
                .catch(error => console.error('Error fetching _id values:', error));
        }
    });
    
}
function populateSprintDropdowns(sprint_element_id) {
    console.log("sprint_run_mappings : " , sprint_run_mappings)
    console.log("available_sprints : " , available_sprints)

    console.log("request for populate sprint dropdpwn" , sprint_element_id )
    // Example for populating dropdowns; replace with actual data fetching
    const rundropdowns = document.querySelectorAll('[id^="run_"]');

    let sprintdropdowns;
    if (sprint_element_id === null){
        sprintdropdowns = document.querySelectorAll('[id^="sprint_"]');
        console.log(sprintdropdowns);
        rundropdowns.forEach(runSelect => {
            runSelect.innerHTML = '<option value="">Select Run</option>'; 
        });
    }
    else{
        sprintdropdowns = document.querySelectorAll(`#${sprint_element_id}`);
        console.log("after clicking on add ")
        console.log(sprintdropdowns)
    }
    sprintdropdowns.forEach(sprintSelect => {
        // Populate each sprint dropdown
        sprintSelect.innerHTML = '<option value="">Select Sprint</option>'; 
        available_sprints.forEach(sprint => {
            const option = document.createElement('option');
            option.value = sprint;
            option.textContent = sprint;
            sprintSelect.appendChild(option);
        });
        const curr_sprint_field_id = sprintSelect.id;
        const closest_run_field = document.querySelector(`#${curr_sprint_field_id}`).closest('.form-group').querySelector('[id^="run_"]');
        console.log("closest run field is ",closest_run_field, "for sprint : ",curr_sprint_field_id )
        // Add change event listener for each sprint dropdown
        sprintSelect.addEventListener('change', (event) => {
            const selectedSprint = event.target.value;
            if (selectedSprint && closest_run_field) {
                populateRunDropdowns(sprint_run_mappings[selectedSprint], closest_run_field);
            }
        });
    });
    
}

function populateRunDropdowns(runs, run_field) {
    run_field.innerHTML = '<option value="">Select Run</option>'; 
    runs.forEach(runItem => {
        const option = document.createElement('option');
        option.value = runItem.run;
        option.textContent = "run:"+runItem.run+"; "+"build:"+runItem.build+"; "+"stack:"+runItem.stack+"; "+"duration:"+runItem.load_duration+"hrs";
        run_field.appendChild(option);
    });
}


function addSprintRunFields() {
    fieldCounter++;
    const container = document.getElementById('fieldsContainer');
    let newFields = `
        <div class="form-group row inside_fields" id="sprintRunGroup_${fieldCounter}">
            <div class="col">
                <label for="sprint_${fieldCounter}">Sprint Field ${fieldCounter} :</label>
                <select class="form-control req-for-view-report" id="sprint_${fieldCounter}" name="sprint_${fieldCounter}" required>
                    <option value="">Select Sprint</option>
                    <!-- Options will be populated via JavaScript -->
                </select>
                <div class="error-message"></div>
            </div>
            <div class="col">
                <label for="run_${fieldCounter}">Run Field ${fieldCounter} :</label>
                <select class="form-control run-element req-for-view-report" id="run_${fieldCounter}" name="run_${fieldCounter}" required>
                    <option value="">Select Run</option>
                    <!-- Options will be populated via JavaScript -->
                </select>
                <div class="error-message"></div>
            </div>

    `;
    if (fieldCounter!=1){
        newFields = newFields + `<div>
                                    <span><button type="button" class="remove_btn" onclick="removeFields(${fieldCounter})"><i class="fa-solid fa-xmark"></i></button></span>
                                </div>
                                `
    }
    else{
        newFields = newFields + `<div class="hidden-content">
                                    <span><button type="button" class="remove_btn" >x</button></span>
                                </div>
                                `
    }
    newFields = newFields + `</div>`
    
    container.insertAdjacentHTML('beforeend', newFields);
    populateSprintDropdowns("sprint_"+fieldCounter);
}

function removeFields(id) {
    const fieldGroup = document.querySelector(`#sprint_${id}`).closest('.form-group');
    fieldGroup.remove();
}


function validateURL(url) {
    const urlPattern = new RegExp('^(https?:\\/\\/)?' + 
        '((([a-zA-Z\\d]([a-zA-Z\\d-]*[a-zA-Z\\d])*)\\.?)+[a-zA-Z]{2,}|' + 
        '((\\d{1,3}\\.){3}\\d{1,3}))' + 
        '(\\:\\d+)?(\\/[-a-zA-Z\\d%_.~+]*)*' + 
        '(\\?[;&a-zA-Z\\d%_.~+=-]*)?' + 
        '(\\#[-a-zA-Z\\d_]*)?$', 'i');
    return !!urlPattern.test(url);
}

function validateEmail(email) {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
}

function validatePublishForm() {
    if (publishing_already_in_progress){
        showNotification("Warning : Report publishing already in progress. Please wait till its completion ", "warning");
    }
    else
    {
        let isValid = true;
        const fields = document.querySelectorAll('#inputForm .form-control');

        fields.forEach(field => {
            const errorMessageDiv = field.nextElementSibling;
            if (!field.value.trim()) {
                errorMessageDiv.textContent = 'This field is required.';
                isValid = false;
            } else {
                errorMessageDiv.textContent = '';
            }

            if (field.id === 'url' && !validateURL(field.value)) {
                errorMessageDiv.textContent = 'Please enter a valid URL.';
                isValid = false;
            }

            if (field.id === 'email_address' && !validateEmail(field.value)) {
                errorMessageDiv.textContent = 'Please enter a valid email address.';
                isValid = false;
            }
        });

        if (isValid) {
            startPublishLogsEventSource()
            publishReportToConfluence();
            scrollToBlock('logWindow')
        }
    }
}

function publishReportToConfluence() {
    publishing_already_in_progress=true;
    const formData = new FormData(document.getElementById('inputForm'));
    const sprintRuns = [];

    document.querySelectorAll('[id^="sprint_"]').forEach((sprintSelect, index) => {
        const sprint_id = String(sprintSelect.id);
        main_id = sprint_id.split("_")[1];
        const sprint = sprintSelect.value;
        run_elem = document.querySelector(`#run_${main_id}`);
        const run = run_elem.value;
        if (sprint && run) {
            sprintRuns.push([parseInt(sprint, 10), parseInt(run, 10)]);
        }
    });
    formData.append('sprint_runs', JSON.stringify(sprintRuns));

    console.log(formData)

    showNotification(" Report publishing in progress... ", "info");
    
    fetch('/publish_report', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            publishing_already_in_progress=false;
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        publishing_already_in_progress=false;
        showNotification(data.message, data.status)
    })
    .catch(error => {
        publishing_already_in_progress=false;
        console.error('Fetch error at /view_report POST request :', error); // Log the error for debugging
        // Show a notification with the error message
        showNotification(`An error occurred: ${error.message}. Please try again later.`, "error");
    });

}

function showNotification(message, type) {
    const statusMessage = document.getElementById('statusMessage');
    const statusText = document.getElementById('statusText');

    statusMessage.className = 'notification ' + type;
    statusText.textContent = message;
    statusMessage.style.display = 'block';
}

function clearNotification() {
    document.getElementById('statusMessage').style.display = 'none';
}

function startPublishLogsEventSource() {
    if (window.publish_eventSource && window.publish_eventSource.readyState !== EventSource.CLOSED) {
        console.log("publish_eventSource already open, not reopening.");
        return;
    }
    window.publish_eventSource = new EventSource("/publish_logs_stream");
    const logs_loadingAnimation = document.getElementById("logs_loadingAnimation");
    logs_loadingAnimation.style.display = 'block';

    log_window = document.getElementById("logWindow");
    publish_eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        // showNotification(data.message, data.status);
        var newData = document.createElement("div");
        newData.innerHTML = getCurrentTime() + " - " + data.status.toUpperCase() + " : "+ data.message;
        log_window.appendChild(newData);
        scrollToBottom("logWindow");

          // Check message content
        if (data.status.includes("success") || data.status.includes("error")) {
            logs_loadingAnimation.style.display = 'none'; // Hide loading animation
            showNotification(data.message, data.status);
            var separator = document.createElement("hr");
            log_window.appendChild(separator);
            publishing_already_in_progress = false;
            
        } else {
            logs_loadingAnimation.style.display = 'block'; // Show loading animation
        }
    };
    
    publish_eventSource.onerror = function(event) {
        showNotification('Error receiving updates from the publish_logs_stream eventsource server ' +  event.message, 'error');
        console.error("publish_logs_stream error : ", event);
        publish_eventSource.close();  // Handle connection issues
        publishing_already_in_progress = false;
    };
};

function scrollToBottom(id) {
    var logWindow = document.getElementById(id);
    logWindow.scrollTop = logWindow.scrollHeight;
}

function getCurrentTime() {
    var currentDate = new Date();
    var hours = currentDate.getHours();
    var minutes = currentDate.getMinutes();
    var seconds = currentDate.getSeconds();

    // Add leading zeros if necessary
    hours = hours < 10 ? '0' + hours : hours;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    seconds = seconds < 10 ? '0' + seconds : seconds;

    return hours + ":" + minutes + ":" + seconds;
}

function validateViewReport() {
    if (report_generating_already_in_progress){
        showNotification("Warning : Report generation already in progress. Please wait till its completion ", "warning");
    }
    else{
        let isValid = true;
        const fields = document.querySelectorAll('#inputForm .req-for-view-report');
        fields.forEach(field => {
            const errorMessageDiv = field.nextElementSibling;
            if (!field.value.trim()) {
                errorMessageDiv.textContent = 'This field is required.';
                isValid = false;
            } else {
                errorMessageDiv.textContent = '';
            }
        });
        if (isValid) {
            ReportWindowElement = document.getElementById("ReportWindow")
            ReportWindowElement.style.marginBottom = "1065px"; //no need to change this value anytime
            scrollToBlock("ReportWindow")
            ReportWindowElement.innerHTML = '';
            startReportDataEventSource();
            ViewReport();
            setTimeout(function() {
                ReportWindowElement.style.marginBottom = "1px";
            }, 1000);
        }
    }
    
}

function ViewReport() {
    report_generating_already_in_progress=true
    const formData = new FormData(document.getElementById('inputForm'));
    const sprintRuns = [];
    document.querySelectorAll('[id^="sprint_"]').forEach((sprintSelect, index) => {
        const sprint_id = String(sprintSelect.id);
        main_id = sprint_id.split("_")[1];
        const sprint = sprintSelect.value;
        run_elem = document.querySelector(`#run_${main_id}`);
        const run = run_elem.value;
        if (sprint && run) {
            sprintRuns.push([parseInt(sprint, 10), parseInt(run, 10)]);
        }
    });
    formData.append('sprint_runs', JSON.stringify(sprintRuns));
    
    showNotification("Report Generation in progress... ", "info");

    fetch('/view_report', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            report_generating_already_in_progress=false
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        report_generating_already_in_progress=false
        showNotification(data.message, data.status)
    })
    .catch(error => {
        report_generating_already_in_progress=false
        console.error('Fetch error at /view_report POST request :', error); // Log the error for debugging
        // Show a notification with the error message
        showNotification(`An error occurred: ${error.message}. Please try again later.`, "error");
    });
}

function startReportDataEventSource() {
    // Check if report_eventsource already exists and is active
    if (window.report_eventsource && window.report_eventsource.readyState !== EventSource.CLOSED) {
        console.log("EventSource already open, not reopening.");
        return;
    }

    window.report_eventsource = new EventSource("/report_data_queue_route");
    const generateContents_interval = setInterval(generateContents, 5000);

    const report_loadingAnimation = document.getElementById("report_loadingAnimation");
    const report_loadingAnimation_bottom = document.getElementById("report_loadingAnimation_bottom");
    report_loadingAnimation.style.display = 'block'; // Show loading animation
    report_loadingAnimation_bottom.style.display = 'block'; // Show loading animation

    report_window = document.getElementById("ReportWindow");
    report_eventsource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        var newData = document.createElement("div");
        newData.innerHTML = data.message;
        report_window.appendChild(newData);

         // Check message content
        if (data.status.includes("success") || data.status.includes("error")) {
            report_loadingAnimation.style.display = 'none'; // Hide loading animation
            report_loadingAnimation_bottom.style.display = 'none'; // Hide loading animation
            showNotification(data.message, data.status);
            generateContents();
            clearInterval(generateContents_interval);
            report_generating_already_in_progress=false
            
        } else {
            report_loadingAnimation.style.display = 'block'; // Show loading animation
            report_loadingAnimation_bottom.style.display = 'block'; // Show loading animation
            // generateContents();
        }
    };
    
    report_eventsource.onerror = function(event) {
        console.error("report_data_stream error:", event);
        showNotification("Error  receiving updates from the report_data_stream eventsource server : " + event.message, "error");
        report_eventsource.close();  // Handle connection issues
        clearInterval(generateContents_interval);
        report_generating_already_in_progress=false
    };
}

// Scroll to the top of the page when the button is clicked
function scrollToBlock(id) {
    const element = document.getElementById(id);
    if (element) {
        // Calculate the top position of the element relative to the viewport
        const rect = element.getBoundingClientRect();
        // Calculate the top position of the element relative to the document
        const elementTop = window.pageYOffset + rect.top;
        // Calculate the desired scroll position with a 100px gap at the top
        const scrollToPosition = elementTop - 60;

        // Smoothly scroll to the desired position
        window.scrollTo({
            top: scrollToPosition,
            behavior: 'smooth'
        });
    }
}


function checkVisibility() {
    const reportWindow = document.getElementById('ReportWindow');
    const down_button = document.getElementById('scroll_through_report_slowly');
    const up_button = document.getElementById('scroll_up');
    const contents = document.getElementById('contents');

    function updateButtonVisibility() {
        const rect = reportWindow.getBoundingClientRect();
        // const isAtTop = rect.top >= 0 && rect.top <= window.innerHeight;
        const isAtTop = rect.top <=63;

        if (isAtTop) {
            down_button.style.display = 'block'; // Show button
            up_button.style.display = 'block'; // Show button
            contents.style.position = 'sticky';
            contents.style.top = '30px';
            contents.style.left = '5px';
            contents.style.zIndex = '1000';

        } else {
            down_button.style.display = 'none'; // Hide button
            up_button.style.display = 'none'; // Hide button
            contents.style.position = '';
            contents.style.top = '';
            contents.style.left = '';
            contents.style.zIndex = '';
        }
    }

    // Initial check
    updateButtonVisibility();

    // Check visibility on scroll and resize
    window.addEventListener('scroll', updateButtonVisibility);
    window.addEventListener('resize', updateButtonVisibility);
}

// Initialize the visibility check
checkVisibility();


// Variable to hold the interval ID
let scrollInterval = null;
let isScrolling = false;

// Function to start or stop scrolling
function toggleScroll() {
    const button = document.getElementById('scroll_through_report_slowly');

    if (isScrolling) {
        // If scrolling is active, stop it
        clearInterval(scrollInterval);
        isScrolling = false;
        // Change button icon back to normal
        button.innerHTML = '<i class="fas fa-arrow-down"></i>';
    } else {
        // If scrolling is not active, start it
        scrollInterval = setInterval(function() {
            window.scrollBy(0, 1); // Scroll down 1px at a time
            if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight) {
                clearInterval(scrollInterval); // Stop scrolling when reaching the bottom
                isScrolling = false;
                // Change button icon back to normal
                button.innerHTML = '<i class="fas fa-arrow-down"></i>';
            }
        }, 1); // Adjust interval for scrolling speed
        isScrolling = true;
        // Change button icon to indicate "stop scrolling"
        button.innerHTML = '<i class="fa-solid fa-pause"></i>'; // Use a different icon to indicate stop
    }
}
function generateContents() {
    console.log("request for contents list fillup");
    const reportWindow = document.getElementById('ReportWindow');
    const contents = document.getElementById('contents');
    contents.innerHTML = `
        <h5 id="contents_heading" class="text-center btn disabled"><i class="fa-solid fa-list"></i> Contents </h5>
        <div class="input-group mb-3">
        <div class="input-group-prepend"><span class="input-group-text"><i class="fas fa-search"></i></span></div>
            <input type="text" id="searchBox" class="form-control" placeholder="Search...">
        </div>
    `;

    const ul = document.createElement('ul');
    ul.style.listStyleType = 'none';
    ul.style.padding = '0';
    ul.style.margin = '0';

    const headers = reportWindow.querySelectorAll('h2, h3'); // Find all h2 and h3 tags

    let lastH2Li = null; // To keep track of the last h2 element for nesting h3

    headers.forEach(header => {
        const id = header.textContent.trim().replace(/\s+/g, '-').toLowerCase();
        header.id = id;

        const li = document.createElement('li');
        li.style.width = '100%'; // Ensure the li occupies the full width
        li.style.display = 'block'; // Make li a block element

        const h2Container = document.createElement('div'); // Create a container div for the icon and link
        h2Container.style.display = 'flex'; // Use flexbox to align items horizontally
        h2Container.style.alignItems = 'center'; // Center align icon and link vertically
        h2Container.style.width = '100%'; // Make sure the container occupies the full width
        h2Container.style.cursor = 'pointer'; // Make the container appear clickable

        const toggleIcon = document.createElement('i');
        toggleIcon.className = 'fa fa-plus-square';
        toggleIcon.style.marginRight = '5px';

        const link = document.createElement('a');
        link.href = `#${id}`;
        link.textContent = header.textContent;
        link.style.display = 'block'; // Make the link block-level to occupy the full width
        link.style.width = '100%'; // Ensure the link occupies the full width
        link.style.padding = '5px'; // Adjust padding to apply hover effect across the full block
        link.style.textDecoration = 'none';
        link.style.color = '#007bff';
        link.style.transition = 'background-color 0.3s';
        link.style.borderBottom = '1px solid #ddd';

        // Add hover effect for the entire block
        link.addEventListener('mouseover', () => {
            link.style.backgroundColor = '#f1f1f1';
        });
        link.addEventListener('mouseout', () => {
            link.style.backgroundColor = '';
        });

        if (header.tagName.toLowerCase() === 'h2') {
            h2Container.appendChild(toggleIcon);
            h2Container.appendChild(link);
            li.appendChild(h2Container); // Append the container div to li
            ul.appendChild(li);

            const nestedUl = document.createElement('ul');
            nestedUl.style.listStyleType = 'none';
            nestedUl.style.paddingLeft = '20px';
            nestedUl.style.display = 'none'; // Hidden by default

            li.appendChild(nestedUl);
            lastH2Li = nestedUl;

            // Add toggle functionality for collapsing/expanding
            toggleIcon.addEventListener('click', (e) => {
                e.preventDefault(); // Prevent default behavior
                const isExpanded = nestedUl.style.display === 'block';

                if (isExpanded) {
                    nestedUl.style.display = 'none';
                    toggleIcon.className = 'fa fa-plus-square';
                } else {
                    nestedUl.style.display = 'block';
                    toggleIcon.className = 'fa fa-minus-square';
                }
            });

            // Add click event to link for navigation
            link.addEventListener('click', (e) => {
                // Let the anchor default behavior happen to scroll to the element
            });
        } else if (header.tagName.toLowerCase() === 'h3' && lastH2Li) {
            lastH2Li.appendChild(li); // Nest h3 under the last h2
            li.appendChild(link);
        }
    });

    contents.appendChild(ul);

    // Filter function for the search box
    const searchBox = document.getElementById('searchBox');
    searchBox.addEventListener('input', () => {
        const filter = searchBox.value.toLowerCase();
        const links = ul.getElementsByTagName('a');

        Array.from(links).forEach(link => {
            const text = link.textContent.toLowerCase();
            if (text.includes(filter)) {
                link.style.display = 'block'; // Show matching link
            } else {
                link.style.display = 'none'; // Hide non-matching link
            }
        });
    });
}



// Call the function to generate contents links

$(document).ready(function() {
    // Delegate the event handling to the document or a parent container
    $(document).on('click', '.sortable', function() {
        var $this = $(this);
        var order = $this.data('order');

        // Get the parent table of the clicked header
        var $table = $this.closest('table');
        var $rows = $table.find('tbody tr').toArray();

        // Sort rows based on the column and order
        $rows.sort(function(a, b) {
            // Extract text from the corresponding column in both rows
            var aText = $(a).find('td').eq($this.index()).text().trim();
            var bText = $(b).find('td').eq($this.index()).text().trim();

            // Ensure aText and bText are strings, else set them to empty strings
            aText = typeof aText === 'string' ? aText : '';
            bText = typeof bText === 'string' ? bText : '';

            // Handle special values like NaN
            if (aText === "NaN") aText = Number.NEGATIVE_INFINITY;
            if (bText === "NaN") bText = Number.NEGATIVE_INFINITY;

            // Remove special characters like arrows and extract numeric values
            var aNumeric = parseFloat(aText.replace(/[^0-9.-]+/g, ''));
            var bNumeric = parseFloat(bText.replace(/[^0-9.-]+/g, ''));

            // Compare numeric values if both are valid numbers
            if (!isNaN(aNumeric) && !isNaN(bNumeric)) {
                return (order === 'desc' ? (bNumeric - aNumeric) : (aNumeric - bNumeric));
            }

            // Fallback to string comparison if the values are not numeric
            return (order === 'desc' ? (aText > bText) : (aText < bText)) ? 1 : -1;
        });

        // Reverse the order for the next click
        $this.data('order', order === 'desc' ? 'asc' : 'desc');

        // Remove existing sort classes from all headers in the same table
        $this.closest('tr').find('.sortable').removeClass('asc desc');

        // Add the sort class to the clicked header
        $this.addClass(order === 'desc' ? 'asc' : 'desc');

        // Append sorted rows to the table body
        $.each($rows, function(index, row) {
            $table.children('tbody').append(row);
        });
    });
});