function [X FeatMap] = inst2feat(inputdata, opt)
%Function has two forms depending on what is passed in for opt:
%function [X FeatMap] = inst2feat(inputdata, fThresh), for use on training data when a new Feature Map needs to be created
%function [X FeatMap] = inst2feat(inputdata, FeatMap), for use on testing data when an old Feature Map needs to be used
% Convert instance data (text feature vectors) to numerical feature vectors across several tasks
% Since the mappings from text features to indices in the numerical feature vector must be consistent
% across all tasks, we must convert features from all t tasks all at once.
% Also Return back feature map, which gives the mappings of text feature -> index in feature array
% This map can be used to convert test data to the same type of numerical feature vector using this
% function and passing the map in for opt
%
% @params:
% (t dimensional cellarray) inputdata - cell array that contains a sample data cellarray for each task,
% each cell in ith cellarray contains a data instance for the ith task,
% each data instance itself is a cell array (as a row vector) where each of its cells contain  
% some text feature for that instance (features are not necessarily ordered).
%
% (int) fThresh - the minimum amount of times a word should appear to be included as a feature
% (containers.Map) FeatMap - a old feature map (maps features->index in feature vector) to generate numerical features from
% 
% @returns:
%    (t dimensional cellarray) X - Cell array that contains t ni by d matrices, where ni is the sample size for the 
%    ith task. The ith row of the jth matrix is the numerical feature vector corresponding 
%    the text features from the ith row of the sample data cellarray for the jth task (jth cell in inputdata)
%    (containers.Map) FeatMap - maps text feature names to indices in numerical feature vector
%                                                                                         
%Based on code from: https://github.com/faridani/MatlabNLP                                                                                

if isa(opt, 'double') %create features from scratch, opt==fThresh
    fThresh = opt;
    pfeats = containers.Map(); %possible features
    %build map of all encountered features (words)
    for t = 1:size(inputdata,2) 
        taskdata = inputdata{t}; %get instances for task t 
        for i = 1:size(taskdata,1) 
            instance = taskdata{i};
            for j = 1:size(instance,2)
                word = (cell2mat(instance(j)));
                if isKey(pfeats, word)
                   pfeats(word) = pfeats(word)+1;  %feature previously seen
                elseif (~strcmp(word,' ')) && (~strcmp(word,''))
                    pfeats(word) = 1; %add this as possible feature
                end
            end
        end
    end

    %Only use features that have been encountered at least fThresh times
    features = containers.Map();
    posskeys = keys(pfeats);
    for i=1:size(posskeys,2)
        if pfeats(posskeys{i})>=fThresh
            features(posskeys{i})=1;
        end
    end
    featkeys = keys(features);

elseif isa(opt, 'containers.Map') %create features from Feature Map, opt==FeatMap
    FeatMap = opt;
    featkeys = keys(FeatMap);
end 

%init matrices in X
X = {};
for t = 1:size(inputdata,2)
    taskdata = inputdata{t};
    X = {X{:} zeros(size(taskdata,1),length(featkeys))};
end
%put in values for X
for t = 1:size(inputdata,2)
    taskdata = inputdata{t};
    for i = 1:size(taskdata,1)
        instance = taskdata{i};
        str = [];
        for j = 1:size(instance,2)
            word = (cell2mat(instance(j)));
            str = [str ,' ',word];
        end
        X{t}(i,:) = term_count(str, featkeys);
    end
end

if isa(opt, 'double') %create featmap is opt==fThresh, else FeatMap is set as opt (still return it just for consistency)
    FeatMap=containers.Map(featkeys, 1:length(featkeys));
end
