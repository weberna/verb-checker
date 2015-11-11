#!/bin/bash
#build and run the java file passed in with Mallet dependencies
#to run do ./run-classifier.sh VChainClassifier.java instance_file where_to_print_output classifier_file original_label_file
#classpath variable should be equal to /full/path/to/mallet/class and /full/path/to/mallet/lib/mallet-deps.jar
#make sure to include working directory in classpath (seperate paths with ':')
classpath="/home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:."

noext="`basename $1 .java`"
echo "`javac -cp $classpath $1`"	#Compile 
echo "`java -cp $classpath $noext --instances $2 --output $3 --classifier $4 --origlabels $5`"  #Run

#to evaluate results, use python eval_results.py resultsfile correctlabels origlabels
