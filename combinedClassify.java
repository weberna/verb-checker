/* ***************************************************
	combinedClassify
	A classifier that uses both models, modified off 
	Mallet's Csv2Vectors 
****************************************************** */
import java.util.Iterator;
import java.util.logging.*;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.regex.*;
import java.io.*;
import java.nio.charset.Charset;

import cc.mallet.classify.*;
import cc.mallet.pipe.iterator.*;
import cc.mallet.types.*;
import cc.mallet.util.*;


public class combinedClassify {
	
	public static double THRESHOLD = 0.0;
	private static Logger logger = MalletLogger.getLogger(combinedClassify.class.getName());
		//only really need to use first 4 options
	static CommandOption.File inputFile =	new CommandOption.File
		(combinedClassify.class, "input", "FILE", true, null,
		 "The file containing data to be classified, one instance per line", null);

	static CommandOption.File corrInstanceFile =	new CommandOption.File
		(combinedClassify.class, "corr-instances", "FILE", true, null,
		 "The file containing correction data to be classified, one instance per line", null);

	static CommandOption.File outputFile = new CommandOption.File
		(combinedClassify.class, "output", "FILE", true, new File("output"),
		 "Write predictions to this file; Using - indicates stdout.", null);

	static CommandOption.File classifierFile = new CommandOption.File
		(combinedClassify.class, "classifier", "FILE", true, new File("classifier"),
		 "Use the pipe and alphabets from a previously created vectors file.\n" +
		 "   Allows the creation, for example, of a test set of vectors that are\n" +
		 "   compatible with a previously created set of training vectors", null);

	static CommandOption.File corrClassifierFile = new CommandOption.File
		(combinedClassify.class, "corr-classifier", "FILE", true, new File("corr-classifier"),
		 "The classifier file for the correction classifier", null); 

	static CommandOption.File labelFile = new CommandOption.File
		(combinedClassify.class, "labels", "FILE", true, new File("labels"),
		 "File containing the original labels, one per line", null); 
	
	static CommandOption.File testClassifierFile = new CommandOption.File
		(combinedClassify.class, "test-classifier", "FILE", true, new File("test-classifier"),
		 "Use the pipe and alphabets from a previously created vectors file.\n" +
		 "   Allows the creation, for example, of a test set of vectors that are\n" +
		 "   compatible with a previously created set of training vectors", null);

//The default regex assumes some name in the front (first group is name) seperate by space/comma, (second group is data)
	static CommandOption.String lineRegex = new CommandOption.String
		(combinedClassify.class, "line-regex", "REGEX", true, "^(\\S*)[\\s,]*(.*)$",
		 "Regular expression containing regex-groups for label, name and data.", null);
	
	static CommandOption.Integer nameOption = new CommandOption.Integer
		(combinedClassify.class, "name", "INTEGER", true, 1,  //group 1 is name
		 "The index of the group containing the instance name.\n" +
         "   Use 0 to indicate that the name field is not used.", null);

	static CommandOption.Integer dataOption = new CommandOption.Integer
		(combinedClassify.class, "data", "INTEGER", true, 2,  //group 2 is data
		 "The index of the group containing the data.", null);

	static CommandOption.String encoding = new CommandOption.String
		(combinedClassify.class, "encoding", "STRING", true, Charset.defaultCharset().displayName(),
		 "Character encoding for input file", null);
	
	/* Read the output file labels into an array list*/
	public static ArrayList<String>	readOutputFile(File f) {
		ArrayList<String> ret = new ArrayList<String>();
		try {
			BufferedReader outfile = new BufferedReader(new FileReader(f));
			String ln = outfile.readLine();
			while(ln != null) {
				ret.add(ln);
				ln = outfile.readLine();
			}
		} catch(java.io.FileNotFoundException e) {
			System.err.println("Could not find file " + e.getMessage());
		} catch(java.io.IOException e) {
			System.err.println(e.getMessage());
		}
		return ret;
	}
	
