/* ***************************************************
	VChainClassifier
	A MaxEnt classifier for verb tense aspect
	modified from Mallet's Csv2Vectors 
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


public class VChainClassifier {
	
	private static Logger logger = MalletLogger.getLogger(VChainClassifier.class.getName());
		//only really need to use first 4 options
	static CommandOption.File inputFile =	new CommandOption.File
		(VChainClassifier.class, "instances", "FILE", true, null,
		 "The file containing instance data to be classified, one instance per line", null);

	static CommandOption.File outputFile = new CommandOption.File
		(VChainClassifier.class, "output", "FILE", true, new File("output"),
		 "Write predictions to this file; Using - indicates stdout.", null);

	static CommandOption.File classifierFile = new CommandOption.File
		(VChainClassifier.class, "classifier", "FILE", true, new File("classifier"),
		 "Use the pipe and alphabets from a previously created vectors file.\n" +
		 "   Allows the creation, for example, of a test set of vectors that are\n" +
		 "   compatible with a previously created set of training vectors", null);

	static CommandOption.File labelFile = new CommandOption.File
		(VChainClassifier.class, "origlabels", "FILE", true, new File("labels"),
		 "File containing the original labels, one per line", null); 
	
//The default regex assumes some name in the front (first group is name) seperate by space/comma, (second group is data)
	static CommandOption.String lineRegex = new CommandOption.String
		(VChainClassifier.class, "line-regex", "REGEX", true, "^(\\S*)[\\s,]*(.*)$",
		 "Regular expression containing regex-groups for label, name and data.", null);
	
	static CommandOption.Integer nameOption = new CommandOption.Integer
		(VChainClassifier.class, "name", "INTEGER", true, 1,  //group 1 is name
		 "The index of the group containing the instance name.\n" +
         "   Use 0 to indicate that the name field is not used.", null);

	static CommandOption.Integer dataOption = new CommandOption.Integer
		(VChainClassifier.class, "data", "INTEGER", true, 2,  //group 2 is data
		 "The index of the group containing the data.", null);

	static CommandOption.String encoding = new CommandOption.String
		(VChainClassifier.class, "encoding", "STRING", true, Charset.defaultCharset().displayName(),
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
		CommandOption.setSummary (VChainClassifier.class,
								  "A tool for classifying a stream of unlabeled instances");
		CommandOption.process (VChainClassifier.class, args);
		
		// Print some helpful messages for error cases
		if (args.length == 0) {
			CommandOption.getList(VChainClassifier.class).printUsage(false);
			System.exit (-1);
		}
		if (inputFile == null) {
			throw new IllegalArgumentException ("You must include `--input FILE ...' in order to specify a"+
								"file containing the instances, one per line.");
		}
		
	  // Read both classifiers from file
		Classifier classifier = null;
		try { //load first classifier
			ObjectInputStream ois =
				new ObjectInputStream (new BufferedInputStream(new FileInputStream (classifierFile.value)));
			
			classifier = (Classifier) ois.readObject();
			ois.close();
		} catch (Exception e) {
			throw new IllegalArgumentException("Problem loading classifier from file " + classifierFile.value +
							   ": " + e.getMessage());
		}
		// Read instances from the file
		Reader fileReader;
		if (inputFile.value.toString().equals ("-")) {
		    fileReader = new InputStreamReader (System.in);
		}
		else {
			fileReader = new InputStreamReader(new FileInputStream(inputFile.value), encoding.value);
		}
		Iterator<Instance> csvIterator = 
			new CsvIterator (fileReader, Pattern.compile(lineRegex.value),
			dataOption.value, 0, nameOption.value);
		Iterator<Instance> iterator = 
			classifier.getInstancePipe().newIteratorFrom(csvIterator);

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

//		classifier.print();
        System.out.println(classifier.getInstancePipe().getDataAlphabet().size());
		System.out.println(classifier.getInstancePipe().getTargetAlphabet().size());
		ArrayList<String> labels = readOutputFile(labelFile.value); //get labels
		ListIterator labelIter = labels.listIterator();
		//process throught all instances
		while(iterator.hasNext()) { 
			Instance instance = iterator.next();
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
			double bestValue = 0;
			String bestLabelStr = null;
			Label bestLabel = null;
			//iterate through all labels, choose most likely correction
			for(int i=0; i < classifier.getLabelAlphabet().size(); i++) { 
				Label l = labs.getLabelAtRank(i);
				double m = 1.0;
				if(l.toString().equals(origLabel.toString())) { //set threshold value
					m = 1.0;
				}

				double tempValue = m * labs.value(l);
				if(tempValue > bestValue) {
					bestValue = tempValue;
					bestLabel = l;
					bestLabelStr = l.toString();
				}
			}

			out.println(bestLabelStr);  
		}
		if (! outputFile.value.toString().equals ("-")) {
			out.close();
		}
//		MaxEnt a = (MaxEnt)corrClassifier;
//		a.printRank(new PrintWriter(System.out));
	}
}

    

