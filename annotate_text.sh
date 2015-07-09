#!/bin/bash
#echo "`java -cp /home/user/reu2015/programs/stanford-corenlp/*:. -Xmx2g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,depparse -file $1`"
echo "`java -cp /home/user/reu2015/programs/stanford-corenlp/*:. -Xmx3g edu.stanford.nlp.pipeline.StanfordCoreNLP [ -props annotate_properties.prop ] -file $1`"
