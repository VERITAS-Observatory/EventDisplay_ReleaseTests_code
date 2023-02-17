# run epoch wise anasum analysis
# for all zenith angles and background models

if [[ $# < 2 ]]; then
echo "
   ./anasum_yearly_all.sh <runparameter file> <SUB/FFF>
   --> Step 1 to analyse run-wise with anasum (SUB)
   --> Step 2 to combine anasum file (FFF)
"
exit
fi

RPARA=${1}
COM=${2}
  
# for N in "0.5deg" ""  LZE_0.5deg MZE_0.5deg SZE_0.5deg SZE MZE LZE WOBBLE
for N in "0.5deg" ""  LZE_0.5deg MZE_0.5deg SZE_0.5deg
do
   for R in IGNOREACCEPTANCE
   do 
      ./anasum_yearly.sh ${RPARA} ${COM} "${N}" "${R}"
   done
done
