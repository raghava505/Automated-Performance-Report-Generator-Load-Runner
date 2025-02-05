document.addEventListener("DOMContentLoaded", () => {
    const stackField = document.getElementById("stack_json_file");
    const loadnameField = document.getElementById("loadname");
    const simulator_grid = document.getElementById('simulator-grid');

    let active_count_id =document.getElementById('active_count_id')

    let simulators = [];
    let online_sims = 0;
    let offline_sims = 0;

    // Ensure both fields exist in the DOM
    if (!stackField || !loadnameField) {
        console.error("One or both fields (stack, loadname) are missing in the DOM.");
        return;
    }

    // Helper function to check if both fields are filled
    const areBothFieldsFilled = () => {
        return stackField.value.trim() !== "" && loadnameField.value.trim() !== "";
    };

    // Function to handle the POST request
    const getSimulators = () => {
        stack_json_file_name=stackField.value+"_nodes.json",
        loadname=loadnameField.value,

        fetch(`/get_simulators_list?stack_json_file_name=${stack_json_file_name}&loadname=${loadname}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(`Error: ${errorData.message}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                showNotification(data.message, data.status);
                console.log("Response from server:", data);
                simulators = data.result_data;
                input_files = data.input_files;
                fill_inputfiles_dropdown(input_files);
                populateSimulatorGrid(simulators);
            })
            .catch(error => {
                // console.error("Error:", error);
                showNotification(`${error.message}.`, "error");
            });
        
    };
    // Event listeners for both fields
    const handleInputChange = () => {
        simulators=[]
        online_sims=0
        offline_sims=0
        if (areBothFieldsFilled()) {
            simulator_grid.innerHTML = ""
            active_count_id.innerHTML = ""
            getSimulators();
        }
    };

    stackField.addEventListener("change", handleInputChange);
    loadnameField.addEventListener("change", handleInputChange);

    function populateSimulatorGrid(simulators) {
        console.log(simulators)
        if (!simulators || simulators.length === 0) {
            console.log('No simulators found. Exiting function.');
            return;
        }
        showNotification(`Fetched ${simulators.length} simulators`, 'info');
    
        let gridHTML = '<div class="row">';
        
        simulators.forEach(sim => {            
            gridHTML += `
                <div class="card mb-2 mr-2 simulator_card offline">
                    <div class="loading-bar"></div>
                    <button class="position-absolute btn btn-sm btn-primary refresh-btn"><i class="fa-solid fa-arrows-rotate fa-xs"></i></button>
                    <div class="text-center">
                        <span class="offline_status"><i class="fa-solid fa-solid fa-ban mx-1 pt-1" style="color: red;"></i><span class="status-text">Offline</span></span>
                        <span class="online_status"><i class="fa-solid fa-circle  mx-1 pt-1" style="color: green;"></i><span class="status-text">Online</span></span>
                    </div>
    
                    <div class="pt-2 text-center">
                        <h6 class="card-title"><i class="fa-solid fa-desktop fa-xs"></i> ${sim}</h6>
                        <div class="table-container"></div>
                    </div>
                </div>
            `;
        });

        gridHTML += '</div>'; // Close the row div
        simulator_grid.innerHTML = gridHTML; // Update the HTML once all fetch requests are resolved
        document.getElementById("main-refresh").click();
    
        // Select all simulator cards
        const simulatorCards = document.querySelectorAll('.simulator_card');
    
        // Add scroll event listener to each card
        simulatorCards.forEach(card => {
            card.addEventListener('scroll', (event) => {
                // Get the current scroll position of the card that was scrolled
                const scrollTop = event.target.scrollTop;
                
                // Sync all other cards' scroll positions with the card being scrolled
                simulatorCards.forEach(otherCard => {
                    if (otherCard !== event.target) {
                        otherCard.scrollTop = scrollTop;
                    }
                });
            });
        });
    }
    

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
    
    function fill_inputfiles_dropdown(inputfiles_list){
        console.log(inputfiles_list);
        const loadtypeSelect = document.getElementById('inputfile');
        loadtypeSelect.innerHTML = '<option value="">Select Input File</option>'; // Reset options

        inputfiles_list.forEach(db => {
            const option = document.createElement('option');
            option.value = db;
            option.textContent = db;
            loadtypeSelect.appendChild(option);
        });
    
    }
    
    // Show loading animation
    function toggleLoading(card, show) {
        const loadingBar = card.querySelector(".loading-bar");
        loadingBar.classList.toggle("active", show);
    }

    async function refreshSimulator(card, table_container,formData) {
        console.log("formData:",formData)
        const sim = card.querySelector(".card-title").textContent;
        toggleLoading(card, true);
        showNotification(`Fetching health of ${sim}...`, 'info');
        
        table_container.innerHTML = "";
        
        try {
            let response;
            if (formData) {
                response = await fetch(`/call_check_sim_health?sim_hostname=${sim}`, {
                    method: 'POST',
                    body: formData
                });
            } else {
                response = await fetch(`/call_check_sim_health?sim_hostname=${sim}`);
            }
            const data = await response.json();

            if (data.main_params) {
                // const table_container = document.querySelector('.table-container'); // Ensure this is your target container
                const container = document.createElement('div');
                container.className = 'container';

                // Initialize row for cards
                let row = document.createElement('div');
                row.className = 'row';

                if (data.load_remaining_dur_in_sec) {
                    const remainingDurInSec = Number(data.load_remaining_dur_in_sec);
                    if (remainingDurInSec === 0) {
                        console.log("The remaining time is 0");
                    } 
                    else {
                        const formatSecondsToHHMMSS = (seconds) => {
                            const hours = String(Math.floor(seconds / 3600)).padStart(2, '0');
                            const minutes = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
                            const remainingSeconds = String(seconds % 60).padStart(2, '0');
                            return `${hours}:${minutes}:${remainingSeconds}`;
                        };
                    
                        const formattedDuration = formatSecondsToHHMMSS(remainingDurInSec);
                        duration_remaining_html = `
                            <p class="my-2 p-1 rounded load_progress_widget"><i class="fa-solid fa-circle-exclamation fa-lg"></i> load is running currently!<br> <span>${formattedDuration}</span> remaining... </p>
                        `;
                        table_container.innerHTML += duration_remaining_html;
                    }
                }
                
                let count = 0;
                data.main_params.forEach(([key, value], index) => {
                    const card = document.createElement('div');
                    card.className = 'simulator_sub_cards col rounded py-2 text-center bg-light position-relative';
                
                    value_font_factor = Math.floor(String(value).length / 12);
                    console.log(value_font_factor,key,value)
                    card.innerHTML = `
                        <h${value_font_factor+5} class="text-primary mb-1">${value}</h${value_font_factor+5}>
                        <small class="text-muted" style="font-size: 8px;">${key}</small>
                    `;
                
                    row.appendChild(card);
                    count++;
                
                    if (count === 2 || index === data.main_params.length - 1) {
                        container.appendChild(row);
                        if (count === 2) {
                            row = document.createElement('div');
                            row.className = 'row';
                            count = 0;
                        }
                    }
                });
                

                // Append the container to thetable container
                table_container.appendChild(container);
            } else {
                console.log('No data found in the main_params');
            }

            if (data.table_data_result) {
                showNotification(data.message,data.status);
                Object.entries(data.table_data_result).forEach(([section, sectionData]) => {
                    console.log(section.split('_'))
                    const table = document.createElement('table');
                    table.classList.add('dataframe', 'table', 'table-bordered', 'table-hover', 'table-sm', 'text-center', 'custom-table', 'simulator_card_table');
                    
                    const tableHead = `
                        <thead>
                            <tr>
                                <th class="sortable" data-column="" data-order="desc">${section.split('_')[0]}</th>
                                <th class="sortable" data-column="" data-order="desc">${section.split('_')[1]}</th>
                            </tr>
                        </thead>
                    `;

                    const tableBody = Object.entries(sectionData)
                        .map(([key, value]) => `
                            <tr>
                                <td>${key}</td>
                                <td>${value}</td>
                            </tr>
                        `)
                        .join('');

                    table.innerHTML = tableHead + `<tbody>${tableBody}</tbody>`;
                    
                    // Append the new table to the table container
                    table_container.appendChild(table);
                    
                });
                if (card.classList.contains("offline")){
                    online_sims +=1
                }
                card.classList.add("online");
                card.classList.remove("offline");
            }
            else{
                const small = document.createElement('small');
                if (!formData){
                    if (card.classList.contains("online")){
                        offline_sims -=1
                    }
                    card.classList.remove("online");
                    card.classList.add("offline");
                    showNotification(`Error fetching health for ${sim}. Check the card content for detailed error.`,data.status)
                }
                else{
                    showNotification(`Error occured while updating params for ${sim}. Check the card content for detailed error.`,data.status)
                }
                
                small.innerHTML = data.message;
                table_container.appendChild(small);

            }
            console.log("offline sim : ",offline_sims)
            console.log("online sim : ",online_sims)
            // active_count_id.innerHTML = `(<span style="font-weight: 700;font-size: medium; color:rgb(0, 162, 0);">${online_sims}</span>/<span style="font-weight: 900;font-size: small;">${simulators.length}</span>) Online`
            active_count_id.innerHTML =`<i class="fa-solid fa-circle fa-2xs" style="color: green;"></i>
                                        <span style="font-weight: 700; font-size: medium; color: rgb(0, 162, 0);">${online_sims}</span>
                                        <span style="font-size: 16px; color: #888;">/</span>
                                        <span style="font-weight: 900; font-size: small;">${simulators.length}</span> 
                                        <span class="text-muted" style="font-size: 12px;">Simulators Online</span>`

        } catch (error) {
            console.error(`Error refreshing simulator ${sim}:`, error);
        } finally {
            toggleLoading(card, false);
        }
    };


    // Add event listener to the parent container or document
    document.addEventListener('click', (e) => {
        // Check if the clicked element is a refresh button
        if (e.target.closest('.refresh-btn')) {
            const card = e.target.closest('.simulator_card');
            const table_container = card.querySelector('.table-container');
            console.log(table_container);
            refreshSimulator(card, table_container);
        }
    });


    // Refresh all simulator cards
    document.getElementById("main-refresh").addEventListener("click", () => {
        const simulatorCards = document.querySelectorAll(".simulator_card");
    
        if (simulatorCards.length === 0) {
            showNotification('No simulators found. Please select stack and loadname to view simulators assosiated with them','warning');
        } else {
            simulatorCards.forEach((card) => {
                const table_container = card.querySelector(".table-container"); 
                refreshSimulator(card, table_container);
            });
        }
    });
    

    document.getElementById("update_sim_params_button").addEventListener("click", () => {
            let isValid = true;
            const fields = document.querySelectorAll('#SimulatorForm .form-control');

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
                const form = document.getElementById('SimulatorForm');
                const formData = new FormData(form);
                const stack_json_file_name = stackField.value + "_nodes.json";
                formData.set('stack_json_file', stack_json_file_name);
                document.querySelectorAll(".simulator_card").forEach((card) => {

                    const table_container = card.querySelector(".table-container"); 
                    refreshSimulator(card,table_container,formData);
                });
            }
    });

    document.getElementById("view_asset_dist_btn").addEventListener("click", () => {
        let isValid = true;
        const fields = document.querySelectorAll('#SimulatorForm .form-control');

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
            const form = document.getElementById('SimulatorForm');
            const view_and_validate_asset_dist = document.getElementById('view_and_validate_asset_dist');
            const formData = new FormData(form);
            const stack_json_file_name = stackField.value + "_nodes.json";
            formData.set('stack_json_file', stack_json_file_name);
            formData.append('only_for_validation', "pass_something_to_represent_true");

            fetch(`/call_check_sim_health?sim_hostname=${simulators[0]}`, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(`Error: ${errorData.message}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                showNotification(data.message, data.status);
                console.log("Response from server for viewing asset distribution:", data);
            
                // Access the asset distribution data
                const assetDistData = data.asset_dist_data;

                let htmlContent = ` <h6 class="text-center mt-4">
                                        <i class="fas fa-network-wired fa-xs"></i> Asset Distribution Logic
                                    </h6>
                                    <table border="1" style="width: 100%; border-collapse: collapse;font-size:11px;background-color:white;" class="dataframe table-bordered table-sm text-center mb-5">
                                        <tr class="">
                                            <th>Key</th>
                                            <th>Value</th>
                                        </tr>`;
            
                // Loop through the asset distribution data
                for (const [key, value] of Object.entries(assetDistData)) {
                    let displayValue;
            
                    // Check if the value is an array (and should be displayed as a sub-table)
                    if (Array.isArray(value)) {
                        displayValue = '<table border="1" class="dataframe table table-bordered table-hover table-sm text-center custom-table shadow">';
                        displayValue += `
                            <thead>
                                <tr>
                                    <th class="sortable" data-column="index" data-order="desc">index</th>
                                    <th class="sortable" data-column="domain" data-order="desc">domain</th>
                                    <th class="sortable" data-column="assets" data-order="desc">assets</th>
                                </tr>
                            </thead>
                            <tbody>`;

                        // Loop through the array and display each item in a sub-table
                        value.forEach((item, index) => {
                            displayValue += `
                                <tr>
                                    <td>${index}</td>  
                                    <td>${item[0]}</td> 
                                    <td>${item[1]}</td> 
                                </tr>
                            `;
                        });
                        displayValue += '</tbody></table>';
                        displayValue = `<td style="padding: 8px; text-align: center; max-height: 200px; overflow-y: auto; display: block; height: 200px;">${displayValue}</td>`;


                    } else if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
                        const arrayValue = JSON.parse(value);
                        displayValue = '<table border="1" class="dataframe table table-bordered table-hover table-sm text-center custom-table shadow">';
                        displayValue += `
                            <thead>
                                <tr>
                                    <th class="sortable" data-column="index" data-order="desc">index</th>
                                    <th class="sortable" data-column="assets" data-order="desc">assets</th>
                                </tr>
                            </thead>
                            <tbody>`;

                        // Loop through the array and display each item in a sub-table
                        arrayValue.forEach((item, index) => {
                            displayValue += `
                                <tr>
                                    <td>${index}</td> 
                                    <td>${item}</td> 
                                </tr>
                            `;
                        });
                        displayValue += '</tbody></table>';
                        displayValue = `<td style="padding: 8px; text-align: center; max-height: 200px;overflow-y: auto; display: block; height: 200px;">${displayValue}</td>`;

                    } else {
                        // Otherwise, just display the value directly (if it's a string or number)
                        displayValue = `<td style="padding: 8px; text-align: center;">${value}</td>`;
                    }
                    // Add the row to the main table
                    htmlContent += `
                        <tr>
                            <td style="padding: 8px; text-align: center; vertical-align: top;">${key}</td>
                            ${displayValue}
                        </tr>
                    `;
                }
                htmlContent += '</table>';
                view_and_validate_asset_dist.innerHTML = htmlContent;
            })
            .catch(error => {
                // console.error("Error:", error);
                showNotification(`${error.message}.`, "error");
            });
        }
});

    async function callShellCommandReq(card, command,table_container) {
        // table_container.innerHTML = "";
        const sim = card.querySelector(".card-title").textContent;
        toggleLoading(card, true);
        showNotification(`Executing ${command} in ${sim}...`, 'info');
        const small = document.createElement('small');

        try {
            let response;
            response = await fetch(`/call_execute_shell_command?sim_hostname=${sim}&shell_command=${command}`);
            
            const data = await response.json();
            showNotification(data.message,data.status);
            // small.innerHTML += data.message+"<br> output:"+data.result,data.status;
            display_simcard_notification(card,data.message+". result:"+data.result,data.status);

        } catch (error) {
            console.error(`Error executing ${command} in simulator ${sim}:`, error);
            showNotification(error,"error");
            // small.innerHTML += `Error executing ${command} in simulator ${sim}:` + error;

        } finally {
            toggleLoading(card, false);
        }
        // table_container.appendChild(small);
    };

    document.getElementById("enroll_assets_button").addEventListener("click", () => {
        if (confirm("Are you sure you want to enroll endpointsim instances?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");
        
            if (simulatorCards.length === 0) {
                showNotification('No simulators found. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                simulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./BringUpInstances.sh",table_container);
                });
            }
        }
    });

    document.getElementById("kill_assets_button").addEventListener("click", (event) => {

        if (confirm("Are you sure you want to kill all endpointsim instances?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");
    
            if (simulatorCards.length === 0) {
                showNotification('No simulators found. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                simulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"killall endpointsim",table_container);
                });
            }
        }
    });

    document.getElementById("start_load_button").addEventListener("click", () => {
        if (confirm("Are you sure you want to start the load from all simulators?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");
        
            if (simulatorCards.length === 0) {
                showNotification('No simulators found. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                simulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./SendTrigger.sh",table_container);
                });
            }
        }
    });
    

    document.getElementById("stop_load_button").addEventListener("click", () => {
        if (confirm("Are you sure you want to stop the load from all simulators?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");
        
            if (simulatorCards.length === 0) {
                showNotification('No simulators found. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                simulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"pkill -f 'simulator/LoadTrigger.py'",table_container);
                });
            }
        }
    });

    document.getElementById("pull_latest_code_btn").addEventListener("click", () => {

        const simulatorCards = document.querySelectorAll(".simulator_card");
    
        if (simulatorCards.length === 0) {
            showNotification('No simulators found. Please select stack and loadname to view simulators assosiated with them','warning');
        } else {
            simulatorCards.forEach((card) => {
                const table_container = card.querySelector(".table-container"); 
            callShellCommandReq(card,"git stash;git stash clear;git pull origin main",table_container);
            });
        }
    });

    function display_simcard_notification(card, message, type) {
        // Remove any existing notification in the card
        const existingNotification = card.querySelector(".simcard-notification");
        if (existingNotification) {
            existingNotification.remove();
        }
    
        // Create a notification container
        const notification = document.createElement("div");
        notification.className = "simcard-notification alert alert-info alert-dismissible fade show";
        notification.role = "alert";
        notification.style.position = "absolute";
        notification.style.bottom = "0";
        notification.style.width = "99%";
        notification.style.margin = "0 2.5%";
        notification.style.zIndex = "10";
    
        // Add the message
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close btn btn-sm btn-outline-danger" aria-label="Close"><i class="fa-solid fa-xmark"></i></button>
        `;
    
        // Add close button functionality
        notification.querySelector(".btn-close").addEventListener("click", () => {
            notification.remove();
        });
    
        // Append notification to the card
        card.appendChild(notification);
    
        // Automatically remove the notification after 1 minute (60000 milliseconds)
        setTimeout(() => {
            notification.remove();
        }, 10000);        
    }
    
    // Select all the simulator cards
    const simulatorCards = document.querySelectorAll('.simulator_card');

    // Function to sync scroll for all cards
    const syncScroll = (event) => {
        // Get the scroll position of the currently scrolled card
        const scrollTop = event.target.scrollTop;

        // Sync all other cards with the same scroll position
        simulatorCards.forEach(card => {
            if (card !== event.target) {
                card.scrollTop = scrollTop;
            }
        });
    };

    // Add scroll event listener to each simulator card
    simulatorCards.forEach(card => {
        card.addEventListener('scroll', syncScroll);
    });
});
