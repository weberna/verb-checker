function featMat = inst2feat(inputcellarray, fThresh)
% Convert instance data (text feature vectors) to numerical feature vectors 
% 
% @params:
% (cellarray) inputcellarray - cell array where each cell contains a data instance,
% each data instance is a cell array (as a row vector) where each of its cells contain  
% some text feature for that instance (features are not necessarily ordered).
%
% (int) fThresh - the minimum amount of times a word should appear to be included in the feature vector
% 
% @returns:
%    matrix where ith row is feature vector for ith instance
%                                                                                         
%Based on code from: https://github.com/faridani/MatlabNLP                                                                                

pfeats = containers.Map(); %possible features

for i = 1:size(inputcellarray,1) %all instances
    instance = inputcellarray{i};
    for j=1:size(instance,2)
        word = (cell2mat(instance(j)));
        if isKey(pfeats, word)
           pfeats(word) = pfeats(word)+1;
        elseif (~strcmp(word,' ')) && (~strcmp(word,''))
            pfeats(word) = 1;
        end
    end
end

features = containers.Map();
posskeys = keys(pfeats);

for i=1:size(posskeys,2)
    if pfeats(posskeys{i})>=fThresh
        features(posskeys{i})=1;
    end
end
featkeys = keys(features);

outputMatrix = zeros(size(inputcellarray,1),length(featkeys));
for i = 1:size(inputcellarray,1)
    instance = inputcellarray{i};
    str = [];
    for j =1:size(instance,2)
        word = (cell2mat(instance(j)));
        str = [str ,' ',word];
    end
    outputMatrix(i,:) = term_count(str, featkeys);
end
featMat = outputMatrix;

end
