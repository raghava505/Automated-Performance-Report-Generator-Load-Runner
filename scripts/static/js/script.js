let sprint_run_mappings = {};
let fieldCounter = 0;
let available_sprints = [];
let already_in_progress = false;

// window.onload = function() {
//     const data = localStorage.getItem('already_in_progress');
//     if (data) {
//         console.log("Restored data: ", data);
//         already_in_progress = data;
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
                <label for="sprint_${fieldCounter}">Sprint Field ${fieldCounter}:</label>
                <select class="form-control" id="sprint_${fieldCounter}" name="sprint_${fieldCounter}" required>
                    <option value="">Select Sprint</option>
                    <!-- Options will be populated via JavaScript -->
                </select>
                <div class="error-message"></div>
            </div>
            <div class="col">
                <label for="run_${fieldCounter}">Run Field ${fieldCounter}:</label>
                <select class="form-control run-element" id="run_${fieldCounter}" name="run_${fieldCounter}" required>
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

function validateForm() {
    if (already_in_progress){
        showNotification("Warning : Report generation already in progress. Please wait till its completion ", "warning");
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
            publishReportToConfluence();
            document.getElementById("logWindow").scrollIntoView({ behavior: "smooth" });

        }
    }
}

function publishReportToConfluence() {
    already_in_progress=true;
    // localStorage.setItem('already_in_progress', true);

    const formData = new FormData(document.getElementById('inputForm'));

    const sprintRuns = [];
    document.querySelectorAll('[id^="sprint_"]').forEach((sprintSelect, index) => {
        const sprint = sprintSelect.value;
        const run = document.querySelector(`#run_${index + 1}`).value;
        if (sprint && run) {
            sprintRuns.push([parseInt(sprint, 10), parseInt(run, 10)]);
        }
    });
    formData.append('sprint_runs', JSON.stringify(sprintRuns));

    console.log(formData)


    showNotification("Info : Report generation has started ", "info");

    // const notificationInterval = setInterval(() => {
    //     showNotification("Info : Report generation in progress ... ", "info");
    // }, 10000); // 10 seconds

    // let timeoutNotificationInterval;

    // const timeoutNotification = setTimeout(() => {
    //     clearInterval(notificationInterval); // Stop the original 10-second interval notifications
    //     showNotification("Info : Still processing ...", "info");

    //     // Set up a new interval to trigger timeout notifications every 10 seconds
    //     timeoutNotificationInterval = setInterval(() => {
    //         showNotification("Info : Almost done... Please be patient.", "info");
    //     }, 10000); // 10 seconds
    // }, 360000); // 6 mins
    
    fetch('/publish_report', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // showNotification(data.message, data.status);
        // clearInterval(timeoutNotificationInterval);
        // clearInterval(notificationInterval);
        // clearTimeout(timeoutNotification); 
        already_in_progress=false;
        // localStorage.setItem('already_in_progress', false);
    })
    .catch(error => {
        // showNotification('Error submitting the form. Please try again.', 'error');
        // clearInterval(timeoutNotificationInterval);
        // clearInterval(notificationInterval);
        // clearTimeout(timeoutNotification); 
        already_in_progress=false;
        // localStorage.setItem('already_in_progress', false);
    });

    startEventSource()
    
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

function startEventSource() {
    let eventSource = new EventSource("/event_stream");
            
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        showNotification(data.message, data.status);
        var newData = document.createElement("div");
        newData.innerHTML = getCurrentTime() + " - " + data.status.toUpperCase() + " : "+ data.message;
        document.getElementById("logWindow").appendChild(newData);
        scrollToBottom("logWindow");

        if (data.status === 'success' || data.status === 'error') {
            already_in_progress = false;
            // Optionally update the progress status in localStorage
            // localStorage.setItem('already_in_progress', false);
            var separator = document.createElement("hr");
            // Append the separator to the log window
            document.getElementById("logWindow").appendChild(separator);
            eventSource.close();
        }
    };
    
    eventSource.onerror = function() {
        showNotification('Error receiving updates from the server.', 'error');
        already_in_progress = false;
        eventSource.close();
        // Optionally update the progress status in localStorage
        // localStorage.setItem('already_in_progress', false);
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