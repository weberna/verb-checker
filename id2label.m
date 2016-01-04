function labels = id2label(data, featMap, filename)
%  Convert a vector of label ids
%  to a cell array of string labels
%  label to id mappings are determined by
%  featMap
%  Also optionally print these results to a file if filename is passed in
%  @param:
%       data - column vector of integer ids
%       containers.Map() featMap - map from string labels to integer ids
%       filename - optional parameter, names file to print result to
%  @ret:
%       labels - cell array of respective string labels 

rmap = reverseMap(featMap);
labels = {};
for i=data'
    if i==0 
        i=1;
        end

    lab = rmap(i);
    lab = lab{1};
    labels = {labels{:} lab};
end

if nargin > 2
    file = fopen(filename, 'w');
    for i=labels 
        fprintf(file, '%s\n', i{1});
    end
end
    
