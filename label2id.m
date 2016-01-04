function [labIds labelMap] = label2id(Y)
% Convert target vector containing textual labels to a vector containing the corresponding unique numerical ids for the labels
%
% @params:
%      Y - n by t cell array, where Y{i}(j, 1) contains the corresponding label for the jth sample of the ith task
%       (each task has seperate label set)
%
%  @ret:
%     n by t cellarray labIds - where labIds{i}(j,1) contains the corresponding label id for the jth sample of the ith task
%     containers.Map labelMap - maps label name to label id
%


labelMap = containers.Map();
labIds = {};
id = 1;
for i = 1:size(Y,2) 
    tlabels = Y{i}(:, 1); %labels for a specific task 
    for j=1:size(tlabels,1)
        label = (cell2mat(tlabels(j)));
        if isKey(labelMap, label)  
            labIds{i}(j,1) = labelMap(label);
        else %new label, add to map
            labelMap(label) = id;
            labIds{i}(j,1) = labelMap(label);
            id = id + 1;
        end
    end
end


