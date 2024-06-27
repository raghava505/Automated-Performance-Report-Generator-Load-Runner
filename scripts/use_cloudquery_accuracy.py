if __name__ == "__main__":
    from cloudquery.accuracy import cloud_accuracy
    from settings import stack_configuration
    import json
    variables = {
        "start_time_str_ist":"2024-06-27 02:00",
        "load_duration_in_hrs":12,
        "test_env_file_name":'s4_nodes.json',
        "load_type": "CloudQuery",
        "load_name": "AWS_MultiCustomer",
    }
    stack_obj = stack_configuration(variables)
    stack_obj.log.info("******* Calculating accuracies for cloudquery Load...")
    cloud_accuracy_obj= cloud_accuracy(stack_obj=stack_obj,variables=variables)
    cloudquery_accuracies = cloud_accuracy_obj.calculate_accuracy()