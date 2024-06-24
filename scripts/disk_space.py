import json
from helper import execute_point_prometheus_query

class DISK:
    def __init__(self,stack_obj):
        self.curr_ist_start_time=stack_obj.start_timestamp
        self.curr_ist_end_time=stack_obj.end_timestamp
        self.stack_obj=stack_obj

        # self.kafka_total_space = {}
        # for pnode in self.stack_details['pnodes']:
        #     capacity = self.stack_details[pnode]['storage']['kafka']
        #     if str(capacity).endswith('T'):
        #         self.kafka_total_space[pnode] = float(str(capacity)[:-1]) * 1e+12
        #         self.kafka_total_space[pnode+'v'] = float(str(capacity)[:-1]) * 1e+12
        #     elif str(capacity).endswith('G'):
        #         self.kafka_total_space[pnode] = float(str(capacity)[:-1]) * 1e+9
        #         self.kafka_total_space[pnode+'v'] = float(str(capacity)[:-1]) * 1e+9

        self.get_hdfs_total_space_query=f"sort(sum(uptycs_hdfs_node_config_capacity{{cluster_id=~'clst1'}}) by (hdfsdatanode))"
        self.remaining_hdfs_space_query=f"sort(uptycs_hdfs_node_remaining_capacity{{cluster_id=~'clst1'}})"

        self.get_kafka_total_space = "sum(kafka_disk_volume_size) by (host_name)"
        self.kafka_disk_used_percentage="uptycs_percentage_used{partition=~'/data/kafka'}"

        self.pg_partition_used_in_bytes="uptycs_used_disk_bytes{partition=~'/pg',node_type='pg'}"
        self.data_partition_used_in_bytes="uptycs_used_disk_bytes{partition=~'/data',node_type='pg'}"

    def extract_data(self,query,timestamp , TAG):
        final=dict()
        result= execute_point_prometheus_query(self.stack_obj,timestamp,query)
        for res in result:
            node = res['metric'][TAG]
            remaining =  float(res['value'][1])
            final[node] = remaining
        return final 
    
    def calculate_disk_usage(self,TYPE):
        self.stack_obj.log.info(f"-------processing {TYPE} disk space calculation------")
        if TYPE == 'hdfs':
            total_space = self.extract_data(self.get_hdfs_total_space_query,self.curr_ist_start_time,'hdfsdatanode')
            remaining_space_before_load = self.extract_data(self.remaining_hdfs_space_query,self.curr_ist_start_time,'hdfsdatanode')
            remaining_space_after_load = self.extract_data(self.remaining_hdfs_space_query,self.curr_ist_end_time,'hdfsdatanode')
            nodes = [node for node in remaining_space_before_load]
            self.stack_obj.log.info(f"remaining before load {remaining_space_before_load}")
            self.stack_obj.log.info(f"remaining after load {remaining_space_after_load}")
        elif TYPE=="kafka":
            total_space=self.extract_data(self.get_kafka_total_space,self.curr_ist_start_time,'host_name')
            used_space_before_load = self.extract_data(self.kafka_disk_used_percentage,self.curr_ist_start_time,'host_name')
            used_space_after_load = self.extract_data(self.kafka_disk_used_percentage,self.curr_ist_end_time,'host_name')
            self.stack_obj.log.info(f"used_space_before_load : {used_space_before_load}")
            self.stack_obj.log.info(f"used_space_after_load : {used_space_after_load}")
            nodes = [node for node in used_space_before_load]
        self.stack_obj.log.info(f"Total {TYPE} space configured: ")
        self.stack_obj.log.info(json.dumps(total_space, indent=4))
        self.stack_obj.log.info(f"nodes : {nodes}")
        save_dict={}
        bytes_in_a_tb=(1024**4)
        bytes_in_a_gb=(1024**3)

        for node in nodes:
            try:
                if TYPE=='hdfs':
                    total = total_space[node]/bytes_in_a_tb
                    remaining_before_load = remaining_space_before_load[node]/bytes_in_a_tb
                    remaining_after_load = remaining_space_after_load[node]/bytes_in_a_tb
                    percentage_used_before_load=((total-remaining_before_load)/total)*100
                    percentage_used_after_load=((total-remaining_after_load)/total)*100
                elif TYPE=='kafka':
                    total = total_space[node]/bytes_in_a_gb
                    percentage_used_before_load=used_space_before_load[node]
                    percentage_used_after_load=used_space_after_load[node]
                used_space=(percentage_used_after_load-percentage_used_before_load)*total*(1024/100)
                save_dict[node] = {f"{TYPE}_total_space_configured_in_tb" : total , f"{TYPE}_disk_used_percentage_before_load" :percentage_used_before_load,f"{TYPE}_disk_used_percentage_after_load":percentage_used_after_load,f"{TYPE} used_space_during_load_in_gb":used_space}
            except Exception as e:
                self.stack_obj.log.error(f"error calculating {TYPE} usage for node {node}")
        self.stack_obj.log.info("Final dictionary to save : " , )
        self.stack_obj.log.info(json.dumps(save_dict, indent=4))
        return TYPE,save_dict

    def pg_disk_calc(self,TYPE):
        self.stack_obj.log.info(f"------processing {TYPE} disk space calculation------")
        save_dict={}
        pg_used_before_load_in_bytes = self.extract_data(self.pg_partition_used_in_bytes,self.curr_ist_start_time,'host_name')
        pg_used_after_load_in_bytes = self.extract_data(self.pg_partition_used_in_bytes,self.curr_ist_end_time,'host_name')
        data_used_before_load_in_bytes = self.extract_data(self.data_partition_used_in_bytes,self.curr_ist_start_time,'host_name')
        data_used_after_load_in_bytes = self.extract_data(self.data_partition_used_in_bytes,self.curr_ist_end_time,'host_name')
        nodes = [node for node in pg_used_before_load_in_bytes]
        self.stack_obj.log.info(nodes)
        bytes_in_a_gb=(1024**3)
        for node in nodes:
            total_pg_partition_disk_used = (pg_used_after_load_in_bytes[node]-pg_used_before_load_in_bytes[node])/bytes_in_a_gb
            total_data_partition_disk_used = (data_used_after_load_in_bytes[node]-data_used_before_load_in_bytes[node])/bytes_in_a_gb
            self.stack_obj.log.info(f"for node {node}, pg_used_after_load_in_bytes : {pg_used_after_load_in_bytes[node]} , pg_used_before_load_in_bytes : {pg_used_before_load_in_bytes[node]}")
            self.stack_obj.log.info(f"for node {node}, data_used_after_load_in_bytes : {data_used_after_load_in_bytes[node]} , data_used_before_load_in_bytes : {data_used_before_load_in_bytes[node]}")
            save_dict[node] = {
                "/pg (used before load in GB)":pg_used_before_load_in_bytes[node]/bytes_in_a_gb,
                "/pg (used after load in GB)":pg_used_after_load_in_bytes[node]/bytes_in_a_gb,
                "/pg (used in GB) (After -  Before)" : total_pg_partition_disk_used,

                "/data (used before load in GB)":data_used_before_load_in_bytes[node]/bytes_in_a_gb,
                "/data (used after load in GB)":data_used_after_load_in_bytes[node]/bytes_in_a_gb,
                "/data (used in GB) (After -  Before)" : total_data_partition_disk_used}
        self.stack_obj.log.info("Final dictionary to save : " , )
        self.stack_obj.log.info(json.dumps(save_dict, indent=4))
        return TYPE,save_dict

    def save(self,_ ,current_build_data):
        TYPE ,save_dict=_
        if save_dict == {}:
            self.stack_obj.log.warning(f"Disk space usage for {TYPE} is empty ... Not saving this key into mongo")
        else:
            current_build_data[f"{TYPE}_disk_used_space"] = save_dict
        return current_build_data
    
    def make_calculations(self):
        current_build_data={}
        current_build_data=self.save(self.calculate_disk_usage('kafka'),current_build_data)
        current_build_data=self.save(self.calculate_disk_usage('hdfs'),current_build_data)
        current_build_data=self.save(self.pg_disk_calc('pg'),current_build_data)
        return current_build_data
    