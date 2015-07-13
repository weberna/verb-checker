/* Copyright (C) 2003 University of Pennsylvania.
   This file is part of "MALLET" (MAchine Learning for LanguagE Toolkit).
   http://www.cs.umass.edu/~mccallum/mallet
   This software is provided under the terms of the Common Public License,
   version 1.0, as published by http://www.opensource.org.  For further
   information, see the file `LICENSE' included with this distribution. */

/* A hacked together modification of mallet's SimpleTagger program 
	much of the code is similar/copied exactly (the reason being the
	SimpleTagger program cannot be extended). Most changes are in the 
	apply() method and the end of the main method.
	Note that this program does not do training, so do your training with 
	the SimpleTagger program
*/
	
import cc.mallet.fst.*;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Reader;
import java.io.BufferedReader;
import java.io.FileReader;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.List;
import java.util.Random;
import java.util.logging.Logger;
import java.util.regex.Pattern;

import cc.mallet.types.Alphabet;
import cc.mallet.types.AugmentableFeatureVector;
import cc.mallet.types.ArraySequence;
import cc.mallet.types.FeatureVector;
import cc.mallet.types.FeatureVectorSequence;
import cc.mallet.types.Instance;
import cc.mallet.types.InstanceList;
import cc.mallet.types.LabelAlphabet;
import cc.mallet.types.LabelSequence;
import cc.mallet.types.Sequence;
import cc.mallet.types.SequencePairAlignment;

import cc.mallet.pipe.Pipe;
import cc.mallet.pipe.iterator.LineGroupIterator;

import cc.mallet.util.CommandOption;
import cc.mallet.util.MalletLogger;


public class VerbTagger {
	
	public static final double THRESHOLD = 1.0;

	private static Logger logger =
		MalletLogger.getLogger(VerbTagger.class.getName());

	private VerbTagger() {
	}

	private static final CommandOption.String testOption = new CommandOption.String
		(VerbTagger.class, "test", "lab or seg=start-1.continue-1,...,start-n.continue-n",
		 true, null,
		 "Test measuring labeling or segmentation (start-i, continue-i) accuracy", null);

	private static final CommandOption.File modelOption = new CommandOption.File
		(VerbTagger.class, "model-file", "FILENAME", true, null,
		 "The filename for reading (train/run) or saving (train) the model.", null);

	private static final CommandOption.Integer nBestOption = new CommandOption.Integer
		(VerbTagger.class, "n-best", "INTEGER", true, 1,
		 "How many answers to output", null);
	
	private static final CommandOption.Integer cacheSizeOption = new CommandOption.Integer
		(VerbTagger.class, "cache-size", "INTEGER", true, 100000,
		 "How much state information to memoize in n-best decoding", null);
	
	private static final CommandOption.Boolean includeInputOption = new CommandOption.Boolean
		(VerbTagger.class, "include-input", "true|false", true, false,
		 "Whether to include the input features when printing decoding output", null);

	private static final CommandOption.File outputFileOption = new CommandOption.File
		(VerbTagger.class, "output-file", "FILENAME", true, null,
		 "File that contains the current (and possibly incorrect) verb labels for the data", null);

	private static final CommandOption.List commandOptions =
		new CommandOption.List (
								"Testing and running a generic tagger.",
								new CommandOption[] {
									testOption,
									modelOption,
									nBestOption,
									cacheSizeOption,
									includeInputOption,
									outputFileOption

								});


	/**
	 * Test a transducer on the given test data, evaluating accuracy
	 * with the given evaluator
	 *
	 * @param model a <code>Transducer</code>
	 * @param eval accuracy evaluator
	 * @param testing test data
	 */
	public static void test(TransducerTrainer tt, TransducerEvaluator eval,
							InstanceList testing) {
		eval.evaluateInstanceList(tt, testing, "Testing");
	}

	/**
	 * Apply a transducer to an input sequence to produce the k highest-scoring
	 * output sequences.
	 *
	 * @param model the <code>Transducer</code>
	 * @param input the input sequence
	 * @param k the number of answers to return
	 * @return array of the k highest-scoring output sequences
	 */
	public static Sequence[] apply(Transducer model, Sequence input, int k) {
		Sequence[] answers;
		if (k == 1) {
			answers = new Sequence[1];
			answers[0] = model.transduce (input);
		}
		else {
			MaxLatticeDefault lattice =
				new MaxLatticeDefault (model, input, null, cacheSizeOption.value());

			answers = lattice.bestOutputSequences(k).toArray(new Sequence[0]);
		}

		return answers;
	}

