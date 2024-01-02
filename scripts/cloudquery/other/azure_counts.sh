#!/bin/bash
logs_path="~/cloud_query_sim/azure_multi/logs"
total_sum=0
total_sum2=0
total_sum3=0

for i in long-azure-sim1;
do
    result=$(ssh abacus@$i "cd $logs_path;
                            tail -10 \"\$(ls -trh | tail -1)\" | awk '/Total no\.of events happened till now:/ {sum+=\$NF} END {print sum}'")
    ((total_sum += result))
    
    result2=$(ssh abacus@$i "cd $logs_path;
                            tail -10 \"\$(ls -trh | tail -1)\" | awk '/Total no\.of modified events happened till now:/ {sum+=\$NF} END {print sum}'")
    ((total_sum2 += result2))

    result3=$(ssh abacus@$i "cd $logs_path;
                            tail -10 \"\$(ls -trh | tail -1)\" | awk '/Total no\.of inventory events happened till now:/ {sum+=\$NF} END {print sum}'")
    ((total_sum3 += result3))
done

# Formatting functions to display counts in millions
format_in_millions() {
    printf "%.2f million" $(echo "scale=2; $1 / 1000000" | bc)
}

echo "Total inventory count: $(format_in_millions $total_sum3)"
echo "Total inventory count / hour: $(format_in_millions $(($total_sum3 / 12)))"
echo ""
echo "Total cloud trail events count: $(format_in_millions $total_sum2)"
echo "Total cloud trail events count / hour: $(format_in_millions $(($total_sum2 / 12)))"
echo ""
echo "Total count: $(format_in_millions $total_sum)"
echo "Total count / hour: $(format_in_millions $(($total_sum / 12)))"
echo ""
echo "Ratio (inventory:events): 1:$(($total_sum2 / $total_sum3))"

