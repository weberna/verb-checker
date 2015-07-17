#!/bin/bash
echo "`java -cp /home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:. cc.mallet.fst.SimpleTagger --train true --fully-connected false --model-file $1 $2`"
#echo "`java -cp /home/user/reu2015/programs/mallet/class:/home/user/reu2015/programs/mallet/lib/mallet-deps.jar:. cc.mallet.fst.SimpleTagger --train true --model-file $1 $2`"