	public static void main (String[] args) throws FileNotFoundException, IOException {

		// Process the command-line options
		CommandOption.setSummary (combinedClassify.class,
								  "A tool for classifying a stream of unlabeled instances");
		CommandOption.process (combinedClassify.class, args);
		
		// Print some helpful messages for error cases
		if (args.length == 0) {
			CommandOption.getList(combinedClassify.class).printUsage(false);
			System.exit (-1);
		}
		if (inputFile == null) {
			throw new IllegalArgumentException ("You must include `--input FILE ...' in order to specify a"+
								"file containing the instances, one per line.");
		}
		

	  // Read both classifiers from file
		Classifier classifier = null;
		Classifier corrClassifier = null;
		Classifier testClassifier = null;
		try { //load first classifier
			ObjectInputStream ois =
				new ObjectInputStream (new BufferedInputStream(new FileInputStream (classifierFile.value)));
			
			classifier = (Classifier) ois.readObject();
			ois.close();
		} catch (Exception e) {
			throw new IllegalArgumentException("Problem loading classifier from file " + classifierFile.value +
							   ": " + e.getMessage());
		}
		try { //load second clasifier
			ObjectInputStream ois =
				new ObjectInputStream (new BufferedInputStream(new FileInputStream (corrClassifierFile.value)));
			
			corrClassifier = (Classifier) ois.readObject();
			ois.close();
		} catch (Exception e) {
			throw new IllegalArgumentException("Problem loading classifier from file " + corrClassifierFile.value +
							   ": " + e.getMessage());
		}

/*		try { //load test clasifier
			ObjectInputStream ois =
				new ObjectInputStream (new BufferedInputStream(new FileInputStream (testClassifierFile.value)));
			
			testClassifier = (Classifier) ois.readObject();
			ois.close();
		} catch (Exception e) {
			throw new IllegalArgumentException("Problem loading classifier from file " + testClassifierFile.value +
							   ": " + e.getMessage());
		}*/

		// Read instances from the file
		Reader fileReader;
		if (inputFile.value.toString().equals ("-")) {
		    fileReader = new InputStreamReader (System.in);
		}
		else {
			fileReader = new InputStreamReader(new FileInputStream(inputFile.value), encoding.value);
		}
		Reader fileReaderCorr; 
		if (inputFile.value.toString().equals ("-")) {
		    fileReaderCorr = new InputStreamReader (System.in);
		}
		else {
			fileReaderCorr = new InputStreamReader(new FileInputStream(corrInstanceFile.value), encoding.value);
		}

		Iterator<Instance> csvIterator = 
			new CsvIterator (fileReader, Pattern.compile(lineRegex.value),
			dataOption.value, 0, nameOption.value);
		Iterator<Instance> iterator = 
			classifier.getInstancePipe().newIteratorFrom(csvIterator);
		Iterator<Instance> corrIterator = 
			new CsvIterator (fileReaderCorr, Pattern.compile(lineRegex.value),
			dataOption.value, 0, nameOption.value);

		// Write classifications to the output file
		PrintStream out = null;

		if (outputFile.value.toString().equals ("-")) {
			out = System.out;
		}
		else {
			out = new PrintStream(outputFile.value, encoding.value);
		}
		
		classifier.getInstancePipe().getDataAlphabet().stopGrowth();
		classifier.getInstancePipe().getTargetAlphabet().stopGrowth();
		corrClassifier.getInstancePipe().getDataAlphabet().stopGrowth();
		corrClassifier.getInstancePipe().getTargetAlphabet().stopGrowth();

		ArrayList<String> labels = readOutputFile(labelFile.value); //get labels
		ListIterator labelIter = labels.listIterator();
		//process throught all instances
		while (iterator.hasNext() && corrIterator.hasNext()) { 
			Instance instance = iterator.next();
			Instance corrInstance = corrIterator.next(); 
			String origLabelStr = null;
			Label origLabel = null;


			//get the original (possibly wrong) labels
			if(labelIter.hasNext()) {
				origLabelStr = labelIter.next().toString();	
				origLabel = classifier.getLabelAlphabet().lookupLabel(origLabelStr);
			}
			else {
				System.out.println("Out of labels");
			}
			Labeling labs = classifier.classify(instance).getLabeling();
			//create instance from string data for main classifier
		/*	String labStrData = origLabelStr + "corrAspect " + corrInstance.getData();		
			Instance newInstance = corrClassifier.getInstancePipe().instancesFrom(new Instance(labStrData, null, null, null))[0];
			Labeling corrLabs = corrClassifier.classify(newInstance).getLabeling(); //classifier for second part of model*/

			double bestValue = 0;
			String bestLabelStr = null;
			Label bestLabel = null;
			//iterate through all labels, choose most likely correction
			for(int i=0; i < classifier.getLabelAlphabet().size(); i++) { 
				Label l = labs.getLabelAtRank(i);
				//Add aspect lable as feature 
//				String labStrData2 = l.toString() + "corrAspect " + corrInstance.getData();	 //use this for generative

				String labStrData = origLabelStr + "corrAspect " + corrInstance.getData();		
				//Send the new string instance throught the 2nd classifier's pipe, then get the labeling from classifying it
				Instance newInstance = corrClassifier.getInstancePipe().instancesFrom(new Instance(labStrData, null, null, null))[0];
//				Instance newInstance2 = testClassifier.getInstancePipe().instancesFrom(new Instance(labStrData2, null, null, null))[0]; //testing
				Labeling corrLabs = corrClassifier.classify(newInstance).getLabeling(); //classifier for second part of model
		//		Labeling testLabs = testClassifier.classify(newInstance2).getLabeling(); //classifier for second part of model
				double m = 1.0;
				if(l.toString().equals(origLabel.toString())) {
					m = 1.0;
				}
//				double testValue = 0.5 * b * testLabs.value(origLabel) * labs.value(l);
				double tempValue = m * corrLabs.value(l);
//				double tempValue = testValue + (m*corrLabs.value(l));
			//	out.println(corrLabs.value(l));
			//	out.println(labs.value(l));
				if(tempValue > bestValue) {
					bestValue = tempValue;
					bestLabel = l;
					bestLabelStr = l.toString();
				}
			}
	/*		if(!bestLabelStr.equals(origLabelStr)) {
				System.out.println(labs.value(origLabel) + " " + labs.value(bestLabel) + " " + corrLabs.value(origLabel) + " " + bestValue);
			}*/

/*			String newStrData = bestLabel.toString() + "corrAspect " + strInstance.getData();	
			Instance newInstance = corrClassifier.getInstancePipe().instancesFrom(new Instance(newStrData, null, null, null))[0];
			Labeling corrLabs = corrClassifier.classify(newInstance).getLabeling(); //classifier for second part of model
			if(origLabel != null && (bestValue - (corrLabs.value(origLabel) * labs.value(origLabel)) < THRESHOLD)) {
				out.println(origLabel.toString());
			}
			else {
				out.println(bestLabelStr);
			} */
			out.println(bestLabelStr);
		}
		if (! outputFile.value.toString().equals ("-")) {
			out.close();
		}
	}
}

    

