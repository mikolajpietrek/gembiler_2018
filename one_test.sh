python3 kompilator.py "$1.imp" "$1.mr"
cat "$1.imp"
./maszyna-rejestrowa-cln "$1.mr"