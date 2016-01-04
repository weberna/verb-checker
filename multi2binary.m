function [bX bY] = multi2binary(X, Y, sub_amounts)
%Convert a set of data with multi class labels to 
%a set of data with labels of value -1 or 1 for binary 
%classification
%Use subsampling to take care of unbalanced distribution of class labels
%Params:
% t cell array X - each cell contains a data matrix for a certain task 
% (we subsample for each class using data only from the task it belongs to)
% t cell array Y - each cell contains the label vector for the corresponding task and sample in mX
% sub_amounts - a map from class label to doubles, value gives how much to subsample negative instances for that label
% Returns:
%   cell array bX, bY - cell arrays were each cell contains the data or labels (a -1 or 1) for the ith class, 
% NOTE that the length of X should equal the length of Y
bX = {};
bY = {};
for i=1:length(X) %for all tasks
    labs = unique(Y{i});
    for j=1:length(labs) %for all labels in the task
        lab = labs(j);
        amount = sub_amounts(lab);
        [subX subY] = subsample(X{i}, Y{i}, lab, amount);
        bX = {bX{:} subX};
        bY = {bY{:} subY};
    end
end
end

    

