document.addEventListener("DOMContentLoaded", () => {
    const stackField = document.getElementById("stack_json_file");
    const loadnameField = document.getElementById("loadname");
    const simulator_grid = document.getElementById('simulator-grid');
    let update_sim_params_button = document.getElementById('update_sim_params_button')
    update_sim_params_button.addEventListener('click', ValidateSimulatorForm)

    let simulator_refresh_button =document.getElementById('simulator_refresh_button')
    simulator_refresh_button.addEventListener('click', trigger_populateSimulatorGrid)

    let active_count_id =document.getElementById('active_count_id')


    let simulators = [];
    

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
    const sendPostRequest = () => {
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
                simulators = data.result_data
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
        if (areBothFieldsFilled()) {
            simulator_grid.innerHTML = ""
            active_count_id.innerHTML = ""
            sendPostRequest();
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
        showNotification(`Fetching health of all ${simulators.length} simulators...`, 'info');
    
        let fetchPromises = simulators.map(sim => {
            
            return fetch(`/call_check_sim_health?sim_hostname=${sim}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            throw new Error(`${errorData.message}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // showNotification(data.message, data.status);
                    console.log("Response from server for :",sim ," : ", data);
                    return {
                        sim,
                        data
                    };
                })
                .catch(error => {
                    // showNotification(`${error.message}.`, "error");
                    console.error("Error during fetch for:", sim, error);
                    return {
                        sim,
                        data: {
                            message: "Failed to fetch health data.",
                            command_outputs: {},
                            test_input_params: {}
                        },
                        error:error
                    };
                });
        });
    
        Promise.all(fetchPromises)
        .then(results => {
            showNotification(`Fetched health of all ${simulators.length} simulators`, 'success');

            let gridHTML = '<div class="row">';
            let online_sims = 0
            let offline_sims = 0

            results.forEach(result => {
                const sim = result.sim;
                const dataObjects = {
                    "command outputs": result.data.command_outputs || {},
                    "test input contents": result.data.testinput_content || {},
                    "test input params": result.data.test_input_params || {}
                };

                let tablesHTML = '';

                // Loop through each data object to generate the corresponding table
                for (let [label, dataObject] of Object.entries(dataObjects)) {
                    const tableRowsHTML = Object.entries(dataObject)
                        .map(([key, value]) => `
                            <tr>
                                <td>${key}</td>
                                <td>${value}</td>
                            </tr>
                        `)
                        .join('');

                    if (tableRowsHTML) {
                        tablesHTML += `
                            <table style="font-size: 9px;" class="dataframe table table-bordered table-hover table-sm text-center custom-table simulator_card_table">
                                <thead>
                                    <tr>
                                        <th class="sortable" data-column="node_type" data-order="desc">${label}</th>
                                        <th class="sortable" data-column="avg" data-order="desc">value</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${tableRowsHTML}
                                </tbody>
                            </table>
                        `;
                    } else {
                        tablesHTML += `<span style="font-size: 9px;">${result.error} <br>${label} not found!</span>`;
                        result.error=""
                    }
                }
                
                if (Object.keys(dataObjects["command outputs"]).length) {
                    online_sims+=1
                }
                else{
                    offline_sims+=1
                }
                gridHTML += `
                    <div class="card mb-2 mx-1 simulator_card ${Object.keys(dataObjects["command outputs"]).length ? 'online' : 'offline'}">
                        <span class="${Object.keys(dataObjects["command outputs"]).length ? 'online_status' : 'offline_status'}">
                            <i class="${Object.keys(dataObjects["command outputs"]).length ? 'fa-solid fa-circle fa-sm mx-1 pt-2' : 'fa-solid fa-xmark fa-lg mx-1 pt-1'}" style="color: ${Object.keys(dataObjects["command outputs"]).length ? 'green' : 'red'};"></i>
                            <span class="status-text">${Object.keys(dataObjects["command outputs"]).length ? 'Online' : 'Offline'}</span>
                        </span>
                        <div class="pt-2 text-center">
                            <h6 class="card-title">${sim}</h6>
                            ${tablesHTML}
                        </div>
                    </div>
                `;
            });

            gridHTML += '</div>'; // Close the row div
            simulator_grid.innerHTML = gridHTML; // Update the HTML once all fetch requests are resolved
            total_sims = online_sims+offline_sims
            active_count_id.innerHTML = `(<span style="font-weight: 700;font-size: medium; color:rgb(0, 162, 0);">${online_sims}</span>/<span style="font-weight: 900;font-size: small;">${total_sims}</span>) Online`

        })
        .catch(error => {
            // console.error('Error rendering the simulator grid:', error);
            showNotification('Failed to populate simulator grid.'+error, 'error');
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
    
    function UpdateSimulatorParams(simulators){
        // const formData = new FormData(document.getElementById('SimulatorForm'));
        const form = document.getElementById('SimulatorForm');
        // Create a FormData object
        const formData = new FormData(form);
        // Generate the new value for 'stack_json_file_name'
        const stack_json_file_name = stackField.value + "_nodes.json";

        formData.set('stack_json_file', stack_json_file_name);

        showNotification("Updating simulator params in progress... ", "info");
        simulators.map(sim => {
            return fetch(`/call_update_sim_params?sim_hostname=${sim}`, {
                method: 'POST',
                body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            throw new Error(`${errorData.message}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    showNotification(data.message, data.status);
                    console.log("Response from server:", data);
                    // populateSimulatorGrid(simulators);
                })
                .catch(error => {
                    console.error("Error:", error);
                    showNotification(`${error.message}.`, "error");
                });
            });
        // populateSimulatorGrid(simulators);
    }

    function ValidateSimulatorForm() {

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
            UpdateSimulatorParams(simulators);
            // populateSimulatorGrid(simulators);
        }
        
    }
    function trigger_populateSimulatorGrid(){
        if (!simulators || simulators.length === 0) {
            // console.log('No simulators found. Exiting function.');
            showNotification(`No simulators found, please select stack and loadname to view simulators associated to them`, 'warning');
            return;
        }
        populateSimulatorGrid(simulators);
    }
});
