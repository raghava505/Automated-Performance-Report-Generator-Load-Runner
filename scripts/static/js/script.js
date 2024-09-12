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
        
        // Using a smaller Unicode character for the circle • (U+2022)
        const smallCircleIcon = '\u2022';

        option.textContent = `run${runItem.run}${smallCircleIcon}${runItem.build}${smallCircleIcon}${runItem.stack}${smallCircleIcon}${runItem.load_duration}hrs${smallCircleIcon}${runItem.load_start_time_ist}`;
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
            startPublishLogsEventSource();
            publishReportToConfluence();
            var logWindow = document.getElementById("collapsable_logs_window");
            if (logWindow.classList.contains("collapsed_logs_window")) {
                toggle_logs_window();
            }
            scrollToTop()
            // scrollToBlock('logWindow')
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
        newData.innerHTML = getCurrentTime() + "-" + data.status.toUpperCase() + ":"+ data.message;
        log_window.appendChild(newData);
        scrollToBottom("logWindow");

          // Check message content
        if (data.status.includes("success") || data.status.includes("error")) {
            logs_loadingAnimation.style.display = 'none'; // Hide loading animation
            showNotification(data.message, data.status);
            // var separator = document.createElement("hr");
            // separator.style.color="white";
            // log_window.appendChild(separator);
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
            ReportWindowElement = document.getElementById("ReportWindow");
            ReportWindowElement.style.marginBottom = "1065px"; //no need to change this value anytime
            scrollToBlock("ReportWindow");
            ReportWindowElement.innerHTML = '';
            startReportDataEventSource();
            ViewReport();
            setTimeout(function() {
                ReportWindowElement.style.marginBottom = "1px";
            }, 10000);
        }
    }
    
}

function ViewReport() {
    report_generating_already_in_progress=true
    const report_loadingAnimation = document.getElementById("report_loadingAnimation");
    const report_loadingAnimation_bottom = document.getElementById("report_loadingAnimation_bottom");
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
    report_loadingAnimation.style.display = 'none'; // Hide loading animation
    report_loadingAnimation_bottom.style.display = 'none'; // Hide loading animation
}

function startReportDataEventSource() {
    generateContents();
    // Check if report_eventsource already exists and is active
    if (window.report_eventsource && window.report_eventsource.readyState !== EventSource.CLOSED) {
        console.log("EventSource already open, not reopening.");
        return;
    }

    window.report_eventsource = new EventSource("/report_data_queue_route");
    let generateContents_interval = setInterval(generateContents, 5000);

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
        const scrollToPosition = elementTop - 87;

        // Smoothly scroll to the desired position
        window.scrollTo({
            top: scrollToPosition,
            behavior: 'smooth'
        });
    }
}