	/* Convience method that does all that is needed in one go,
		finds both the absolute best sequence, as well as its weight, and
		the weight of the original sequence inputed in.
		@ret:
			An ArrayList of SequencePairAlignments (ie a structure that holds the output sequence and its weight)
			The first element of the return value is the original output/weight, the second element is the best output/weight
	*/
	public static ArrayList<SequencePairAlignment<Object, Object>> getAllSequenceData(Transducer model, Sequence input, Sequence origOut) {
			ArrayList<SequencePairAlignment<Object, Object>> ret = new ArrayList<SequencePairAlignment<Object, Object>>(2);
			MaxLatticeDefault bestLattice= 	
				new MaxLatticeDefault (model, input, null, cacheSizeOption.value());
			MaxLatticeDefault origLattice= 	
				new MaxLatticeDefault (model, input, origOut, cacheSizeOption.value());
			List<SequencePairAlignment<Object, Object>> newOut = bestLattice.bestOutputAlignments(1);
			List<SequencePairAlignment<Object, Object>> oldOut = origLattice.bestOutputAlignments(1);
			ret.add(oldOut.get(0));
			ret.add(newOut.get(0));
			return ret;
	}
	
	public static double getSequenceWeight(Transducer model, Sequence input, Sequence output) {
		MaxLatticeDefault lattice =
			new MaxLatticeDefault (model, input, output, cacheSizeOption.value());

			List<SequencePairAlignment<Object, Object>> result= lattice.bestOutputAlignments(1);
			String name = output.get(output.size()-1).toString();	
			double weight = result.get(0).getWeight(); //score achieved by running through given output states

			weight += model.getState(model.stateIndexOfString(name)).getFinalWeight();	//add in final weight
			return weight;
	}
	/*
		Find the best sequence including the final weight	
	*/
	public static Sequence getBestSequence(Transducer model, Sequence input) {
		int k = 3; //how many of the top sequences to compare
		int bestIndex = 0; //index into answers holds the best seq
		double bestWeight = 0;
		Sequence[] answers;		
		MaxLatticeDefault lattice = 
			new MaxLatticeDefault(model, input, null, cacheSizeOption.value());
		List<SequencePairAlignment<Object, Object>> bestSeqs = lattice.bestOutputAlignments(k);
		answers = lattice.bestOutputSequences(k).toArray(new Sequence[0]);
		for(int i = 0; i < k; i++) {
			double weight = bestSeqs.get(i).getWeight(); //weight before final state weight added in
			String name = answers[i].get(input.size()-1).toString(); 
			weight += model.getState(model.stateIndexOfString(name)).getFinalWeight();	//add in final weight
			if(weight > bestWeight) {
				bestWeight = weight;	
				bestIndex = i;
			}
		}
		return answers[bestIndex];
	}

	/* Read the output file and return the sequences of verbs for each sentence, these
		can be passed into a MaxLattice in order to find the weight of the current labels
		in order to decide if they need to be corrected
	*/
	public static ArrayList<String>	readOutputFile(File f) {
		ArrayList<String> ret = new ArrayList<String>();
		try {
			BufferedReader outfile = new BufferedReader(new FileReader(f));
			String foo = outfile.readLine();
			while(foo != null) {
				ret.add(foo);
				foo = outfile.readLine();
			}
		} catch(java.io.FileNotFoundException e) {
			System.err.println("Could not find file " + e.getMessage());
		} catch(java.io.IOException e) {
			System.err.println(e.getMessage());
		}
		return ret;
	}

