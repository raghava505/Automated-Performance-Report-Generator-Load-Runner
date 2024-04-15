time_ranges = {
    "below_20s":[0,20000],
    "between_20s_and_40s":[20000,40000],
    "between_40s_and_60s":[40000,60000],
    "between_60s_and_80s":[60000,80000],
    "between_80s_and_100s":[80000,100000],
    "between_100s_and_120s":[100000,120000],
    "between_120s_and_140s":[120000,140000],
    "between_140s_and_160s":[140000,160000],
    "between_160s_and_180s":[160000,180000],
    "between_180s_and_200s":[180000,200000],
    "above_200s":[200000,10000000000],
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

    complete_query=f"""
            SELECT 
            metric,
            {var1} FROM ({var2}) t GROUP BY metric order by 1;            
            """
    return complete_query