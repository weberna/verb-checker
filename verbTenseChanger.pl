#!/usr/bin/perl

#0 - Base Form
#1 - Past Simple
#2 - Past Participle
#3 - 3rd Person Singular
#4 - Present Participle
my $irrVerbFile = "/home/user/reu2015/programs/IrregularVerbs.txt";
my @verbList;
my $word = $ARGV[0];
my $inForm = $ARGV[1];
my $outForm = $ARGV[2];
verbChangeInit();
my $response = changeVerbForm($word, $inForm, $outForm);
#print $response."\n";
print $response;

sub verbChangeInit(){
	open IRVF, $irrVerbFile;
	@verbList=<IRVF>;
}

sub changeVerbForm(){
	my $verb =lc(shift);
	my $isTense = shift;
	my $reqTense =shift;
	my $irregLine = isIrregular($verb, $isTense);
	if($irregLine != -1){
		return getIrregular($irregLine, $reqTense);
	}
	else{
		return regularChangeVerbForm($verb, $isTense, $reqTense);
	}
}

sub regularChangeVerbForm(){
        my $verb =shift;
        my $isTense = shift;
        my $reqTense =shift;
	if($reqTense==2) {
		$reqTense = 1;
	}
	if($reqTense==0) {
		return $verb;
	}
	if(($isTense ==0) && ($reqTense==1)){
		return getPastForBase($verb);
	}
	if(($isTense ==0) && ($reqTense==3)){
		return getTSingleForBase($verb);
    }
	if(($isTense ==0) && ($reqTense==4)){
        return getPPForBase($verb);
    }
}

sub getPPForBase(){
        my $verb = shift;
        my @verbChars = split(//,$verb);
        my $verbLen = @verbChars;
        if(($verbChars[$verbLen -1] eq "e") && ($verbChars[$verLen -2] eq "i")){
                return substr($verb,0,$verbLen-2)."ying";
        }
	if($verbChars[$verbLen -1] eq "e"){
                return substr($verb,0,$verbLen-1)."ing";
	}
        return $verb."ing";
}

sub getTSingleForBase(){
        my $verb = shift;
        return $verb."s";
}


sub getPastForBase(){
	my $verb = shift;
	my @verbChars = split(//,$verb);
	my $verbLen = @verbChars;
	if($verbChars[$verbLen -1] eq "e"){
		return $verb."d";
	}
	else{
		return $verb."ed";
	}
}

sub getIrregular(){
	my $lineNos = shift;
	my $reqTense = shift;
	my @verbLine = split(/ /, $verbList[$lineNos]);
	return $verbLine[$reqTense];
}
 
sub isIrregular(){
	my $verb=shift;
	my $tense=shift;
	my $i;
	for($i=0;$i<@verbList;$i++){
		my $vline = $verbList[$i];
		my @verbLine = split(/ /,$vline);
		if($verbLine[$tense] eq lc($verb)){
			return $i;
		}
	}
	return -1;
}

1;


		
