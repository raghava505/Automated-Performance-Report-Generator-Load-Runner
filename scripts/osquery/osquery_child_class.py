from parent_load_details import parent

class osquery_child(parent):
    load_specific_details={
            "MultiCustomer" : {
                "total_number_of_customers": "120",
                "number_of_customers_with_auto_exception_enabled": "0",
                "test_title": "Multiple Customer Rule Engine and Control Plane Load",
                "total_assets": "80K Control Plane + 15K Multi customer",
                "assets_per_cust":"125",
                "alert_rules_enabled_per_cust":39,
                "alert_rules_triggered_per_cust":33,
                "records_sent_per_hour_per_customer": "8,164,800",
                "records_sent_per_hour" : "979,776,000",
                "input_file": "rhel7-6tab_12rec.log",
                "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
            },
            "SingleCustomer":{
                "total_number_of_customers": 1,
                "number_of_customers_with_auto_exception_enabled": 1,
                "test_title": "Single Customer Rule Engine Load",
                "total_assets": "24576",
                "assets_per_cust":"24576",
                "alert_rules_enabled_per_cust":39,
                "alert_rules_triggered_per_cust":33,
                "records_sent_per_hour": "1.592 B",
                "input_file": "rhel7-6tab_12rec.log",
                "events_table_name": "dns_lookup_events, socket_events, process_events, process_file_events"
            },
            "ControlPlane":{
                "total_number_of_customers": "1",
                "test_title": "Single Customer Control Plane Load",
                "total_assets": "200K",
                "redis_switchover_case_time_ist":""
            },
    }
    