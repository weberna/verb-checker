#!/bin/bash
#build and run the java file passed in with Mallet dependencies
classpath="/home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:."
noext="`basename $1 .java`"
echo "`javac -cp $classpath $1`"	#Compile 
echo "`java -cp $classpath $noext --input $2 --output - --classifier $3`"  #Run
