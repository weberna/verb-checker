#!/bin/bash
echo "`javac -cp /home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:. VerbTagger.java ResultsEvaluator.java`"
echo "`java -cp /home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:. VerbTagger --include-input true --output-file labels.lab --model-file $1 $2`"
#echo "`java -cp /home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:. VerbTagger --model-file $1 $2`"
