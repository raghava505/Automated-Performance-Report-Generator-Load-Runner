#!/bin/bash
logs_path="~/multi-customer-cqsim/gcp/logs"
total_sum=0
total_sum2=0
total_sum3=0

for i in s4simhost1b s4simhost1d s4simhost2b s4simhost2d s4simhost3b s4simhost3d s4simhost4b s4simhost4d s4simhost5b s4simhost5d s4simhost6b s4simhost6d;
do
    result=$(ssh abacus@$i "cd $logs_path;
                            tail -100 \"\$(ls -trh | tail -1)\" | awk '/Total no\.of events happened till now :/ {sum+=\$NF} END {print sum}'")
    ((total_sum += result))

    result2=$(ssh abacus@$i "cd $logs_path;
                            tail -100 \"\$(ls -trh | tail -1)\" | awk '/Total no\.of modified events happened during load:/ {sum+=\$NF} END {print sum}'")
    ((total_sum2 += result2))

    result3=$(ssh abacus@$i "cd $logs_path;
                            tail -100 \"\$(ls -trh | tail -1)\" | awk '/Total no\.of inventory events happened during load:/ {sum+=\$NF} END {print sum}'")
    ((total_sum3 += result3))
done

# Formatting function to display counts in millions
format_in_millions() {
    printf "%.2f million" $(echo "scale=2; $1 / 1000000" | bc)
}

echo "Total inventory count: $(format_in_millions $total_sum3)"
echo "Total inventory count / hour: $(format_in_millions $(($total_sum3 / 12)))"
echo ""
echo "Total cloud log events count: $(format_in_millions $total_sum2)"
echo "Total cloud log events count / hour: $(format_in_millions $(($total_sum2 / 12)))"
echo ""
echo "Total count: $(format_in_millions $total_sum)"
echo "Total count / hour: $(format_in_millions $(($total_sum / 12)))"
echo ""
ratio=$(bc <<< "scale=2; $total_sum2 / $total_sum3")
echo "Ratio (inventory:events): 1:$ratio"

