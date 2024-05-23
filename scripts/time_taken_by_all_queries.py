time_ranges = {
    "below_1ms":[0,1],
    "between_1ms_and_5ms":[1,5],
    "between_5ms_and_50ms":[5,50],
    "between_50ms_and_500ms":[50,500],
    "between_500ms_and_1s":[500,1000],
    "between_1s_and_10s":[1000,10000],
    "above_10s":[10000,10000000000],
}

base_query_for_all = """
            SELECT
                '{}_time' AS metric,
                {}
            FROM presto_query_logs
            WHERE upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
        """

base_query_for_dags = """
            SELECT
                '{}_time' AS metric,
                {}
            FROM presto_query_logs
            WHERE upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>' and client_tags like '%dagName%'
        """

base_query_for_nondags = """
            SELECT
                '{}_time' AS metric,
                {}
            FROM presto_query_logs
            WHERE upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>' and client_tags not like '%dagName%'
        """

base_query_for_complete_table = """
            SELECT
                source,
                '{}_time' AS metric,
                {}
            FROM presto_query_logs
            WHERE upt_time > timestamp '<start_utc_str>' and upt_time < timestamp '<end_utc_str>'
            group by 1
        """
time_types = ["queued","analysis","cpu","wall"]


def get_query_single_type(time_type,tag):
    var2=""
    for key,val in time_ranges.items():
        var2+=f"SUM(CASE WHEN CAST({time_type}_time AS bigint) BETWEEN {val[0]} AND {val[1]} THEN 1 ELSE 0 END) AS \"{key}\",\n"
    var2 = var2[:-2]
    if tag=="all":
        return base_query_for_all.format(time_type,var2)
    elif tag=="dag":
        return base_query_for_dags.format(time_type,var2)
    elif tag=="nondag":
        return base_query_for_nondags.format(time_type,var2)
    elif tag=="complete_table":
        return base_query_for_complete_table.format(time_type,var2)

def get_full_query(tag):
    var1=""
    for key in time_ranges.keys():
        var1 += f"""SUM("{key}") AS "{key}",\n"""
    var1=var1[:-2]

    var2=""
    for i,time_type in enumerate(time_types):
        var2+=get_query_single_type(time_type,tag)
        if i+1 != len(time_types):
            var2+="\n UNION ALL \n"
    if tag=="complete_table":
        complete_query=f"""
            SELECT 
            source,
            metric,
            {var1} FROM ({var2}) t GROUP BY 1,2 order by 1,2;            
            """
        columns = ['source','metric']+list(time_ranges.keys())
    else:
        complete_query=f"""
                SELECT 
                metric,
                {var1} FROM ({var2}) t GROUP BY metric order by 1;            
                """
        columns = ['metric']+list(time_ranges.keys())
    return complete_query,columns