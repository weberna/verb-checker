import java.util.Iterator;
import java.util.logging.*;
import java.util.regex.*;
import java.io.*;
import java.nio.charset.Charset;

import cc.mallet.classify.*;
import cc.mallet.pipe.iterator.*;
import cc.mallet.types.*;
import cc.mallet.util.*;

/**
 * Command line tool for classifying a sequence of  
 *  instances directly from text input, without
 *  creating an instance list.
 *  <p>
 * 
 *  @author David Mimno
 *  @author Gregory Druck
 */

public class combinedClassify {

	private static Logger logger = MalletLogger.getLogger(combinedClassify.class.getName());

	static CommandOption.File inputFile =	new CommandOption.File
		(combinedClassify.class, "input", "FILE", true, null,
		 "The file containing data to be classified, one instance per line", null);

	static CommandOption.File outputFile = new CommandOption.File
		(combinedClassify.class, "output", "FILE", true, new File("output"),
		 "Write predictions to this file; Using - indicates stdout.", null);

	static CommandOption.String lineRegex = new CommandOption.String
		(combinedClassify.class, "line-regex", "REGEX", true, "^(\\S*)[\\s,]*(.*)$",
		 "Regular expression containing regex-groups for label, name and data.", null);
	
	static CommandOption.Integer nameOption = new CommandOption.Integer
		(combinedClassify.class, "name", "INTEGER", true, 1,
		 "The index of the group containing the instance name.\n" +
         "   Use 0 to indicate that the name field is not used.", null);

	static CommandOption.Integer dataOption = new CommandOption.Integer
		(combinedClassify.class, "data", "INTEGER", true, 2,
		 "The index of the group containing the data.", null);
	
	static CommandOption.File classifierFile = new CommandOption.File
		(combinedClassify.class, "classifier", "FILE", true, new File("classifier"),
		 "Use the pipe and alphabets from a previously created vectors file.\n" +
		 "   Allows the creation, for example, of a test set of vectors that are\n" +
		 "   compatible with a previously created set of training vectors", null);

	static CommandOption.String encoding = new CommandOption.String
		(combinedClassify.class, "encoding", "STRING", true, Charset.defaultCharset().displayName(),
		 "Character encoding for input file", null);

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
		
	  // Read classifier from file
		Classifier classifier = null;
		try {
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
		
		// gdruck@cs.umass.edu
		// Stop growth on the alphabets. If this is not done and new
		// features are added, the feature and classifier parameter
		// indices will not match.  
		classifier.getInstancePipe().getDataAlphabet().stopGrowth();
		classifier.getInstancePipe().getTargetAlphabet().stopGrowth();
		
		while (iterator.hasNext()) {
			Instance instance = iterator.next();
			
			Labeling labs = 
				classifier.classify(instance).getLabeling();
			for(int i=0; i < classifier.getLabelAlphabet().size(); i++) {
				String lab_name = labs.getLabelAtRank(i).toString();
				double val = labs.getValueAtRank(i);
				out.println(lab_name + " " + val);
			}
				out.println("------------------------------");
		}
		if (! outputFile.value.toString().equals ("-")) {
			out.close();
		}
	}
}

    

