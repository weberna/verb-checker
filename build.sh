#!/bin/bash
#build and run the java file passed in with CoreNLP dependencies
noext="`basename $1 .java`"
echo "`javac -cp /home/user/reu2015/programs/stanford-corenlp/*:. $1`" #compile 
echo "`java -cp /home/user/reu2015/programs/stanford-corenlp/*:. $noext`"