function checkVisibility() {
    const reportWindow = document.getElementById('ReportWindow');
    const report_action_fixed_buttons = document.querySelectorAll('.right_fixed_elements');
    const contents = document.getElementById('contents');    

    function updateButtonVisibility() {
        const rect = reportWindow.getBoundingClientRect();
        const isAtTop = rect.top <=90;

        report_action_fixed_buttons.forEach(button => {
            button.style.display = isAtTop ? 'block' : 'none';
        });

        if (isAtTop) {
            contents.style.position = 'sticky';
            contents.style.top = '30px';
            contents.style.zIndex = '1000';

        } else {
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
        button.innerHTML = '<i class="fas fa-arrow-down fa-lg"></i>';
    } else {
        // If scrolling is not active, start it
        scrollInterval = setInterval(function() {
            window.scrollBy(0, 0.5); // Scroll down 1px at a time
            if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight) {
                clearInterval(scrollInterval); // Stop scrolling when reaching the bottom
                isScrolling = false;
                // Change button icon back to normal
                button.innerHTML = '<i class="fas fa-arrow-down fa-lg"></i>';
            }
        }, 1); // Adjust interval for scrolling speed
        isScrolling = true;
        // Change button icon to indicate "stop scrolling"
        button.innerHTML = '<i class="fa-solid fa-pause fa-lg"></i>'; // Use a different icon to indicate stop
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
        
        const baseId = header.textContent.trim().replace(/\s+/g, '-').toLowerCase();
        const id = `${baseId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`; // Combine baseId, current time, and random string
        header.id = id;

        // const id = header.textContent.trim().replace(/\s+/g, '-').toLowerCase();
        // header.id = id;

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


function addNewRow(event) {
    // Prevent the default action of the button
    event.preventDefault();

    // Find the button that was clicked
    const button = event.target;

    const tableId = button.getAttribute('data-table-id');
    const table = document.getElementById(tableId);
    const tableName = table.getAttribute('load_info_header');
    const row = table.insertRow();

    // Get the headers from the first row to use as names for textareas
    const headers = table.rows[0].cells;
    
    // Iterate over the cells in the header row to match the width and set the name attribute
    for (let i = 0; i < headers.length - 1; i++) {
        const cell = row.insertCell();
        const headerCell = headers[i];
        cell.style.width = headerCell.offsetWidth + 'px'; // Match the cell width to the header cell width
        cell.style.backgroundColor = "white";

        // Get the column name from the header
        const columnName = headerCell.innerText.trim();
        cell.innerHTML = `<textarea class="form-control" name="${tableName}___${columnName}" style="width:100%; height:100%; text-align:left;"></textarea>`;
    }

    // Add the Remove button cell
    const removeCell = row.insertCell();
    removeCell.style.backgroundColor = "white";
    removeCell.innerHTML = '<button type="button" class="btn btn-danger btn-sm add_remove_row_btns remove-row"><i class="fa-solid fa-trash"></i></button>';
}


document.addEventListener('DOMContentLoaded', function() {
    // Use event delegation to handle click events on dynamically added rows
    document.body.addEventListener('click', function(event) {
        // Check if the clicked element or its ancestor is a button with the 'remove-row' class
        if (event.target.closest('.remove-row')) {
            removeRow(event);
        }
    });

    document.body.addEventListener('click', function(event) {
        if (event.target.closest('.add_new_row')) {
            addNewRow(event);
        }
    });


    document.body.addEventListener('click', function(event) {
        if (event.target.classList.contains('save_table')) { // Save button
            save_table_to_mongo(event);
        }
    });


});

function removeRow(event) {
    // Prevent the default action of the button
    event.preventDefault();

    // Find the button that was clicked
    const button = event.target;

    // Get the row (tr) element that contains the button
    const row = button.closest('tr');

    // Remove the row from the table
    console.log("remove row triggered : " , row)
    if (row) {
        row.parentNode.removeChild(row);
    }
}

function save_table_to_mongo(event){
    console.log(event)
    event.preventDefault();
    const form = event.target.closest('form');
    console.log("closest form is : " , form)
    const formData = new FormData(form);    
    fetch('/submit_table', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        showNotification(data.message, data.status)
    })
    .catch(error => {
        console.error('Fetch error at /view_report POST request :', error); // Log the error for debugging
        // Show a notification with the error message
        showNotification(`An error occurred: ${error.message}. Please try again later.`, "error");
    });
}

// Clear logWindow content
document.getElementById("clearLogsBtn").addEventListener("click", function() {
    document.getElementById("logWindow").innerHTML = `<div>$ report publishing logs will be displayed here
                                                        </div>
                                                        <br>`;
});

// Copy logWindow content to clipboard
document.getElementById("copyLogsBtn").addEventListener("click", function() {
    const logWindow = document.getElementById("logWindow");
    const range = document.createRange();
    range.selectNodeContents(logWindow);
    const selection = window.getSelection();
    selection.removeAllRanges(); // Clear any previous selections
    selection.addRange(range);
    document.execCommand("copy");
    console.log("copy called")
    try {
        document.execCommand("copy");
        showCopiedTooltip();
    } catch (err) {
        alert("Failed to copy logs. Please try again.");
    }
    
    // Clear the selection after copying
    selection.removeAllRanges();
});

function showCopiedTooltip() {
    const tooltip = document.getElementById("copiedTooltip");
    tooltip.classList.add("show-tooltip");

    // Hide the tooltip after 2 seconds
    setTimeout(function() {
        tooltip.classList.remove("show-tooltip");
    }, 2000);
}
// document.getElementById("toggleButton").addEventListener("click", function() {
//     var logWindow = document.getElementById("collapsable_logs_window");
//     var mainContent = document.getElementById("mainContent");

//     // Toggle the collapsed class
//     console.log(logWindow.classList)

//     logWindow.classList.toggle("collapsed");
//     console.log(logWindow.classList)
    
//     // Adjust main content position
//     if (logWindow.classList.contains("collapsed")) {
//         console.log("collapsed class found .. in logwindoe")
//         // mainContent.classList.remove("contract");
//         logWindow.classList.add("col-md-2");
//         logWindow.classList.remove("col-md-4");
        
//         mainContent.classList.add("col-md-8");
//         mainContent.classList.remove("col-md-6");
//         this.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
//     } else {
//         // mainContent.classList.add("contract");
//         logWindow.classList.remove("col-md-2");
//         logWindow.classList.add("col-md-4");

//         mainContent.classList.remove("col-md-8");
//         mainContent.classList.add("col-md-6");
//         this.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
//     }
// });

function toggle_logs_window(){
    var logWindow = document.getElementById("collapsable_logs_window");
    var mainContent = document.getElementById("mainContent");
    var toggleButton = document.getElementById("toggleButton");

    // Toggle the collapsed class
    console.log(logWindow.classList)

    logWindow.classList.toggle("collapsed_logs_window");
    console.log(logWindow.classList)
    
    // Adjust main content position
    if (logWindow.classList.contains("collapsed_logs_window")) {
        console.log("collapsed_logs_window class found .. in logwindoe")
        // mainContent.classList.remove("contract");
        logWindow.classList.add("col-md-2");
        logWindow.classList.remove("col-md-4");
        
        mainContent.classList.add("col-md-8");
        mainContent.classList.remove("col-md-6");
        toggleButton.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
    } else {
        // mainContent.classList.add("contract");
        logWindow.classList.remove("col-md-2");
        logWindow.classList.add("col-md-4");

        mainContent.classList.remove("col-md-8");
        mainContent.classList.add("col-md-6");
        toggleButton.innerHTML = '<i class="fa-solid fa-xmark"></i>';
    }
}


function CreatePDFfromHTMLWithStyling() {
    var divContents = $("#ReportWindow").clone();
    divContents.find('.collapse').removeClass('collapse');
    var divHTML = divContents.html();

    // Create a temporary window for the PDF generation
    var printWindow = window.open('', '', 'height=400,width=800');

    // Copy the contents of the original window's head (styles and meta tags)
    var headContent = `
    <html>
      <head>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
          @media print {
            img {
              max-width: 100%;
              height: auto;
            }
            /* Remove margins, padding, and other unwanted styles */
            body {
              margin: 0;
              padding: 0;
            }
            .no-print {
              display: none;
            }
          }
        </style>
      </head>
    `;

    printWindow.document.write(headContent);
    printWindow.document.write('<body>');
    printWindow.document.write(divHTML);  
    printWindow.document.write('</body></html>');
    printWindow.document.close();

    // Delay the print operation to allow styles to load fully
    setTimeout(function() {
        // Trigger print dialog
        printWindow.focus(); // Ensure the new window is focused
        printWindow.print();
        printWindow.close();
    }, 1000);  // Adjust delay as necessary
    
}


function convertImagesToBase64(element) {
    const imgElements = element.find('img');

    return Promise.all(imgElements.map((index, img) => {
        return new Promise((resolve, reject) => {
            try {
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                const imgElement = new Image();
                
                imgElement.crossOrigin = 'Anonymous'; // Handle CORS issues
                imgElement.src = img.src;

                imgElement.onload = function() {
                    try {
                        canvas.width = imgElement.width;
                        canvas.height = imgElement.height;
                        context.drawImage(imgElement, 0, 0);
                        const dataURL = canvas.toDataURL('image/png');
                        img.src = dataURL;
                        resolve();
                    } catch (drawError) {
                        console.error("Error drawing image on canvas: ", drawError);
                        resolve(); // Continue even if drawing fails
                    }
                };

                imgElement.onerror = function() {
                    console.error("Failed to load image: " + img.src);
                    resolve(); // Continue even if the image fails to load
                };
            } catch (error) {
                console.error("Unexpected error in image conversion: ", error);
                resolve(); // Continue even in case of unexpected errors
            }
        });
    }).get());
}
function SaveHTMLAsWordDocumentWithImages() {
    try {
        showNotification("Generating word document ...", "info");

        var divContents = $("#ReportWindow").clone();
        divContents.find('.collapse').removeClass('collapse');

        convertImagesToBase64(divContents).then(() => {
            try {
                var divHTML = divContents.html();

                var headContent = `
                <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
                <head>
                    <meta charset='utf-8'>
                    <title>Document</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                        }
                        img {
                            max-width: 100%;
                            height: auto;
                        }
                    </style>
                </head>
                <body>
                    ${divHTML}
                </body>
                </html>
                `;

                var blob = new Blob(['\ufeff', headContent], {
                    type: 'application/msword'
                });

                var link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'document.doc';

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showNotification("successfully downloaded Word document", "success");

            } catch (blobError) {
                console.error("Error creating Word document blob: ", blobError);
                showNotification("Failed to create the Word document. Please try again.", "error");
            }
        }).catch((convertError) => {
            console.error("Error during image conversion: ", convertError);
            showNotification("Failed to convert images. The document might not include all images ", "error");

        });
    } catch (error) {
        console.error("Unexpected error in SaveHTMLAsWordDocumentWithImages: ", error);
        showNotification("An unexpected error occurred while generating word document ", "error");

    }
}




function download_html_doc() {
    showNotification("Generating html document ...", "info");
    try{
        // Clone the ReportWindow element to avoid modifying the original
        var content = document.getElementById("ReportWindow").cloneNode(true);

        // Remove the 'collapse' class from all elements inside the cloned content
        var collapsedElements = content.querySelectorAll('.collapse');
        collapsedElements.forEach(element => {
            element.classList.remove('collapse');
        });

        // Convert images to base64 before generating the HTML file
        convertImagesToBase64_HTML(content).then(() => {
            // Get the contents of the <style> tags and <link> tags in the <head>
            var headContent = document.querySelector('head').innerHTML;

            // Wrap the content with a complete HTML structure
            var fullHTML = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Exported HTML</title>
                ${headContent}  <!-- Include styles and scripts -->
            </head>
            <body>
                ${content.innerHTML}  <!-- The content of the ReportWindow div -->
                
                <!-- Include inline JavaScript if needed -->
                <script>
                // You can add your custom JavaScript functions here if needed.
                </script>
            </body>
            </html>`;

            // Create a new Blob with the full HTML content, specifying the MIME type as HTML
            var blob = new Blob([fullHTML], { type: "text/html" });

            // Create a download link dynamically
            var downloadLink = document.createElement("a");
            downloadLink.download = "export.html";

            // Create a URL for the Blob and set it as the href attribute
            downloadLink.href = window.URL.createObjectURL(blob);

            // Programmatically click the download link to trigger the download
            downloadLink.click();
            showNotification("successfully downloaded html document", "success");

        });
        
    }
    catch (error) {
        console.error("Unexpected error in SaveHTMLAsWordDocumentWithImages: ", error);
        showNotification("An unexpected error occurred while generating word document ", "error");

    }
}

// Function to convert all images in an element to base64
function convertImagesToBase64_HTML(element) {
    const imgElements = element.querySelectorAll('img');

    return Promise.all(Array.from(imgElements).map((img) => {
        return new Promise((resolve, reject) => {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            const imgElement = new Image();
            
            imgElement.crossOrigin = 'Anonymous'; // Handle CORS issues
            imgElement.src = img.src;

            imgElement.onload = function() {
                canvas.width = imgElement.width;
                canvas.height = imgElement.height;
                context.drawImage(imgElement, 0, 0);
                const dataURL = canvas.toDataURL('image/png');
                img.src = dataURL;
                resolve();
            };

            imgElement.onerror = function() {
                console.error("Failed to load image: " + img.src);
                resolve(); // Continue even if the image fails to load
            };
        });
    }));
}


function toggleCollapseExpand() {
    var toggleButton = document.getElementById("toggleBetween_expand_collapse");
    var toggleIcon = document.getElementById("toggleIcon");
    var collapsibles = document.querySelectorAll("#ReportWindow .collapse");

    if (toggleButton.getAttribute("data-expanded") === "true") {
        // Collapse all
        collapsibles.forEach(function(collapsible) {
            $(collapsible).collapse('hide'); // Use jQuery for smooth collapse
        });
        toggleButton.innerHTML = '<i id="toggleIcon" class="fas fa-expand"></i> Expand All';
        toggleButton.setAttribute("data-expanded", "false");
    } else {
        // Expand all
        collapsibles.forEach(function(collapsible) {
            $(collapsible).collapse('show'); // Use jQuery for smooth expand
        });
        toggleButton.innerHTML = '<i id="toggleIcon" class="fas fa-compress"></i> Collapse All';
        toggleButton.setAttribute("data-expanded", "true");
    }
}

