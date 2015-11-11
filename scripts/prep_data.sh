#!/bin/bash
#Run through pipeline of processes to create data needed to use classifier
#Prerequistie data needed:
#	Need to have text and delimited text version for 
#	both training and testing fce data as well as the standford pos xml versions for them
#In this file:
#	trainout.xml = filename of stanford xml version of training fce text data
#	trainout_delim.xml = filename stanford xml version of training fce delimited text

#mallet_path should equal your /relative/path/to/mallet/bin/mallet so replace as needed
mallet_path="mallet/bin/mallet"

#The step BELOW takes the longest, to save time, this step serializes the list of Sentence objects
#Only need to do this step if training data is changed
#in trainout_delim.p and future steps just load this data (using Pickle module)
#echo "`python process_data.py prep temp.xml trainout_delim.xml trainout_delim.p`"

#Create instance file for training
echo "`python process_data.py training trainout_delim.in trainout_delim.p`"
#convert instance file to mallet form and then train
echo "`$mallet_path import-file --input trainout_delim.in --output trainout_delim.mallet`"
echo "`$mallet_path train-classifier --input trainout_delim.mallet --output-classifier classifier --trainer MaxEnt --random-seed 0`"
#Same with first step, but with testing data, only nneds to be done is testing data is changed
#echo "`python process_data.py prep testout.xml testout_delim.xml testout_delim.p`"
#Create testing instances, put correct and original labels in seperate files
echo "`python process_data.py testing testout_delim.in corrlabels origlabels testout_delim.p`"

#use run_combinined.sh to run classifier useing the data produced by this script
