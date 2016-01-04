function [X, Y] = readInstances(filename, t)
%
% Read in sample data from filename, each row of this file represents
% a sample
%
% t denotes how many tasks the sample data is for, and thus determines how many labels
% are on each sample. The first t entries in a row are labels (normally just use 1)
%
% @ret: Returns a cell array X and Y,
%
%       X is a n by d matrix, where n is the number of samples, d is the dimensionality of the data 
%       Y is a n by t matrix, where Y(i,j) contains the corresponding label for the ith sample of the jth task

fid = fopen(filename);
line = fgetl(fid);
Y = {};
X = {};
while ischar(line);
    datacell = textscan(line, '%s');
    labels = transpose(datacell{1}(1:t)); %get first n entries, transpose to row vector 
    feats = transpose(datacell{1}(t+1:size(datacell{1}, 1)));
    Y = [Y; labels]; 
    X = [X; {feats}];
    line = fgetl(fid);
end
fclose(fid);
end
    
    
    

