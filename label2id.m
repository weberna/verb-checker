function labIds = label2id(Y)
% Convert target vector containing textual labels to numerical ids
%
% @params:
%      Y - n by t cell array, where Y(i,j) contains the corresponding label for the ith sample of the jth task
%
%  @ret:
%     n by t matrix, where i,j contains the corresponding label id for the ith sample of the jth task
%
% Note to use in malsar convert make cell array {labIds(:, 1), labIds(:, 2) ...}


labelMap = containers.Map();
labIds = zeros(size(Y, 1), size(Y, 2));
id = 1;
for i = 1:size(Y,2) 
    tlabels = Y(:, i); %labels for a specific task 
    for j=1:size(tlabels,1)
        label = (cell2mat(tlabels(j)));
        if isKey(labelMap, label)  
            labIds(j,i) = labelMap(label);
        else
            labelMap(label) = id;
            labIds(j,i) = labelMap(label);
            id = id + 1;
        end
    end
end

