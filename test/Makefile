

all:
	rm -rf test.cpp
	python3 ../schemec/examples.py > test.cpp
	g++-4.7 -O2 -Wall -g -std=c++11 -o test test.cpp
