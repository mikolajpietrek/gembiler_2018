rm tests/*.mr 2>/dev/null
rm errors/*.mr 2>/dev/null

if [ "$1" == "tests" ] ; then
	path="tests"
elif [ "$1" == "errors" ] ; then
	path="errors"
else
	echo "uruchamianie: podaj 'tests' lub 'errors' jako parametr"
	exit 1
fi

for FILE in $path/*.imp; do
	printf '\n%.0s' {1..20}
	#tput reset
	echo $FILE
	echo
	FN="${FILE%%.*}"
	cat "$FN.imp"
	python3 kompilator.py "$FN.imp" "$FN.mr"
	./_exercise/maszyna-rejestrowa-cln "$FN.mr"
	read -p "Nacisnij dowolny klawisz, aby testowac dalej... " -n1 -s
done

echo