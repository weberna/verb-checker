function labels = labelData(W, instances, labelMap)
%Do a 1 vs all multiclass classification using the 
%binary classifiers in matrix W, where the ith column of W
%is a binary classifier for the the label that is mapped to 
%by i using the labelMap
% Params:
%   (matrix of n columns) W - the classifier weights
%   (matrix of s row)s instances - instance data to label
%   (map from integer -> label) - maps indices in W to name of class
labels = {};
for i=1:size(instances, 1)
    label = classify(W, instances(i, :), labelMap);
    labels = {labels{:} label};
end
end

%do a single 1 vs all classification
function label = classify(W, instance, labelMap)

scores = zeros(1, size(W, 2));
for i=1:size(W, 2)
    score = instance * W(:, i);
    scores(i) = scores(i) + score;
end
index = datasample(find(scores==max(scores)), 1); %if there is tie score, choose randomly


label = labelMap(index);
label = label{1};

end

