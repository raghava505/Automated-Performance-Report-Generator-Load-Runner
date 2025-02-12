document.addEventListener("DOMContentLoaded", () => {
    const stackField = document.getElementById("stack_json_file");
    const loadnameField = document.getElementById("loadname");
    const simulator_grid = document.getElementById('simulator-grid');
    let selected_count_id = document.getElementById('selected_count_id');
    let live_assets_in_configdb_count = document.getElementById('live_assets_in_configdb_count');
    let active_count_id =document.getElementById('active_count_id');
    
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
        stack_json_file_name=stackField.value;
        loadname=loadnameField.value;
        const simulators_loading_animation = document.getElementById("simulators_loading_animation");
        simulators_loading_animation.style.display = 'block';
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
                simulators_loading_animation.style.display = 'none';
                live_assets_in_configdb_count.style.display = "block";
                button_to_get_live_assets_count_from_configdb.click();
            })
            .catch(error => {
                // console.error("Error:", error);
                showNotification(`${error.message}.`, "error");
                simulators_loading_animation.style.display = 'none';
            });
        
    };
    // Event listeners for both fields
    const handleInputChange = () => {
        simulators=[]
        online_sims=0
        offline_sims=0
        if (areBothFieldsFilled()) {
            simulator_grid.innerHTML = "";
            active_count_id.innerHTML = "";
            selected_count_id.innerHTML = "";
            getSimulators();
        }
    };

    const DynamicForm = () => {
        let selected_value = loadnameField.value.trim().toLowerCase()
        document.querySelectorAll(".sub_load_form").forEach(sub_load_form => {
            sub_load_form.style.display = "none";
        });
        document.getElementById(`${selected_value}_part_of_the_form`).style.display = "block";
    }

    stackField.addEventListener("change", handleInputChange);
    loadnameField.addEventListener("change", handleInputChange);
    loadnameField.addEventListener("change", DynamicForm);
    DynamicForm();


    function populateSimulatorGrid(simulators) {
        console.log(simulators)
        if (!simulators || simulators.length === 0) {
            console.log('No simulators found/selected. Exiting function.');
            return;
        }
        showNotification(`Fetched ${simulators.length} simulators`, 'info');
    
        let gridHTML = '<div class="row">';
        
        simulators.forEach(sim => {            
            gridHTML += `
                <div class="card mb-2 mr-2 simulator_card offline">
                    <div class="loading-bar"></div>
                    <button class="position-absolute btn btn-sm btn-info refresh-btn"><i class="fa-solid fa-arrows-rotate fa-xs"></i></button>

                    <input class="position-absolute btn btn-sm checkbox_class btn-uptycs" type="checkbox" checked>

                    <div class="text-center">
                        <span class="offline_status"><i class="fa-solid fa-solid fa-ban mx-1 pt-1" style="color: red;"></i><span class="status-text">Offline</span></span>
                        <span class="online_status"><i class="fa-solid fa-circle  mx-1 pt-1" style="color: green;"></i><span class="status-text">Online</span></span>
                    </div>
    
                    <div class="pt-2 text-center">
                        <h6 class="card-title name_of_the_simulator"><i class="fa-solid fa-desktop fa-xs"></i> ${sim}</h6>


                        <div class="col text-center main_live_assets_element">
                            <button style="background: none; border: none; padding: 0; cursor: pointer;" class="live_assets_btn">
                                <i class="fa-solid fa-sync fa-sm"></i>
                            </button>
                            <div class="live_assets_loader" style="display:none;">
                                <div class="spinner-border spinner-border-sm" role="status">
                                    <span class="sr-only">Loading...</span>
                                </div>
                            </div>
                
                            <span class="text-right">
                                <span class="store_live_count_in">
                                    <span style="font-weight: 700; font-size: medium; color: rgb(0, 156, 0);">0</span>
                                </span>
                                <span class="text-muted" style="font-size: 12px;"> Live assets in configdb </span>
                            </span>
                        </div>


                        <div class="table-container"></div>
                    </div>
                </div>
            `;
        });

        gridHTML += '</div>'; // Close the row div
        simulator_grid.innerHTML = gridHTML; // Update the HTML once all fetch requests are resolved
        // document.getElementById("pull_latest_code_btn").click();
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

        attachCheckboxListeners();
        attachToggleButtonListener();
    }
    

    $(document).on('click', '.sortable', function () {
        var $this = $(this);
        var order = $this.data('order');
    
        // Get the parent table of the clicked header
        var $table = $this.closest('table');
    
        // Select immediate rows of the tbody to avoid affecting nested tables
        var $rows = $table.children('tbody').children('tr').filter(function () {
            return !$(this).find('table').length; // Exclude rows containing nested tables
        }).toArray();
    
        // Sort rows based on the column and order
        $rows.sort(function (a, b) {
            var aText = $(a).find('td').eq($this.index()).text().trim();
            var bText = $(b).find('td').eq($this.index()).text().trim();
    
            // Handle special values and numeric comparisons
            if (aText === "NaN") aText = Number.NEGATIVE_INFINITY;
            if (bText === "NaN") bText = Number.NEGATIVE_INFINITY;
    
            var aNumeric = parseFloat(aText.replace(/[^0-9.-]+/g, ''));
            var bNumeric = parseFloat(bText.replace(/[^0-9.-]+/g, ''));
    
            if (!isNaN(aNumeric) && !isNaN(bNumeric)) {
                return (order === 'desc' ? (bNumeric - aNumeric) : (aNumeric - bNumeric));
            }
    
            return (order === 'desc' ? (aText > bText) : (aText < bText)) ? 1 : -1;
        });
    
        // Reverse the order for the next click
        $this.data('order', order === 'desc' ? 'asc' : 'desc');
    
        // Remove existing sort classes from all headers in the same table
        $this.closest('tr').find('.sortable').removeClass('asc desc');
        $this.addClass(order === 'desc' ? 'asc' : 'desc');
    
        // Append sorted rows to the table body without disrupting nested tables
        $.each($rows, function (index, row) {
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
                let chart_hidden = true;
                if (data.load_remaining_dur_in_sec) {
                    const remainingDurInSec = Number(data.load_remaining_dur_in_sec);
                    if (remainingDurInSec === 0) {
                        console.log("The remaining time is 0");
                        chart_hidden = true
                    } 
                    else {
                        chart_hidden = false
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

                if (data.cpu_stats) {

                    const chartClass = chart_hidden ? "chart-hidden" : "";
                    table_container.innerHTML += `
                      <div class="simulator_sub_cards">
                        <div class="chart-container ${chartClass}" style="display: block;">
                          <canvas id="cpuUsageChart_${sim}" width="400" height="300" style="height: 300px;"></canvas>
                        </div>
                      </div>
                    `;
                  }
                
                let count = 0;
                data.main_params.forEach(([key, value], index) => {
                    const card = document.createElement('div');
                    card.className = 'simulator_sub_cards col rounded py-2 text-center bg-light position-relative';
                
                    value_font_factor = Math.floor(String(value).length / 12);
                    console.log(value_font_factor,key,value)
                    card.innerHTML = `
                        <h${value_font_factor+5} class="text-uptycs mb-1">${value}</h${value_font_factor+5}>
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

                cpuUsageChart = initialize_chart(`cpuUsageChart_${sim}`)
                updateChart(cpuUsageChart, data.cpu_stats);
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
    document.getElementById('button_to_get_live_assets_count_from_configdb').addEventListener('click', async () => {
        const stack_json_file = stackField.value.trim();
    
        if (stack_json_file === "") {
            showNotification("Empty stack field found to fetch live assets count.", "info");
            return;
        }
    
        // Fetch for the main live assets count (runs asynchronously, does NOT block execution)
        const mainLiveAssetsPromise = fetchLiveAssetsCount("", live_assets_in_configdb_count);
    
        const simulatorCards = document.querySelectorAll(".simulator_card");
    
        const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
            const checkbox = card.querySelector(".checkbox_class");
            return checkbox && checkbox.checked;
        });
    
        if (selectedSimulatorCards.length === 0) {
            showNotification('No simulators found/selected. Please select stack and loadname to view simulators associated with them', 'warning');
        } else {
            // Fetch live asset count for selected simulator cards in parallel (does NOT wait for mainLiveAssetsPromise)
            const simulatorPromises = selectedSimulatorCards.map(async (card) => {
                const simname = card.querySelector(".card-title")?.textContent?.trim();
                const main_live_assets_element = card.querySelector(".main_live_assets_element");
    
                if (simname && main_live_assets_element) {
                    return fetchLiveAssetsCount(simname, main_live_assets_element);
                } else {
                    console.warn("Missing simulator name or main live assets element in card:", card);
                    return null;
                }
            });
    
            // Wait for all simulator fetches to complete
            await Promise.all(simulatorPromises);
        }
    
        // We do NOT await mainLiveAssetsPromise before starting simulatorPromises, so it runs in parallel
        await mainLiveAssetsPromise;
    });
    
    async function fetchLiveAssetsCount(sim_hostname, live_assets_in_configdb_count_element) {
        if (!live_assets_in_configdb_count_element) {
            console.error("Invalid live_assets_in_configdb_count_element:", live_assets_in_configdb_count_element);
            return;
        }
    
        const button = live_assets_in_configdb_count_element.querySelector(".live_assets_btn");
        const loader = live_assets_in_configdb_count_element.querySelector(".live_assets_loader");
        const store_live_count_in = live_assets_in_configdb_count_element.querySelector(".store_live_count_in");
    
        if (!button || !loader || !store_live_count_in) {
            console.error("One or more elements are missing inside live_assets_in_configdb_count_element:", live_assets_in_configdb_count_element);
            return;
        }
    
        button.style.display = "none";
        loader.style.display = "inline";
    
        try {
            const response = await fetch(`/get_live_assets_count_from_configdb?stack_json_file=${stackField.value.trim()}&sim_hostname=${sim_hostname}`, {
                method: 'GET',
            });
    
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Error: ${errorData.message}`);
            }
    
            const data = await response.json();
            console.log("Fetched data for:", sim_hostname, "is -", data);
            showNotification(data.message, data.status);
    
            store_live_count_in.innerHTML = `<span style="font-weight: 700; font-size: medium; color: rgb(0, 156, 0);">${data.count}</span>`;
    
        } catch (error) {
            console.error(`Could not connect to API for fetching live asset count for ${sim_hostname}:`, error);
            showNotification(`Could not connect to API for fetching live asset count.`, "error");
    
            store_live_count_in.innerHTML = `<span style="font-weight: 700; font-size: medium; color: red;">Error</span>`;
        } finally {
            console.log("Reached finally for:", sim_hostname);
            button.style.display = "inline";
            loader.style.display = "none";
        }
    }

    // Add event listener to the parent container or document
    document.addEventListener('click', (e) => {
        // Check if the clicked element is a refresh button
        if (e.target.closest('.live_assets_btn')) {
            const card = e.target.closest('.simulator_card');
            const simname = card.querySelector(".card-title")?.textContent?.trim();
            const main_live_assets_element = card.querySelector(".main_live_assets_element");
            fetchLiveAssetsCount(simname, main_live_assets_element);
        }
    });
    

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

    document.getElementById(`toggle_cpu_charts`).addEventListener('click', function () {
        const chartContainers = document.querySelectorAll('.chart-container');
        let isAnyVisible = Array.from(chartContainers).some(container => !container.classList.contains('chart-hidden'));
      
        chartContainers.forEach(container => {
          if (isAnyVisible) {
            container.classList.add('chart-hidden');
          } else {
            container.classList.remove('chart-hidden');
          }
        });

        // chartContainers.forEach(container => {
        //     if (!container.classList.contains('chart-hidden')) {
        //       container.classList.add('chart-hidden');
        //     } else {
        //       container.classList.remove('chart-hidden');
        //     }
        //   });
      });



      document.getElementById("main-refresh").addEventListener("click", () => {
        const simulatorCards = document.querySelectorAll(".simulator_card");

        const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
            const checkbox = card.querySelector(".checkbox_class");
            return checkbox && checkbox.checked;
          });
    
        if (selectedSimulatorCards.length === 0) {
            showNotification('No simulators found/selected. Please select stack and loadname to view simulators assosiated with them','warning');
        } else {
            selectedSimulatorCards.forEach((card) => {
                const table_container = card.querySelector(".table-container"); 
                refreshSimulator(card, table_container);
            });
        }
    });


   // Function to handle all button clicks
function handleUpdateParams(buttonType) {
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
        if (confirm("Are you sure you want to update parameters in the selected simulators? Note: The unchecked simulators will be ignored for asset distribution.")) {
            const form = document.getElementById('SimulatorForm');
            const formData = new FormData(form);
            
            // Append the clicked button type to formData
            formData.append("button_clicked", buttonType);

            // Select only checked simulator cards
            const simulatorCards = document.querySelectorAll(".simulator_card");
            const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
                const checkbox = card.querySelector(".checkbox_class");
                return checkbox && checkbox.checked;
            });

            if (selectedSimulatorCards.length === 0) {
                showNotification('No simulators found/selected. Please select stack and loadname to view simulators associated with them', 'warning');
            } else {
                // Extract simulator names and add to FormData
                const selectedSimulators = selectedSimulatorCards.map(card => {
                    return card.querySelector(".name_of_the_simulator").textContent.trim();
                });

                // Append to formData as a comma-separated string
                formData.append("selected_simulators", selectedSimulators.join(','));

                // Refresh each selected simulator with updated form data
                selectedSimulatorCards.forEach(card => {
                    const table_container = card.querySelector(".table-container");
                    refreshSimulator(card, table_container, formData);
                });
            }
        }
    }
}