	public static void main (String[] args) throws Exception {
		Reader trainingFile = null, testFile = null;
		InstanceList trainingData = null, testData = null;
		int numEvaluations = 0;
		int iterationsBetweenEvals = 16;
		int restArgs = commandOptions.processOptions(args);
		ArrayList<ArraySequence<String>> outSeqs = null;

		if (restArgs == args.length) {
			commandOptions.printUsage(true);
			throw new IllegalArgumentException("Missing data file(s)");
		}
		testFile = new FileReader(new File(args[restArgs]));
		Pipe p = null;
		CRF crf = null;
		TransducerEvaluator eval = null;

		if (modelOption.value == null) {
			commandOptions.printUsage(true);
			throw new IllegalArgumentException("Missing model file option");
		}
		ObjectInputStream s =    //read crf file
			new ObjectInputStream(new FileInputStream(modelOption.value));
		crf = (CRF) s.readObject();
		s.close();
		p = crf.getInputPipe();
		
		if(outputFileOption.value != null) {  //read the output sequence file and put them into correct format to be read by crf
			ArrayList<String> strseq = readOutputFile(outputFileOption.value);
			Iterator iter = strseq.iterator();
			int sentences = 0;
			while(iter.hasNext()) {	 //find the number of sentences in the data in order to allocate size to outSeqs
				String str = iter.next().toString();
				if(str.equals("") || !iter.hasNext()) { //reached delimiter or end of input
					sentences += 1;
				}
			}
			outSeqs = new ArrayList<ArraySequence<String>>(sentences);
			if(crf != null) {
				ListIterator liter = strseq.listIterator();
				ArrayList<String> senSeq = new ArrayList<String>(); //holds a single sentence
				int senIndex = 0;
				while(liter.hasNext()) {
					int index = liter.nextIndex();
					String sname = liter.next().toString(); //state name
					if(sname.equals("")) { //end of sentence, add the sequence to outSeqs and clear the sentence array
						String[] temp = new String[senSeq.size()];
						outSeqs.add(new ArraySequence<String>(senSeq.toArray(temp))); //add sentence
						senSeq.clear();  
					}
					else { //add token to sentence 
						senSeq.add(sname);
						if(!liter.hasNext()) { //incase there is no empty line at the end
							String[] temp = new String[senSeq.size()];
							outSeqs.add(new ArraySequence<String>(senSeq.toArray(temp))); //add sentence
						}
					}
				}
			}
			else {
				System.err.println("No CRF file"); 		
			}
		}
	
		if (testOption.value != null) {
			p.setTargetProcessing(true);
			testData = new InstanceList(p);
			testData.addThruPipe(new LineGroupIterator(testFile,
													   Pattern.compile("^\\s*$"), true));
		}
		else {
				p.setTargetProcessing(false);
				testData = new InstanceList(p);
				testData.addThruPipe(
									 new LineGroupIterator(testFile,
														   Pattern.compile("^\\s*$"), true));
		}
		logger.info ("Number of predicates: "+p.getDataAlphabet().size());
    
		if (testOption.value != null) {
			if (testOption.value.startsWith("lab")) {
					eval = new ResultsEvaluator(new InstanceList[] {trainingData, testData}, new String[] {"Training", "Testing"});
			}
			else if (testOption.value.startsWith("seg=")) {
				String[] pairs = testOption.value.substring(4).split(",");
				if (pairs.length < 1) {
					commandOptions.printUsage(true);
					throw new IllegalArgumentException
						("Missing segment start/continue labels: " + testOption.value);
				}
				String startTags[] = new String[pairs.length];
				String continueTags[] = new String[pairs.length];

				for (int i = 0; i < pairs.length; i++) {
					String[] pair = pairs[i].split("\\.");
					if (pair.length != 2) {
						commandOptions.printUsage(true);
						throw new
							IllegalArgumentException
							("Incorrectly-specified segment start and end labels: " + pairs[i]);
					}
					startTags[i] = pair[0];
					continueTags[i] = pair[1];
				}
				eval = new MultiSegmentationEvaluator(new InstanceList[] {trainingData, testData}, new String[] {"Training", "Testing"}, 
													  startTags, continueTags);
			}
			else {
					commandOptions.printUsage(true);
					throw new IllegalArgumentException("Invalid test option: " +
													   testOption.value);
			}
		}

		if (p.isTargetProcessing()) {
			Alphabet targets = p.getTargetAlphabet();
			StringBuffer buf = new StringBuffer("Labels:");
			for (int i = 0; i < targets.size(); i++)
				buf.append(" ").append(targets.lookupObject(i).toString());
			logger.info(buf.toString());
		}
		if (eval != null) { //TEST CRF 
			test(new NoopTransducerTrainer(crf), eval, testData);
		}
		else {  //RUN CRF 
			boolean includeInput = includeInputOption.value();
			for (int i = 0; i < testData.size(); i++) {
				Sequence input = (Sequence)testData.get(i).getData();  
				Sequence[] outputs;
				if(outSeqs != null) {
					outputs = new Sequence[1];
					ArrayList<SequencePairAlignment<Object, Object>> seqData = getAllSequenceData(crf, input, outSeqs.get(i));
					SequencePairAlignment<Object, Object> origOut = seqData.get(0);
					SequencePairAlignment<Object, Object> bestOut = seqData.get(1);
					if(origOut.output().size() != bestOut.output().size()) {
						System.err.println("There was an error getting the sequences");
					}
					/*	check if the difference between sequence weights is great enough to justify 
					  making the correction in the text
					*/
					if(bestOut.getWeight() - origOut.getWeight() < THRESHOLD) { 
						outputs[0] = origOut.output();  //no big enough change, make no corrections(use original) 
			//System.out.println("ORIGINAL");	
					}
					else {
						outputs[0] = bestOut.output(); //make the correction (use best sequence)
			//	System.out.println("BEST");
					}
				}
				else {
			//		System.out.println("TESTING");
					outputs = apply(crf, input, nBestOption.value); 
				}

				int k = outputs.length;
				boolean error = false;
				for (int a = 0; a < k; a++) {
					if (outputs[a].size() != input.size()) {
						logger.info("Failed to decode input sequence " + i + ", answer " + a);
						error = true;
					}
				}
				if (! error) {
					for (int j = 0; j < input.size(); j++) {
						StringBuffer buf = new StringBuffer();
						for (int a = 0; a < k; a++) {
							buf.append(outputs[a].get(j).toString()).append(" ");
						}
						if (includeInput) {
							FeatureVector fv = (FeatureVector)input.get(j);
							buf.append(fv.toString(true));                
						}
						System.out.println(buf.toString());
					}
					System.out.println();
				} 
				
			}
		}

		if (trainingFile != null) { trainingFile.close(); }
		if (testFile != null) { testFile.close(); }
	}
}
