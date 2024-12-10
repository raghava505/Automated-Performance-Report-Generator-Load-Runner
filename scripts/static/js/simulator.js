document.addEventListener("DOMContentLoaded", () => {
    const stackField = document.getElementById("stack");
    const loadnameField = document.getElementById("loadname");

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
        // const postData = {
        stack_json_file_name=stackField.value+"_nodes.json",
        loadname=loadnameField.value,
        // };
        fetch(`/get_simulators_list?stack_json_file_name=${stack_json_file_name}&loadname=${loadname}`)
        .then(response => response.json())
            .then((data) => {
                console.log("Response from server:", data.main_osquery_data_simulator);
                populateSimulatorGrid(data.main_osquery_data_simulator);

            })
            .catch((error) => {
                console.error("Error:", error);
            });
    };
    // Event listeners for both fields
    const handleInputChange = () => {
        if (areBothFieldsFilled()) {
            sendPostRequest();
        }
    };

    stackField.addEventListener("change", handleInputChange);
    loadnameField.addEventListener("change", handleInputChange);

    function populateSimulatorGrid(simulators) {
        const simulator_grid = document.getElementById('simulator-grid');
        let gridHTML = '<div class="ml-2 row">';
    
        simulators.forEach(sim => {
            gridHTML += `
                <div class="card mb-2 mx-1 simulator_card shadow offline">
                    <span class="offline_status">
                        <i class="fa-solid fa-xmark fa-lg mx-1" style="color: red;"></i>
                        <span class="status-text">Offline</span>
                    </span>
                    <span class="online_status">
                        <i class="fa-solid fa-circle fa-sm mx-1" style="color: green;"></i>
                        <span class="status-text">Online</span>
                    </span>
                    <div class="p-2 mt-2 text-center">
                        <h6 class="card-title">${sim}</h6>
                        <p class="card-text">endpointsim:10 <br> node:10</p>
                    </div>
                </div>`;
        });
    
        gridHTML += '</div>'; // Close the row div
        simulator_grid.innerHTML = gridHTML; // Update the HTML once
    }
    
});