// Attach event listeners to all buttons
document.getElementById("update_sim_params_button").addEventListener("click", () => handleUpdateParams("update_all"));
document.getElementById("update_num_msgs").addEventListener("click", () => handleUpdateParams("update_num_msgs"));
document.getElementById("update_inputfile").addEventListener("click", () => handleUpdateParams("update_inputfile"));


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
            const simulatorCards = document.querySelectorAll(".simulator_card");
            const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
                const checkbox = card.querySelector(".checkbox_class");
                return checkbox && checkbox.checked;
            });
            const selectedSimulators = selectedSimulatorCards.map(card => {
                return card.querySelector(".name_of_the_simulator").textContent.trim();
              });
          
              // Append to formData as a comma-separated string

            const form = document.getElementById('SimulatorForm');
            const view_and_validate_asset_dist = document.getElementById('view_and_validate_asset_dist');
            const formData = new FormData(form);
            formData.append("selected_simulators", selectedSimulators.join(','));


            fetch(`/view_asset_dist`, {
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
        table_container.innerHTML = "";
        const sim = card.querySelector(".card-title").textContent;
        toggleLoading(card, true);
        showNotification(`Executing ${command} in ${sim}...`, 'info');
        const small = document.createElement('small');
        fetch(`/call_execute_shell_command?sim_hostname=${sim}&shell_command=${command}`)
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
                small.innerHTML += `status : ${data.status}<br> Output : ${data.output}<br> ${data.message}`;
                small.classList.add("card-notfication",data.status) 
                // small.style.color = "green";
                // display_simcard_notification(card,data.message+". result:"+data.result,data.status);

            })
            .catch(error => {
                console.error(`Error executing ${command} in simulator ${sim}:`, error);
                showNotification(error.message, "error");
                small.innerHTML += `Error executing ${command} in simulator ${sim}. <br> ${error.message}`;
                small.classList.add("card-notfication","error") 

                // small.style.color = "red";
            })
            .finally(() => {
                toggleLoading(card, false);
            });

        table_container.appendChild(small);

    };

    document.getElementById("enroll_assets_button").addEventListener("click", () => {
        if (confirm("Are you sure you want to enroll endpointsim instances in selected simulators?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");

            const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
                const checkbox = card.querySelector(".checkbox_class");
                return checkbox && checkbox.checked;
              });

        
            if (selectedSimulatorCards.length === 0) {
                showNotification('No simulators found/selected. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                selectedSimulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./BringUpInstances.sh",table_container);
                });
            }
        }
    });

    document.getElementById("kill_assets_button").addEventListener("click", (event) => {

        if (confirm("Are you sure you want to kill all endpointsim instances in the selected simulators?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");

            const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
                const checkbox = card.querySelector(".checkbox_class");
                return checkbox && checkbox.checked;
              });
    
            if (selectedSimulatorCards.length === 0) {
                showNotification('No simulators found/selected. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                selectedSimulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./KillInstances.sh",table_container);
                });
            }
        }
    });

    document.getElementById("start_load_button").addEventListener("click", () => {
        if (confirm("Are you sure you want to start the load from the selected simulators?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");
            
            const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
                const checkbox = card.querySelector(".checkbox_class");
                return checkbox && checkbox.checked;
              });
        
            if (selectedSimulatorCards.length === 0) {
                showNotification('No simulators found/selected. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                selectedSimulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./SendTrigger.sh",table_container);
                });
            }
        }
    });

    document.getElementById("stop_load_button").addEventListener("click", () => {
        if (confirm("Are you sure you want to stop the load in the selected simulators?")) {
            const simulatorCards = document.querySelectorAll(".simulator_card");

            const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
                const checkbox = card.querySelector(".checkbox_class");
                return checkbox && checkbox.checked;
              });
        
            if (selectedSimulatorCards.length === 0) {
                showNotification('No simulators found/selected. Please select stack and loadname to view simulators assosiated with them','warning');
            } else {
                selectedSimulatorCards.forEach((card) => {
                    const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./StopTrigger.sh",table_container);
                });
            }
        }
    });

    document.getElementById("pull_latest_code_btn").addEventListener("click", () => {

        const simulatorCards = document.querySelectorAll(".simulator_card");
        const selectedSimulatorCards = Array.from(simulatorCards).filter(card => {
            const checkbox = card.querySelector(".checkbox_class");
            return checkbox && checkbox.checked;
          });
    
        if (selectedSimulatorCards.length === 0) {
            showNotification('No simulators found/selected. Please select stack and loadname to view simulators assosiated with them','warning');
        } else {
            selectedSimulatorCards.forEach((card) => {
                const table_container = card.querySelector(".table-container"); 
                callShellCommandReq(card,"./PullLatestCode.sh",table_container);

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



    function updateCheckboxCounter() {
        const checkboxes = document.querySelectorAll('.checkbox_class');
        const checkedCount = Array.from(checkboxes).filter(checkbox => checkbox.checked).length;
        const totalCheckboxes = checkboxes.length;
      
        // Display the updated count
        const counterElement = document.getElementById('checkbox-counter');
        counterElement.innerHTML = `<span style="font-weight: 700; font-size: medium;">${checkedCount}</span><span style="font-size: 16px; color: #888;"> / </span><span style="font-weight: 900; font-size: small;color:black">${totalCheckboxes}</span>`;
      }
      
      // Attach event listeners to all checkboxes
      function attachCheckboxListeners() {
        // const selected_count_id = document.getElementById('selected_count_id');
      
        const txt = `
        <i class="fa-solid fa-check fa-2xs" style="color: rgb(19, 15, 255);"></i>
        <span id="checkbox-counter" style="font-weight: 700; font-size: medium; color: rgba(105,16,217,255);">0</span>
        <span class="text-muted" style="font-size: 12px;"> Simulators Selected</span>
        `;
        selected_count_id.innerHTML = txt;
      
        const checkboxes = document.querySelectorAll('.checkbox_class');
        checkboxes.forEach(checkbox => {
          checkbox.addEventListener('change', updateCheckboxCounter);
        });
      
        updateCheckboxCounter(); // Initial count
      }
      
      // Function to toggle all checkboxes
      function toggleCheckboxes() {
        const checkboxes = document.querySelectorAll('.checkbox_class');
        const areAllChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
      
        checkboxes.forEach(checkbox => {
          checkbox.checked = !areAllChecked;
        });
      
        updateCheckboxCounter(); // Update the counter after toggling
      }
      
      // Attach event listener to the toggle button
      function attachToggleButtonListener() {
        const toggleButton = document.getElementById('select_deselect');
        toggleButton.addEventListener('click', toggleCheckboxes);
      }
      

      document.getElementById('moreAboutInputFileBtn').addEventListener('click', async () => {
        const inputFileSelect = document.getElementById('inputfile');
        const selectedInputFile = inputFileSelect.value;
        document.getElementById('inputFileMetadataContent').innerHTML = "Fetching metadata..."
    
        if (!selectedInputFile) {
            alert('Please select an input file before clicking the "More about inputfile" button.');
            return;
        }
    
        // Programmatically trigger the modal only after validation
        $('#InputFiles_Modal').modal('show');
    
        // Update modal title with the selected input file

        fetch(`/get_inputfile_metadata_from_sim?inputfile_name=${encodeURIComponent(selectedInputFile)}&sim_hostname=${simulators[0]}`)
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
                console.log("inputfile metadata Response from server:", data);
                const metadataContent = formatMetadataToHTML(data.input_file_details);
                document.getElementById('InputFiles_ModalTitle').textContent = `${data.modal_heading}`;
                document.getElementById('inputFileMetadataContent').innerHTML = metadataContent;
                attachToggleListeners(); // Attach toggle functionality after setting the content
                
            })
            .catch(error => {
                // console.error("Error:", error);
                document.getElementById('inputFileMetadataContent').innerHTML = '<div class="alert alert-danger">Error fetching metadata. Please try again.</div>';
                console.log(error);
                showNotification(`${error.message}.`, "error");
            });
    });
    
    function formatMetadataToHTML(data) {
        let html = `
            <table class="table table-bordered table-sm text-center" style="width: 100%; table-layout: auto;">
        `;
    
        function formatValue(key, value, parentId) {
            if (typeof value === 'object' && value !== null) {
                const nestedTableId = `${parentId}-${key.replace(/\s+/g, '-')}`;
                return `
                    <button type="button" class="btn btn-link btn-sm p-0 toggle-nested" data-target="#${nestedTableId}" style="font-size: 13px;">
                        Show Details
                    </button>
                    <div id="${nestedTableId}" class="nested-table-container" style="display: none;">
                        ${generateNestedTable(value, nestedTableId)}
                    </div>
                `;
            }
            return value !== undefined ? value.toString() : 'N/A';
        }
    
        function generateNestedTable(obj, parentId) {
            let nestedHtml = `
                <table border="1" class="dataframe table table-bordered table-hover table-sm text-center" style="width: 100%; table-layout: auto;">
                <thead><tr>
                    <th class="sortable" data-column="" data-order="desc">sort</th>
                    <th class="sortable" data-column="" data-order="desc">sort</th>
                </tr>
                </thead>
                <tbody>
            `;
            for (const [nestedKey, nestedValue] of Object.entries(obj)) {
                nestedHtml += `
                    
                    <tr>
                        <td style="word-break: break-word;">${nestedKey}</td>
                        <td style="word-break: break-word;">${formatValue(nestedKey, nestedValue, parentId)}</td>
                    </tr>
                `;
            }
            nestedHtml += '</table>';
            return nestedHtml;
        }
    
        for (const [key, value] of Object.entries(data)) {
            html += `
                <tr>
                    <th style="width:25%;">${key}</th>
                    <td style="word-break: break-word;">${formatValue(key, value, 'root')}</td>
                </tr>
            `;
        }
    
        html += '</tbody></table>';
    
        return html;
    }
    
    
    // Attach event listeners after the modal content is set
    function attachToggleListeners() {
        document.querySelectorAll('.toggle-nested').forEach(button => {
            button.addEventListener('click', function (event) {
                event.preventDefault();
                const target = document.querySelector(this.dataset.target);
                if (target) {
                    target.style.display = target.style.display === 'none' ? 'block' : 'none';
                    this.textContent = target.style.display === 'none' ? 'Show Details' : 'Hide Details';
                }
            });
        });
    }
    // Initialize the chart when the page loads
    // function initialize_chart(chart_id){
    //     const ctx = document.getElementById(chart_id).getContext('2d');
    
    //     let cpuUsageChart = new Chart(ctx, {
    //         type: 'line',
    //         data: {
    //         labels: [],
    //         datasets: [{
    //             label: 'CPU Usage %',
    //             data: [],
    //             backgroundColor: 'rgba(138, 43, 226, 0.3)',
    //             borderColor: 'rgba(138, 43, 226, 1)',
    //             borderWidth: 0.4,
    //             fill: true,
    //             pointRadius: 0.9, // Remove the dots from the chart
    //             cubicInterpolationMode: 'monotone' // Smoothen the curve
    //         }]
    //         },
    //         options: {
    //         responsive: true,
    //         scales: {
    //             x: {
    //             ticks: {
    //                 callback: function (value, index, ticks) {
    //                     const totalLabels = cpuUsageChart.data.labels.length;

    //                     if (totalLabels > 5) {
    //                     const interval = Math.floor(totalLabels / 10); // Split data evenly into 5 ticks
    //                     return index % interval === 0 ? this.getLabelForValue(value) : '';
    //                     }
    //                     return this.getLabelForValue(value); // Show all labels if <= 5
    //                 },
    //                 maxTicksLimit: 5,  // Additional safeguard to enforce 5 ticks
    //                 font: {
    //                     size: 6 // Keep the font size smaller
    //                 }
    //                 }
    //             },
    //             y: {
    //             beginAtZero: true,
    //             suggestedMax: 100,
    //             ticks: {
    //                 font: {
    //                 size: 6 // Set the y-tick font size to a smaller value
    //                 }
    //             }
    //             }
    //         },
    //         plugins: {
    //             legend: { display: false },
    //             title: {
    //               display: true,
    //               text: 'CPU busy %',
    //               font: {
    //                 size: 10, // Set a smaller font size
    //                 weight: 'normal' // Make the title non-bold
    //               }
    //             }
    //           }
              
    //         }
    //     });
    //     return cpuUsageChart
    // }

    // function updateChart(chart, data) {
    //     data.forEach(point => {
    //     chart.data.labels.push(point.time);
    //     chart.data.datasets[0].data.push(point.value);
    //     });
    
    //     // Maintain only the last 300 values
    //     if (chart.data.labels.length > 300) {
    //     chart.data.labels.splice(0, chart.data.labels.length - 300);
    //     chart.data.datasets[0].data.splice(0, chart.data.datasets[0].data.length - 300);
    //     }
    //     chart.update();
    // }    


    function initialize_chart(chart_id) {
        const ctx = document.getElementById(chart_id).getContext('2d');
      
        let usageChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: [],
            datasets: [
              {
                label: 'Average CPU Usage %',
                data: [],
                backgroundColor: 'rgba(138, 43, 226, 0.3)',
                borderColor: 'rgba(138, 43, 226, 1)',
                borderWidth: 0.4,
                fill: true,
                pointRadius: 0.9,
                cubicInterpolationMode: 'monotone'
              },
              {
                label: 'Average Memory Usage (GB)',
                data: [],
                backgroundColor: 'rgba(34, 139, 34, 0.3)',
                borderColor: 'rgba(34, 139, 34, 1)',
                borderWidth: 0.4,
                fill: true,
                pointRadius: 0.9,
                cubicInterpolationMode: 'monotone'
              }
            ]
          },
          options: {
            responsive: true,
            scales: {
              x: {
                ticks: {
                  callback: function (value, index, ticks) {
                    const totalLabels = usageChart.data.labels.length;
      
                    if (totalLabels > 5) {
                      const interval = Math.floor(totalLabels / 10);
                      return index % interval === 0 ? this.getLabelForValue(value) : '';
                    }
                    return this.getLabelForValue(value);
                  },
                  maxTicksLimit: 5,
                  font: { size: 6 }
                }
              },
              y: {
                beginAtZero: true,
                suggestedMax: 100,
                ticks: {
                  font: { size: 6 }
                }
              }
            },
            plugins: {
              legend: {
                labels: {
                  font: { size: 6 },
                  boxWidth: 5, // Small legend color box size
                  boxHeight: 5
                }
              }
            }
          }
        });
      
        return usageChart;
      }
      
      function updateChart(chart, data) {
        data.forEach(point => {
          chart.data.labels.push(point.time);
          chart.data.datasets[0].data.push(point.cpu); 
          chart.data.datasets[1].data.push(point.memory); 
        });
      
        // Maintain only the last 300 values
        if (chart.data.labels.length > 300) {
          chart.data.labels.splice(0, chart.data.labels.length - 300);
          chart.data.datasets[0].data.splice(0, chart.data.datasets[0].data.length - 300);
          chart.data.datasets[1].data.splice(0, chart.data.datasets[1].data.length - 300);
        }
      
        chart.update();
      }
      


});
