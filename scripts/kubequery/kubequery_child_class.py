from parent_load_details import parent

class kubequery_child(parent):
    load_specific_details={
                "KubeQuery_SingleCustomer":{
                "total_number_of_customers": 1,
                "test_title": "Kubequery and K8sosquery Load",
                "total_assets": 200,
                "total_number_of_clusters": 4
            },
                "SelfManaged_SingleCustomer":{
                "total_number_of_customers": 1,
                "test_title": "SelfManaged Containers Load",
                "total_assets": 200,
            },
    }
    