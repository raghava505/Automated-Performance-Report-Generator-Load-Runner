import pandas as pd
from io import StringIO
import numpy as np
from helper import execute_trino_query
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
#configdb_command = "PGPASSWORD=pguptycs psql -h {} -U uptycs -p 5432 -d configdb -c \"select read_password from customer_database where database_name='upt_{}';\"".format(remote_host,self.stack_details['domain'])
from time_taken_by_all_queries import get_full_query,time_ranges

class TRINO_ANALYSE:
    def __init__(self,stack_obj):
        self.start_utc_str=stack_obj.start_time_str_utc
        self.end_utc_str=stack_obj.end_time_str_utc
        self.dnode = stack_obj.execute_trino_queries_in

    def get_trino_commands(self):
        limit=20
        TIME_AGGREGATIONS = """
                                SUM(CAST(wall_time AS bigint)) AS total_wall_time,
                                SUM(CAST(queued_time AS bigint)) AS total_queued_time,
                                SUM(CAST(cpu_time AS bigint)) AS total_cpu_time,
                                COALESCE(SUM(CAST(analysis_time AS bigint)),0) AS total_analysis_time,
                                
                                ROUND(AVG(CAST(wall_time AS bigint)),3) AS avg_wall_time,
                                ROUND(AVG(CAST(queued_time AS bigint)),3) AS avg_queued_time,
                                ROUND(AVG(CAST(cpu_time AS bigint)),3) AS avg_cpu_time,
                                COALESCE(ROUND(AVG(CAST(analysis_time AS bigint)),3),0) AS avg_analysis_time,

                                MAX(CAST(wall_time AS bigint)) AS max_wall_time,
                                MAX(CAST(queued_time AS bigint)) AS max_queued_time,
                                MAX(CAST(cpu_time AS bigint)) AS max_cpu_time,
                                COALESCE(MAX(CAST(analysis_time AS bigint)),0) AS max_analysis_time
                            """
        TIME_COLUMNS = ['total_wall_time','total_queued_time','total_cpu_time','total_analysis_time','avg_wall_time','avg_queued_time','avg_cpu_time','avg_analysis_time','max_wall_time','max_queued_time','max_cpu_time','max_analysis_time']
        AVG_COMPARE_TIME_COLUMNS = ['avg_wall_time','avg_queued_time','avg_cpu_time','avg_analysis_time']
        TOTAL_COMPARE_TIME_COLUMNS = ['total_wall_time','total_queued_time','total_cpu_time','total_analysis_time']

        return {
            "Total number of trino queries executed from each source" : {
                "query" :  "SELECT\
                                source,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(*) as total_count\
                            FROM presto_query_logs\
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 1\
                            ORDER BY 1;",
                "columns":['source','success_count','failure_count','total_count'],
                "schema":{
                    "merge_on_cols" : ["source"],
                    "compare_cols":["total_count"]
                }
            },
            "Total number of trino queries executed from each source grouped by query_operation" : {
                "query" :  "SELECT\
                                source,\
                                COALESCE(query_operation,'NaN') AS query_operation,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(*) as total_count\
                            FROM presto_query_logs\
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY 1,2\
                            ORDER BY 1,2;",
                "columns":['source','query_operation','success_count','failure_count','total_count'],
                "schema":{
                    "merge_on_cols" : ["source","query_operation"],
                    "compare_cols":["total_count"]
                }
            },
            "Total number of failed queries grouped by failure message" : {
                "query" :  "select \
                                source,\
                                failure_message,\
                                count(*) as failure_count \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            and query_status='FAILURE' \
                            group by 1,2 \
                            order by 1;",
                "columns":['source','failure_message','failure_count'],
                "schema":{
                    "merge_on_cols" : ['source','failure_message'],
                    "compare_cols":["failure_count"]
                }
            },
            # "Number of queries running each hour":{
            #     "query" :  f"select \
            #                     'day-' || CAST(upt_day AS varchar) AS upt_day,\
            #                     'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
            #                     count(*) as total_queries,\
            #                     COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
            #                     COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
            #                     COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
            #                     COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
            #                     {TIME_AGGREGATIONS}\
            #                 from presto_query_logs \
            #                 where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
            #                 GROUP BY 'day-' || CAST(upt_day AS varchar), 'batch-' || CAST(upt_batch AS varchar) \
            #                 ORDER BY upt_day,upt_batch LIMIT 168;",
            #     "columns":['upt_day','upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries']+TIME_COLUMNS,
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #     }
            # },
            "Time taken by the queries on an hourly basis":{
                "query" :  f"select \
                                'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                                count(*) as total_queries,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
                                COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
                                {TIME_AGGREGATIONS}\
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY  'batch-' || CAST(upt_batch AS varchar) \
                            ORDER BY avg_wall_time desc;",
                "columns":['upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries']+TIME_COLUMNS,
                "schema":{
                    "merge_on_cols" : ["upt_batch"],
                    "compare_cols":["total_queries"]+AVG_COMPARE_TIME_COLUMNS+TOTAL_COMPARE_TIME_COLUMNS,
                }
            },
            "Time taken by queries by each source":{
                "query" :  f"select \
                                source,\
                                count(*) as total_queries,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
                                COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
                                {TIME_AGGREGATIONS}\
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            group by 1 \
                            order by 7,8;",
                "columns":['source','total_queries','success_count','failure_count','like_queries','regex_queries']+TIME_COLUMNS,
                "schema":{
                    "merge_on_cols" : ["source"],
                    "compare_cols":AVG_COMPARE_TIME_COLUMNS+TOTAL_COMPARE_TIME_COLUMNS,
                }
            },
            "Time taken by queries executed from all sources on an hourly basis":{
                "query" :  f"select \
                                source,\
                                'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                                count(*) as total_queries,\
                                COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
                                COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
                                COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
                                COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
                                {TIME_AGGREGATIONS}\
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            GROUP BY source,'batch-' || CAST(upt_batch AS varchar) \
                            ORDER BY avg_wall_time desc LIMIT 100;",
                "columns":['source','upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries']+TIME_COLUMNS,
                "schema":{
                    "merge_on_cols" : ["source","upt_batch"],
                    "compare_cols":["total_queries"]+AVG_COMPARE_TIME_COLUMNS,
                }
            },
            # "client tag details of failed dags":{
            #     "query" :  "select \
            #                 source,\
            #                 count(*),client_tags,failure_message \
            #                 from presto_query_logs \
            #                 where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
            #                 and query_status='FAILURE' \
            #                 and client_tags like '%dagName%'\
            #                 group by 1,3,4 \
            #                 order by 2 desc;",
            #     "columns":['source','failed_count','client_tags','failure_message'],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
            "Total time taken by each dag":{
                "query" :  f"""WITH dag_summary AS (\
                                    SELECT\
                                    COALESCE(\
                                        REGEXP_EXTRACT(client_tags, '\\"dagName\\": \\"([^,}}]+)\\"', 1),\
                                        'Unknown'\
                                    ) AS dagName,\
                                    COUNT(*) AS total_count, \
                                    {TIME_AGGREGATIONS}\
                                    FROM presto_query_logs\
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and \
                                    client_tags NOT LIKE '%SCHEDULED_GLOBAL_TAG_RULE%' \
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                                    GROUP BY 1 
                                ),
                                scheduled_global_tag_rule_summary AS (\
                                    SELECT\
                                    'SCHEDULED_GLOBAL_TAG_RULE' AS dagName,\
                                    COUNT(*) AS total_count, \
                                    {TIME_AGGREGATIONS}\
                                    FROM presto_query_logs\
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and \
                                    client_tags LIKE '%SCHEDULED_GLOBAL_TAG_RULE%'\
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                                    GROUP BY 1 
                                )\
                                SELECT * FROM dag_summary\
                                UNION ALL\
                                SELECT * FROM scheduled_global_tag_rule_summary\
                                ORDER BY avg_wall_time DESC LIMIT 100;\
                            """,
                "columns":['dagName','total_count']+TIME_COLUMNS,
                "schema":{
                    "merge_on_cols" : ["dagName"],
                    "compare_cols":["total_count"]+AVG_COMPARE_TIME_COLUMNS,
                }
            },
            "Total time taken by each dag in each upt_batch":{
                "query" :  f"""WITH dag_summary AS (\
                                    SELECT
                                    COALESCE(
                                        REGEXP_EXTRACT(client_tags, '\\"dagName\\": \\"([^,}}]+)\\"', 1),
                                        'Unknown'
                                    ) AS dagName,upt_batch,
                                    COUNT(*) AS total_count, \
                                    {TIME_AGGREGATIONS}\
                                    FROM presto_query_logs
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and
                                    client_tags NOT LIKE '%SCHEDULED_GLOBAL_TAG_RULE%' 
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
                                    GROUP BY 1,2
                                ),
                                scheduled_global_tag_rule_summary AS (\
                                    SELECT
                                    'SCHEDULED_GLOBAL_TAG_RULE' AS dagName,upt_batch,
                                    COUNT(*) AS total_count, \
                                    {TIME_AGGREGATIONS}\
                                    FROM presto_query_logs
                                    WHERE client_tags IS NOT NULL and client_tags like '%dagName%' and
                                    client_tags LIKE '%SCHEDULED_GLOBAL_TAG_RULE%' 
                                    and upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
                                    GROUP BY 1,2
                                )\
                                SELECT * FROM dag_summary\
                                UNION ALL\
                                SELECT * FROM scheduled_global_tag_rule_summary\
                                ORDER BY avg_wall_time DESC LIMIT 150;\
                            """,
                "columns":['dagName','upt_batch','total_count']+TIME_COLUMNS,
                "schema":{
                    "merge_on_cols" : ["dagName","upt_batch"],
                    "compare_cols":["total_count"]+AVG_COMPARE_TIME_COLUMNS,
                }
            },

            # "Total time taken by each non-dag query":{
            #     "query" :  """SELECT
            #                 COALESCE(
            #                     source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryType\\":\\"([^,}]+)\\"', 1),source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryName\\":\\"([^,}]+)\\"', 1),source  ,
            #                     'Unknown'
            #                 ) AS query_type_or_name,
            #                 COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , sum(CAST(analysis_time as bigint)) as total_analysis_time, sum(queued_time) as total_queued_time
            #                 FROM presto_query_logs
            #                 WHERE client_tags IS NOT NULL and client_tags not like '%dagName%' and 
            #                 upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
            #                 GROUP BY 1 order by 3 desc;""",
            #     "columns":['query_type_or_name','total_count','total_wall_time','total_cpu_time','total_analysis_time','total_queued_time'],
            #     "schema":{
            #         "merge_on_cols" : ["query_type_or_name"],
            #         "compare_cols":["total_count","total_wall_time",'total_queued_time','total_cpu_time','total_analysis_time'],
            #     }
            # },

            #delete this table after 2 sprints
            # "Time taken by etl-jobs queries on an hourly basis":{
            #     "query" :  "select \
            #                     'day-' || CAST(upt_day AS varchar) AS upt_day,\
            #                     'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
            #                     count(*) as total_queries,\
            #                     COUNT(CASE WHEN query_status = 'SUCCESS' THEN 1 END) as success_count,\
            #                     COUNT(CASE WHEN query_status = 'FAILURE' THEN 1 END) as failure_count,\
            #                     COUNT(CASE WHEN query_text LIKE '%like%' THEN 1 END) AS like_queries,\
            #                     COUNT(CASE WHEN query_text LIKE '%regex%' THEN 1 END) AS regex_queries,\
            #                     SUM(CAST(wall_time AS bigint)) AS total_wall_time,\
            #                     SUM(CAST(queued_time AS bigint)) AS total_queued_time,\
            #                     SUM(CAST(cpu_time AS bigint)) AS total_cpu_time,\
            #                     SUM(CAST(analysis_time AS bigint)) AS total_analysis_time\
            #                 from presto_query_logs \
            #                 where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
            #                 and source='etl-jobs'\
            #                 GROUP BY 'day-' || CAST(upt_day AS varchar), 'batch-' || CAST(upt_batch AS varchar) \
            #                 ORDER BY upt_day, upt_batch;",
            #     "columns":['upt_day','upt_batch','total_queries','success_count','failure_count','like_queries','regex_queries','total_wall_time','total_queued_time','total_cpu_time','total_analysis_time'],
            #     "schema":{
            #         "merge_on_cols" : ["upt_batch"],
            #         "compare_cols":["total_wall_time"],
            #     }
            # },
            #delete this table after 2 sprints
            # "Total time taken by each non-dag query in each upt_batch":{
            #     "query" :  """SELECT
            #                 COALESCE(
            #                     source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryType\\":\\"([^,}]+)\\"', 1),source || '-' || REGEXP_EXTRACT(client_tags, '\\"queryName\\":\\"([^,}]+)\\"', 1),source  ,
            #                     'Unknown'
            #                 ) AS query_type_or_name,upt_day,upt_batch,
            #                 COUNT(*) AS total_count, sum(wall_time) as total_wall_time, sum(cpu_time) as total_cpu_time , sum(CAST(analysis_time as bigint)) as total_analysis_time, sum(queued_time) as total_queued_time
            #                 FROM presto_query_logs
            #                 WHERE client_tags IS NOT NULL and client_tags not like '%dagName%' and 
            #                 upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
            #                 GROUP BY 1,2,3 order by 5 desc;""",
            #     "columns":['query_type_or_name','upt_day','upt_batch','total_count','total_wall_time','total_cpu_time','total_analysis_time','total_queued_time'],
            #     "schema":{
            #         "merge_on_cols" : ["query_type_or_name","upt_batch"],
            #         "compare_cols":["total_wall_time"],
            #     }
            # },
            
            f"Top {limit} slowest queries sorted by analysis time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(analysis_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            f"Top {limit} slowest queries sorted by cpu time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(cpu_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            f"Top {limit} slowest queries sorted by wall time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(wall_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            f"Top {limit} queries with high queued time":{
                "query" :  f"select \
                            source,\
                            client_tags,\
                            'day-' || CAST(upt_day AS varchar) AS upt_day,'batch-' || CAST(upt_batch AS varchar) AS upt_batch,\
                            analysis_time,cpu_time,queued_time,wall_time,schema,query_operation,query_status,failure_message \
                            from presto_query_logs \
                            where upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'\
                            order by CAST(queued_time AS bigint) desc \
                            limit {limit};",
                "columns":['source','client_tags','upt_day','upt_batch','analysis_time','cpu_time','queued_time','wall_time','schema','query_operation','query_status','failure_message'],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            "Distribution of time taken by all the queries from each source" : {
                "query" :  get_full_query("complete_table")[0],
                "columns": get_full_query("complete_table")[1],
                "schema":{
                    "merge_on_cols" : [],
                    "compare_cols":[],
                }
            },
            # "Distribution of time taken by all the queries" : {
            #     "query" :  get_full_query("all")[0],
            #     "columns":get_full_query("all")[1],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
            # "Distribution of time taken by all the DAGs" : {
            #     "query" :  get_full_query("dag")[0],
            #     "columns":get_full_query("dag")[1],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
            # "Distribution of time taken by all non-DAGs" : {
            #     "query" :  get_full_query("nondag")[0],
            #     "columns":get_full_query("nondag")[1],
            #     "schema":{
            #         "merge_on_cols" : [],
            #         "compare_cols":[],
            #         "do_not_compare":True
            #     }
            # },
          }
    
    def fetch_trino_results(self):
        save_dict={}       
        commands = self.get_trino_commands()
        for heading,value in commands.items():
            raw_command=value['query']
            columns=value['columns']
            schema = value["schema"]
            query = raw_command.replace("<start_utc_str>",self.start_utc_str).replace( "<end_utc_str>", self.end_utc_str)
            print(f"\n************************** {heading} ************************ :\n {query}")
            output= execute_trino_query(self.dnode,query)
            # if not output or output.strip()=="":
            #     raise RuntimeError(f"ERROR : command output is empty. Check if trino @ {self.dnode} is in good state. Terminating program ...")
            stringio = StringIO(output)
            df = pd.read_csv(stringio, header=None, names=columns)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
            print("Numeric columns : " , numeric_cols)
            print("Non-Numeric columns : " , non_numeric_cols)

            fill_values = {}
            fill_values.update({col: 0 for col in numeric_cols})
            fill_values.update({col: "NaN" for col in non_numeric_cols})

            df = df.fillna(fill_values)
            # integer_columns = df.select_dtypes(include='int').columns
            # string_columns = df.select_dtypes(include='object').columns
            # new_row=dict([(int_col,df[int_col].sum()) for int_col in integer_columns])
            # new_row.update(dict([(str_col,"TOTAL") for str_col in string_columns]))
            # df = df._append(new_row, ignore_index=True)
            if df.empty: continue
            df = df.head(168)
            print(df)
            try:
                df["query_operation"] = df["query_operation"].astype(str)
            except:
                pass
            # df.to_csv("152_"+heading+".csv")
            save_dict[heading] = {
                "schema":schema,
                "table":df.to_dict(orient="records")
            }

        return save_dict
    
if __name__=='__main__':
    print("Testing trino queries analysis ...")
    from settings import stack_configuration

    start_time_str_ist = "2024-06-22 00:00"
    load_duration_in_hrs=24
    
    calc = TRINO_ANALYSE(stack_obj=stack_configuration('s1_nodes.json',start_time_str_ist,load_duration_in_hrs))
    trino_queries = calc.fetch_trino_results()
    import pandas as pd
    from pymongo import MongoClient

    # Create a sample DataFrame
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Osquery_LoadTests']  # Replace 'your_database_name' with your actual database name
    collection = db['Testing']  # Replace 'your_collection_name' with your actual collection name

    collection.insert_one({"data":trino_queries})